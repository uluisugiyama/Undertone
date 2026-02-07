import random
from app import app, db
from models import Song
from music_standards import GENRE_TAXONOMY

# Realistic mappings for 50-song seed
ARTIST_TRACK_POOL = {
    "Metalcore": [
        ("As I Lay Dying", "Confined"),
        ("August Burns Red", "Marianas Trench"),
        ("Killswitch Engage", "The End of Heartache"),
        ("Bring Me The Horizon", "Shadow Moses"),
        ("Architects", "Doomsday"),
        ("Parkway Drive", "Carrion"),
        ("All That Remains", "Two Weeks")
    ],
    "Rock": [
        ("Arctic Monkeys", "Do I Wanna Know?"),
        ("Foo Fighters", "Everlong"),
        ("Nirvana", "Smells Like Teen Spirit"),
        ("The Killers", "Mr. Brightside"),
        ("Red Hot Chili Peppers", "Californication"),
        ("Queens of the Stone Age", "No One Knows")
    ],
    "Industrial": [
        ("Nine Inch Nails", "Closer"),
        ("Marilyn Manson", "The Beautiful People"),
        ("Rammstein", "Du Hast"),
        ("Ministry", "Stigmata"),
        ("Fear Factory", "Replica")
    ],
    "Jazz": [
        ("Miles Davis", "So What"),
        ("John Coltrane", "Giant Steps"),
        ("Dave Brubeck", "Take Five"),
        ("Thelonious Monk", "Round Midnight"),
        ("Charles Mingus", "Goodbye Pork Pie Hat")
    ],
    "Electronic": [
        ("Daft Punk", "One More Time"),
        ("The Chemical Brothers", "Galvanize"),
        ("Aphex Twin", "Windowlicker"),
        ("Justice", "D.A.N.C.E."),
        ("Deadmau5", "Strobe")
    ],
    "Classical": [
        ("Ludwig van Beethoven", "Symphony No. 5"),
        ("Wolfgang Amadeus Mozart", "Lacrimosa"),
        ("Johann Sebastian Bach", "Toccata and Fugue in D Minor"),
        ("Frédéric Chopin", "Nocturne op.9 No.2")
    ]
}

def seed_data():
    with app.app_context():
        # Clear existing songs
        Song.query.delete()
        
        genres = list(GENRE_TAXONOMY.keys())
        
        for i in range(50):
            genre = random.choice(genres)
            parent = GENRE_TAXONOMY[genre]
            
            # Pick a realistic artist/track if available, otherwise generic
            pool = ARTIST_TRACK_POOL.get(genre) or ARTIST_TRACK_POOL.get(parent)
            if pool:
                artist, title = random.choice(pool)
            else:
                artist, title = f"Artist {i}", f"Song Title {i}"

            song = Song(
                artist=artist,
                title=title,
                genre=genre,
                bpm=random.randint(60, 200),
                decibel_peak=round(random.uniform(-30.0, -2.0), 1),
                year=random.randint(1970, 2024),
                mainstream_score=random.randint(0, 100)
            )
            db.session.add(song)
        
        db.session.commit()
        print("Successfully seeded 50 songs with artist/title info.")

if __name__ == "__main__":
    seed_data()
