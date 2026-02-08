from app import app, db, calculate_mainstream_score
from models import Song, SongTag
from lastfm_client import LastFMClient
import time
import random

LASTFM_API_KEY = "3f37633189fe9607a8eb374c727e5b65"

def refine_algorithms():
    """
    Phase 11: Refine scores and tags for all songs in the database.
    This simulates a cron job that keeps the data fresh and accurate.
    """
    client = LastFMClient(LASTFM_API_KEY)
    
    with app.app_context():
        songs = Song.query.all()
        print(f"Refining {len(songs)} songs...")
        
        for song in songs:
            try:
                # 1. Update Popularity
                info = client.get_track_info(song.artist, song.title)
                new_score = calculate_mainstream_score(info.get('listeners', 0))
                
                if new_score != song.mainstream_score:
                    print(f"  Updating {song.title}: {song.mainstream_score} -> {new_score}")
                    song.mainstream_score = new_score
                
                # 2. Refine Tags (Merge new tags, update counts)
                tags = client.get_track_tags(song.artist, song.title)
                if tags:
                    # In a real refinement, we might want to keep user tags and merge
                    # For now just refresh
                    # SongTag.query.filter_by(song_id=song.id).delete()
                    existing_tags = {t.tag_name: t for t in song.tags}
                    for t_data in tags:
                        name = t_data['name']
                        if name in existing_tags:
                            existing_tags[name].count = t_data['count']
                        else:
                            new_tag = SongTag(song_id=song.id, tag_name=name, count=t_data['count'])
                            db.session.add(new_tag)
                            
                # 3. Phase 12: Flagging contradictions
                # (e.g. if the song is tagged 'heavy' but has low decibel peak)
                is_heavy_db = song.decibel_peak > -10.0
                tag_names = [t['name'].lower() for t in tags]
                
                song.is_contradictory = False
                song.contradiction_reason = None

                if 'heavy metal' in tag_names and not is_heavy_db:
                    song.is_contradictory = True
                    song.contradiction_reason = f"Tagged 'heavy metal' but decibel peak is low ({song.decibel_peak} dB)"
                elif 'ambient' in tag_names and song.bpm > 130:
                    song.is_contradictory = True
                    song.contradiction_reason = f"Tagged 'ambient' but BPM is high ({song.bpm})"
                
                if song.is_contradictory:
                    print(f"  [FLAGGED] {song.title}: {song.contradiction_reason}")
                
                db.session.commit()
                time.sleep(0.2) # Polite
            except Exception as e:
                print(f"  Error refining {song.title}: {e}")
                db.session.rollback()

if __name__ == "__main__":
    refine_algorithms()
