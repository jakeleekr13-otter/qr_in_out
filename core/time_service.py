import requests
import streamlit as st
from datetime import datetime
import pytz
from typing import Tuple, Optional

class TimeService:
    @staticmethod
    @st.cache_data(ttl=60)
    def get_current_time(timezone_str: str = "Asia/Seoul") -> Tuple[datetime, bool]:
        """
        Get the current time for a given timezone.
        Attempts to use World Time API first, then falls back to TimeAPI.io, 
        and finally falls back to server local time.
        Returns: (datetime object, is_synchronized)
        """
        # Attempt 1: World Time API
        try:
            url = f"http://worldtimeapi.org/api/timezone/{timezone_str}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                dt_str = data.get("datetime")
                if dt_str:
                    return datetime.fromisoformat(dt_str), True
        except Exception:
            pass # Try next source
        
        # Attempt 2: TimeAPI.io
        try:
            url = f"https://timeapi.io/api/Time/current/zone?timeZone={timezone_str}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                dt_str = data.get("dateTime")
                if dt_str:
                    # timeapi.io dateTime format might need slight adjustment for fromisoformat
                    # common format: "2026-02-05T09:45:38.0000000"
                    return datetime.fromisoformat(dt_str).replace(tzinfo=pytz.timezone(timezone_str)), True
        except Exception:
            pass # Failure here will lead to server time fallback

        # Fallback to local system time
        try:
            tz = pytz.timezone(timezone_str)
            return datetime.now(tz), False
        except Exception:
            # Absolute fallback to UTC if timezone is invalid
            return datetime.now(pytz.UTC), False

    @staticmethod
    def show_time_sync_status(is_synced: bool, current_time: datetime):
        """
        Display time synchronization status in Streamlit UI.
        """
        status_color = "green" if is_synced else "orange"
        status_text = "Synchronized to World Time API" if is_synced else "Not Synchronized (Using Server Time)"
        
        st.markdown(f"""
            <div style="padding: 10px; border-radius: 5px; background-color: rgba(0,0,0,0.05); border-left: 5px solid {status_color};">
                <span style="font-weight: bold; color: {status_color};">Time Status: {status_text}</span><br>
                <span>Current Time: {TimeService.format_time_for_display(current_time)}</span>
            </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def format_time_for_display(dt: datetime) -> str:
        return dt.strftime("%Y-%m-%d %H:%M:%S (%Z)")
