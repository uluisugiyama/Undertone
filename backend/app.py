from flask import Flask, jsonify, request, session, send_from_directory
from flask_migrate import Migrate
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from models import db, Song, User, UserLibrary, UserRating, PersonalTrending, SongTag, SearchLog
from music_standards import is_fast_tempo, is_heavy, get_parent_genre
import os
import random
import math
from datetime import datetime
import google.generativeai as genai
import json
from dotenv import load_dotenv
from lastfm_client import LastFMClient

load_dotenv() # Load variables from .env


app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.secret_key = 'undertone-secret-key-poc' # Change this in production
CORS(app, supports_credentials=True)

LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def calculate_mainstream_score(listeners):
    if listeners <= 0:
        return 0
    # Logarithmic scale: 10M listeners -> 100, 1M -> 86, 100k -> 71, 10k -> 57, 1k -> 43, 100 -> 28, 10 -> 14
    score = int(math.log10(listeners) * 14.3)
    return min(100, max(0, score))

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

# --- EXTERNAL API ENDPOINTS ---

@app.route('/search/external')
def search_external():
    query = request.args.get('q')
    if not query:
        return jsonify([])
    
    client = LastFMClient(LASTFM_API_KEY)
    results = client.search_track(query)
    return jsonify(results)

@app.route('/song/import', methods=['POST'])
def import_song():
    data = request.json
    artist = data.get('artist')
    title = data.get('title')
    
    if not artist or not title:
        return jsonify({"error": "Artist and Title required"}), 400

    # Check if exists
    existing = Song.query.filter_by(artist=artist, title=title).first()
    if existing:
        return jsonify(existing.to_dict()), 200
        
    client = LastFMClient(LASTFM_API_KEY)
    info = client.get_track_info(artist, title)
    tags = client.get_track_tags(artist, title)
    
    # Create with enrichment
    new_song = Song(
        artist=artist,
        title=title,
        genre=tags[0]['name'].title() if tags else "Unknown",
        bpm=random.randint(70, 160),
        decibel_peak=round(random.uniform(-18.0, -8.0), 1),
        year=2024,
        mainstream_score=calculate_mainstream_score(info.get('listeners', 0))
    )
    db.session.add(new_song)
    db.session.flush()
    
    from models import SongTag
    for t in tags:
        new_tag = SongTag(song_id=new_song.id, tag_name=t['name'], count=t['count'])
        db.session.add(new_tag)
        
    db.session.commit()
    return jsonify(new_song.to_dict()), 201

@app.route('/admin/contradictions')
def get_contradictions():
    flagged = Song.query.filter_by(is_contradictory=True).all()
    return jsonify([s.to_dict() for s in flagged])

# --- AUTH ENDPOINTS ---

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "User already exists"}), 400
    
    hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
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
    search_log_id = data.get('search_log_id')
    
    if UserLibrary.query.filter_by(user_id=session['user_id'], song_id=song_id).first():
        return jsonify({"message": "Song already in library"}), 200
    
    entry = UserLibrary(user_id=session['user_id'], song_id=song_id)
    db.session.add(entry)

    # Phase 6: Search Success Logic
    if search_log_id:
        log = SearchLog.query.get(search_log_id)
        if log:
            log.selected_song_id = song_id
            db.session.add(log)
    
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

    # Phase 7: Shared Taste - Refine tags based on user comment
    if comment and len(comment) > 5:
        refine_prompt = f"""
        Analyze this user review for a song: "{comment}"
        Identify 1-3 musical tags or moods mentioned (e.g., 'chill', 'energetic', 'dark', 'bass-heavy').
        Return ONLY a JSON list of strings: ["tag1", "tag2"]
        """
        try:
            refine_response = model.generate_content(refine_prompt)
            clean_tags = refine_response.text.replace('```json', '').replace('```', '').strip()
            new_tags = json.loads(clean_tags)
            
            for t_name in new_tags:
                t_name = t_name.lower().strip()
                tag = SongTag.query.filter_by(song_id=song_id, tag_name=t_name).first()
                if tag:
                    tag.count += 1
                else:
                    tag = SongTag(song_id=song_id, tag_name=t_name, count=1)
                    db.session.add(tag)
            db.session.commit()
        except Exception as e:
            print(f"Tag refinement error: {e}")

    return jsonify({"message": "Rating saved and metadata refined"}), 201

@app.route('/search/intent')
def search_intent():
    intent = request.args.get('intent', '')
    if not intent:
        return jsonify([])

    # 1. Use Gemini to parse intent into structured filters
    prompt = f"""
    Analyze the following music search intent: "{intent}"
    Return a JSON object with:
    - artist (string or null)
    - genres (list of strings)
    - mood (string or null)
    - year_start (int or null)
    - year_end (int or null)
    - tempo (string: 'slow', 'medium', 'fast' or null)
    - keywords (list of strings for search)
    - external_search_query (A string optimized for searching Last.fm if the local DB might not have this, otherwise null)
    Return ONLY JSON.
    """
    
    try:
        response = model.generate_content(prompt)
        # Clean potential markdown from response
        clean_response = response.text.replace('```json', '').replace('```', '').strip()
        parsed_intent = json.loads(clean_response)
    except Exception as e:
        print(f"Gemini error: {e}")
        # Fallback to empty intent if Gemini fails
        parsed_intent = {"artist": None, "genres": [], "mood": None, "year_start": None, "year_end": None, "tempo": None, "keywords": [], "external_search_query": None}

    # Phase 6: Log Intent
    new_log = SearchLog(
        user_id=session.get('user_id'),
        intent=intent,
        mode=request.args.get('mode', 'all')
    )
    db.session.add(new_log)
    db.session.commit()
    
    query = Song.query # Initialize query before applying filters

    # Apply Mode Filter (Mainstream vs Niche)
    mode = request.args.get('mode', 'all')
    if mode == 'mainstream':
        query = query.filter(Song.mainstream_score >= 70)
    elif mode == 'niche':
        query = query.filter(Song.mainstream_score < 70)

    # Apply Filters from parsed intent
    if parsed_intent.get('artist'):
        query = query.filter(Song.artist.ilike(f"%{parsed_intent['artist']}%"))
    
    if parsed_intent.get('year_start'):
        query = query.filter(Song.year >= parsed_intent['year_start'])
    if parsed_intent.get('year_end'):
        query = query.filter(Song.year <= parsed_intent['year_end'])

    if parsed_intent.get('tempo') == 'slow':
        query = query.filter(Song.bpm < 100)
    elif parsed_intent.get('tempo') == 'medium':
        query = query.filter(Song.bpm >= 100, Song.bpm <= 125)
    elif parsed_intent.get('tempo') == 'fast':
        query = query.filter(Song.bpm > 125)

    # Keywords (Artist, Title, Genre, Tags)
    keywords = parsed_intent.get('keywords', [])
    for kw in keywords:
        query = query.filter(or_(
            Song.artist.ilike(f"%{kw}%"),
            Song.title.ilike(f"%{kw}%"),
            Song.genre.ilike(f"%{kw}%"),
            Song.tags.any(SongTag.tag_name.ilike(f"%{kw}%"))
        ))

    songs = query.limit(50).all()
    all_songs = [song.to_dict() for song in songs]
    
    # 2. Collaborative API Logic: If results are low, search Last.fm using Gemini's query
    ext_query = parsed_intent.get('external_search_query')
    if (len(all_songs) < 5 or "drake" in intent.lower()) and ext_query:
        client = LastFMClient(LASTFM_API_KEY)
        external_results = client.search_track(ext_query, limit=10)
        
        # Merge external results that aren't already in all_songs
        existing_keys = set(f"{s['artist'].lower()}|{s['title'].lower()}" for s in all_songs)
        
        for res in external_results:
            key = f"{res['artist'].lower()}|{res['title'].lower()}"
            if key not in existing_keys:
                all_songs.append({
                    "artist": res['artist'],
                    "title": res['title'],
                    "ai_recommendation": True, # Treat as AI/External rec for UI
                    "genre": "External Discovery",
                    "bpm": "Unknown",
                    "decibel_peak": "Unknown"
                })
                existing_keys.add(key)

    return jsonify({
        "songs": all_songs,
        "search_log_id": new_log.id
    })

@app.route('/songs/explore')
def explore_songs():
    # Get 30 random songs for the 'Explore' section
    songs = Song.query.order_by(db.func.random()).limit(30).all()
    return jsonify([s.to_dict() for s in songs])

@app.route('/recommendations')
def get_recommendations():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session['user_id']
    
    # 1. Fetch songs the user has rated highly (4 or 5 stars)
    high_ratings = UserRating.query.filter(UserRating.user_id == user_id, UserRating.rating >= 4).all()
    if not high_ratings:
        return jsonify([]) # No data to base recommendations on
    
    liked_song_ids = [r.song_id for r in high_ratings]
    
    # 2. Identify frequent tags and GENRES among highly rated songs
    tag_counts = {}
    genre_counts = {}
    for song_id in liked_song_ids:
        song = Song.query.get(song_id)
        genre_counts[song.genre] = genre_counts.get(song.genre, 0) + 1
        for t in song.tags:
            tag_counts[t.tag_name] = tag_counts.get(t.tag_name, 0) + 1
            
    # Get top 5 tags and top 1 genre
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_tag_names = [t[0] for t in sorted_tags]
    
    sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
    fav_genre = sorted_genres[0][0] if sorted_genres else None
    
    # 3. Find other songs that share tags OR the favorite genre
    user_library_ids = [entry.song_id for entry in UserLibrary.query.filter_by(user_id=user_id).all()]
    potential_matches = Song.query.filter(Song.id.notin_(user_library_ids)).all()
    
    recs = []
    for song in potential_matches:
        song_tags = [t.tag_name for t in song.tags]
        tag_overlap = set(top_tag_names).intersection(set(song_tags))
        
        score = len(tag_overlap)
        if song.genre == fav_genre:
            score += 2 # Genre match counts for a lot!
            
        if score > 0:
            song_dict = song.to_dict()
            song_dict['match_score'] = score
            recs.append(song_dict)
            
    # Sort by score and mainstream score
    recs = sorted(recs, key=lambda x: (x['match_score'], x['mainstream_score']), reverse=True)
    
    return jsonify(recs[:10])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
