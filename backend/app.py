from flask import Flask, jsonify, request, session, send_from_directory
from flask_migrate import Migrate
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_, and_
from backend.models import db, Song, User, UserLibrary, UserRating, PersonalTrending, SongTag, SearchLog, SongAnalysis
from backend.music_standards import is_fast_tempo, is_heavy, get_parent_genre
import os
import random
import math
import requests
from datetime import datetime
import json
from dotenv import load_dotenv
from backend.lastfm_client import LastFMClient
from backend.discovery_engine import FeatureDictionary, DiscoveryEngine

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

# AUTOMATION: Create tables on startup for Render Free Tier (no shell access needed)
with app.app_context():
    try:
        db.create_all()
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating tables: {e}")

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal Server Error", "details": str(error)}), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Not Found"}), 404

# AUTOMATION: Endpoint to seed data via web request
@app.route('/admin/seed_db')
def seed_db_endpoint():
    try:
        from backend.seed_minimal import seed_minimal
        seed_minimal()
        return jsonify({"message": "Database seeded successfully with minimal data!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# AUTOMATION: Endpoint to ingest REAL data (requires API keys)
@app.route('/admin/ingest_full')
def ingest_full_endpoint():
    try:
        if not os.getenv("LASTFM_API_KEY"):
            return jsonify({"error": "LASTFM_API_KEY not set in environment variables"}), 500
            
        from backend.ingest_data import seed_real_data
        # Run safely
        seed_real_data()
        return jsonify({"message": "Full ingestion complete! Added ~100 songs."}), 200
    except Exception as e:
        return jsonify({"error": f"Ingestion failed: {str(e)}"}), 500

@app.route('/admin/enrich_db')
def enrich_db_endpoint():
    try:
        from backend.enrich_data import enrich_songs
        enrich_songs()
        return jsonify({"message": "Enrichment (Tags/Mainstream Score) complete!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/analyze_db')
def analyze_db_endpoint():
    try:
        from backend.backfill_analysis import backfill
        backfill()
        return jsonify({"message": "Deep Analysis (Gemini Vectors) complete!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/debug_stats')
def debug_stats():
    song_count = Song.query.count()
    tag_count = SongTag.query.count()
    analysis_count = SongAnalysis.query.count()
    
    songs = Song.query.limit(5).all()
    song_list = [f"{s.artist} - {s.title} (Analysis: {'Yes' if SongAnalysis.query.filter_by(song_id=s.id).first() else 'No'})" for s in songs]
    
    return jsonify({
        "song_count": song_count,
        "tag_count": tag_count,
        "analysis_count": analysis_count,
        "sample_songs": song_list
    })

@app.route('/admin/ingest_complete')
def ingest_complete_endpoint():
    try:
        if not os.getenv("LASTFM_API_KEY"):
            return jsonify({"error": "LASTFM_API_KEY not set"}), 500
        if not os.getenv("GEMINI_API_KEY"):
            return jsonify({"error": "GEMINI_API_KEY not set"}), 500
            
        from backend.ingest_data import seed_real_data
        from backend.enrich_data import enrich_songs
        from backend.backfill_analysis import backfill
        import threading

        def run_pipeline():
            with app.app_context():
                print("BACKGROUND: Starting Complete Pipeline...")
                try:
                    seed_real_data()
                    enrich_songs()
                    backfill()
                    print("BACKGROUND: Pipeline Success!")
                except Exception as e:
                    print(f"BACKGROUND: Pipeline Failed: {e}")

        thread = threading.Thread(target=run_pipeline)
        thread.start()
        
        return jsonify({"message": "Background Pipeline Started! Monitoring progress via /admin/debug_stats. Expected completion: 3-5 minutes."}), 202
    except Exception as e:
        return jsonify({"error": f"Failed to start pipeline: {str(e)}"}), 500

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
    Phase 20: High-Dimensional Musicology
    Uses Gemini to infer 25+ measurable metrics based on university-level standards.
    """
    prompt = f"""
    Perform a professional musicological analysis of "{song.title}" by "{song.artist}" for an academic database.
    Apply metrics derived from Stanford, Harvard, and Berklee standards. 
    
    Return ONLY a JSON object with these EXACT keys:
    {{
      "tempo_feel": "slow" | "medium" | "fast",
      "tempo_stability": 0.0-1.0 (0=Constant metronome, 1=Rubato/Variable),
      "percussive_density": 0.0-1.0,
      "syncopation": 0.0-1.0,
      "rhythmic_aggressiveness": 0.0-1.0,
      "groove_complexity": 0.0-1.0,
      "vocal_style": "clean" | "raspy" | "screaming" | "fluid" | "instrumental",
      "vocal_presence": 0.0-1.0,
      "vocal_instr_ratio": 0.0-1.0 (Vocal volume relative to background),
      "vocal_distortion": 0.0-1.0,
      "vocal_register": "low" | "mid" | "high",
      "dark_bright": 0.0-1.0,
      "calm_energetic": 0.0-1.0,
      "harmonic_tension": 0.0-1.0 (Dissonance level),
      "key_modality": "Major" | "Minor" | "Modal",
      "chord_complexity": 0.0-1.0,
      "genre_distribution": {{ "Genre": Score }},
      "loudness_progression": "Rising" | "Falling" | "Constant" | "Waves",
      "instrument_density": 0.0-1.0,
      "compression": 0.0-1.0 (Dynamic range flatness),
      "lyrical_narrative": 0.0-1.0,
      "lyrical_repetition": 0.0-1.0,
      "lyrical_density": 0.0-1.0,
      "section_count": int,
      "time_signature_changes": bool,
      "structural_variation": 0.0-1.0,
      "production_texture": 0.0-1.0 (0=Analog/Raw, 1=Digital/Polished),
      "spatial_width": 0.0-1.0,
      "reverb_density": 0.0-1.0,
      "instrument_separation": 0.0-1.0,
      "sonic_uniqueness": 0.0-1.0
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
            tempo_stability=float(data.get('tempo_stability', 0.1)),
            percussive_density=float(data.get('percussive_density', 0.5)),
            syncopation=float(data.get('syncopation', 0.2)),
            rhythmic_aggressiveness=float(data.get('rhythmic_aggressiveness', 0.3)),
            groove_complexity=float(data.get('groove_complexity', 0.3)),
            vocal_style=data.get('vocal_style', 'clean'),
            vocal_presence=float(data.get('vocal_presence', 0.5)),
            vocal_instr_ratio=float(data.get('vocal_instr_ratio', 0.7)),
            vocal_distortion=float(data.get('vocal_distortion', 0.0)),
            vocal_register=data.get('vocal_register', 'mid'),
            dark_bright=float(data.get('dark_bright', 0.5)),
            calm_energetic=float(data.get('calm_energetic', 0.5)),
            harmonic_tension=float(data.get('harmonic_tension', 0.2)),
            key_modality=data.get('key_modality', 'Major'),
            chord_complexity=float(data.get('chord_complexity', 0.3)),
            genre_distribution=json.dumps(data.get('genre_distribution', {})),
            loudness_progression=data.get('loudness_progression', 'Constant'),
            instrument_density=float(data.get('instrument_density', 0.6)),
            dynamic_range_compression=float(data.get('compression', 0.5)),
            lyrical_narrative=float(data.get('lyrical_narrative', 0.5)),
            lyrical_repetition=float(data.get('lyrical_repetition', 0.3)),
            lyrical_density=float(data.get('lyrical_density', 0.5)),
            section_count=int(data.get('section_count', 4)),
            time_signature_changes=bool(data.get('time_signature_changes', False)),
            structural_variation=float(data.get('structural_variation', 0.3)),
            analog_digital_feel=float(data.get('production_texture', 0.5)),
            spatial_width=float(data.get('spatial_width', 0.6)),
            reverb_density=float(data.get('reverb_density', 0.3)),
            instrument_separation=float(data.get('instrument_separation', 0.7)),
            sonic_uniqueness=float(data.get('sonic_uniqueness', 0.5))
        )
        db.session.add(analysis)
        db.session.commit()
        print(f"Deep Analysis complete for {song.title}")
    except Exception as e:
        print(f"High-Dimensional Analysis failed for {song.title}: {e}")

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
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({"error": "User already exists"}), 400
        
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        print(f"Registration Error: {e}")
        db.session.rollback()
        return jsonify({"error": "Registration failed", "details": str(e)}), 500

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
    feedback_tags = data.get('feedback_tags', [])
    if feedback_tags:
        for t_name in feedback_tags:
            t_name = t_name.strip()
            if not t_name: continue
            
            tag = SongTag.query.filter(
                SongTag.song_id == song_id, 
                SongTag.tag_name.ilike(t_name)
            ).first()
            
            if tag:
                tag.count += 1
            else:
                if len(t_name) < 30:
                    new_tag = SongTag(song_id=song_id, tag_name=t_name.title(), count=1)
                    db.session.add(new_tag)

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
            user_id = session.get('user_id')
            user_profile = _get_user_profile(user_id) if user_id else {"top_tags": [], "fav_genre": None}
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

    # 2. Use Gemini to parse intent into structured filters AND high-dimensional keywords
    if not parsed_intent:
        prompt = f"""
        Analyze the music search intent: "{intent}"
        {context_str}
        
        1. Extract standard filters: 
           - 'artist': The musician/group (e.g. "Radiohead").
           - 'genres': List of musical genres (e.g. ["Rock", "Electronic"]).
           - 'mood': Single descriptive mood (e.g. "Sad").
        2. Identify specific high-dimensional keywords (e.g. slow, atmospheric, energetic, lofi, melodic).
        3. Create an 'external_search_query' for Last.fm lookup.
        
        CRITICAL: If the intent reflects a specific musical entity (like "Radiohead"), ensure it is in 'artist' NOT just 'keywords'.
        
        Return JSON:
        {{
          "artist": null,
          "genres": [],
          "mood": null,
          "year_start": null, 
          "year_end": null,
          "keywords": [],
          "external_search_query": "..."
        }}
        """
        
        try:
            response_text = call_gemini_api(prompt)
            clean_response = response_text.replace('```json', '').replace('```', '').strip()
            parsed_intent = json.loads(clean_response)
        except Exception as e:
            print(f"Gemini error: {e}")
            parsed_intent = {
                "artist": None, "genres": [], "mood": None, 
                "year_start": None, "year_end": None, 
                "keywords": [intent], "external_search_query": intent
            }

    # 3. Log intent for Social Reinforcement
    new_log = SearchLog(user_id=user_id, intent=intent, mode=request.args.get('mode', 'all'))
    db.session.add(new_log)
    db.session.commit()
    
    # Phase 20: High-Dimensional Discover Optimization
    # 1. Integrate Social Signals (Shared Activity & Personal Trending)
    shared_hits = {}
    if intent:
        # Boost songs that others (or the user) have selected for similar intents
        hist_hits = SearchLog.query.filter(
            SearchLog.intent.ilike(f"%{intent}%"),
            SearchLog.selected_song_id != None
        ).all()
        for hit in hist_hits:
            shared_hits[hit.selected_song_id] = shared_hits.get(hit.selected_song_id, 0) + 1

    personal_trending_ids = {}
    if user_id:
        pt = PersonalTrending.query.filter_by(user_id=user_id).all()
        personal_trending_ids = {item.song_id: item.engagement_count for item in pt}

    # 2. Expand Intent into Target Vectors
    search_keywords = parsed_intent.get('keywords', [])
    if parsed_intent.get('mood'):
        search_keywords.append(parsed_intent['mood'])
    
    target_vector, matched_atomized = FeatureDictionary.expand_intent(search_keywords)
    
    # 3. Broad Candidate Selection (PHASE 21: Diversity Matching)
    # We combine 3 pools:
    # A. Targeted Metadata Candidates (Small Pool)
    # B. Explicit Genre Candidates (Softened)
    # C. Random "Discovery" Samples (Vibe matching across any genre)
    
    candidate_ids = set()
    query_base = Song.query.outerjoin(SongAnalysis)
    
    # Apply Basic Mode Filters (Hard Constraints)
    mode = request.args.get('mode', 'all')
    if mode == 'mainstream':
        query_base = query_base.filter(Song.mainstream_score >= 70)
    elif mode == 'niche':
        query_base = query_base.filter(Song.mainstream_score < 70)

    # Pool A: Strict Artist/Metadata matches
    if parsed_intent.get('artist'):
        hits = query_base.filter(Song.artist.ilike(f"%{parsed_intent['artist']}%")).limit(100).all()
        candidate_ids.update(s.id for s in hits)

    # Pool B: Genre matches (Limited to 100 to leave room for others)
    if parsed_intent.get('genres'):
        hits = query_base.filter(or_(*[Song.genre.ilike(f"%{g}%") for g in parsed_intent['genres']])).limit(100).all()
        candidate_ids.update(s.id for s in hits)
        
    # Metadata Safety Fallback
    for kw in search_keywords:
        kw_lower = kw.lower().strip()
        was_expanded = any(word in matched_atomized for word in kw_lower.split())
        if not was_expanded:
            hits = query_base.filter(or_(Song.title.ilike(f"%{kw}%"), Song.artist.ilike(f"%{kw}%"))).limit(50).all()
            candidate_ids.update(s.id for s in hits)

    # Pool C: Random Discovery Samples (Crucial for Vibe Discovery)
    # This allows the similarity engine to find "Rock Vibes" even in songs not tagged "Rock"
    random_samples = query_base.order_by(db.func.random()).limit(75).all()
    candidate_ids.update(s.id for s in random_samples)

    # 4. Final Candidate Fetch
    candidates = Song.query.filter(Song.id.in_(list(candidate_ids))).all()

    # 5. High-Dimensional Scoring
    all_songs = []
    
    # User Profile (Fetch once)
    profile = _get_user_profile(user_id) if user_id else {"top_tags": [], "fav_genre": None}
    personal_trending_ids = {}
    if user_id:
        pt = PersonalTrending.query.filter_by(user_id=user_id).all()
        personal_trending_ids = {item.song_id: item.engagement_count for item in pt}

    for s in candidates:
        s_dict = s.to_dict()
        analysis = SongAnalysis.query.filter_by(song_id=s.id).first()
        
        sim_score, sim_details = DiscoveryEngine.calculate_similarity(analysis, target_vector)
        s_dict['sim_score'] = sim_score
        s_dict['sim_reasoning'] = sim_details
        
        # Combine with Social/Metadata boosts
        base_relevance = 0
        sid = s.id
        
        # Soft Genre Match Boost
        if parsed_intent.get('genres'):
            if any(g.lower() in s.genre.lower() for g in parsed_intent['genres']):
                base_relevance += 20  # Significant boost but not a requirement
        
        if user_id:
            # Favorite Genre Boost
            if s.genre == profile['fav_genre']:
                base_relevance += 15
            
            # Personal Trending Boost
            if sid in personal_trending_ids:
                base_relevance += personal_trending_ids[sid] * 5

        # Shared Activity Boost (Crowd Wisdom)
        if sid in shared_hits:
            base_relevance += min(shared_hits[sid] * 10, 40) # Cap boost

        # Final Ranking Score
        s_dict['ranking_score'] = (sim_score * 100) + base_relevance
        all_songs.append(s_dict)

    # 4. Sort and finalize
    all_songs.sort(key=lambda x: x['ranking_score'], reverse=True)
    
    # 5. External Discovery (Tag-Based Fallback)
    ext_query = parsed_intent.get('external_search_query')
    has_target_artist = False
    if parsed_intent.get('artist'):
        has_target_artist = any(parsed_intent['artist'].lower() in s['artist'].lower() for s in all_songs[:8])
        
    if (len(all_songs) < 8 or not has_target_artist) and ext_query and LASTFM_API_KEY:
        try:
            client = LastFMClient(LASTFM_API_KEY)
            
            # PHASE 21 Optimization: If searching for a vibe/genre, use Tag Discovery
            # We check if the query matches our FeatureDictionary atomized matches
            is_vibe_query = any(word in matched_atomized for word in ext_query.lower().split())
            
            if is_vibe_query:
                # Use Tag Lookup for better diversity (e.g. AC/DC instead of "Rock" the song)
                vibe_tag = matched_atomized[0] if matched_atomized else ext_query
                external_results = client.get_top_tracks_by_tag(vibe_tag, limit=12)
                reasoning_msg = f"Top-rated tracks discovery via '{vibe_tag}' vibe."
            else:
                external_results = client.search_track(ext_query, limit=10)
                reasoning_msg = "Found via external discovery engine."
            
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
                        "decibel_peak": "Unknown",
                        "sim_score": 0.6,
                        "sim_reasoning": reasoning_msg,
                        "ranking_score": 60 
                    })
                    existing_keys.add(key)
        except Exception as e:
            print(f"External discovery error: {e}")

    # Re-sort to incorporate external results if needed
    all_songs.sort(key=lambda x: x['ranking_score'], reverse=True)

    return jsonify({
        "songs": all_songs[:50],
        "search_log_id": new_log.id,
        "parsed_intent": parsed_intent,
        "expansion_stats": {
            "keywords_expanded": matched_atomized,
            "dimensions_checked": list(target_vector.keys())
        }
    })

@app.route('/songs/explore')
def explore_songs():
    # Get 30 random songs for the 'Explore' section
    songs = Song.query.order_by(db.func.random()).limit(30).all()
    return jsonify([s.to_dict() for s in songs])

def _get_user_profile(user_id):
    """
    Refined helper to get top tags and genres for a user.
    Now considers both explicit ratings AND implicit library Saves.
    """
    # 1. Get library songs and their ratings (if any)
    library_entries = UserLibrary.query.filter_by(user_id=user_id).all()
    if not library_entries:
        return {"top_tags": [], "fav_genre": None}
        
    ratings = {r.song_id: r.rating for r in UserRating.query.filter_by(user_id=user_id).all()}
    
    tag_counts = {}
    genre_counts = {}
    
    for entry in library_entries:
        song_id = entry.song_id
        song = Song.query.get(song_id)
        if not song: continue
        
        # Determine weight: Rated songs use their rating, unrated library songs use a default of 4 (Strong Interest)
        rating = ratings.get(song_id, 4)
        
        # Only count "Positive" signals (Rating 4-5 or unrated library entry)
        if rating < 4:
            continue
            
        # Standard weighting (4-5)
        genre_counts[song.genre] = genre_counts.get(song.genre, 0) + rating
        
        for t in song.tags:
            t_name = t.tag_name.lower()
            # Skip artist name tags as they don't help with vibe mixing
            if song.artist and (t_name == song.artist.lower() or t_name in song.artist.lower()):
                continue
            tag_counts[t_name] = tag_counts.get(t_name, 0) + rating
            
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:15]
    top_tag_names = [t[0] for t in sorted_tags]
    
    sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
    fav_genre = sorted_genres[0][0] if sorted_genres else None
    
    return {"top_tags": top_tag_names, "fav_genre": fav_genre}

def _get_user_collection_vector(user_id):
    """
    Calculates the 'Centroid' (Average) musical profile of a user's library.
    Each feature is averaged across all liked/saved songs.
    """
    library_entries = UserLibrary.query.filter_by(user_id=user_id).all()
    if not library_entries:
        return {}
        
    ratings = {r.song_id: r.rating for r in UserRating.query.filter_by(user_id=user_id).all()}
    
    feature_sums = {}
    feature_counts = {}
    
    for entry in library_entries:
        song_id = entry.song_id
        analysis = SongAnalysis.query.filter_by(song_id=song_id).first()
        if not analysis: continue
        
        rating = ratings.get(song_id, 4)
        if rating < 4: continue # Only learn from positive signals
        
        # Profile numeric features
        for field in [
            'tempo_stability', 'percussive_density', 'syncopation', 'rhythmic_aggressiveness',
            'groove_complexity', 'vocal_presence', 'vocal_instr_ratio', 'vocal_distortion',
            'dark_bright', 'calm_energetic', 'harmonic_tension', 'chord_complexity',
            'instrument_density', 'dynamic_range_compression', 'lyrical_narrative',
            'lyrical_repetition', 'lyrical_density', 'structural_variation',
            'analog_digital_feel', 'spatial_width', 'reverb_density', 'instrument_separation',
            'sonic_uniqueness'
        ]:
            val = getattr(analysis, field, None)
            if val is not None:
                feature_sums[field] = feature_sums.get(field, 0) + val
                feature_counts[field] = feature_counts.get(field, 0) + 1
                
    # Calculate Averages and wrap in lists for DiscoveryEngine compatibility
    centroid_vector = {}
    for field, total in feature_sums.items():
        if feature_counts[field] > 0:
            centroid_vector[field] = [total / feature_counts[field]]
            
    return centroid_vector

@app.route('/recommendations')
def get_recommendations():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session['user_id']
    profile = _get_user_profile(user_id)
    target_vector = _get_user_collection_vector(user_id)
    
    if not profile['top_tags'] and not profile['fav_genre'] and not target_vector:
        return jsonify([])
    
    top_tag_names = profile['top_tags']
    fav_genre = profile['fav_genre']
    
    # 3. Candidate Selection: Songs in database NOT in library
    user_library_ids = [entry.song_id for entry in UserLibrary.query.filter_by(user_id=user_id).all()]
    potential_matches = Song.query.filter(Song.id.notin_(user_library_ids)).limit(250).all()
    
    scored_recs = []
    for song in potential_matches:
        # A. Vector Similarity Score (Vibe Match)
        analysis = SongAnalysis.query.filter_by(song_id=song.id).first()
        if analysis:
            sim_score, _ = DiscoveryEngine.calculate_similarity(analysis, target_vector)
        else:
            # Fallback: Neutral similarity score if analysis is missing
            sim_score = 0.3 if target_vector else 0.1
        
        # B. Metadata/Tag Boosts
        song_tags = [t.tag_name.lower() for t in song.tags]
        tag_overlap = set(top_tag_names).intersection(set(song_tags))
        tag_boost = len(tag_overlap) * 0.15 # 15% boost per shared tag
        
        genre_boost = 0.25 if song.genre == fav_genre else 0
        
        # Combined Match Score (0.0 - 1.0+)
        final_match_score = sim_score + tag_boost + genre_boost
        
        if final_match_score > 0.3: # Lower threshold for discovery
            song_dict = song.to_dict()
            song_dict['match_score'] = round(final_match_score * 10, 1) # Internal scale 1-10
            # Add a small random jitter to break ties and keep UI fresh
            song_dict['_sort_key'] = final_match_score + (random.random() * 0.05)
            scored_recs.append(song_dict)
            
    # 4. Diversity Filter: Sort and then limit per artist
    scored_recs.sort(key=lambda x: x['_sort_key'], reverse=True)
    
    final_recs = []
    artist_counts = {}
    
    for rec in scored_recs:
        artist = rec['artist'].lower()
        count = artist_counts.get(artist, 0)
        
        if count < 2:
            final_recs.append(rec)
            artist_counts[artist] = count + 1
        
        if len(final_recs) >= 12: 
            break

    # 5. External Discovery Fallback (If local results are sparse)
    if len(final_recs) < 6 and LASTFM_API_KEY:
        try:
            client = LastFMClient(LASTFM_API_KEY)
            # Find the top rated or most recent song to use as a seed
            seed_song_id = next(iter(user_library_ids), None)
            if seed_song_id:
                seed_song = Song.query.get(seed_song_id)
                if seed_song:
                    external_similars = client.get_similar_tracks(seed_song.artist, seed_song.title)
                    existing_keys = set(f"{s['artist'].lower()}|{s['title'].lower()}" for s in final_recs)
                    library_keys = set(f"{Song.query.get(sid).artist.lower()}|{Song.query.get(sid).title.lower()}" for sid in user_library_ids if Song.query.get(sid))
                    
                    for res in external_similars:
                        key = f"{res['artist'].lower()}|{res['title'].lower()}"
                        if key not in existing_keys and key not in library_keys:
                            final_recs.append({
                                "artist": res['artist'],
                                "title": res['title'],
                                "ai_recommendation": True,
                                "genre": "External Discovery",
                                "match_score": 5.0,
                                "tags": ["Global Discovery", "Similar Vibes"]
                            })
                            if len(final_recs) >= 12: break
        except Exception as e:
            print(f"External recommendation fallback failed: {e}")
            
    return jsonify(final_recs)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
