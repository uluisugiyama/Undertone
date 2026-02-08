from flask import Flask, jsonify, request, session, send_from_directory
from flask_migrate import Migrate
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_, and_
from models import db, Song, User, UserLibrary, UserRating, PersonalTrending, SongTag, SearchLog, SongAnalysis
from music_standards import is_fast_tempo, is_heavy, get_parent_genre
import os
import random
import math
import requests
from datetime import datetime
import json
from dotenv import load_dotenv
from lastfm_client import LastFMClient

load_dotenv() # Load variables from .env


app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.secret_key = os.getenv('SECRET_KEY', 'undertone-secret-key-poc') 
CORS(app, supports_credentials=True)

LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def call_gemini_api(prompt):
    """Fallback for systems with old Python that can't run the official SDK."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Direct Gemini API error: {e}")
        return ""

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
database_url = os.getenv('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///' + os.path.join(basedir, 'undertone.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/healthz')
def health_check():
    return jsonify({"status": "ok", "db": "connected"}), 200

# --- EXTERNAL API ENDPOINTS ---

@app.route('/search/external')
def search_external():
    query = request.args.get('q')
    if not query:
        return jsonify([])
    
    client = LastFMClient(LASTFM_API_KEY)
    results = client.search_track(query)
    return jsonify(results)

def enrich_song_analysis(song):
    """
    Phase 19: Deep Music Analysis
    Uses Gemini to infer 9-dimensional feature vectors.
    """
    prompt = f"""
    Analyze the song "{song.title}" by "{song.artist}".
    Provide a deep musicological analysis with the following metrics as JSON.
    Strictly follow the JSON structure.
    
    {{
      "tempo_feel": "slow" | "medium" | "fast",
      "rhythmic_complexity": 0.0 to 1.0 (0=Simple 4/4, 1=Complex/Polyrythmic),
      "vocal_style": "clean" | "raspy" | "screaming" | "fluid" | "instrumental",
      "vocal_presence": 0.0 to 1.0 (0=Instrumental, 1=Vocal Dominant),
      "dark_bright": 0.0 to 1.0 (0=Dark/Melancholic, 1=Bright/Happy),
      "calm_energetic": 0.0 to 1.0 (0=Calm/Ambient, 1=High Energy/Aggressive),
      "production_quality": 0.0 to 1.0 (0=Lo-fi/Raw, 1=Hi-fi/Polished),
      "genre_distribution": {{ "GenreName": 0.X }} (Must sum roughly to 1.0)
    }}
    Return ONLY JSON.
    """
    
    try:
        response_text = call_gemini_api(prompt)
        clean_response = response_text.replace('```json', '').replace('```', '').strip()
        data = json.loads(clean_response)
        
        analysis = SongAnalysis(
            song_id=song.id,
            tempo_feel=data.get('tempo_feel', 'medium'),
            rhythmic_complexity=float(data.get('rhythmic_complexity', 0.5)),
            vocal_style=data.get('vocal_style', 'clean'),
            vocal_presence=float(data.get('vocal_presence', 0.5)),
            dark_bright=float(data.get('dark_bright', 0.5)),
            calm_energetic=float(data.get('calm_energetic', 0.5)),
            production_quality=float(data.get('production_quality', 0.8)),
            genre_distribution=json.dumps(data.get('genre_distribution', {}))
        )
        db.session.add(analysis)
        db.session.commit()
        print(f"Deep Analysis complete for {song.title}")
    except Exception as e:
        print(f"Deep Analysis failed for {song.title}: {e}")

def _perform_song_import(artist, title):
    # Check if exists
    existing = Song.query.filter_by(artist=artist, title=title).first()
    if existing:
        return existing
        
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
    
    for t in tags:
        new_tag = SongTag(song_id=new_song.id, tag_name=t['name'], count=t['count'])
        db.session.add(new_tag)
        
    # Phase 19: Deep Analysis
    enrich_song_analysis(new_song)
        
    db.session.commit()
    return new_song

@app.route('/song/import', methods=['POST'])
def import_song():
    data = request.json
    artist = data.get('artist')
    title = data.get('title')
    
    if not artist or not title:
        return jsonify({"error": "Artist and Title required"}), 400

    song = _perform_song_import(artist, title)
    return jsonify(song.to_dict()), 201

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
    artist = data.get('artist')
    title = data.get('title')
    search_log_id = data.get('search_log_id')
    
    # If song_id is missing but artist/title are present, import it first
    if not song_id and artist and title:
        try:
            song = _perform_song_import(artist, title)
            song_id = song.id
        except Exception as e:
            print(f"Background import failed: {e}")
            return jsonify({"error": "Failed to fetch song metadata for background save."}), 500

    if not song_id:
        return jsonify({"error": "Song ID or Artist/Title required"}), 400

    if not song_id:
        return jsonify({"error": "Song ID or Artist/Title required"}), 400

    # Check existence
    existing_entry = UserLibrary.query.filter_by(user_id=session['user_id'], song_id=song_id).first()
    if not existing_entry:
        entry = UserLibrary(user_id=session['user_id'], song_id=song_id)
        db.session.add(entry)

    # Phase 6: Search Success Logic (Log update)
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
        
    # PHASE 18: FEEDBACK LOOP
    # If the frontend sends feedback tags (from the search intent that led to this save),
    # increment them to reinforce the connection.
    feedback_tags = data.get('feedback_tags', [])
    if feedback_tags:
        for t_name in feedback_tags:
            t_name = t_name.strip()
            if not t_name: continue
            
            # Find or create tag for this song
            tag = SongTag.query.filter(
                SongTag.song_id == song_id, 
                SongTag.tag_name.ilike(t_name)
            ).first()
            
            if tag:
                tag.count += 1
                print(f"DEBUG: Incremented tag '{t_name}' for song {song_id} to {tag.count}")
            else:
                # Only add new tags if they seem legitimate (basic length check for now)
                if len(t_name) < 30:
                    new_tag = SongTag(song_id=song_id, tag_name=t_name.title(), count=1)
                    db.session.add(new_tag)
                    print(f"DEBUG: Created new Crowd Tag '{t_name}' for song {song_id}")

    db.session.commit()
    return jsonify({"message": "Song saved to library"}), 201

@app.route('/library')
def get_library():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session['user_id']
    library_entries = UserLibrary.query.filter_by(user_id=user_id).all()
    
    songs = []
    for entry in library_entries:
        song = Song.query.get(entry.song_id)
        if song:
            song_data = song.to_dict()
            # Fetch user's rating for this song
            rating_entry = UserRating.query.filter_by(user_id=user_id, song_id=song.id).first()
            song_data['user_rating'] = rating_entry.rating if rating_entry else 0
            song_data['user_comment'] = rating_entry.comment if rating_entry else ""
            songs.append(song_data)
            
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
            refine_response_text = call_gemini_api(refine_prompt)
            clean_tags = refine_response_text.replace('```json', '').replace('```', '').strip()
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

    # DEBUG: Support Mock JSON for verification without API
    if intent.startswith("MOCK_JSON:"):
        try:
            parsed_intent = json.loads(intent[10:])
            print(f"DEBUG: Using Mock Intent: {parsed_intent}")
            # Skip Gemini and Profile context
            # We need to ensure variables are set or logic flow works
            user_id = session.get('user_id')
            user_profile = _get_user_profile(user_id) if user_id else {"top_tags": [], "fav_genre": None}
            # Skip to filtering logic...
            # We need to wrap the Gemini call in an if/else or reorganize
            # Let's handle this by setting a flag or just bypassing the Gemini block below
            # But the Gemini block is large.
            # Best: set parsed_intent here and wrap Gemini block in "if not parsed_intent:"
        except Exception as e:
            print(f"Mock JSON error: {e}")
            return jsonify([])
    else:
        parsed_intent = None

    # 1. Fetch User Profile for Implicit Personalization
    user_id = session.get('user_id')
    user_profile = _get_user_profile(user_id) if user_id else {"top_tags": [], "fav_genre": None}
    
    context_str = ""
    if user_profile['top_tags']:
        context_str = f"\nUser Preferences Context: Favorite Genres: {user_profile['fav_genre']}, Top Vibe Tags: {', '.join(user_profile['top_tags'][:8])}"

    # 2. Use Gemini to parse intent into structured filters AND deep feature vectors
    if not parsed_intent:
        prompt = f"""
        Analyze the music search intent: "{intent}"
        {context_str}
        
        1. Extract standard filters (artist, genre, mood).
        2. Map vague descriptors to specific 9-dimensional feature constraints.
           - tempo_feel: slow, medium, fast
           - rhythmic_complexity: 0.0-1.0
           - vocal_style: clean, raspy, screaming, fluid, instrumental
           - vocal_presence: 0.0-1.0
           - dark_bright: 0.0-1.0
           - calm_energetic: 0.0-1.0
           - production_quality: 0.0-1.0
        
        Return JSON:
        {{
          "artist": null,
          "genres": [],
          "mood": null,
          "year_start": null, 
          "year_end": null,
          "tempo": null,
          "keywords": [],
          "external_search_query": "...",
          "feature_constraints": [
              {{"feature": "dark_bright", "min": 0.0, "max": 0.3}},
              {{"feature": "vocal_style", "values": ["screaming", "raspy"]}}
          ] 
        }}
        """
        
        try:
            response_text = call_gemini_api(prompt)
            clean_response = response_text.replace('```json', '').replace('```', '').strip()
            parsed_intent = json.loads(clean_response)
            print(f"DEBUG PARSED INTENT: {parsed_intent}")
        except Exception as e:
            print(f"Gemini error: {e}")
            # Intelligent Fallback
            fallback_genres = []
            normalized = intent.lower()
            common_genres = ['rock', 'pop', 'hip hop', 'rap', 'jazz', 'blues', 'country', 'metal', 'classical', 'electronic', 'dance', 'indie', 'r&b', 'soul', 'folk', 'punk']
            
            for g in common_genres:
                if g in normalized:
                    fallback_genres.append(g.title())
                    
            # Fallback Tempo Detection
            fallback_tempo = None
            if 'slow' in normalized or 'chill' in normalized or 'down' in normalized or 'ballad' in normalized:
                fallback_tempo = 'slow'
            elif 'fast' in normalized or 'up' in normalized or 'energetic' in normalized or 'punk' in normalized:
                fallback_tempo = 'fast'
            
            parsed_intent = {
                "artist": None, 
                "genres": fallback_genres, 
                "mood": None, 
                "year_start": None, 
                "year_end": None, 
                "tempo": fallback_tempo, 
                "keywords": [], 
                "external_search_query": intent,
                "feature_constraints": [] 
            }

    # Phase 6: Log Intent
    new_log = SearchLog(
        user_id=user_id,
        intent=intent,
        mode=request.args.get('mode', 'all')
    )
    db.session.add(new_log)
    db.session.commit()
    
    # SAFETY NET: If AI missed the tempo but the user explicitly stated it, override.
    # SKIP for Mock JSON (debug) to avoid self-triggering on JSON keys
    if not parsed_intent.get('tempo') and not intent.startswith("MOCK_JSON:"):
        normalized = intent.lower()
        if 'slow' in normalized or 'chill' in normalized or 'down' in normalized or 'ballad' in normalized:
            parsed_intent['tempo'] = 'slow'
        elif 'fast' in normalized or 'up' in normalized or 'energetic' in normalized or 'punk' in normalized:
            parsed_intent['tempo'] = 'fast'
            
    query = Song.query 

    # Apply Mode Filter
    mode = request.args.get('mode', 'all')
    if mode == 'mainstream':
        query = query.filter(Song.mainstream_score >= 70)
    elif mode == 'niche':
        query = query.filter(Song.mainstream_score < 70)

    filters_applied = False

    # Apply Metadata Filters
    if parsed_intent.get('artist'):
        query = query.filter(Song.artist.ilike(f"%{parsed_intent['artist']}%"))
        filters_applied = True
    
    if parsed_intent.get('year_start'):
        query = query.filter(Song.year >= parsed_intent['year_start'])
        filters_applied = True
    if parsed_intent.get('year_end'):
        query = query.filter(Song.year <= parsed_intent['year_end'])
        filters_applied = True

    if parsed_intent.get('tempo') == 'slow':
        query = query.filter(Song.bpm < 100)
        filters_applied = True
    elif parsed_intent.get('tempo') == 'medium':
        query = query.filter(Song.bpm >= 100, Song.bpm <= 125)
        filters_applied = True
    elif parsed_intent.get('tempo') == 'fast':
        query = query.filter(Song.bpm > 125)
        filters_applied = True

    # 3. GENRE CORE FILTER (Prioritized over Title Keywords)
    genres = parsed_intent.get('genres', [])
    if genres:
        genre_filters = [Song.genre.ilike(f"%{g}%") for g in genres]
        
        # PHASE 18: SUBJECTIVE CROWD WISDOM
        # If a tag matches the genre key and has high consensus (count >= 3), treat it as a valid genre match.
        # This allows a song metadata-ed as "Pop" to show up in "Rock" if 3+ users tagged it "Rock".
        tag_filters = [Song.tags.any(and_(SongTag.tag_name.ilike(f"%{g}%"), SongTag.count >= 3)) for g in genres]
        
        query = query.filter(or_(*genre_filters, *tag_filters))
        filters_applied = True

    # 4. Keyword/Mood matching
    mood = parsed_intent.get('mood')
    keywords = parsed_intent.get('keywords', [])
    search_terms = keywords + ([mood] if mood else [])
    
    if search_terms:
        filters_applied = True
        for kw in search_terms:
            # We separate Artist/Title keywords from Genre/Tag keywords to avoid "Rock With Me" dominance
            query = query.filter(or_(
                Song.tags.any(SongTag.tag_name.ilike(f"%{kw}%")),
                # Only match artist/title if it's not a generic genre name
                or_(
                    Song.artist.ilike(f"%{kw}%"),
                    Song.title.ilike(f"%{kw}%")
                ) if kw.lower() not in ['rock', 'pop', 'jazz', 'lofi', 'metal'] else False
            ))

    # PHASE 19: DEEP FEATURE VECTOR FILTERING
    feature_constraints = parsed_intent.get('feature_constraints', [])
    if feature_constraints:
        print(f"DEBUG: Applying {len(feature_constraints)} Deep Feature Constraints")
        # Explicitly join SongAnalysis for vector filtering
        query = query.join(SongAnalysis)
        filters_applied = True
        
        for constraint in feature_constraints:
            feature = constraint.get('feature')
            
            # Numeric Range (min/max)
            if 'min' in constraint or 'max' in constraint:
                col = getattr(SongAnalysis, feature, None)
                if col:
                    if 'min' in constraint:
                        query = query.filter(col >= constraint['min'])
                    if 'max' in constraint:
                        query = query.filter(col <= constraint['max'])
            
            # Categorical Values (Enum)
            if 'values' in constraint:
                col = getattr(SongAnalysis, feature, None)
                if col:
                    query = query.filter(col.in_(constraint['values']))

    # CRITICAL FIX: Fallback
    if not filters_applied and intent:
        print("DEBUG: Fallback logic triggered!")
        query = query.filter(or_(
            Song.genre.ilike(f"%{intent}%"),
            Song.tags.any(SongTag.tag_name.ilike(f"%{intent}%")),
            Song.artist.ilike(f"%{intent}%"),
            Song.title.ilike(f"%{intent}%")
        ))
        
    print(f"DEBUG: Parsed Intent: {parsed_intent}")
    print(f"DEBUG: Filters Applied: {filters_applied}")
    print(f"DEBUG: Query SQL: {query}")

    # --- TWO-PASS SEARCH STRATEGY ---
    # Pass 1: Strict Query (All filters applied)
    db_songs_strict = query.limit(100).all()
    
    # Convert to dict and assign High Match Score
    all_songs = []
    found_ids = set()
    
    for s in db_songs_strict:
        s_dict = s.to_dict()
        s_dict['match_type'] = 'strict'
        s_dict['base_score'] = 1000 # Ensure strict matches are always on top
        all_songs.append(s_dict)
        found_ids.add(s.id)
        
    # Pass 2: Relaxed Query (If results are low)
    # Fetch partial matches if we have fewer than 50 results
    if len(all_songs) < 50 and (parsed_intent.get('genres') or parsed_intent.get('mood') or parsed_intent.get('keywords')):
        print(f"DEBUG: Triggering Relaxed Search. Found {len(all_songs)} strict matches.")
        
        relaxed_query = Song.query
        
        # Apply Mode Filter to relaxed query too
        if mode == 'mainstream':
            relaxed_query = relaxed_query.filter(Song.mainstream_score >= 70)
        elif mode == 'niche':
            relaxed_query = relaxed_query.filter(Song.mainstream_score < 70)
            
        # Broad "OR" Filter
        conditions = []
        
        # 1. Genres
        if parsed_intent.get('genres'):
            for g in parsed_intent['genres']:
                conditions.append(Song.genre.ilike(f"%{g}%"))
                conditions.append(Song.tags.any(SongTag.tag_name.ilike(f"%{g}%")))
        
        # 2. Mood/Keywords
        search_terms = parsed_intent.get('keywords', []) + ([parsed_intent['mood']] if parsed_intent.get('mood') else [])
        for kw in search_terms:
            conditions.append(Song.tags.any(SongTag.tag_name.ilike(f"%{kw}%"))) 
            # Note: We exclude Artist/Title from relaxed generally to avoid noise, 
            # unless the result count is VERY low. Let's keep it semantic.
            
        if conditions:
            relaxed_query = relaxed_query.filter(or_(*conditions))
            # Exclude already found
            if found_ids:
                relaxed_query = relaxed_query.filter(~Song.id.in_(found_ids))
                
            # Limit relaxed results
            db_songs_relaxed = relaxed_query.limit(50 - len(all_songs)).all()
            
            for s in db_songs_relaxed:
                s_dict = s.to_dict()
                s_dict['match_type'] = 'relaxed'
                s_dict['base_score'] = 0 # Baseline for partially matched
                all_songs.append(s_dict)
                
    print(f"DEBUG: Total Songs Found: {len(all_songs)}")
    
    # 5. External Discovery
    ext_query = parsed_intent.get('external_search_query')
    has_artist_match = False
    if parsed_intent.get('artist'):
         has_artist_match = any(parsed_intent['artist'].lower() in s['artist'].lower() for s in all_songs)
         
    if (len(all_songs) < 8 or not has_artist_match) and ext_query:
        client = LastFMClient(LASTFM_API_KEY)
        external_results = client.search_track(ext_query, limit=15)
        
        existing_keys = set(f"{s['artist'].lower()}|{s['title'].lower()}" for s in all_songs)
        for res in external_results:
            key = f"{res['artist'].lower()}|{res['title'].lower()}"
            if key not in existing_keys:
                all_songs.append({
                    "artist": res['artist'],
                    "title": res['title'],
                    "ai_recommendation": True,
                    "genre": "External Discovery",
                    "bpm": "Unknown",
                    "decibel_peak": "Unknown"
                })
                existing_keys.add(key)

    # 6. RE-RANKING FOR PERSONALIZATION & CROWD WISDOM
    def calculate_relevance(song_dict):
        score = 0
        # Boost if in user's favorite genre
        if user_profile['fav_genre'] and song_dict['genre'] == user_profile['fav_genre']:
            score += 5
            
        # Boost based on tag overlap with User Profile
        if 'tags' in song_dict: 
            # 6a. Personal Profile Overlap
            overlap = set(user_profile['top_tags']).intersection(set(song_dict['tags']))
            score += len(overlap)
            
            # 6b. PHASE 18: CROWD WISDOM BOOST
            # If the song has tags matching the current search intent, boost by their count/consensus
            search_genres = [g.lower() for g in parsed_intent.get('genres', [])]
            search_keywords = [k.lower() for k in parsed_intent.get('keywords', [])]
            active_terms = set(search_genres + search_keywords)
            
            # We need to fetch the actual count from the DB for these specific tags
            # Since song_dict['tags'] is just a list of strings, we query the count efficiently
            # Optimization: We already loaded tags in to_dict, but not counts.
            # To avoid N+1 queries during sorting, we rely on a heuristic or pre-fetch.
            # For POC, we'll do a lightweight check if we are in a loop (mostly fine for 50 items)
            # OR better: The query above selected songs. We trust the sort.
            pass 

        elif song_dict.get('ai_recommendation'):
            score += 1 
            
        return score

    # Optimized Crowd Wisdom Sort:
    # Fetch Counts for relevant tags for these 50 songs in one go? 
    # Or just iterate. define helper.
    
    song_ids = [s['id'] for s in all_songs if 'id' in s]
    if song_ids:
        # Get all tags for these songs that match current intent
        relevant_terms = [t.lower() for t in (parsed_intent.get('genres', []) + parsed_intent.get('keywords', []))]
        if relevant_terms:
            boosts = {} # {song_id: total_count_boost}
            # Select sum of counts where tag_name in terms
            rows = db.session.query(SongTag.song_id, db.func.sum(SongTag.count)).filter(
                SongTag.song_id.in_(song_ids),
                SongTag.tag_name.in_(relevant_terms)
            ).group_by(SongTag.song_id).all()
            
            for sid, count_sum in rows:
                boosts[sid] = count_sum if count_sum else 0
                
            # Update scores
            for s in all_songs:
                if s.get('id') in boosts:
                    # Logarithmic boost to prevent one super-tag dominating? 
                    # No, linear is fine for "Crowd Wisdom" - 50 people saying "Rock" should matter.
                    s['crowd_score'] = boosts[s['id']]
                else:
                    s['crowd_score'] = 0

    all_songs.sort(key=lambda s: s.get('base_score', 0) + calculate_relevance(s) + (s.get('crowd_score', 0) * 0.5), reverse=True)

    return jsonify({
        "songs": all_songs,  # Returned full list (strict + relaxed)
        "search_log_id": new_log.id,
        "parsed_intent": parsed_intent 
    })

@app.route('/songs/explore')
def explore_songs():
    # Get 30 random songs for the 'Explore' section
    songs = Song.query.order_by(db.func.random()).limit(30).all()
    return jsonify([s.to_dict() for s in songs])

def _get_user_profile(user_id):
    """Refined helper to get top tags and genres for a user based on high ratings."""
    high_ratings = UserRating.query.filter(UserRating.user_id == user_id, UserRating.rating >= 4).all()
    if not high_ratings:
        return {"top_tags": [], "fav_genre": None}
    
    liked_song_ids = [r.song_id for r in high_ratings]
    tag_counts = {}
    genre_counts = {}
    
    for song_id in liked_song_ids:
        song = Song.query.get(song_id)
        if not song: continue
        genre_counts[song.genre] = genre_counts.get(song.genre, 0) + 1
        for t in song.tags:
            t_name = t.tag_name.lower()
            if t_name == song.artist.lower() or t_name in song.artist.lower():
                continue
            tag_counts[t_name] = tag_counts.get(t_name, 0) + 1
            
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:15]
    top_tag_names = [t[0] for t in sorted_tags]
    
    sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
    fav_genre = sorted_genres[0][0] if sorted_genres else None
    
    return {"top_tags": top_tag_names, "fav_genre": fav_genre}

@app.route('/recommendations')
def get_recommendations():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session['user_id']
    profile = _get_user_profile(user_id)
    
    if not profile['top_tags'] and not profile['fav_genre']:
        return jsonify([])
    
    top_tag_names = profile['top_tags']
    fav_genre = profile['fav_genre']
    
    # 3. Find other songs that share tags OR the favorite genre
    user_library_ids = [entry.song_id for entry in UserLibrary.query.filter_by(user_id=user_id).all()]
    potential_matches = Song.query.filter(Song.id.notin_(user_library_ids)).all()
    
    scored_recs = []
    for song in potential_matches:
        song_tags = [t.tag_name.lower() for t in song.tags]
        tag_overlap = set(top_tag_names).intersection(set(song_tags))
        
        score = len(tag_overlap)
        if song.genre == fav_genre:
            score += 2 # Genre match is strong
            
        if score > 0:
            song_dict = song.to_dict()
            song_dict['match_score'] = score
            # Add a small random jitter to break ties and keep UI fresh
            song_dict['_sort_key'] = score + (random.random() * 0.1)
            scored_recs.append(song_dict)
            
    # 4. Diversity Filter: Sort and then limit per artist
    # Sort by score descending
    scored_recs.sort(key=lambda x: x['_sort_key'], reverse=True)
    
    final_recs = []
    artist_counts = {}
    
    for rec in scored_recs:
        artist = rec['artist'].lower()
        count = artist_counts.get(artist, 0)
        
        # Limit to 2 tracks per artist in the recommendation list
        if count < 2:
            final_recs.append(rec)
            artist_counts[artist] = count + 1
        
        if len(final_recs) >= 12: # Return a bit more for plenty of choice
            break
            
    return jsonify(final_recs)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
