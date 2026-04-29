import os
import random
import threading
from datetime import datetime


class NachIdGenerator:
    _used_nach_ids = set()
    _lock = threading.Lock()
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    _storage_file = os.path.join(_BASE_DIR, "data", "nach_ids.txt")

    @classmethod
    def _load_used_ids(cls):
        if os.path.exists(cls._storage_file):
            with open(cls._storage_file, "r", encoding="utf-8") as file:
                cls._used_nach_ids = set(line.strip() for line in file if line.strip())

    @classmethod
    def _save_used_ids(cls):
        os.makedirs(os.path.dirname(cls._storage_file), exist_ok=True)
        with open(cls._storage_file, "w", encoding="utf-8") as file:
            for nach_id in cls._used_nach_ids:
                file.write(nach_id + "\n")

    @classmethod
    def generate_nach_id(cls) -> str:
        cls._load_used_ids()
        date_str = datetime.now().strftime("%Y%m%d")

        with cls._lock:
            for _ in range(100):
                suffix = f"{random.randint(0, 999999):06d}"
                nach_id = f"NACH{date_str}{suffix}"

                if nach_id not in cls._used_nach_ids:
                    cls._used_nach_ids.add(nach_id)
                    cls._save_used_ids()
                    return nach_id

            raise Exception("Failed to generate unique NACH ID after 100 attempts")
