from datetime import datetime, time
from typing import Dict, Tuple, Any, Optional

class TimeValidator:
    @staticmethod
    def parse_time_string(time_str: str) -> time:
        """Parse strict HH:MM string to time object."""
        return datetime.strptime(time_str, "%H:%M").time()

    @staticmethod
    def is_within_allowed_hours(current_time: datetime, allowed_hours: Any) -> Tuple[bool, str]:
        """
        Check if current_time is within allowed_hours.
        allowed_hours can be a dict or AllowedHours object.
        Returns (is_allowed, message).
        """
        if not allowed_hours:
            # If no hours defined, usually implies always allowed or strictly denied depending on policy.
            # Based on PRD context, we usually check valid objects. 
            # If explicit None passed, we might assume allowed or denied.
            # PRD for Checkpoint implies allowed_hours is mandatory.
            return True, "Always allowed (No restrictions)"

        # Handle object vs dict
        if isinstance(allowed_hours, dict):
            start_str = allowed_hours.get("start_time")
            end_str = allowed_hours.get("end_time")
        else:
            start_str = allowed_hours.start_time
            end_str = allowed_hours.end_time

        if not start_str or not end_str:
             return True, "Invalid allowed hours configuration"

        current_t = current_time.time()
        start_t = TimeValidator.parse_time_string(start_str)
        end_t = TimeValidator.parse_time_string(end_str)

        # Handle overnight case (e.g. 22:00 to 06:00)
        if start_t > end_t:
            if current_t >= start_t or current_t <= end_t:
                return True, "Within allowed hours"
        else:
            # Standard case (e.g. 09:00 to 18:00)
            if start_t <= current_t <= end_t:
                return True, "Within allowed hours"
        
        return False, "Outside of allowed hours"

    @staticmethod
    def format_countdown(seconds: float) -> str:
        """Format seconds into MM:SS."""
        if seconds < 0:
            seconds = 0
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
