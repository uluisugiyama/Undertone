import random
import time
import os
from dotenv import load_dotenv
from backend.app import app, db
from backend.models import Song
from backend.music_standards import GENRE_TAXONOMY
from backend.lastfm_client import LastFMClient

load_dotenv()
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")

def seed_real_data():
    client = LastFMClient(LASTFM_API_KEY)
    
    with app.app_context():
        print("Clearing existing songs...")
        Song.query.delete()
        db.session.commit()
        
        genres = list(GENRE_TAXONOMY.keys())
        total_songs = 0
        target_total = 100
        songs_per_genre = 10
        
        print(f"Starting real data ingestion for {len(genres)} genres...")
        
        for genre in genres:
            if total_songs >= target_total:
                break
                
            print(f"Fetching top tracks for genre: {genre}")
            tracks = client.get_top_tracks_by_tag(genre, limit=songs_per_genre)
            
            if not tracks:
                # Try parent genre if subgenre returns nothing
                parent = GENRE_TAXONOMY[genre]
                if parent:
                    print(f"  No tracks for {genre}, trying parent: {parent}")
                    tracks = client.get_top_tracks_by_tag(parent, limit=songs_per_genre)
            
            for t_data in tracks:
                # Check if song already exists to avoid duplicates
                existing = Song.query.filter_by(artist=t_data['artist'], title=t_data['title']).first()
                if existing:
                    continue
                
                # Create song with real metadata and randomized objective traits
                # (Traits will be refined in Phase 10)
                song = Song(
                    artist=t_data['artist'],
                    title=t_data['title'],
                    genre=genre,
                    bpm=random.randint(60, 180),
                    decibel_peak=round(random.uniform(-25.0, -5.0), 1),
                    year=random.randint(1990, 2024),
                    mainstream_score=0 # Will be updated by enrich_data.py
                )
                db.session.add(song)
                total_songs += 1
            
            db.session.commit()
            print(f"  Added {len(tracks)} tracks for {genre}. Total: {total_songs}")
            # Be polite to API
            time.sleep(0.5)

        print(f"Successfully ingested {total_songs} real songs from Last.fm.")

if __name__ == "__main__":
    seed_real_data()
