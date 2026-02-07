from flask import Flask, jsonify, request, session, send_from_directory
from flask_migrate import Migrate
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Song, User, UserLibrary, UserRating, PersonalTrending
from music_standards import is_fast_tempo, is_heavy, get_parent_genre
import os
from datetime import datetime

app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.secret_key = 'undertone-secret-key-poc' # Change this in production
CORS(app, supports_credentials=True)

@app.route('/gui')
def gui_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/gui/profile')
def gui_profile():
    return send_from_directory(app.static_folder, 'profile.html')

# Catch-all for other static files in the frontend directory
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# Basic SQLite configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'undertone.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

@app.route('/')
def hello_world():
    return jsonify({"message": "Hello World! Undertone API is running."})

# --- AUTH ENDPOINTS ---

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "User already exists"}), 400
    
    hashed_pw = generate_password_hash(password)
    new_user = User(username=username, password_hash=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        return jsonify({"message": "Logged in successfully", "username": user.username}), 200
    
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return jsonify({"message": "Logged out successfully"}), 200

@app.route('/me')
def get_me():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({"logged_in": True, "username": user.username}), 200
    return jsonify({"logged_in": False}), 200

# --- LIBRARY & RATING ENDPOINTS ---

@app.route('/library/save', methods=['POST'])
def save_to_library():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    song_id = data.get('song_id')
    
    if UserLibrary.query.filter_by(user_id=session['user_id'], song_id=song_id).first():
        return jsonify({"message": "Song already in library"}), 200
    
    entry = UserLibrary(user_id=session['user_id'], song_id=song_id)
    db.session.add(entry)
    
    # Track engagement for Personal Trending
    trending = PersonalTrending.query.filter_by(user_id=session['user_id'], song_id=song_id).first()
    if trending:
        trending.engagement_count += 1
        trending.last_engaged_at = datetime.utcnow()
    else:
        trending = PersonalTrending(user_id=session['user_id'], song_id=song_id)
        db.session.add(trending)
        
    db.session.commit()
    return jsonify({"message": "Song saved to library"}), 201

@app.route('/library')
def get_library():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    library_entries = UserLibrary.query.filter_by(user_id=session['user_id']).all()
    songs = [Song.query.get(entry.song_id).to_dict() for entry in library_entries]
    return jsonify(songs)

@app.route('/song/rate', methods=['POST'])
def rate_song():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    song_id = data.get('song_id')
    rating = data.get('rating')
    comment = data.get('comment')
    
    existing = UserRating.query.filter_by(user_id=session['user_id'], song_id=song_id).first()
    if existing:
        existing.rating = rating
        existing.comment = comment
        existing.rated_at = datetime.utcnow()
    else:
        new_rating = UserRating(user_id=session['user_id'], song_id=song_id, rating=rating, comment=comment)
        db.session.add(new_rating)
    
    db.session.commit()
    return jsonify({"message": "Rating saved"}), 201

@app.route('/search/objective')
def search_objective():
    # Get query parameters
    genre_query = request.args.get('genre')
    tempo_query = request.args.get('tempo') # 'fast', 'slow', or 'any'
    loudness_query = request.args.get('loudness') # 'heavy', 'mellow', or 'any'

    query = Song.query

    if genre_query:
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
