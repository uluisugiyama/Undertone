import requests

class LastFMClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://ws.audioscrobbler.com/2.0/"

    def get_track_tags(self, artist, track):
        params = {
            "method": "track.getTopTags",
            "artist": artist,
            "track": track,
            "api_key": self.api_key,
            "format": "json",
            "autocorrect": 1
        }
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            # Extract tags
            tags_raw = data.get('toptags', {}).get('tag', [])
            # Return top 10 tags
            return [{"name": t['name'], "count": int(t.get('count', 0))} for t in tags_raw[:10]]
        except Exception as e:
            print(f"Error fetching tags for {artist} - {track}: {e}")
            return []

    def get_similar_tracks(self, artist, track):
        params = {
            "method": "track.getSimilar",
            "artist": artist,
            "track": track,
            "api_key": self.api_key,
            "format": "json",
            "autocorrect": 1,
            "limit": 5
        }
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            similar = data.get('similartracks', {}).get('track', [])
            return [{"artist": t['artist']['name'], "title": t['name']} for t in similar]
        except Exception as e:
            print(f"Error fetching similar tracks for {artist} - {track}: {e}")
            return []
