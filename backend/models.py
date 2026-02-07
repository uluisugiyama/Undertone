from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

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

    def __repr__(self):
        return f'<Song {self.id}: {self.genre} ({self.bpm} BPM)>'
