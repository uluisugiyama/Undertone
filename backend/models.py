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
    
    # Tempo & Rhythm
    tempo_feel = db.Column(db.String(50)) # slow, medium, fast
    rhythmic_complexity = db.Column(db.Float) # 0.0 - 1.0 (Simple 4/4 -> Math Rock)
    
    # Vocals
    vocal_style = db.Column(db.String(50)) # clean, raspy, screaming, fluid, instrumental
    vocal_presence = db.Column(db.Float) # 0.0 (Instrumental) - 1.0 (Vocal dominant)
    
    # Mood & Emotion
    dark_bright = db.Column(db.Float) # 0.0 (Dark/Melancholic) - 1.0 (Bright/Happy)
    calm_energetic = db.Column(db.Float) # 0.0 (Chill) - 1.0 (High Energy)
    
    # Texture & Production
    production_quality = db.Column(db.Float) # 0.0 (Lo-fi/Raw) - 1.0 (Polished/Hifi)
    
    # Genre Blending (Stored as JSON string)
    genre_distribution = db.Column(db.Text) # e.g. {"Rock": 0.7, "Pop": 0.3}
    
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)
