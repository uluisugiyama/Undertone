import random
import time
import os
from dotenv import load_dotenv
from backend.app import app, db
from backend.models import Song, SongTag
from backend.music_standards import GENRE_TAXONOMY, get_parent_genre
from backend.lastfm_client import LastFMClient

LASTFM_API_KEY = "3f37633189fe9607a8eb374c727e5b65"

def bulk_load():
    client = LastFMClient(LASTFM_API_KEY)
    
    with app.app_context():
        print("Starting bulk data load...")
        
        genres = list(GENRE_TAXONOMY.keys())
        total_added = 0
        
        # 1. Load by Genres (to ensure coverage)
        print("Loading by genres...")
        for genre in genres:
            print(f"Fetching 50 tracks for {genre}...")
            tracks = client.get_top_tracks_by_tag(genre, limit=50)
            
            for t_data in tracks:
                existing = Song.query.filter_by(artist=t_data['artist'], title=t_data['title']).first()
                if not existing:
                    song = Song(
                        artist=t_data['artist'],
                        title=t_data['title'],
                        genre=genre,
                        bpm=random.randint(60, 180),
                        decibel_peak=round(random.uniform(-25.0, -5.0), 1),
                        year=random.randint(1970, 2024),
                        mainstream_score=0
                    )
                    db.session.add(song)
                    total_added += 1
            
            db.session.commit()
            print(f"  Processed {genre}. Total songs in DB: {Song.query.count()}")
            time.sleep(0.3)

        # 2. Load Global Top Charts (for more 'lots' of songs)
        print("Loading global top charts (multiple pages)...")
        for page in range(1, 6): # 5 pages of 50 = 250 songs
            print(f"Fetching global chart page {page}...")
            tracks = client.get_global_top_tracks(limit=50, page=page)
            
            for t_data in tracks:
                existing = Song.query.filter_by(artist=t_data['artist'], title=t_data['title']).first()
                if not existing:
                    # For global tracks, we might not know the genre yet, 
                    # use 'Pop' as fallback or try to fetch tags (slow)
                    # For now, let's just use 'Pop' and let enrichment handle it if we add tag-based genre detection later
                    song = Song(
                        artist=t_data['artist'],
                        title=t_data['title'],
                        genre='Pop', 
                        bpm=random.randint(60, 180),
                        decibel_peak=round(random.uniform(-25.0, -5.0), 1),
                        year=random.randint(1970, 2024),
                        mainstream_score=0
                    )
                    db.session.add(song)
                    total_added += 1
            
            db.session.commit()
            print(f"  Processed page {page}. Total songs in DB: {Song.query.count()}")
            time.sleep(0.3)

        print(f"Bulk load complete. Added {total_added} new songs.")

if __name__ == "__main__":
    bulk_load()
