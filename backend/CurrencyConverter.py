import json
import urllib.request
import urllib.error
import os
from datetime import datetime, date
from typing import Dict, Optional

class CurrencyConverter:
    """Handles real-time currency conversion using ExchangeRate-API with local caching"""
    
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    _CACHE_FILE = os.path.join(_BASE_DIR, "data", "currency_rates.json")
    _API_URL = "https://api.exchangerate-api.com/v4/latest/INR"
    
    _rates = {}
    _last_updated = None

    @staticmethod
    def _load_cache():
        """Load rates from local cache"""
        if not CurrencyConverter._rates:
            if os.path.exists(CurrencyConverter._CACHE_FILE):
                try:
                    with open(CurrencyConverter._CACHE_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        CurrencyConverter._rates = data.get("rates", {})
                        CurrencyConverter._last_updated = data.get("date", "")
                except Exception:
                    CurrencyConverter._rates = {}
            else:
                CurrencyConverter._rates = {}

    @staticmethod
    def _save_cache(data: Dict):
        """Save rates to local cache"""
        try:
            os.makedirs(os.path.dirname(CurrencyConverter._CACHE_FILE), exist_ok=True)
            with open(CurrencyConverter._CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass

    @staticmethod
    def get_latest_rates() -> Dict:
        """Fetch latest rates from API or return cached ones if fresh"""
        CurrencyConverter._load_cache()
        
        today = date.today().isoformat()
        
        # If cache is from today, use it to avoid redundant API calls
        if CurrencyConverter._last_updated == today and CurrencyConverter._rates:
            return CurrencyConverter._rates
            
        # Otherwise, try to fetch fresh rates from API
        try:
            req = urllib.request.Request(CurrencyConverter._API_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    rates = data.get("rates", {})
                    if rates:
                        CurrencyConverter._rates = rates
                        CurrencyConverter._last_updated = today
                        CurrencyConverter._save_cache({"date": today, "rates": rates})
                        return rates
        except Exception:
            # If network fails, return whatever we have in cache
            pass
            
        return CurrencyConverter._rates

    @staticmethod
    def get_exchange_rate(currency: str) -> float:
        """Get 1 Unit of foreign currency in INR (e.g. 1 USD = 83.12 INR)"""
        rates = CurrencyConverter.get_latest_rates()
        if not rates or currency not in rates:
            # Fallback to some common hardcoded rates if even cache is empty
            defaults = {
                "USD": 83.12, "EUR": 90.45, "GBP": 105.30, 
                "AED": 22.63, "SGD": 61.75, "AUD": 54.20,
                "CAD": 60.85, "JPY": 0.56, "CHF": 92.10
            }
            return defaults.get(currency.upper(), 0.0)
            
        # 1 INR = rate foreign
        # 1 foreign = 1 / rate INR
        return round(1 / rates[currency.upper()], 4)

    @staticmethod
    def convert_to_inr(amount: float, currency: str) -> float:
        """Convert foreign amount to INR"""
        rate = CurrencyConverter.get_exchange_rate(currency)
        return round(amount * rate, 2)

    @staticmethod
    def convert_from_inr(amount: float, currency: str) -> float:
        """Convert INR amount to foreign currency"""
        rate = CurrencyConverter.get_exchange_rate(currency)
        if rate == 0: return 0.0
        return round(amount / rate, 2)
