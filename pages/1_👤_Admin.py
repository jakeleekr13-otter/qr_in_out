import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta, date
import pytz
import time as time_module
from core.models import Checkpoint, Guest, AllowedHours, AdminSettings
from core.storage import JSONStorage
from core.auth import AuthManager
from core.time_service import TimeService
from utils.helpers import (
    get_checkpoint_name, get_guest_name, get_guest_email,
    is_valid_email, checkpoint_name_exists, guest_email_exists
)

# Initialize storage
storage = JSONStorage()

# Page Config
st.set_page_config(page_title="Admin - QR In/Out", page_icon="👤", layout="wide")

# Session State for Auth
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False
if "force_setup" not in st.session_state:
    st.session_state.force_setup = False

# Check for existing admin account
admin_creds = storage.get_admin_credentials()

# --- Auth Flow ---

if not st.session_state.admin_authenticated:
    # LOGIN MODE
    st.title("👤 Admin Login")
    
    # First time / Reset scenario
    if not admin_creds:
        st.info("ℹ️ System Not Configured. Please log in with default credentials.")
        st.caption("Default Username: **admin** | Default Password: **admin**")
    
    with st.form("admin_login_form"):
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        
        login_submitted = st.form_submit_button("Log In", type="primary")
        
        if login_submitted:
            # Scenario A: First Run (No stored creds) - Check hardcoded defaults
            if not admin_creds:
                if username_input == "admin" and password_input == "admin":
                    st.session_state.admin_authenticated = True
                    st.session_state.force_setup = True
                    st.success("✅ Default login successful. Please set up your secure account.")
                    time_module.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ Invalid default credentials.")
            
            # Scenario B: Normal Run - Check stored creds
            else:
                if username_input == admin_creds["username"] and \
                   AuthManager.verify_password(password_input, admin_creds["password_hash"]):
                    st.session_state.admin_authenticated = True
                    st.session_state.force_setup = False
                    st.success("✅ Login successful")
                    time_module.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")
    
    # Recovery Hint
    if admin_creds:
        with st.expander("🔑 Forgot Login Details?"):
            st.warning("""
            **Account Recovery:**
            There is no automatic password reset.
            To reset the system to default (admin/admin), an administrator with server access must verify identity and delete the credentials file manually:
            
            `rm data/admin_credentials.json`
            
            After deletion, refresh this page to log in with default credentials.
            """)

elif st.session_state.force_setup:
    # FORCE SETUP MODE (Interim step after default login)
    st.title("🛡️ Security Setup")
    st.warning("⚠️ You are using the default account. You MUST create a secure administrator account to proceed.")
    
    with st.form("admin_setup_form"):
        st.write("### Create New Administrator")
        new_username = st.text_input("New Username *", placeholder="admin")
        new_password = st.text_input("New Password *", type="password", help="Minimum 6 characters")
        confirm_password = st.text_input("Confirm Password *", type="password")
        
        setup_submitted = st.form_submit_button("Save & Login", type="primary")
        
        if setup_submitted:
            errors = []
            if not new_username:
                errors.append("Username is required")
            if not new_password or len(new_password) < 6:
                errors.append("Password must be at least 6 characters")
            if new_password != confirm_password:
                errors.append("Passwords do not match")
                
            if errors:
                for e in errors: st.error(f"❌ {e}")
            else:
                # Save Account (This effectively disables default admin/admin login)
                creds = {
                    "username": new_username,
                    "password_hash": AuthManager.hash_password(new_password),
                    "created_at": datetime.now().isoformat()
                }
                storage.save_admin_credentials(creds)
                
                # Exit setup mode
                st.session_state.force_setup = False
                
                st.balloons()
                st.success("✅ Administrator account secured! Entering dashboard...")
                time_module.sleep(1)
                st.rerun()

else:
    # DASHBOARD MODE (Authenticated & Configured)
    st.title("👤 Admin Dashboard")
    
    # Sidebar: Logout
    with st.sidebar:
        st.write(f"Logged in as: **{admin_creds['username'] if admin_creds else 'Setup User'}**")
        if st.button("Log Out", type="secondary"):
            st.session_state.admin_authenticated = False
            st.session_state.force_setup = False
            st.rerun()
        st.divider()

    # Load Settings
    settings = storage.load_admin_settings()

    # Sidebar for navigation within Admin page
    menu = st.sidebar.radio(
        "Menu",
        ["Checkpoint Management", "Guest Management", "Activity Logs", "Statistics Dashboard", "System Settings"]
    )

    if menu == "Checkpoint Management":
        st.header("🏢 Checkpoint Management")
        
        tab1, tab2, tab3 = st.tabs(["📝 Create New Checkpoint", "✏️ Edit Checkpoint", "⚠️ Danger Zone"])
        
        with tab1:
            st.subheader("Create New Checkpoint")
            with st.form("create_checkpoint"):
                name = st.text_input("Checkpoint Name *", placeholder="e.g., Main Entrance")
                location = st.text_input("Location", placeholder="e.g., Building A, 1st Floor")

                col1, col2 = st.columns(2)
                with col1:
                    start_time = st.time_input("Allowed Start Time", value=time(9, 0))
                with col2:
                    end_time = st.time_input("Allowed End Time", value=time(18, 0))

                qr_mode = st.radio(
                    "QR Code Mode",
                    options=["static", "dynamic"],
                    format_func=lambda x: "Static (Printable)" if x == "static" else "Dynamic (Auto-refreshing)",
                    index=1
                )

                col1, col2 = st.columns(2)
                with col1:
                    admin_password = st.text_input("Host Password *", type="password", help="For Host Mode Access (Min 4 chars)")
                with col2:
                    password_confirm = st.text_input("Confirm Host Password *", type="password")

                guests = storage.get_active_guests()
                allowed_guests = st.multiselect(
                    "Allowed Guests (Multiselect)",
                    options=[g["id"] for g in guests],
                    format_func=lambda x: f"{get_guest_name(x)} ({get_guest_email(x)})",
                    help="If 0 are selected, all guests will be blocked"
                )

                submitted = st.form_submit_button("Create", type="primary")

                if submitted:
                    errors = []
                    if not name:
                        errors.append("Checkpoint name is required")
                    elif checkpoint_name_exists(name):
                        errors.append("Checkpoint name already exists")
                    
                    if not admin_password or len(admin_password) < 4:
                        errors.append("Password must be at least 4 characters")
                    elif admin_password != password_confirm:
                        errors.append("Passwords do not match")

                    if errors:
                        for error in errors:
                            st.error(f"❌ {error}")
                    else:
                        cp = Checkpoint.create_new(
                            name=name,
                            location=location,
                            allowed_hours=AllowedHours(
                                start_time=start_time.strftime("%H:%M"),
                                end_time=end_time.strftime("%H:%M")
                            ),
                            qr_mode=qr_mode,
                            admin_password_hash=AuthManager.hash_password(admin_password),
                            allowed_guests=allowed_guests
                        )
                        storage.add("checkpoints", cp.to_dict())
                        st.success(f"✅ Checkpoint '{name}' has been created!")
                        if len(allowed_guests) == 0:
                            st.warning("⚠️ No guests allowed. Everyone will be blocked.")
                        time_module.sleep(1)
                        st.rerun()

        with tab2:
            st.subheader("Edit Checkpoint")
            checkpoints = storage.get_active_checkpoints()
            if not checkpoints:
                st.info("No checkpoints registered.")
            else:
                selected_id = st.selectbox(
                    "Select Checkpoint to Edit",
                    options=[c["id"] for c in checkpoints],
                    format_func=get_checkpoint_name,
                    key="edit_cp_select"
                )
                
                if selected_id:
                    cp_data = storage.get_by_id("checkpoints", selected_id)
                    with st.form("edit_checkpoint"):
                        e_name = st.text_input("Checkpoint Name *", value=cp_data["name"])
                        e_location = st.text_input("Location", value=cp_data["location"])
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            e_start = st.time_input("Allowed Start Time", value=datetime.strptime(cp_data["allowed_hours"]["start_time"], "%H:%M").time())
                        with c2:
                            e_end = st.time_input("Allowed End Time", value=datetime.strptime(cp_data["allowed_hours"]["end_time"], "%H:%M").time())
                        
                        e_qr_mode = st.radio(
                            "QR Code Mode",
                            options=["static", "dynamic"],
                            format_func=lambda x: "Static" if x == "static" else "Dynamic",
                            index=0 if cp_data["qr_mode"] == "static" else 1
                        )
                        
                        e_guests = st.multiselect(
                            "Allowed Guests",
                            options=[g["id"] for g in storage.get_active_guests()],
                            default=cp_data["allowed_guests"],
                            format_func=lambda x: f"{get_guest_name(x)} ({get_guest_email(x)})"
                        )
                        
                        st.info("Enter a new password to change HOST password. Leave blank to keep current.")
                        e_password = st.text_input("New Host Password", type="password")
                        
                        e_submitted = st.form_submit_button("Update", type="primary")
                        
                        if e_submitted:
                            errors = []
                            if not e_name:
                                errors.append("Name is required")
                            elif checkpoint_name_exists(e_name, selected_id):
                                errors.append("Checkpoint name already exists")
                            
                            if e_password and len(e_password) < 4:
                                errors.append("Password must be at least 4 characters")
                                
                            if errors:
                                for error in errors:
                                    st.error(f"❌ {error}")
                            else:
                                updates = {
                                    "name": e_name,
                                    "location": e_location,
                                    "allowed_hours": {
                                        "start_time": e_start.strftime("%H:%M"),
                                        "end_time": e_end.strftime("%H:%M")
                                    },
                                    "qr_mode": e_qr_mode,
                                    "allowed_guests": e_guests
                                }
                                if e_password:
                                    updates["admin_password_hash"] = AuthManager.hash_password(e_password)
                                
                                storage.update("checkpoints", selected_id, updates)
                                st.success("✅ Checkpoint updated successfully!")
                                time_module.sleep(1)
                                st.rerun()

        with tab3:
            st.subheader("Delete Checkpoint")
            checkpoints = storage.get_active_checkpoints()
            if not checkpoints:
                st.info("No checkpoints registered.")
            else:
                del_id = st.selectbox("Select Checkpoint to Delete", [c["id"] for c in checkpoints], format_func=get_checkpoint_name, key="del_cp_select")
                st.warning("⚠️ Warning: Deleting a checkpoint will make it unusable. Historical records are preserved.")
                
                if st.button("Delete Checkpoint", type="secondary"):
                    if st.session_state.get("confirm_del_cp_id") == del_id:
                        storage.soft_delete_checkpoint(del_id)
                        st.success("✅ Checkpoint deleted.")
                        st.session_state.confirm_del_cp_id = None
                        time_module.sleep(1)
                        st.rerun()
                    else:
                        st.session_state.confirm_del_cp_id = del_id
                        st.error("⚠️ Click again to confirm deletion.")

    elif menu == "Guest Management":
        st.header("👤 Guest Management")
        
        t1, t2, t3 = st.tabs(["👤 Register New Guest", "✏️ Edit Guest", "⚠️ Danger Zone"])
        
        with t1:
            st.subheader("Register New Guest")
            with st.form("create_guest"):
                st.write("**📋 Required Info**")
                c1, c2 = st.columns(2)
                with c1:
                    g_name = st.text_input("Name *", placeholder="John Doe")
                with c2:
                    g_email = st.text_input("Email *", placeholder="john@example.com")
                
                st.write("**📋 Optional Info**")
                g_phone = st.text_input("Phone", placeholder="010-1234-5678")
                
                st.write("**🌍 Timezone and Permissions**")
                g_timezone = st.selectbox("Timezone", options=pytz.all_timezones, index=pytz.all_timezones.index(settings["default_guest_timezone"]))
                
                use_custom_hours = st.checkbox("Set custom allowed hours (Optional)")
                g_allowed_hours = None
                if use_custom_hours:
                    c1, c2 = st.columns(2)
                    with c1:
                        g_start = st.time_input("Allowed Start Time", value=time(8, 0))
                    with c2:
                        g_end = st.time_input("Allowed End Time", value=time(20, 0))
                    g_allowed_hours = AllowedHours(start_time=g_start.strftime("%H:%M"), end_time=g_end.strftime("%H:%M"))
                    
                g_checkpoints = st.multiselect(
                    "Allowed Checkpoints (Multiselect)",
                    options=[c["id"] for c in storage.get_active_checkpoints()],
                    format_func=lambda x: get_checkpoint_name(x)
                )
                
                g_submitted = st.form_submit_button("Register", type="primary")
                
                if g_submitted:
                    errors = []
                    if not g_name: errors.append("Name is required")
                    if not g_email: 
                        errors.append("Email is required")
                    elif not is_valid_email(g_email):
                        errors.append("Invalid email format")
                    elif guest_email_exists(g_email):
                        errors.append("Email already registered")
                    
                    if errors:
                        for e in errors: st.error(f"❌ {e}")
                    else:
                        new_guest = Guest.create_new(
                            name=g_name,
                            email=g_email,
                            phone=g_phone if g_phone else None,
                            timezone=g_timezone,
                            allowed_checkpoints=g_checkpoints,
                            allowed_hours=g_allowed_hours
                        )
                        storage.add("guests", new_guest.to_dict())
                        st.success(f"✅ Guest '{g_name}' registered successfully!")
                        time_module.sleep(1)
                        st.rerun()

        with t2:
            st.subheader("Edit Guest")
            guests = storage.get_active_guests()
            if not guests:
                st.info("No guests registered.")
            else:
                selected_g_id = st.selectbox("Select Guest to Edit", [g["id"] for g in guests], format_func=lambda x: f"{get_guest_name(x)} ({get_guest_email(x)})")
                if selected_g_id:
                    g_data = storage.get_by_id("guests", selected_g_id)
                    with st.form("edit_guest"):
                        eg_name = st.text_input("Name *", value=g_data["name"])
                        eg_email = st.text_input("Email *", value=g_data["email"])
                        eg_phone = st.text_input("Phone", value=g_data.get("phone", "") or "")
                        eg_timezone = st.selectbox("Timezone", options=pytz.all_timezones, index=pytz.all_timezones.index(g_data["timezone"]))
                        
                        eg_checkpoints = st.multiselect(
                            "Allowed Checkpoints",
                            options=[c["id"] for c in storage.get_active_checkpoints()],
                            default=g_data["allowed_checkpoints"],
                            format_func=lambda x: get_checkpoint_name(x)
                        )
                        
                        eg_submitted = st.form_submit_button("Update", type="primary")
                        if eg_submitted:
                            errors = []
                            if not eg_name: errors.append("Name is required")
                            if not eg_email: errors.append("Email is required")
                            elif not is_valid_email(eg_email): errors.append("Invalid email format")
                            elif guest_email_exists(eg_email, selected_g_id): errors.append("Email already exists")
                            
                            if errors:
                                for e in errors: st.error(f"❌ {e}")
                            else:
                                updates = {
                                    "name": eg_name,
                                    "email": eg_email,
                                    "phone": eg_phone,
                                    "timezone": eg_timezone,
                                    "allowed_checkpoints": eg_checkpoints
                                }
                                storage.update("guests", selected_g_id, updates)
                                st.success("✅ Guest info updated successfully!")
                                time_module.sleep(1)
                                st.rerun()

        with t3:
            st.subheader("Delete Guest")
            guests = storage.get_active_guests()
            if not guests:
                st.info("No guests registered.")
            else:
                del_g_id = st.selectbox("Select Guest to Delete", [g["id"] for g in guests], format_func=lambda x: f"{get_guest_name(x)} ({get_guest_email(x)})", key="del_guest_select")
                st.warning("⚠️ Warning: Deleting a guest will prevent them from checking in. Historical records are preserved.")
                if st.button("Delete Guest", type="secondary"):
                    if st.session_state.get("confirm_del_g_id") == del_g_id:
                        storage.soft_delete_guest(del_g_id)
                        st.success("✅ Guest deleted.")
                        st.session_state.confirm_del_g_id = None
                        time_module.sleep(1)
                        st.rerun()
                    else:
                        st.session_state.confirm_del_g_id = del_g_id
                        st.error("⚠️ Click again to confirm deletion.")

    elif menu == "Activity Logs":
        st.header("📊 Activity Logs")
        
        view_mode = st.radio("View Mode", ["All", "By Checkpoint", "By Guest"], horizontal=True)
        
        logs = storage.load("activity_logs")
        if not logs:
            st.info("No activity records found.")
        else:
            df = pd.DataFrame(logs)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df["checkpoint_name"] = df["checkpoint_id"].apply(get_checkpoint_name)
            df["guest_name"] = df["guest_id"].apply(get_guest_name)
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=date.today() - timedelta(days=7))
            with col2:
                end_date = st.date_input("End Date", value=date.today())
                
            # Filter by date
            df = df[(df["timestamp"].dt.date >= start_date) & (df["timestamp"].dt.date <= end_date)]
            
            if view_mode == "By Checkpoint":
                cp_filter = st.selectbox("Select Checkpoint", ["All"] + [c["name"] for c in storage.load("checkpoints")])
                if cp_filter != "All":
                    df = df[df["checkpoint_name"] == cp_filter]
            elif view_mode == "By Guest":
                g_filter = st.selectbox("Select Guest", ["All"] + [g["name"] for g in storage.load("guests")])
                if g_filter != "All":
                    df = df[df["guest_name"] == g_filter]
                    
            st.dataframe(
                df[["timestamp", "checkpoint_name", "guest_name", "action", "status"]].sort_values("timestamp", ascending=False),
                use_container_width=True,
                hide_index=True
            )
            
            if st.button("📥 Download CSV"):
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("Download CSV", data=csv, file_name=f"logs_{date.today()}.csv", mime="text/csv")

    elif menu == "Statistics Dashboard":
        st.header("📈 Statistics Dashboard")
        logs = storage.load("activity_logs")
        if not logs:
            st.info("Not enough data to display statistics.")
        else:
            df = pd.DataFrame(logs)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Activities", len(df))
            c2.metric("Success", len(df[df["status"]=="success"]))
            c3.metric("Failure", len(df[df["status"]=="failure"]))
            success_rate = (len(df[df["status"]=="success"]) / len(df)) * 100 if len(df) > 0 else 0
            c4.metric("Success Rate", f"{success_rate:.1f}%")
            
            st.subheader("Activities by Hour")
            df["hour"] = df["timestamp"].dt.hour
            hour_counts = df.groupby("hour").size().reset_index(name="counts")
            st.line_chart(hour_counts.set_index("hour"))
            
            st.subheader("Activities by Checkpoint")
            df["checkpoint_name"] = df["checkpoint_id"].apply(get_checkpoint_name)
            cp_counts = df.groupby("checkpoint_name").size().reset_index(name="counts")
            st.bar_chart(cp_counts.set_index("checkpoint_name"))

    elif menu == "System Settings":
        st.header("⚙️ System Settings")
        
        with st.form("system_settings"):
            new_admin_tz = st.selectbox("Admin Timezone", pytz.all_timezones, index=pytz.all_timezones.index(settings["admin_timezone"]))
            new_default_guest_tz = st.selectbox("Default Guest Timezone", pytz.all_timezones, index=pytz.all_timezones.index(settings["default_guest_timezone"]))
            new_qr_interval = st.number_input("QR Refresh Interval (seconds)", min_value=60, max_value=7200, value=settings["qr_refresh_interval"])
            new_require_sync = st.checkbox("Require Time Sync (Block if API fails)", value=settings["require_time_sync"])
            
            if st.form_submit_button("Save Settings"):
                settings["admin_timezone"] = new_admin_tz
                settings["default_guest_timezone"] = new_default_guest_tz
                settings["qr_refresh_interval"] = new_qr_interval
                settings["require_time_sync"] = new_require_sync
                storage.save_admin_settings(settings)
                st.success("✅ System settings saved!")
                time_module.sleep(1)
                st.rerun()
    
        # Show Time Status
        st.divider()
        curr_time, is_synced = TimeService.get_current_time(settings["admin_timezone"])
        TimeService.show_time_sync_status(is_synced, curr_time)
