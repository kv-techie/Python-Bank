import json
import os

class FeeManager:
    """Manages bank-wide fees and charges from a central configuration"""
    
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FEES_PATH = os.path.join(_BASE_DIR, "data", "fees.json")
    
    def __init__(self):
        self.fees = self._load_fees()
        
    def _load_fees(self):
        """Load fees from JSON file with defaults as fallback"""
        defaults = {
            "cheque_bounce_fee": 500.0,
            "amb_fee": 300.0,
            "loan_prepayment_penalty_percent": 2.0,
            "swift_base_charge": 500.0,
            "swift_step_charge": 1000.0,
            "atm_withdrawal_fee": 25.0,
            "min_balance_threshold": 10000.0
        }
        
        if not os.path.exists(self.FEES_PATH):
            return defaults
            
        try:
            with open(self.FEES_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                # Ensure all default keys exist in loaded config
                for k, v in defaults.items():
                    if k not in loaded:
                        loaded[k] = v
                return loaded
        except Exception as e:
            print(f"Error loading fees: {e}")
            return defaults
            
    def get_fee(self, key: str, default=0.0) -> float:
        """Get a specific fee value"""
        return self.fees.get(key, default)
        
    def update_fee(self, key: str, value: float) -> bool:
        """Update a fee value and persist to disk"""
        self.fees[key] = float(value)
        return self.save()
        
    def save(self) -> bool:
        """Save current fees to JSON"""
        try:
            os.makedirs(os.path.dirname(self.FEES_PATH), exist_ok=True)
            with open(self.FEES_PATH, "w", encoding="utf-8") as f:
                json.dump(self.fees, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving fees: {e}")
            return False

# Global instance
fee_manager = FeeManager()
