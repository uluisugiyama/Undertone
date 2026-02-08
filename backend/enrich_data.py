import os
from dotenv import load_dotenv
from app import app, db
from models import Song, SongTag
from lastfm_client import LastFMClient
import time
import math

load_dotenv()
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")

def calculate_mainstream_score(listeners):
    if listeners <= 0:
        return 0
    # Logarithmic scale: 10M listeners -> 100, 1M -> 86, 100k -> 71, 10k -> 57, 1k -> 43, 100 -> 28, 10 -> 14
    # formula: min(100, log10(listeners) * 14.3)
    score = int(math.log10(listeners) * 14.3)
    return min(100, max(0, score))

def enrich_songs():
    client = LastFMClient(LASTFM_API_KEY)
    
    with app.app_context():
        # Only enrich songs that haven't been enriched yet (mainstream_score is 0)
        songs = Song.query.filter_by(mainstream_score=0).all()
        print(f"Starting enrichment for {len(songs)} songs...")
        
        for song in songs:
            if not song.artist or not song.title:
                continue
            
            print(f"Fetching data for: {song.artist} - {song.title}")
            
            # 1. Fetch Tags
            tags = client.get_track_tags(song.artist, song.title)
            SongTag.query.filter_by(song_id=song.id).delete()
            for t_data in tags:
                new_tag = SongTag(
                    song_id=song.id,
                    tag_name=t_data['name'],
                    count=t_data['count']
                )
                db.session.add(new_tag)
            
            # 2. Fetch Popularity (Track Info)
            info = client.get_track_info(song.artist, song.title)
            listeners = info.get('listeners', 0)
            song.mainstream_score = calculate_mainstream_score(listeners)
            print(f"  Listeners: {listeners}, Calculated Score: {song.mainstream_score}")
            
            db.session.commit()
            # Brief sleep to be polite to the API
            time.sleep(0.2)

        print("Enrichment complete.")

if __name__ == "__main__":
    enrich_songs()
