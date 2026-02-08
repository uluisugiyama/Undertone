import logging
import time
from backend.app import app, db, Song, SongAnalysis, enrich_song_analysis

def backfill():
    with app.app_context():
        # Get songs that need analysis
        analyzed_ids = [sa.song_id for sa in SongAnalysis.query.all()]
        songs = Song.query.filter(Song.id.notin_(analyzed_ids)).all()
        
        print(f"Found {len(songs)} songs to analyze.")
        
        for i, song in enumerate(songs):
            print(f"[{i+1}/{len(songs)}] Analyzing {song.title}...")
            enrich_song_analysis(song)
            time.sleep(2) # Rate limit

if __name__ == "__main__":
    backfill()
