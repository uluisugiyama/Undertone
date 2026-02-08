import os
import sys

# Mocking app context for testing discovery engine
from backend.discovery_engine import FeatureDictionary, DiscoveryEngine

class MockAnalysis:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

def run_tests():
    print("--- STARTING DISCOVERY VERIFICATION ---")
    
    # 1. Test "Fast but Relaxed" (Bossa Nova / Lounge case)
    # Fast tempo but low percussive density and high calm_energetic (relaxing)
    bossa_nova = MockAnalysis(
        tempo_feel="fast",
        percussive_density=0.2,
        rhythmic_aggressiveness=0.1,
        calm_energetic=0.2, # 0.0 = Calm, 1.0 = Energetic in some systems, let's check DICTIONARY
        # In FeatureDictionary: 
        # "energetic": {"calm_energetic": (0.7, 1.0)} -> so 0.2 is Calm.
        harmonic_tension=0.2,
        spatial_width=0.8
    )
    
    intent = ["fast", "minimal"]
    target_vector, _ = FeatureDictionary.expand_intent(intent)
    score, details = DiscoveryEngine.calculate_similarity(bossa_nova, target_vector)
    
    print(f"\nTEST 1: 'Fast' + 'Minimal'")
    print(f"Bossa Nova Score: {score:.2f}")
    print(f"Reasoning: {details}")
    
    # 2. Test "Dark and Melodic"
    emo_track = MockAnalysis(
        dark_bright=0.1,
        harmonic_tension=0.8,
        key_modality="Minor",
        chord_complexity=0.7,
        vocal_presence=0.8
    )
    
    intent = ["dark", "melodic"]
    target_vector, _ = FeatureDictionary.expand_intent(intent)
    score, details = DiscoveryEngine.calculate_similarity(emo_track, target_vector)
    
    print(f"\nTEST 2: 'Dark' + 'Melodic'")
    print(f"Emo Track Score: {score:.2f}")
    print(f"Reasoning: {details}")

    # 3. Test "Heavy" (Metal case)
    metal_track = MockAnalysis(
        rhythmic_aggressiveness=0.9,
        percussive_density=0.9,
        instrument_density=0.9,
        vocal_distortion=0.8,
        calm_energetic=0.9,
        dynamic_range_compression=0.8
    )
    
    intent = ["heavy"]
    target_vector, _ = FeatureDictionary.expand_intent(intent)
    score, details = DiscoveryEngine.calculate_similarity(metal_track, target_vector)
    
    print(f"\nTEST 3: 'Heavy'")
    print(f"Metal Track Score: {score:.2f}")
    print(f"Reasoning: {details}")

    print("\n--- VERIFICATION COMPLETE ---")

if __name__ == "__main__":
    run_tests()
