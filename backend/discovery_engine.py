import math
import json

class FeatureDictionary:
    """
    Maps user language to high-dimensional feature vectors based on 
    measurable musical attributes.
    """
    
    DICTIONARY = {
        "slow": {
            "tempo_feel": "slow",
            "percussive_density": (0.0, 0.4),
            "rhythmic_aggressiveness": (0.0, 0.3),
            "groove_complexity": (0.0, 0.5),
            "reverb_density": (0.3, 1.0)
        },
        "sad": {
            "dark_bright": (0.0, 0.3),
            "calm_energetic": (0.0, 0.4),
            "harmonic_tension": (0.5, 0.9),
            "key_modality": ["Minor", "Modal"],
            "vocal_presence": (0.6, 1.0),
            "tempo_feel": ["slow", "medium"]
        },
        "screaming": {
            "vocal_style": ["screaming"],
            "vocal_distortion": (0.7, 1.0),
            "vocal_instr_ratio": (0.6, 1.0),
            "rhythmic_aggressiveness": (0.6, 1.0),
            "harmonic_tension": (0.5, 1.0)
        },
        "atmospheric": {
            "reverb_density": (0.6, 1.0),
            "spatial_width": (0.7, 1.0),
            "instrument_separation": (0.3, 1.0),
            "percussive_density": (0.0, 0.5),
            "analog_digital_feel": (0.4, 0.8)
        },
        "energetic": {
            "calm_energetic": (0.7, 1.0),
            "percussive_density": (0.6, 1.0),
            "rhythmic_aggressiveness": (0.6, 1.0),
            "loudness_progression": ["Rising", "Waves", "Constant"],
            "instrument_density": (0.6, 1.0)
        },
        "lofi": {
            "analog_digital_feel": (0.0, 0.4),
            "instrument_separation": (0.0, 0.4),
            "reverb_density": (0.2, 0.6),
            "spatial_width": (0.0, 0.5),
            "percussive_density": (0.1, 0.4)
        },
        "melodic": {
            "harmonic_tension": (0.0, 0.4),
            "chord_complexity": (0.4, 1.0),
            "key_modality": ["Major", "Modal"],
            "vocal_presence": (0.5, 1.0),
            "spatial_width": (0.4, 0.8),
            "instrument_density": (0.3, 0.7)
        },
        "heavy": {
            "rhythmic_aggressiveness": (0.7, 1.0),
            "percussive_density": (0.7, 1.0),
            "instrument_density": (0.7, 1.0),
            "vocal_distortion": (0.4, 1.0),
            "calm_energetic": (0.7, 1.0),
            "dynamic_range_compression": (0.6, 1.0)
        },
        "dark": {
            "dark_bright": (0.0, 0.3),
            "harmonic_tension": (0.6, 1.0),
            "calm_energetic": (0.0, 0.6),
            "reverb_density": (0.4, 1.0),
            "vocal_register": ["low"],
            "key_modality": ["Minor"]
        },
        "happy": {
            "dark_bright": (0.7, 1.0),
            "calm_energetic": (0.6, 1.0),
            "key_modality": ["Major"],
            "harmonic_tension": (0.0, 0.3),
            "rhythmic_aggressiveness": (0.0, 0.4)
        },
        "minimal": {
            "instrument_density": (0.0, 0.3),
            "percussive_density": (0.0, 0.4),
            "spatial_width": (0.0, 0.4),
            "vocal_presence": (0.0, 0.5),
            "groove_complexity": (0.0, 0.4)
        },
        "orchestral": {
            "instrument_density": (0.7, 1.0),
            "chord_complexity": (0.6, 1.0),
            "spatial_width": (0.7, 1.0),
            "analog_digital_feel": (0.0, 0.3),
            "section_count": (5, 12)
        },
        "rock": {
            "instrument_density": (0.5, 0.9),
            "percussive_density": (0.5, 0.9),
            "calm_energetic": (0.5, 0.9),
            "analog_digital_feel": (0.0, 0.6)
        },
        "pop": {
            "analog_digital_feel": (0.6, 1.0),
            "percussive_density": (0.4, 0.8),
            "vocal_presence": (0.7, 1.0),
            "harmonic_tension": (0.0, 0.4)
        },
        "jazz": {
            "chord_complexity": (0.7, 1.0),
            "instrument_separation": (0.6, 1.0),
            "groove_complexity": (0.5, 1.0),
            "tempo_stability": (0.2, 0.7)
        },
        "electronic": {
            "analog_digital_feel": (0.7, 1.0),
            "percussive_density": (0.6, 1.0),
            "spatial_width": (0.6, 1.0),
            "reverb_density": (0.3, 0.8)
        }
    }

    @classmethod
    def expand_intent(cls, keywords):
        """
        Decomposes keywords into a unified target vector.
        Supports compound intents by atomizing multi-word phrases.
        Returns (target_vector, matched_keywords)
        """
        target_vector = {}
        matched_keywords = []
        
        # Atomize: Split "sad rock" into ["sad", "rock"] if the full phrase doesn't exist
        for kw in keywords:
            kw = kw.lower().strip()
            if kw in cls.DICTIONARY:
                matched_keywords.append(kw)
            else:
                # If compound phrase not found, try individual words
                words = kw.split()
                if len(words) > 1:
                    for word in words:
                        if word in cls.DICTIONARY:
                            matched_keywords.append(word)
                else:
                    # Keep unmapped keywords in stats but they won't have vector data
                    pass

        for kw in matched_keywords:
            if kw in cls.DICTIONARY:
                for feature, val in cls.DICTIONARY[kw].items():
                    if feature not in target_vector:
                        target_vector[feature] = []
                    target_vector[feature].append(val)
                    
        return target_vector, matched_keywords

class DiscoveryEngine:
    """
    Ranks songs based on similarity to a target feature vector.
    Handles competing constraints and partial matches.
    """
    
    @staticmethod
    def calculate_similarity(song_analysis, target_vector):
        if not song_analysis:
            return 0.0, []
        
        score = 0.0
        details = []
        total_weight = 0
        
        for feature, targets in target_vector.items():
            val = getattr(song_analysis, feature, None)
            if val is None:
                continue
            
            total_weight += 1
            feature_match = 0.0
            
            # Distance calculation depends on target type
            for target in targets:
                # Numeric Range
                if isinstance(target, tuple):
                    min_val, max_val = target
                    if min_val <= val <= max_val:
                        feature_match = 1.0
                    else:
                        # Euclidean distance penalty
                        dist = min(abs(val - min_val), abs(val - max_val))
                        feature_match = max(0, 1.0 - (dist * 2)) 
                
                # Categorical Match
                elif isinstance(target, list):
                    if val in target:
                        feature_match = 1.0
                    else:
                        feature_match = 0.0
                
                # Exact Match
                elif val == target:
                    feature_match = 1.0
            
            score += feature_match
            if feature_match > 0.7:
                details.append(f"Strong match on {feature}")
            elif feature_match > 0.3:
                details.append(f"Partial match on {feature}")

        final_score = (score / total_weight) if total_weight > 0 else 0.5
        return final_score, details

if __name__ == "__main__":
    # Test expansion
    expanded = FeatureDictionary.expand_intent(["slow", "sad"])
    print(f"Expanded Vector: {expanded}")
