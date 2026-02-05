import streamlit as st
import time as time_module
from datetime import datetime, timedelta, date
from PIL import Image
import io
import pytz

# Fix for macOS Homebrew zbar location
import os
import ctypes.util
original_find_library = ctypes.util.find_library

def patched_find_library(name):
    if name == 'zbar':
        # Check standard Homebrew path
        if os.path.exists('/opt/homebrew/lib/libzbar.dylib'):
            return '/opt/homebrew/lib/libzbar.dylib'
    return original_find_library(name)

ctypes.util.find_library = patched_find_library

# Try to import pyzbar
try:
    from pyzbar.pyzbar import decode
    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False
except Exception:
    PYZBAR_AVAILABLE = False

from core.storage import JSONStorage
from core.models import ActivityLog
from core.qr_manager import QRManager
from core.time_service import TimeService
from core.time_validator import TimeValidator
from utils.helpers import get_checkpoint_name

# Initialize storage
storage = JSONStorage()

# Page Config
st.set_page_config(page_title="Guest - QR In/Out", page_icon="👋", layout="wide")

# Custom CSS for Mobile Optimization
st.markdown("""
<style>
    /* Mobile-friendly buttons */
    .stButton > button {
        width: 100%;
        min-height: 50px;
        font-size: 1.1rem;
        border-radius: 8px;
    }

    /* Tabs buttons */
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        font-size: 1rem;
    }

    /* Input fields */
    .stTextInput > div > div > input {
        font-size: 1rem;
        padding: 10px;
    }
    
    /* Camera Input container customization (limited support via CSS) */
    [data-testid="stCameraInput"] {
        border-radius: 12px;
        overflow: hidden;
        border: 2px solid #ddd;
    }
</style>
""", unsafe_allow_html=True)


# --- Helper Functions ---

def verify_guest(name: str, email: str):
    """Verify guest credentials case-insensitively."""
    name_clean = name.strip().lower()
    email_clean = email.strip().lower()
    
    guests = storage.get_active_guests()
    for g in guests:
        if g["name"].strip().lower() == name_clean and g["email"].strip().lower() == email_clean:
            return g
    return None

def get_last_activity(guest_id: str, checkpoint_id: str):
    """Get the last successful activity for a guest at a checkpoint."""
    logs = storage.load("activity_logs")
    # Filter for this guest and checkpoint, success only
    relevant = [
        l for l in logs 
        if l["guest_id"] == guest_id 
        and l["checkpoint_id"] == checkpoint_id 
        and l["status"] == "success"
    ]
    if not relevant:
        return None
    # Sort by timestamp descending
    relevant.sort(key=lambda x: x["timestamp"], reverse=True)
    return relevant[0]

def validate_qr_scan(qr_data, guest, action, current_time, is_synced):
    """
    Validate scanned QR data against rules.
    Returns: (valid: bool, reason: str)
    """
    # 1. Checkpoint existence
    cp_id = qr_data.get("checkpoint_id")
    checkpoint = storage.get_by_id("checkpoints", cp_id)
    
    if not checkpoint:
        return False, "Checkpoint not found."
    
    if checkpoint.get("deleted_at"):
        return False, "This checkpoint has been removed."
    
    # 2. Dynamic QR Validation (Signature, Expiration)
    if qr_data.get("qr_mode") == "dynamic":
        is_valid_dynamic, invalid_reason = QRManager.validate_dynamic_qr(
            qr_data, checkpoint, current_time, is_synced
        )
        if not is_valid_dynamic:
            return False, invalid_reason
            
        # Additional Sequence Check
        qr_seq = qr_data.get("sequence", 0)
        curr_seq = checkpoint.get("current_qr_sequence", 0)
        if qr_seq < curr_seq:
            return False, "Expired QR Code (Old sequence). Please scan a fresh code."

    # 3. Guest Authorization (Checkpoint allowed lists)
    if guest["id"] not in checkpoint["allowed_guests"]:
        return False, "You are not authorized for this checkpoint."
        
    # 4. Checkpoint Operating Hours
    allowed, msg = TimeValidator.is_within_allowed_hours(current_time, checkpoint["allowed_hours"])
    if not allowed:
        return False, f"Checkpoint closed: {msg} ({checkpoint['allowed_hours']['start_time']}-{checkpoint['allowed_hours']['end_time']})"
        
    # 5. Guest Specific Hours
    if guest.get("allowed_hours"):
        allowed, msg = TimeValidator.is_within_allowed_hours(current_time, guest["allowed_hours"])
        if not allowed:
            return False, f"Outside your allowed hours: {msg}"
             
    # 6. Action Consistency (Check-out requires Check-in)
    if action == "check_out":
        last_act = get_last_activity(guest["id"], cp_id)
        if not last_act or last_act["action"] == "check_out":
            # Just a warning or blocking? Usually blocking logic for consistency.
            # But let's allow it with a warning in reason if we want to be strict, or return False.
            return False, "You have not checked in here (or already checked out)."
            
    return True, "Valid"

# --- Main Logic ---

if "guest_authenticated" not in st.session_state:
    st.session_state.guest_authenticated = False
    st.session_state.current_guest = None

if not st.session_state.guest_authenticated:
    st.title("👋 Guest Login")
    
    st.info("Please enter your registered Name and Email to identify yourself.")
    
    with st.form("guest_login"):
        col1, col2 = st.columns(2)
        with col1:
            name_input = st.text_input("Name", placeholder="John Doe")
        with col2:
            email_input = st.text_input("Email", placeholder="john@example.com")
            
        submitted = st.form_submit_button("Login", type="primary")
        
        if submitted:
            if not name_input or not email_input:
                st.error("Please fill in both Name and Email.")
            else:
                guest_obj = verify_guest(name_input, email_input)
                if guest_obj:
                    st.session_state.guest_authenticated = True
                    st.session_state.current_guest = guest_obj
                    st.success(f"Welcome, {guest_obj['name']}!")
                    time_module.sleep(1)
                    st.rerun()
                else:
                    st.error("Guest not found. Please check your credentials.")

else:
    # Authenticated View
    guest = st.session_state.current_guest
    
    # Top Bar
    c1, c2 = st.columns([3, 1])
    with c1:
        st.subheader(f"👋 Hi, {guest['name']}")
        settings_data = storage.load_admin_settings()
        current_time_val, is_synced_val = TimeService.get_current_time(guest["timezone"])
        TimeService.show_time_sync_status(is_synced_val, current_time_val)
        
    with c2:
        if st.button("Log out", type="secondary"):
            st.session_state.guest_authenticated = False
            st.session_state.current_guest = None
            st.rerun()

    st.divider()

    # Tabs for Scan / History
    tab_scan, tab_history = st.tabs(["📸 Scan QR", "📊 My History"])

    with tab_scan:
        st.write("### Check In / Check Out")
        
        action_select = st.radio("Action", ["Check In", "Check Out"], horizontal=True, key="action_selector")
        action_code = "check_in" if action_select == "Check In" else "check_out"
        
        if not PYZBAR_AVAILABLE:
            st.warning("⚠️ `pyzbar` library is not available. Camera scanning might not work properly.")
        
        # Camera Input
        img_buffer = st.camera_input("Scan QR Code")
        
        # Fallback File Uploader
        with st.expander("Or upload QR image"):
            uploaded_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])
            
        to_process = img_buffer or uploaded_file
        
        if to_process:
            try:
                # Open Image
                image = Image.open(to_process)
                
                # Decode
                decoded = decode(image)
                
                if decoded:
                    qr_str = decoded[0].data.decode("utf-8")
                    qr_data_obj = QRManager.parse_qr_content(qr_str)
                    
                    if qr_data_obj and qr_data_obj.get("type") == "qr_in_out":
                        # Validate
                        is_valid, validation_msg = validate_qr_scan(
                            qr_data_obj, guest, action_code, current_time_val, is_synced_val
                        )
                        
                        # Log result
                        status = "success" if is_valid else "failure"
                        
                        log = ActivityLog.create_new(
                            checkpoint_id=qr_data_obj.get("checkpoint_id", "unknown"),
                            guest_id=guest["id"],
                            action=action_code,
                            qr_code_used=qr_str,
                            status=status,
                            failure_reason=validation_msg if not is_valid else None,
                            metadata={"scanned_at": current_time_val.isoformat()}
                        )
                        storage.add("activity_logs", log.to_dict())
                        
                        if is_valid:
                            cp_name = get_checkpoint_name(qr_data_obj.get("checkpoint_id"))
                            st.balloons()
                            st.success(f"✅ Correctly {action_select} at **{cp_name}**!")
                        else:
                            st.error(f"❌ {action_select} Failed: {validation_msg}")
                            
                    else:
                        st.error("Invalid QR Code format.")
                else:
                    st.warning("Could not detect QR code in the image.")
            except Exception as e:
                st.error(f"Error processing image: {e}")

    with tab_history:
        st.write("### Your Recent Activity")
        
        # Date Filter
        hc1, hc2 = st.columns(2)
        with hc1:
            h_start = st.date_input("Start Date", value=date.today() - timedelta(days=7))
        with hc2:
            h_end = st.date_input("End Date", value=date.today())
            
        logs = storage.load("activity_logs")
        my_logs = [l for l in logs if l["guest_id"] == guest["id"]]
        
        # Filter dates
        filtered_logs = []
        for l in my_logs:
            try:
                ts = datetime.fromisoformat(l["timestamp"])
                if h_start <= ts.date() <= h_end:
                    filtered_logs.append(l)
            except ValueError:
                continue
                 
        filtered_logs.sort(key=lambda x: x["timestamp"], reverse=True)
        
        if filtered_logs:
            for l in filtered_logs[:20]: # Show last 20
                ts = datetime.fromisoformat(l["timestamp"])
                cp_name = get_checkpoint_name(l["checkpoint_id"])
                 
                with st.container():
                    lc1, lc2 = st.columns([3, 1])
                    with lc1:
                        st.write(f"**{cp_name}**")
                        st.caption(f"{ts.strftime('%Y-%m-%d %H:%M:%S')}")
                    with lc2:
                        if l["status"] == "success":
                            if l["action"] == "check_in":
                                st.success("IN")
                            else:
                                st.info("OUT")
                        else:
                            st.error("FAIL")
                            if l.get("failure_reason"):
                                st.caption(l["failure_reason"])
                    st.divider()
        else:
            st.info("No records found for this period.")
