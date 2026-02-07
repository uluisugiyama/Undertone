import os
import random
from app import app
from models import db, Song

# Sample data for ingestion
genres = ["Punk Rock", "Metalcore", "Synthpop", "Techno", "Ambient", "Grunge", "Lo-fi", "Trap", "R&B"]
years = list(range(1970, 2025))

def ingest_sample_songs(count=50):
    with app.app_context():
        # Clear existing songs for a clean ingest (optional, but good for testing)
        Song.query.delete()
        
        for i in range(count):
            genre = random.choice(genres)
            bpm = random.randint(60, 200)
            decibel_peak = round(random.uniform(-30.0, -2.0), 1)
            year = random.choice(years)
            mainstream_score = random.randint(0, 100)
            
            song = Song(
                bpm=bpm,
                decibel_peak=decibel_peak,
                genre=genre,
                year=year,
                mainstream_score=mainstream_score
            )
            db.session.add(song)
        
        db.session.commit()
        print(f"Successfully ingested {count} sample songs.")

if __name__ == "__main__":
    ingest_sample_songs()
