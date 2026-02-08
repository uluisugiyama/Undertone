from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    
    library = db.relationship('UserLibrary', backref='user', lazy=True)
    ratings = db.relationship('UserRating', backref='user', lazy=True)

class Song(db.Model):
    __tablename__ = 'songs'

    id = db.Column(db.Integer, primary_key=True)
    artist = db.Column(db.String(255), nullable=True) # New
    title = db.Column(db.String(255), nullable=True) # New
    bpm = db.Column(db.Integer, nullable=False)
    decibel_peak = db.Column(db.Float, nullable=False)
    genre = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    mainstream_score = db.Column(db.Integer, nullable=False) # 0-100 scale

    # Phase 12: Polish & Flagging
    is_contradictory = db.Column(db.Boolean, default=False)
    contradiction_reason = db.Column(db.String(255), nullable=True)

    tags = db.relationship('SongTag', backref='song', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "artist": self.artist,
            "title": self.title,
            "bpm": self.bpm,
            "decibel_peak": self.decibel_peak,
            "genre": self.genre,
            "year": self.year,
            "mainstream_score": self.mainstream_score,
            "is_contradictory": self.is_contradictory,
            "contradiction_reason": self.contradiction_reason,
            "tags": [t.tag_name for t in self.tags]
        }

class SongTag(db.Model):
    __tablename__ = 'song_tags'
    id = db.Column(db.Integer, primary_key=True)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.id'), nullable=False)
    tag_name = db.Column(db.String(100), nullable=False)
    count = db.Column(db.Integer, default=1) # Number of times this tag was applied in Last.fm

class UserLibrary(db.Model):
    __tablename__ = 'user_libraries'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.id'), nullable=False)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserRating(db.Model):
    __tablename__ = 'user_ratings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False) # 1-5
    comment = db.Column(db.Text)
    rated_at = db.Column(db.DateTime, default=datetime.utcnow)

class PersonalTrending(db.Model):
    __tablename__ = 'personal_trendings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.id'), nullable=False)
    engagement_count = db.Column(db.Integer, default=1)
    last_engaged_at = db.Column(db.DateTime, default=datetime.utcnow)

class SearchLog(db.Model):
    __tablename__ = 'search_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    intent = db.Column(db.String(500), nullable=False)
    selected_song_id = db.Column(db.Integer, db.ForeignKey('songs.id'), nullable=True)
    mode = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SongAnalysis(db.Model):
    __tablename__ = 'song_analysis'
    id = db.Column(db.Integer, primary_key=True)
    song_id = db.Column(db.Integer, db.ForeignKey('songs.id'), nullable=False)
    
    # 1. Tempo & Rhythmic Feel
    tempo_feel = db.Column(db.String(50)) 
    tempo_stability = db.Column(db.Float) # 0-1 (Constant -> Variable)
    percussive_density = db.Column(db.Float) # 0-1
    syncopation = db.Column(db.Float) # 0-1
    rhythmic_aggressiveness = db.Column(db.Float) # 0-1
    groove_complexity = db.Column(db.Float) # 0-1
    
    # 2. Vocal Intensity & Style
    vocal_style = db.Column(db.String(50)) 
    vocal_presence = db.Column(db.Float) # 0-1
    vocal_instr_ratio = db.Column(db.Float) # Ratio of vocal to instr energy
    vocal_distortion = db.Column(db.Float) # Harshness/Distortion level
    vocal_register = db.Column(db.String(50)) # Low, Mid, High
    
    # 3. Emotional & Mood Mapping
    dark_bright = db.Column(db.Float) # 0-1
    calm_energetic = db.Column(db.Float) # 0-1
    harmonic_tension = db.Column(db.Float) # 0-1 (Dissonant/Tense)
    key_modality = db.Column(db.String(50)) # Major, Minor, Modal
    chord_complexity = db.Column(db.Float) # 0-1
    
    # 4. Genre Confidence & Blending
    genre_distribution = db.Column(db.Text) # JSON mapping
    
    # 5. Energy & Momentum
    loudness_progression = db.Column(db.String(50)) # Rising, Falling, Constant, Waves
    instrument_density = db.Column(db.Float) # 0-1
    dynamic_range_compression = db.Column(db.Float) # 0-1
    intensity_curve = db.Column(db.Text) # JSON curve
    
    # 6. Lyrical Content & Delivery
    lyrical_narrative = db.Column(db.Float) # 0-1 (Abstract -> Story)
    lyrical_repetition = db.Column(db.Float) # 0-1
    lyrical_density = db.Column(db.Float) # 0-1
    
    # 7. Structural Complexity
    section_count = db.Column(db.Integer)
    time_signature_changes = db.Column(db.Boolean)
    structural_variation = db.Column(db.Float) # 0-1
    
    # 8. Production & Texture
    production_quality = db.Column(db.Float) # Lo-fi -> Hi-fi
    analog_digital_feel = db.Column(db.Float) # 0-1
    spatial_width = db.Column(db.Float) # 0-1
    reverb_density = db.Column(db.Float) # 0-1
    instrument_separation = db.Column(db.Float) # 0-1
    
    # 9. Novelty & Sonic Signature
    sonic_uniqueness = db.Column(db.Float) # 0-1
    
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)
