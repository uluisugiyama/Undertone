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
