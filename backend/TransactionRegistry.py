import os
import json
import random
import shutil
from threading import Lock
from typing import Set


class TransactionRegistry:
    """
    Registry for managing unique transaction IDs
    Ensures no duplicate transaction IDs are generated
    """
    
    _FILE_PATH = "data/transaction_ids.json"
    _MAX_ATTEMPTS = 1000
    _PREFIX = "FHIC"
    
    _ids: Set[str] = set()
    _lock = Lock()
    _initialized = False
    
    @classmethod
    def _initialize(cls):
        """Initialize the registry by loading existing IDs from file"""
        if cls._initialized:
            return
        
        with cls._lock:
            if cls._initialized:  # Double-check after acquiring lock
                return
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(cls._FILE_PATH), exist_ok=True)
            
            # Load existing IDs if file exists
            if os.path.exists(cls._FILE_PATH):
                try:
                    with open(cls._FILE_PATH, 'r', encoding='utf-8') as f:
                        loaded_ids = json.load(f)
                        if isinstance(loaded_ids, list):
                            cls._ids = set(loaded_ids)
                        else:
                            cls._ids = set()
                except Exception as e:
                    print(f"⚠️ Warning: failed to load transaction ids: {e}")
                    cls._ids = set()
            
            cls._initialized = True
    
    @classmethod
    def generate_id(cls) -> str:
        """
        Generate a unique transaction ID
        
        Returns:
            A unique transaction ID in format "FHIC##########"
            
        Raises:
            RuntimeError: If unable to generate unique ID after MAX_ATTEMPTS
        """
        cls._initialize()
        
        with cls._lock:
            attempts = 0
            new_id = ""
            
            while attempts < cls._MAX_ATTEMPTS:
                attempts += 1
                
                # Generate ID: PREFIX + 10 random digits
                random_digits = ''.join(str(random.randint(0, 9)) for _ in range(10))
                new_id = cls._PREFIX + random_digits
                
                if new_id not in cls._ids:
                    cls._ids.add(new_id)
                    cls._save()
                    return new_id
            
            raise RuntimeError(
                f"Failed to generate unique transaction ID after {cls._MAX_ATTEMPTS} attempts."
            )
    
    @classmethod
    def _save(cls):
        """
        Save the current set of IDs to file
        Uses atomic write pattern with temporary file
        """
        temp_file = cls._FILE_PATH + ".tmp"
        
        try:
            # Write to temporary file
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(list(cls._ids), f, indent=2)
            
            # Atomic move (replace existing file)
            try:
                shutil.move(temp_file, cls._FILE_PATH)
            except Exception as e:
                # Fallback: try copy and delete
                try:
                    shutil.copy2(temp_file, cls._FILE_PATH)
                    os.remove(temp_file)
                except Exception as ex:
                    print(f"⚠️ Failed to persist transaction ids: {ex}")
        
        except Exception as e:
            print(f"⚠️ Failed to write transaction ids to temp file: {e}")
            # Clean up temp file if it exists
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
    
    @classmethod
    def get_total_transactions(cls) -> int:
        """
        Get total number of unique transaction IDs generated
        
        Returns:
            Count of unique transaction IDs
        """
        cls._initialize()
        with cls._lock:
            return len(cls._ids)
    
    @classmethod
    def id_exists(cls, txn_id: str) -> bool:
        """
        Check if a transaction ID exists in the registry
        
        Args:
            txn_id: Transaction ID to check
            
        Returns:
            True if ID exists in registry
        """
        cls._initialize()
        with cls._lock:
            return txn_id in cls._ids
    
    @classmethod
    def add_existing_id(cls, txn_id: str):
        """
        Add an existing transaction ID to the registry
        Useful when loading transactions from storage
        
        Args:
            txn_id: Transaction ID to add
        """
        cls._initialize()
        with cls._lock:
            if txn_id not in cls._ids:
                cls._ids.add(txn_id)
                cls._save()
    
    @classmethod
    def clear_registry(cls):
        """
        Clear all transaction IDs from registry
        WARNING: This will reset all transaction IDs
        """
        with cls._lock:
            cls._ids.clear()
            cls._save()
            print("⚠️ Transaction registry cleared!")
    
    @classmethod
    def get_statistics(cls) -> dict:
        """
        Get statistics about the transaction registry
        
        Returns:
            Dictionary with registry statistics
        """
        cls._initialize()
        with cls._lock:
            return {
                "total_ids": len(cls._ids),
                "file_path": cls._FILE_PATH,
                "prefix": cls._PREFIX,
                "id_length": len(cls._PREFIX) + 10
            }


# Convenience function for direct use
def generate_transaction_id() -> str:
    """
    Generate a unique transaction ID
    
    Returns:
        Unique transaction ID
    """
    return TransactionRegistry.generate_id()


# Example usage and testing
if __name__ == "__main__":
    print("Transaction Registry Test")
    print("=" * 60)
    
    # Generate some IDs
    print("\nGenerating 5 transaction IDs:")
    for i in range(5):
        txn_id = TransactionRegistry.generate_id()
        print(f"{i+1}. {txn_id}")
    
    # Show statistics
    stats = TransactionRegistry.get_statistics()
    print(f"\nRegistry Statistics:")
    print(f"  Total IDs: {stats['total_ids']}")
    print(f"  File Path: {stats['file_path']}")
    print(f"  ID Format: {stats['prefix']}{'#' * 10}")
    print(f"  ID Length: {stats['id_length']} characters")
    
    # Test ID existence
    test_id = TransactionRegistry.generate_id()
    print(f"\nTesting ID existence:")
    print(f"  Generated ID: {test_id}")
    print(f"  Exists in registry: {TransactionRegistry.id_exists(test_id)}")
    print(f"  Non-existent ID: {TransactionRegistry.id_exists('FHIC0000000000')}")
    
    print("\n" + "=" * 60)
