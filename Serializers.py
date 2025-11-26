from datetime import date
from typing import Any, Optional


class Serializers:
    """
    Custom serializers for handling date objects in JSON serialization
    
    This module provides utilities for converting between Python date objects
    and ISO format strings for JSON storage.
    """
    
    @staticmethod
    def serialize_date(d: Optional[date]) -> Optional[str]:
        """
        Serialize a date object to ISO format string
        
        Args:
            d: Date object to serialize (can be None)
            
        Returns:
            ISO format date string (YYYY-MM-DD) or None
        """
        if d is None:
            return None
        return d.isoformat()
    
    @staticmethod
    def deserialize_date(date_str: Optional[str]) -> Optional[date]:
        """
        Deserialize an ISO format string to date object
        
        Args:
            date_str: ISO format date string (can be None)
            
        Returns:
            Date object or None
        """
        if date_str is None or date_str == "":
            return None
        try:
            return date.fromisoformat(date_str)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def serialize_optional_date(d: Optional[date]) -> Any:
        """
        Serialize an optional date to JSON-compatible value
        
        Args:
            d: Optional date object
            
        Returns:
            ISO format string or None
        """
        return Serializers.serialize_date(d)
    
    @staticmethod
    def deserialize_optional_date(value: Any) -> Optional[date]:
        """
        Deserialize a JSON value to optional date
        
        Args:
            value: JSON value (string, None, or other)
            
        Returns:
            Date object or None
        """
        if value is None:
            return None
        if isinstance(value, str):
            return Serializers.deserialize_date(value)
        return None


# Convenience functions for direct use
def date_to_string(d: Optional[date]) -> Optional[str]:
    """Convert date to ISO string"""
    return Serializers.serialize_date(d)


def string_to_date(s: Optional[str]) -> Optional[date]:
    """Convert ISO string to date"""
    return Serializers.deserialize_date(s)


# Example usage and documentation
if __name__ == "__main__":
    from datetime import date
    
    # Test serialization
    today = date.today()
    print(f"Original date: {today}")
    
    # Serialize
    serialized = Serializers.serialize_date(today)
    print(f"Serialized: {serialized}")
    
    # Deserialize
    deserialized = Serializers.deserialize_date(serialized)
    print(f"Deserialized: {deserialized}")
    
    # Test None handling
    none_serialized = Serializers.serialize_date(None)
    print(f"None serialized: {none_serialized}")
    
    none_deserialized = Serializers.deserialize_date(None)
    print(f"None deserialized: {none_deserialized}")
    
    # Test optional date
    optional_serialized = Serializers.serialize_optional_date(today)
    print(f"Optional serialized: {optional_serialized}")
    
    optional_deserialized = Serializers.deserialize_optional_date(optional_serialized)
    print(f"Optional deserialized: {optional_deserialized}")
