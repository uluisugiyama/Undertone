"""
Academic Music Standards for Undertone.
Thresholds based on general music theory classifications.
"""

def is_fast_tempo(bpm):
    """
    Returns True if BPM > 120.
    Standard classification: 
    - Moderato: 108–120 BPM
    - Allegro: 120–156 BPM (Fast)
    """
    return bpm > 120

def is_heavy(decibel_peak):
    """
    Returns True if the decibel peak exceeds -10.0 dB.
    Note: Lower negative values are quieter (e.g., -20 is quieter than -10).
    Threshold for 'Heavy' in digital peak terms.
    """
    return decibel_peak > -10.0

# Genre Taxonomy Dictionary
# Maps sub-genres to parent categories for strict categorization.
GENRE_TAXONOMY = {
    # Rock & Metal
    "Punk Rock": "Rock",
    "Metalcore": "Metal",
    "Screamo": "Metal",
    "Grunge": "Rock",
    "Alternative Rock": "Rock",
    
    # Electronic
    "Techno": "Electronic",
    "House": "Electronic",
    "Dubstep": "Electronic",
    "Ambient": "Electronic",
    
    # Pop & Urban
    "Synthpop": "Pop",
    "K-Pop": "Pop",
    "Trap": "Hip-Hop",
    "R&B": "Urban",
    "Lo-fi": "Chill"
}

def get_parent_genre(genre):
    """Returns the parent category if it exists in the taxonomy, otherwise returns the genre itself."""
    return GENRE_TAXONOMY.get(genre, genre)
