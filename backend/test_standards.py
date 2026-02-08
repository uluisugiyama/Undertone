import pytest
from backend.music_standards import is_fast_tempo, is_heavy, get_parent_genre

def test_standards():
    print("Testing Music Standards...")
    
    # Test Tempo
    assert is_fast_tempo(130) == True
    assert is_fast_tempo(110) == False
    print("Tempo logic: OK")
    
    # Test Heaviness
    assert is_heavy(-5.0) == True
    assert is_heavy(-15.0) == False
    print("Heaviness logic: OK")
    
    # Test Taxonomy
    assert get_parent_genre("Punk Rock") == "Rock"
    assert get_parent_genre("Metalcore") == "Metal"
    assert get_parent_genre("Jazz") == "Jazz" # Default
    print("Taxonomy logic: OK")
    
    print("All Phase 2 tests passed!")

if __name__ == "__main__":
    test_standards()
