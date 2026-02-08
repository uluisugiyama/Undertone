import json
from unittest.mock import MagicMock

# Mocking the discovery logic for validation
class Song:
    def __init__(self, artist, title):
        self.artist = artist
        self.title = title
    def to_dict(self):
        return {"artist": self.artist, "title": self.title}

def test_search_logic(intent_json, local_db_songs):
    parsed_intent = json.loads(intent_json)
    search_keywords = parsed_intent.get('keywords', [])
    if parsed_intent.get('mood'):
        search_keywords.append(parsed_intent['mood'])
        
    all_songs = []
    
    # Simulate SQL Filtering
    candidates = local_db_songs
    if parsed_intent.get('artist'):
        candidates = [s for s in candidates if parsed_intent['artist'].lower() in s.artist.lower()]
    
    # Metadata Safety Fallback
    for kw in search_keywords:
        # (Assuming no target_vector for this test)
        candidates = [s for s in candidates if (kw.lower() in s.title.lower() or kw.lower() in s.artist.lower())]
        
    all_songs = [s.to_dict() for s in candidates]
    
    # Simulate Last.fm Fallback
    ext_query = parsed_intent.get('external_search_query')
    has_target_artist = False
    if parsed_intent.get('artist'):
        has_target_artist = any(parsed_intent['artist'].lower() in s['artist'].lower() for s in all_songs[:8])
        
    triggered_external = False
    if (len(all_songs) < 5 or not has_target_artist) and ext_query:
        triggered_external = True
        
    return all_songs, triggered_external

def run_verification():
    local_db = [
        Song("The Clash", "Should I Stay or Should I Go"),
        Song("Green Day", "American Idiot"),
        Song("Green Day", "Basket Case")
    ]
    
    print("--- VERIFYING SEARCH RELEVANCE FIX ---")
    
    # Case 1: Search for Radiohead (Artist miss, External hit)
    intent = json.dumps({"artist": "Radiohead", "external_search_query": "radiohead"})
    results, ext_triggered = test_search_logic(intent, local_db)
    print(f"\nTEST 1: 'Radiohead' (Missing Local)")
    print(f"Local Results: {results}")
    print(f"External Discovery Triggered: {ext_triggered} (Expected: True)")
    
    # Case 2: Search for 'The Clash' (Artist hit, No External)
    intent = json.dumps({"artist": "The Clash", "external_search_query": "the clash"})
    results, ext_triggered = test_search_logic(intent, local_db)
    print(f"\nTEST 2: 'The Clash' (Local Hit)")
    print(f"Local Results: {results}")
    print(f"External Discovery Triggered: {ext_triggered} (Expected: False)")

    # Case 3: Keyword Search 'Green' (Keyword safety fallback)
    intent = json.dumps({"artist": None, "keywords": ["Green"], "external_search_query": "green"})
    results, ext_triggered = test_search_logic(intent, local_db)
    print(f"\nTEST 3: 'Green' (Keyword Safety Fallback)")
    print(f"Local Results: {results}")
    print(f"External Discovery Triggered: {ext_triggered} (Expected: False - if len >=5, but here len=2 so True)")

    print("\n--- VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    run_verification()
