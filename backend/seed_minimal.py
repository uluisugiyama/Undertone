from backend.app import app, db
from backend.models import Song, SongTag
import random

def seed_minimal():
    print("Seeding minimal data (No API Key required)...")
    try:
        with app.app_context():
            # Check if data exists
            if Song.query.first():
                print("Data already exists. Skipping minimal seed.")
                return

            # Dummy Data
            songs = [
                {"artist": "The Weeknd", "title": "Blinding Lights", "genre": "Pop", "bpm": 171},
                {"artist": "Daft Punk", "title": "Get Lucky", "genre": "Electronic", "bpm": 116},
                {"artist": "Fleetwood Mac", "title": "Dreams", "genre": "Rock", "bpm": 120},
                {"artist": "Kendrick Lamar", "title": "Humble", "genre": "Hip-Hop", "bpm": 150},
                {"artist": "Tame Impala", "title": "The Less I Know The Better", "genre": "Indie", "bpm": 117}
            ]

            for s_data in songs:
                song = Song(
                    artist=s_data['artist'],
                    title=s_data['title'],
                    genre=s_data['genre'],
                    bpm=s_data['bpm'],
                    decibel_peak=-8.0,
                    year=2020,
                    mainstream_score=90
                )
                db.session.add(song)
                db.session.flush()
                
                # Add a tag
                tag = SongTag(song_id=song.id, tag_name=s_data['genre'], count=100)
                db.session.add(tag)
            
            db.session.commit()
            print(f"Successfully added {len(songs)} minimal songs.")
            
    except Exception as e:
        print(f"Error seeding data: {e}")

if __name__ == "__main__":
    seed_minimal()
