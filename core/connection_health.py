"""
Connection Health Check Module

Monitors server and external service connection status.
Provides real-time connection status badges for Host and Guest pages.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple
import requests
import streamlit as st
import pytz


@dataclass
class ConnectionStatus:
    """Connection status data structure"""
    server_connected: bool          # Streamlit server connection (always True if page loads)
    time_api_connected: bool        # World Time API connection status
    last_check: datetime            # Last check timestamp
    latency_ms: Optional[int]       # Response time in milliseconds
    error_message: Optional[str]    # Error message if any


class ConnectionHealthCheck:
    """
    Connection health monitoring service.

    Provides methods to check connection status and render status badges.
    Uses Streamlit caching to avoid excessive API calls.
    """

    TIME_API_URL = "http://worldtimeapi.org/api/timezone/Etc/UTC"
    CACHE_TTL = 30  # seconds

    @staticmethod
    @st.cache_data(ttl=30)
    def check_time_api() -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Check World Time API connection.

        Returns:
            Tuple of (connected: bool, latency_ms: int or None, error_message: str or None)
        """
        try:
            start_time = datetime.now()
            response = requests.get(
                ConnectionHealthCheck.TIME_API_URL,
                timeout=5
            )
            end_time = datetime.now()

            latency_ms = int((end_time - start_time).total_seconds() * 1000)

            if response.status_code == 200:
                return True, latency_ms, None
            else:
                return False, latency_ms, f"HTTP {response.status_code}"

        except requests.Timeout:
            return False, None, "Connection timeout"
        except requests.ConnectionError:
            return False, None, "Connection error"
        except Exception as e:
            return False, None, str(e)

    @staticmethod
    def get_connection_status() -> ConnectionStatus:
        """
        Get comprehensive connection status.

        Returns:
            ConnectionStatus object with all connection information
        """
        # Server is always connected if this code runs
        server_connected = True

        # Check Time API
        time_api_connected, latency_ms, error_message = ConnectionHealthCheck.check_time_api()

        return ConnectionStatus(
            server_connected=server_connected,
            time_api_connected=time_api_connected,
            last_check=datetime.now(pytz.UTC),
            latency_ms=latency_ms,
            error_message=error_message
        )

    @staticmethod
    def render_status_badge(status: Optional[ConnectionStatus] = None):
        """
        Render connection status badge in Streamlit UI.

        Args:
            status: ConnectionStatus object. If None, fetches fresh status.
        """
        if status is None:
            status = ConnectionHealthCheck.get_connection_status()

        if status.server_connected and status.time_api_connected:
            # All good
            latency_text = f" ({status.latency_ms}ms)" if status.latency_ms else ""
            st.success(f"📶 ✅ 연결 정상{latency_text}")

        elif status.server_connected and not status.time_api_connected:
            # Time API issue
            st.warning("📶 ⚠️ 시간 동기화 불가 - 로컬 시간 사용 중")

        else:
            # Server disconnected (shouldn't happen if page loads)
            st.error("📶 ❌ 서버 연결 끊김 - 네트워크를 확인하세요")

    @staticmethod
    def render_compact_badge(status: Optional[ConnectionStatus] = None) -> str:
        """
        Get a compact badge string for inline display.

        Args:
            status: ConnectionStatus object. If None, fetches fresh status.

        Returns:
            Badge string (e.g., "✅ 45ms" or "⚠️" or "❌")
        """
        if status is None:
            status = ConnectionHealthCheck.get_connection_status()

        if status.server_connected and status.time_api_connected:
            latency_text = f"{status.latency_ms}ms" if status.latency_ms else "OK"
            return f"✅ {latency_text}"
        elif status.server_connected and not status.time_api_connected:
            return "⚠️ 동기화 불가"
        else:
            return "❌ 연결 끊김"
