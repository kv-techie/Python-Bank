from datetime import datetime, timedelta, date


class BankClock:
    """
    Virtual clock for banking simulation
    Allows time manipulation for testing and simulation purposes
    """
    
    _virtual_datetime = datetime.now()
    _datetime_format = "%d-%m-%Y %H:%M:%S"
    _date_format = "%d-%m-%Y"
    _time_format = "%H:%M:%S"
    
    @classmethod
    def now(cls) -> datetime:
        """
        Gets the current virtual date and time
        
        Returns:
            Current virtual datetime
        """
        return cls._virtual_datetime
    
    @classmethod
    def today(cls) -> date:
        """
        Gets the current virtual date
        
        Returns:
            Current virtual date
        """
        return cls._virtual_datetime.date()
    
    @classmethod
    def get_formatted_datetime(cls) -> str:
        """
        Gets formatted date-time string
        
        Returns:
            Formatted string in "dd-MM-yyyy HH:mm:ss" format
        """
        return cls._virtual_datetime.strftime(cls._datetime_format)
    
    @classmethod
    def get_formatted_date(cls) -> str:
        """
        Gets formatted date string
        
        Returns:
            Formatted string in "dd-MM-yyyy" format
        """
        return cls._virtual_datetime.strftime(cls._date_format)
    
    @classmethod
    def get_formatted_time(cls) -> str:
        """
        Gets formatted time string
        
        Returns:
            Formatted string in "HH:mm:ss" format
        """
        return cls._virtual_datetime.strftime(cls._time_format)
    
    @classmethod
    def advance_days(cls, days: int):
        """
        Advances the clock by specified number of days
        
        Args:
            days: Number of days to advance
        """
        cls._virtual_datetime += timedelta(days=days)
    
    @classmethod
    def advance_day(cls):
        """Advances the clock by one day"""
        cls._virtual_datetime += timedelta(days=1)
    
    @classmethod
    def advance_hours(cls, hours: int):
        """
        Advances the clock by specified number of hours
        
        Args:
            hours: Number of hours to advance
        """
        cls._virtual_datetime += timedelta(hours=hours)
    
    @classmethod
    def advance_minutes(cls, minutes: int):
        """
        Advances the clock by specified number of minutes
        
        Args:
            minutes: Number of minutes to advance
        """
        cls._virtual_datetime += timedelta(minutes=minutes)
    
    @classmethod
    def reset(cls):
        """Resets the clock to current real-world time"""
        cls._virtual_datetime = datetime.now()
        print(f"Clock reset to real-world time: {cls.get_formatted_datetime()}")
    
    @classmethod
    def set_datetime(cls, dt: datetime):
        """
        Sets the clock to a specific date-time
        
        Args:
            dt: The datetime to set
        """
        cls._virtual_datetime = dt
    
    @classmethod
    def get_login_banner(cls) -> str:
        """
        Gets a display string for login banner
        
        Returns:
            Multi-line formatted string with date and time
        """
        return f"""Current Date: {cls.get_formatted_date()}
Current Time: {cls.get_formatted_time()}"""
    
    @classmethod
    def get_compact_display(cls) -> str:
        """
        Gets a compact display string for menu headers
        
        Returns:
            Single-line formatted string with date and time
        """
        return f"[{cls.get_formatted_date()} {cls.get_formatted_time()}]"
    
    @classmethod
    def get_year(cls) -> int:
        """
        Gets the year component
        
        Returns:
            Current year
        """
        return cls._virtual_datetime.year
    
    @classmethod
    def get_month(cls) -> int:
        """
        Gets the month component (1-12)
        
        Returns:
            Current month
        """
        return cls._virtual_datetime.month
    
    @classmethod
    def get_day_of_month(cls) -> int:
        """
        Gets the day of month component (1-31)
        
        Returns:
            Current day of month
        """
        return cls._virtual_datetime.day
    
    @classmethod
    def get_hour(cls) -> int:
        """
        Gets the hour component (0-23)
        
        Returns:
            Current hour
        """
        return cls._virtual_datetime.hour
    
    @classmethod
    def get_minute(cls) -> int:
        """
        Gets the minute component (0-59)
        
        Returns:
            Current minute
        """
        return cls._virtual_datetime.minute
    
    @classmethod
    def is_after(cls, d: date) -> bool:
        """
        Checks if current time is after a specific date
        
        Args:
            d: The date to compare
            
        Returns:
            True if virtual time is after the given date
        """
        return cls._virtual_datetime.date() > d
    
    @classmethod
    def is_before(cls, d: date) -> bool:
        """
        Checks if current time is before a specific date
        
        Args:
            d: The date to compare
            
        Returns:
            True if virtual time is before the given date
        """
        return cls._virtual_datetime.date() < d
