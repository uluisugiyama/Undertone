from app import app, db
from models import Song, SongTag
from lastfm_client import LastFMClient
import time

# Use the provided API Key
LASTFM_API_KEY = "3f37633189fe9607a8eb374c727e5b65"

def enrich_songs():
    client = LastFMClient(LASTFM_API_KEY)
    
    with app.app_context():
        songs = Song.query.all()
        print(f"Starting enrichment for {len(songs)} songs...")
        
        for song in songs:
            if not song.artist or not song.title:
                continue
            
            print(f"Fetching tags for: {song.artist} - {song.title}")
            tags = client.get_track_tags(song.artist, song.title)
            
            # Clear existing tags for this song to avoid duplicates if re-running
            SongTag.query.filter_by(song_id=song.id).delete()
            
            for t_data in tags:
                new_tag = SongTag(
                    song_id=song.id,
                    tag_name=t_data['name'],
                    count=t_data['count']
                )
                db.session.add(new_tag)
            
            db.session.commit()
            # Brief sleep to be polite to the API
            time.sleep(0.5)

        print("Enrichment complete.")

if __name__ == "__main__":
    enrich_songs()
