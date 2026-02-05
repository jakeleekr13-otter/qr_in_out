import streamlit as st
import time as time_module
from datetime import datetime, timedelta
import pytz
import io

from core.storage import JSONStorage
from core.qr_manager import QRManager
from core.time_service import TimeService
from core.auth import AuthManager
from core.time_validator import TimeValidator
from utils.helpers import get_checkpoint_name, get_checkpoint_location

# Initialize storage
storage = JSONStorage()

# Page Config
st.set_page_config(page_title="Host - QR In/Out", page_icon="🖥️", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .main .block-container {
        max-width: 100%;
        padding-top: 2rem;
    }
    .qr-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 20px;
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: auto;
        width: fit-content;
    }
    .countdown {
        font-size: 24px;
        font-weight: bold;
        color: #ff9800;
        margin-top: 10px;
    }
    .sequence-no {
        font-size: 16px;
        color: #666;
        margin-top: 5px;
    }
    .status-allowed {
        color: #4CAF50;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .status-blocked {
        color: #F44336;
        font-weight: bold;
        font-size: 1.2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Session state initialization
if "host_authenticated" not in st.session_state:
    st.session_state.host_authenticated = False
    st.session_state.selected_checkpoint_id = None

# --- UI: Unauthenticated State ---
if not st.session_state.host_authenticated:
    st.title("🖥️ Host Page")
    st.subheader("QR Code Display Login")
    
    checkpoints = storage.get_active_checkpoints()
    
    if not checkpoints:
        st.error("No active checkpoints found. Please create one in Admin page.")
    else:
        with st.form("host_login"):
            selected_id = st.selectbox(
                "Select Checkpoint",
                options=[c["id"] for c in checkpoints],
                format_func=lambda x: f"{get_checkpoint_name(x)} ({get_checkpoint_location(x)})"
            )
            password = st.text_input("Admin Password", type="password")
            
            submitted = st.form_submit_button("Start Display", type="primary")
            
            if submitted:
                checkpoint = storage.get_by_id("checkpoints", selected_id)
                if AuthManager.verify_password(password, checkpoint["admin_password_hash"]):
                    st.session_state.host_authenticated = True
                    st.session_state.selected_checkpoint_id = selected_id
                    st.success("✅ Authenticated!")
                    time_module.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Invalid password")

# --- UI: Authenticated State ---
else:
    checkpoint = storage.get_by_id("checkpoints", st.session_state.selected_checkpoint_id)
    settings = storage.load_admin_settings()
    
    # 1. Header & Lock
    col1, col2 = st.columns([6, 1])
    with col1:
        st.header(f"📍 {checkpoint['name']}")
        if checkpoint.get('location'):
            st.caption(checkpoint['location'])
    with col2:
        if st.button("🔒 Lock"):
            st.session_state.host_authenticated = False
            st.session_state.selected_checkpoint_id = None
            st.rerun()
            
    st.divider()
    
    # 2. Time Synchronization Logic (Correction)
    # Use TimeService just to check sync status securely
    synced_time, is_synced = TimeService.get_current_time(settings["admin_timezone"])
    
    # Use system time for visual countdown to avoid cache lag
    # We trust local server time + simple offset if needed, but for now assuming server time is relevant
    current_time_display = datetime.now(pytz.timezone(settings["admin_timezone"]))
    current_time_utc = datetime.now(pytz.UTC)
    
    # 3. Check Allowed Hours
    is_allowed, msg = TimeValidator.is_within_allowed_hours(current_time_display, checkpoint["allowed_hours"])
    
    with st.container():
        col_status, col_time = st.columns([1, 1])
        with col_status:
            st.write("**Status**")
            if is_allowed:
                st.success(f"✅ {msg}")
            else:
                st.error(f"🚫 {msg}")
                
        with col_time:
            st.write(f"**Host Time** ({settings['admin_timezone']})")
            st.write(f"⏰ {current_time_display.strftime('%Y-%m-%d %H:%M:%S')}")
            
    st.divider()
    
    # Show precise sync status below divider or in a simplified way
    # TimeService.show_time_sync_status(is_synced, synced_time) 
    # Moving this to bottom or making it less intrusive if causing layout issues?
    # Let's keep it but ensure it doesn't overlap.

    # 4. Display Content
    if not is_allowed:
        st.warning(f"Regular Hours: {checkpoint['allowed_hours']['start_time']} - {checkpoint['allowed_hours']['end_time']}")
        st.info("QR Code is hidden during off-hours.")
        
        # Auto-refresh to check time status occasionally
        time_module.sleep(5) 
        st.rerun()
        
    else:
        # ALLOWED: Show QR
        
        # Determine QR Mode
        qr_mode = checkpoint["qr_mode"]
        
        if qr_mode == "static":
            # Static QR
            qr_content = QRManager.generate_static_qr_content(checkpoint["id"])
            qr_img = QRManager.generate_qr_image(qr_content, box_size=15)
            
            # Convert to bytes for display/download
            img_bytes = io.BytesIO()
            qr_img.save(img_bytes, format='PNG')
            img_bytes = img_bytes.getvalue()
            
            # Display
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown('<div class="qr-container">', unsafe_allow_html=True)
                st.image(img_bytes, width=400)
                st.markdown('</div>', unsafe_allow_html=True)
                st.info("ℹ️ Static Mode: Valid as long as hours allow.")
            
            # Download
            st.download_button(
                label="🖨️ Download for Print",
                data=img_bytes,
                file_name=f"static_qr_{checkpoint['name']}.png",
                mime="image/png"
            )
            
        else:
            # Dynamic QR
            refresh_interval = settings["qr_refresh_interval"]
            
            # Init Session State for Refreshes if missing
            if "last_refresh_time" not in st.session_state:
                st.session_state.last_refresh_time = current_time_utc
                st.session_state.next_refresh_time = current_time_utc + timedelta(seconds=refresh_interval)
                
                # Increment sequence
                checkpoint["current_qr_sequence"] += 1
                storage.update("checkpoints", checkpoint["id"], {"current_qr_sequence": checkpoint["current_qr_sequence"]})

            # Check if expired
            time_until_refresh = (st.session_state.next_refresh_time - current_time_utc).total_seconds()
            
            if time_until_refresh <= 0:
                # Refresh Triggered!
                st.session_state.last_refresh_time = current_time_utc
                st.session_state.next_refresh_time = current_time_utc + timedelta(seconds=refresh_interval)
                
                checkpoint["current_qr_sequence"] += 1
                storage.update("checkpoints", checkpoint["id"], {"current_qr_sequence": checkpoint["current_qr_sequence"]})
                st.rerun()
            
            # Generate QR Content (using stable session state times to prevent flicker)
            qr_raw_content = QRManager.generate_dynamic_qr_content(
                checkpoint_id=checkpoint["id"],
                current_sequence=checkpoint["current_qr_sequence"],
                issued_at=st.session_state.last_refresh_time, 
                expires_at=st.session_state.next_refresh_time,
                refresh_interval=refresh_interval
            )
            seq = checkpoint["current_qr_sequence"]
            
            qr_img = QRManager.generate_qr_image(qr_raw_content, box_size=15)
            img_bytes = io.BytesIO()
            qr_img.save(img_bytes, format='PNG')
            img_bytes = img_bytes.getvalue()
            
            # Display
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown('<div class="qr-container">', unsafe_allow_html=True)
                st.image(img_bytes, width=400)
                
                # Countdown & Progress
                countdown_str = TimeValidator.format_countdown(time_until_refresh)
                st.markdown(f'<div class="countdown">⏱️ Auto-refresh in: {countdown_str}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="sequence-no">Sequence: #{seq}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Progress bar (Full -> Empty)
                progress = max(0.0, min(1.0, time_until_refresh / refresh_interval))
                st.progress(progress)
                
                st.info("ℹ️ Dynamic Mode: Auto-refreshes for security.")

            # Auto-refresh loop (1s)
            time_module.sleep(1)
            st.rerun()
