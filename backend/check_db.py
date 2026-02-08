from backend.app import app, db
from backend.models import Song, SongTag, SongAnalysis

with app.app_context():
    song_count = Song.query.count()
    tag_count = SongTag.query.count()
    analysis_count = SongAnalysis.query.count()
    
    print(f"Songs: {song_count}")
    print(f"Tags: {tag_count}")
    print(f"Analyses: {analysis_count}")
    
    if song_count > 0:
        sample_song = Song.query.first()
        print(f"Sample Song: {sample_song.artist} - {sample_song.title}")
        print(f"Tags: {[t.tag_name for t in sample_song.tags[:5]]}")
        analysis = SongAnalysis.query.filter_by(song_id=sample_song.id).first()
        if analysis:
            print(f"Analysis exists for sample song: {analysis.dark_bright}, {analysis.calm_energetic}")
        else:
            print("No analysis for sample song.")
