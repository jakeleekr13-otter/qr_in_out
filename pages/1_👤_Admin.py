import streamlit as st
import pandas as pd
import secrets
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
from config.default_credentials import (
    DEFAULT_USERNAME, DEFAULT_PASSWORD, SECURITY_QUESTIONS,
    MAX_LOGIN_ATTEMPTS, LOCKOUT_DURATION_MINUTES
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
if "login_attempts" not in st.session_state:
    st.session_state.login_attempts = 0
if "login_locked_until" not in st.session_state:
    st.session_state.login_locked_until = None
if "recovery_mode" not in st.session_state:
    st.session_state.recovery_mode = False

# Check for existing admin account
admin_creds = storage.get_admin_credentials()

# --- Auth Flow ---

if not st.session_state.admin_authenticated:
    # LOGIN MODE
    st.title("👤 Admin Login")

    # Check if account is locked
    if st.session_state.login_locked_until:
        if datetime.now() < st.session_state.login_locked_until:
            remaining = int((st.session_state.login_locked_until - datetime.now()).total_seconds())
            minutes, seconds = divmod(remaining, 60)
            st.error(f"🔒 Account locked due to multiple failed login attempts.\n\nTry again in {minutes}m {seconds}s")

            # Auto-refresh countdown
            time_module.sleep(1)
            st.rerun()
        else:
            # Unlock account
            st.session_state.login_locked_until = None
            st.session_state.login_attempts = 0
            st.rerun()

    # Recovery Mode
    elif st.session_state.recovery_mode and admin_creds:
        st.title("🔑 Account Recovery")

        # Check if recovery options exist
        has_recovery_question = admin_creds.get("recovery_question")
        has_recovery_code = admin_creds.get("recovery_code_hash")

        if not has_recovery_question and not has_recovery_code:
            st.error("❌ No recovery options configured for this account.")
            st.warning("Recovery requires server access. Please delete `data/admin_credentials.json` and restart.")
            if st.button("← Back to Login"):
                st.session_state.recovery_mode = False
                st.rerun()
        else:
            recovery_method = st.radio("Choose recovery method:",
                                      ["Security Question" if has_recovery_question else None,
                                       "Recovery Code" if has_recovery_code else None],
                                      index=0)

            if recovery_method == "Security Question" and has_recovery_question:
                st.info(f"**Question:** {admin_creds['recovery_question']}")

                with st.form("recovery_question_form"):
                    recovery_answer = st.text_input("Your Answer", type="password")
                    new_password = st.text_input("New Password (min 8 characters)", type="password")
                    confirm_password = st.text_input("Confirm New Password", type="password")

                    if st.form_submit_button("Reset Password", type="primary"):
                        if AuthManager.verify_password(recovery_answer.lower().strip(),
                                                      admin_creds['recovery_answer_hash']):
                            if len(new_password) < 8:
                                st.error("❌ Password must be at least 8 characters")
                            elif new_password != confirm_password:
                                st.error("❌ Passwords do not match")
                            else:
                                # Reset password
                                admin_creds['password_hash'] = AuthManager.hash_password(new_password)
                                storage.save_admin_credentials(admin_creds)

                                st.session_state.recovery_mode = False
                                st.session_state.login_attempts = 0
                                st.session_state.login_locked_until = None

                                st.success("✅ Password reset successful! Please log in with your new password.")
                                time_module.sleep(2)
                                st.rerun()
                        else:
                            st.error("❌ Incorrect security answer")

            elif recovery_method == "Recovery Code" and has_recovery_code:
                st.info("Enter the recovery code that was provided during account setup.")

                with st.form("recovery_code_form"):
                    recovery_code = st.text_input("Recovery Code (32 characters)", type="password")
                    new_password = st.text_input("New Password (min 8 characters)", type="password")
                    confirm_password = st.text_input("Confirm New Password", type="password")

                    if st.form_submit_button("Reset Password", type="primary"):
                        if AuthManager.verify_password(recovery_code.strip(),
                                                      admin_creds['recovery_code_hash']):
                            if len(new_password) < 8:
                                st.error("❌ Password must be at least 8 characters")
                            elif new_password != confirm_password:
                                st.error("❌ Passwords do not match")
                            else:
                                # Reset password
                                admin_creds['password_hash'] = AuthManager.hash_password(new_password)
                                storage.save_admin_credentials(admin_creds)

                                st.session_state.recovery_mode = False
                                st.session_state.login_attempts = 0
                                st.session_state.login_locked_until = None

                                st.success("✅ Password reset successful! Please log in with your new password.")
                                time_module.sleep(2)
                                st.rerun()
                        else:
                            st.error("❌ Incorrect recovery code")

            if st.button("← Back to Login"):
                st.session_state.recovery_mode = False
                st.rerun()

    # Normal Login Mode
    else:
        # First time / Reset scenario
        if not admin_creds:
            st.info("ℹ️ System Not Configured. Please log in with default credentials.")
            st.caption(f"Default Username: **{DEFAULT_USERNAME}** | Default Password: **{DEFAULT_PASSWORD}**")

        with st.form("admin_login_form"):
            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")

            login_submitted = st.form_submit_button("Log In", type="primary")

            if login_submitted:
                # Scenario A: First Run (No stored creds) - Check defaults
                if not admin_creds:
                    if username_input == DEFAULT_USERNAME and password_input == DEFAULT_PASSWORD:
                        st.session_state.admin_authenticated = True
                        st.session_state.force_setup = True
                        st.session_state.login_attempts = 0
                        st.success("✅ Default login successful. Please set up your secure account.")
                        time_module.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"❌ Invalid default credentials. Use {DEFAULT_USERNAME}/{DEFAULT_PASSWORD}")

                # Scenario B: Normal Run - Check stored creds
                else:
                    if username_input == admin_creds["username"] and \
                       AuthManager.verify_password(password_input, admin_creds["password_hash"]):
                        st.session_state.admin_authenticated = True
                        st.session_state.force_setup = False
                        st.session_state.login_attempts = 0
                        st.success("✅ Login successful")
                        time_module.sleep(0.5)
                        st.rerun()
                    else:
                        # Failed login - increment attempts
                        st.session_state.login_attempts += 1
                        remaining = MAX_LOGIN_ATTEMPTS - st.session_state.login_attempts

                        if st.session_state.login_attempts >= MAX_LOGIN_ATTEMPTS:
                            # Lock account
                            st.session_state.login_locked_until = datetime.now() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                            st.error(f"🔒 Account locked for {LOCKOUT_DURATION_MINUTES} minutes due to multiple failed attempts")
                            time_module.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"❌ Invalid username or password ({remaining} attempts remaining)")

        # Recovery Link
        if admin_creds and not st.session_state.recovery_mode:
            if st.button("🔑 Forgot Password?"):
                st.session_state.recovery_mode = True
                st.rerun()

elif st.session_state.force_setup:
    # FORCE SETUP MODE (Interim step after default login)
    st.title("🛡️ Security Setup")
    st.warning("⚠️ You are using the default account. You MUST create a secure administrator account to proceed.")

    with st.form("admin_setup_form"):
        st.write("### 👤 Administrator Account")
        new_username = st.text_input("Username *", placeholder="admin", help="Your administrator username")
        new_password = st.text_input("Password *", type="password", help="Minimum 8 characters recommended")
        confirm_password = st.text_input("Confirm Password *", type="password")

        st.divider()
        st.write("### 🔐 Account Recovery Options")
        st.caption("Set up recovery options in case you forget your password. Both will be configured.")

        # Recovery Question
        st.write("**Option 1: Security Question**")
        recovery_question = st.selectbox("Security Question *", SECURITY_QUESTIONS)
        recovery_answer = st.text_input("Your Answer *", type="password",
                                       help="Answer will be saved (case-insensitive)")

        # Recovery Code
        st.write("**Option 2: Recovery Code**")
        st.caption("A 32-character random code will be generated. **Save it in a safe place!**")

        setup_submitted = st.form_submit_button("Create Account & Continue", type="primary")

        if setup_submitted:
            errors = []

            # Validate credentials
            if not new_username:
                errors.append("Username is required")
            elif len(new_username) < 3:
                errors.append("Username must be at least 3 characters")

            if not new_password:
                errors.append("Password is required")
            elif len(new_password) < 8:
                errors.append("Password must be at least 8 characters (recommended)")

            if new_password != confirm_password:
                errors.append("Passwords do not match")

            # Validate recovery options
            if not recovery_question:
                errors.append("Security question is required")

            if not recovery_answer:
                errors.append("Security answer is required")
            elif len(recovery_answer.strip()) < 2:
                errors.append("Security answer must be at least 2 characters")

            if errors:
                for e in errors:
                    st.error(f"❌ {e}")
            else:
                # Generate recovery code
                recovery_code = secrets.token_hex(16)  # 32 character hex string

                # Save Account
                creds = {
                    "username": new_username,
                    "password_hash": AuthManager.hash_password(new_password),
                    "recovery_question": recovery_question,
                    "recovery_answer_hash": AuthManager.hash_password(recovery_answer.lower().strip()),
                    "recovery_code_hash": AuthManager.hash_password(recovery_code),
                    "created_at": datetime.now().isoformat()
                }
                storage.save_admin_credentials(creds)

                # Exit setup mode
                st.session_state.force_setup = False
                st.session_state.admin_authenticated = False  # Force re-login

                st.balloons()
                st.success("✅ Administrator account created successfully!")

                # Display recovery code
                st.warning(f"""
### 🔑 IMPORTANT: Save Your Recovery Code

**Recovery Code:** `{recovery_code}`

**⚠️ Copy this code and save it in a safe place!**

This code can be used to reset your password if you forget it.
You will NOT see this code again.

---

**Recovery Options Available:**
- Security Question: {recovery_question}
- Recovery Code: (saved above)
                """)

                st.info("Click the button below to return to login and sign in with your new credentials.")

                if st.button("← Return to Login", type="primary"):
                    st.session_state.force_setup = False
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
