from typing import Dict, Any, List
from loguru import logger

class FeatureExtractor:
    def extract(self, tick: Dict[str, Any]) -> List[float]:
        """
        Extract features from a GSI tick.
        Returns a list of floats expected by the XGBoost model.
        """
        try:
            # Basic feature extraction based on standard GSI structure
            # This is a simplified example. Real model needs specific features.
            
            map_data = tick.get('map', {})
            hero_data = tick.get('hero', {}) # This is usually local player specific in standard GSI, 
                                             # but for a spectator GSI it might have all heroes.
                                             # Assuming we are parsing a spectator-like GSI or aggregating.
            
            # For this "Lite" version, let's assume we extract:
            # 1. Game Time
            # 2. Radiant Gold Lead (if available, else 0)
            # 3. Radiant XP Lead (if available, else 0)
            
            game_time = map_data.get('clock_time', 0)
            
            # NOTE: Standard GSI often doesn't give global gold lead directly unless configured specifically.
            # We will try to extract what we can or default to 0.
            radiant_gold = 0
            dire_gold = 0
            radiant_xp = 0
            dire_xp = 0
            
            # If the GSI payload contains team data (Spectator GSI)
            if 'map' in tick:
                # Some GSI integrations provide win_chance directly or team stats
                pass

            # Placeholder features: [Time, GoldDiff, XPDiff]
            # In a real scenario, we would iterate over players to sum net worth if available.
            
            gold_diff = radiant_gold - dire_gold
            xp_diff = radiant_xp - dire_xp
            
            return [float(game_time), float(gold_diff), float(xp_diff)]

        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return [0.0, 0.0, 0.0] # Return safe default
