from datetime import date, datetime, timedelta


class BankClock:
    """
    Virtual clock for banking simulation
    Can run in two modes:
    1. REAL-TIME: Syncs with actual system time
    2. VIRTUAL: Manual time control for simulation/testing
    """

    # Class variables
    _mode = "VIRTUAL"
    _virtual_datetime = datetime.now()
    _datetime_format = "%d-%m-%Y %H:%M:%S"
    _date_format = "%d-%m-%Y"
    _time_format = "%H:%M:%S"

    @classmethod
    def now(cls) -> datetime:
        """Get the current datetime"""
        if cls._mode == "REAL":
            return datetime.now()
        else:
            return cls._virtual_datetime

    @classmethod
    def today(cls) -> date:
        """Get the current date"""
        return cls.now().date()

    @classmethod
    def get_formatted_datetime(cls) -> str:
        """Get formatted date-time string"""
        return cls.now().strftime(cls._datetime_format)

    @classmethod
    def get_formatted_date(cls) -> str:
        """Get formatted date string"""
        return cls.now().strftime(cls._date_format)

    @classmethod
    def get_formatted_time(cls) -> str:
        """Get formatted time string"""
        return cls.now().strftime(cls._time_format)

    @classmethod
    def advance_days(cls, days: int):
        """Advance the clock by specified number of days (VIRTUAL mode only)"""
        if cls._mode == "REAL":
            print("⚠️  Cannot advance time in REAL mode")
            return
        cls._virtual_datetime += timedelta(days=days)

    @classmethod
    def advance_day(cls):
        """Advance the clock by one day"""
        cls.advance_days(1)

    @classmethod
    def advance_hours(cls, hours: int):
        """Advance the clock by specified number of hours (VIRTUAL mode only)"""
        if cls._mode == "REAL":
            print("⚠️  Cannot advance time in REAL mode")
            return
        cls._virtual_datetime += timedelta(hours=hours)

    @classmethod
    def advance_minutes(cls, minutes: int):
        """Advance the clock by specified number of minutes (VIRTUAL mode only)"""
        if cls._mode == "REAL":
            print("⚠️  Cannot advance time in REAL mode")
            return
        cls._virtual_datetime += timedelta(minutes=minutes)

    @classmethod
    def advance_seconds(cls, seconds: int):
        """Advance the clock by specified number of seconds (VIRTUAL mode only)"""
        if cls._mode == "REAL":
            print("⚠️  Cannot advance time in REAL mode")
            return
        cls._virtual_datetime += timedelta(seconds=seconds)

    @classmethod
    def set_datetime(cls, dt: datetime):
        """Set the clock to a specific datetime (VIRTUAL mode only)"""
        if cls._mode == "REAL":
            print("⚠️  Cannot set time in REAL mode")
            return
        cls._virtual_datetime = dt

    @classmethod
    def switch_to_real_mode(cls):
        """Switch to REAL-TIME mode"""
        cls._mode = "REAL"
        print(f"🕐 Switched to REAL-TIME mode: {cls.get_formatted_datetime()}")

    @classmethod
    def switch_to_virtual_mode(cls, freeze_at_current: bool = True):
        """
        Switch to VIRTUAL mode

        Args:
            freeze_at_current: If True, freezes at current real time
                              If False, keeps previous virtual time
        """
        cls._mode = "VIRTUAL"
        if freeze_at_current:
            cls._virtual_datetime = datetime.now()
        print(f"⏸️  Switched to VIRTUAL mode: {cls.get_formatted_datetime()}")

    @classmethod
    def reset(cls):
        """Reset based on current mode"""
        if cls._mode == "REAL":
            print(f"🔄 Clock synced to real-world time: {cls.get_formatted_datetime()}")
        else:
            cls._virtual_datetime = datetime.now()
            print(f"🔄 Clock reset to current time: {cls.get_formatted_datetime()}")

    @classmethod
    def get_mode(cls) -> str:
        """Get current clock mode"""
        return cls._mode

    @classmethod
    def get_login_banner(cls) -> str:
        """Get a display string for login banner"""
        mode_indicator = "🕐 LIVE" if cls._mode == "REAL" else "⏸️  VIRTUAL"
        return f"""{mode_indicator}
Current Date: {cls.get_formatted_date()}
Current Time: {cls.get_formatted_time()}"""

    @classmethod
    def get_compact_display(cls) -> str:
        """Get a compact display string for menu headers"""
        mode_icon = "🕐" if cls._mode == "REAL" else "⏸️"
        return f"{mode_icon} [{cls.get_formatted_date()} {cls.get_formatted_time()}]"

    @classmethod
    def get_year(cls) -> int:
        """Get the year component"""
        return cls.now().year

    @classmethod
    def get_month(cls) -> int:
        """Get the month component (1-12)"""
        return cls.now().month

    @classmethod
    def get_day_of_month(cls) -> int:
        """Get the day of month component (1-31)"""
        return cls.now().day

    @classmethod
    def get_hour(cls) -> int:
        """Get the hour component (0-23)"""
        return cls.now().hour

    @classmethod
    def get_minute(cls) -> int:
        """Get the minute component (0-59)"""
        return cls.now().minute

    @classmethod
    def get_second(cls) -> int:
        """Get the second component (0-59)"""
        return cls.now().second

    @classmethod
    def is_after(cls, d: date) -> bool:
        """Check if current time is after a specific date"""
        return cls.today() > d

    @classmethod
    def is_before(cls, d: date) -> bool:
        """Check if current time is before a specific date"""
        return cls.today() < d

    @classmethod
    def is_same_day(cls, d: date) -> bool:
        """Check if current time is on the same day as given date"""
        return cls.today() == d


# Module-level convenience functions for easier imports
def switch_to_real_mode():
    """Switch to REAL-TIME mode"""
    BankClock.switch_to_real_mode()


def switch_to_virtual_mode(freeze_at_current: bool = True):
    """Switch to VIRTUAL mode"""
    BankClock.switch_to_virtual_mode(freeze_at_current)


def get_mode() -> str:
    """Get current mode"""
    return BankClock.get_mode()
