import requests

BASE_URL = "http://127.0.0.1:5001/search/objective"

def test_filtering():
    print("Testing Objective Search API...")
    
    # Test 1: Fast & Heavy
    response = requests.get(BASE_URL, params={"tempo": "fast", "loudness": "heavy"})
    data = response.json()
    print(f"Fast & Heavy count: {len(data)}")
    for song in data:
        assert song['bpm'] > 120
        assert song['decibel_peak'] > -10.0
    
    # Test 2: Slow & Mellow
    response = requests.get(BASE_URL, params={"tempo": "slow", "loudness": "mellow"})
    data = response.json()
    print(f"Slow & Mellow count: {len(data)}")
    for song in data:
        assert song['bpm'] <= 120
        assert song['decibel_peak'] <= -10.0

    # Test 3: Specific Genre (Metalcore -> Metal)
    # Note: Search currently matches exact genre field, taxonomy mapping in search coming later or integrated
    response = requests.get(BASE_URL, params={"genre": "Metalcore"})
    data = response.json()
    print(f"Metalcore count: {len(data)}")
    for song in data:
        assert song['genre'] == "Metalcore"

    print("API Filtering tests passed!")

if __name__ == "__main__":
    try:
        test_filtering()
    except Exception as e:
        print(f"Test failed: {e}")
