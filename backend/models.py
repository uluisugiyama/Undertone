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
    bpm = db.Column(db.Integer, nullable=False)
    decibel_peak = db.Column(db.Float, nullable=False)
    genre = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    mainstream_score = db.Column(db.Integer, nullable=False) # 0-100 scale

    def to_dict(self):
        return {
            "id": self.id,
            "bpm": self.bpm,
            "decibel_peak": self.decibel_peak,
            "genre": self.genre,
            "year": self.year,
            "mainstream_score": self.mainstream_score
        }

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
