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
            tags_raw = data.get('toptags', {}).get('tag', [])
            return [{"name": t['name'], "count": int(t.get('count', 0))} for t in tags_raw[:10]]
        except Exception as e:
            print(f"Error fetching tags for {artist} - {track}: {e}")
            return []

    def get_track_info(self, artist, track):
        params = {
            "method": "track.getInfo",
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
            track_info = data.get('track', {})
            listeners = int(track_info.get('listeners', 0))
            return {"listeners": listeners}
        except Exception as e:
            print(f"Error fetching track info for {artist} - {track}: {e}")
            return {"listeners": 0}

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

    def get_top_tracks_by_tag(self, tag, limit=10):
        params = {
            "method": "tag.getTopTracks",
            "tag": tag,
            "api_key": self.api_key,
            "format": "json",
            "limit": limit
        }
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            tracks = data.get('tracks', {}).get('track', [])
            return [{"artist": t['artist']['name'], "title": t['name']} for t in tracks]
        except Exception as e:
            print(f"Error fetching top tracks for tag {tag}: {e}")
            return []

    def search_track(self, query, limit=10):
        params = {
            "method": "track.search",
            "track": query,
            "api_key": self.api_key,
            "format": "json",
            "limit": limit
        }
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            tracks = data.get('results', {}).get('trackmatches', {}).get('track', [])
            return [{"artist": t['artist'], "title": t['name']} for t in tracks]
        except Exception as e:
            print(f"Error searching for track {query}: {e}")
            return []
