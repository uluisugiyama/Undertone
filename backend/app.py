from flask import Flask, jsonify, request
from flask_migrate import Migrate
from flask_cors import CORS
from models import db, Song
from music_standards import is_fast_tempo, is_heavy, get_parent_genre
import os

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# Basic SQLite configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'undertone.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

@app.route('/')
def hello_world():
    return jsonify({"message": "Hello World! Undertone API is running."})

@app.route('/search/objective')
def search_objective():
    # Get query parameters
    genre_query = request.args.get('genre')
    tempo_query = request.args.get('tempo') # 'fast', 'slow', or 'any'
    loudness_query = request.args.get('loudness') # 'heavy', 'mellow', or 'any'

    query = Song.query

    if genre_query:
        # Match objective genre or parent taxonomy
        # This is a bit simplistic for a first pass
        # We find songs where the genre matches or maps to the query
        query = query.filter((Song.genre == genre_query))

    results = query.all()

    # Apply manual filters for tempo and loudness based on music_standards
    filtered_results = []
    for song in results:
        match_tempo = True
        if tempo_query == 'fast':
            match_tempo = is_fast_tempo(song.bpm)
        elif tempo_query == 'slow':
            match_tempo = not is_fast_tempo(song.bpm)

        match_loudness = True
        if loudness_query == 'heavy':
            match_loudness = is_heavy(song.decibel_peak)
        elif loudness_query == 'mellow':
            match_loudness = not is_heavy(song.decibel_peak)

        if match_tempo and match_loudness:
            filtered_results.append(song.to_dict())

    return jsonify(filtered_results)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
