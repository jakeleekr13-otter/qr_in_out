#!/usr/bin/env python3
"""
Screenshot Capture Script for QR In/Out System

Uses Playwright to automate browser interactions and capture screenshots
of the running Streamlit application with demo data.

Usage:
    pip install playwright
    playwright install chromium
    python scripts/capture_screenshots.py
"""

import os
import sys
import shutil
import json
import time
import random
import subprocess
import bcrypt
from datetime import datetime, timedelta

from playwright.sync_api import sync_playwright, Page

# ── Configuration ──────────────────────────────────────────────────────────────

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
BACKUP_DIR = os.path.join(PROJECT_ROOT, "data_backup_screenshots")
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets", "screenshots")
PORT = 8503
BASE_URL = f"http://localhost:{PORT}"

# Credentials used in seed data
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin1234"
HOST_PASSWORD = "host1234"
GUEST_NAME = "Sarah Connor"
GUEST_EMAIL = "sarah@example.com"


# ── Utility Functions ─────────────────────────────────────────────────────────

def setup_directories():
    os.makedirs(ASSETS_DIR, exist_ok=True)


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


# ── Data Backup / Restore ─────────────────────────────────────────────────────

def backup_data():
    print("[BACKUP] Saving current data...")
    if os.path.exists(BACKUP_DIR):
        shutil.rmtree(BACKUP_DIR)
    if os.path.exists(DATA_DIR):
        shutil.copytree(DATA_DIR, BACKUP_DIR)
    else:
        os.makedirs(DATA_DIR, exist_ok=True)


def restore_data():
    print("[RESTORE] Restoring original data...")
    if os.path.exists(DATA_DIR):
        shutil.rmtree(DATA_DIR)
    if os.path.exists(BACKUP_DIR):
        shutil.copytree(BACKUP_DIR, DATA_DIR)
        shutil.rmtree(BACKUP_DIR)


# ── Seed Data ─────────────────────────────────────────────────────────────────

def seed_data():
    """Create realistic demo data for screenshots."""
    print("[SEED] Creating demo data...")
    os.makedirs(DATA_DIR, exist_ok=True)

    now = datetime.now()

    # Admin Credentials (matches storage.get_admin_credentials format)
    admin_creds = {
        "username": ADMIN_USERNAME,
        "password_hash": hash_password(ADMIN_PASSWORD),
        "recovery_question": "What was your first pet's name?",
        "recovery_answer_hash": hash_password("buddy"),
        "recovery_code_hash": hash_password("a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"),
        "created_at": (now - timedelta(days=14)).isoformat(),
    }

    # Admin Settings
    admin_settings = {
        "admin_timezone": "Asia/Seoul",
        "default_guest_timezone": "Asia/Seoul",
        "qr_refresh_interval": 30,
        "require_time_sync": False,
    }

    # Checkpoints (first one = static for stable Host screenshot)
    cp_pw = hash_password(HOST_PASSWORD)
    checkpoints = [
        {
            "id": "cp-demo-main",
            "name": "Main Entrance Lobby",
            "location": "Building A, Ground Floor",
            "allowed_hours": {"start_time": "00:00", "end_time": "23:59"},
            "qr_mode": "static",
            "admin_password_hash": cp_pw,
            "allowed_guests": ["guest-sarah", "guest-john", "guest-alex"],
            "current_qr_sequence": 0,
            "created_at": (now - timedelta(days=10)).isoformat(),
            "updated_at": now.isoformat(),
            "deleted_at": None,
        },
        {
            "id": "cp-demo-conf",
            "name": "Conference Room B",
            "location": "Building A, 3rd Floor",
            "allowed_hours": {"start_time": "09:00", "end_time": "18:00"},
            "qr_mode": "dynamic",
            "admin_password_hash": cp_pw,
            "allowed_guests": ["guest-sarah", "guest-john"],
            "current_qr_sequence": 5,
            "created_at": (now - timedelta(days=7)).isoformat(),
            "updated_at": now.isoformat(),
            "deleted_at": None,
        },
        {
            "id": "cp-demo-lounge",
            "name": "Employee Lounge",
            "location": "Building B, 2nd Floor",
            "allowed_hours": {"start_time": "07:00", "end_time": "22:00"},
            "qr_mode": "static",
            "admin_password_hash": cp_pw,
            "allowed_guests": ["guest-sarah", "guest-john", "guest-alex"],
            "current_qr_sequence": 0,
            "created_at": (now - timedelta(days=5)).isoformat(),
            "updated_at": now.isoformat(),
            "deleted_at": None,
        },
    ]

    # Guests
    guests = [
        {
            "id": "guest-sarah",
            "name": "Sarah Connor",
            "email": "sarah@example.com",
            "phone": "010-1234-5678",
            "timezone": "Asia/Seoul",
            "allowed_checkpoints": ["cp-demo-main", "cp-demo-conf", "cp-demo-lounge"],
            "allowed_hours": None,
            "created_at": (now - timedelta(days=10)).isoformat(),
            "updated_at": now.isoformat(),
            "deleted_at": None,
        },
        {
            "id": "guest-john",
            "name": "John Smith",
            "email": "john@example.com",
            "phone": "010-9876-5432",
            "timezone": "Asia/Seoul",
            "allowed_checkpoints": ["cp-demo-main", "cp-demo-conf", "cp-demo-lounge"],
            "allowed_hours": {"start_time": "09:00", "end_time": "18:00"},
            "created_at": (now - timedelta(days=7)).isoformat(),
            "updated_at": now.isoformat(),
            "deleted_at": None,
        },
        {
            "id": "guest-alex",
            "name": "Alex Rodriguez",
            "email": "alex@example.com",
            "phone": "010-5555-1234",
            "timezone": "America/New_York",
            "allowed_checkpoints": ["cp-demo-main", "cp-demo-lounge"],
            "allowed_hours": None,
            "created_at": (now - timedelta(days=3)).isoformat(),
            "updated_at": now.isoformat(),
            "deleted_at": None,
        },
    ]

    # Activity Logs - generate realistic data over 7 days
    logs = []
    action_templates = [
        ("guest-sarah", "cp-demo-main",   "check_in",  "success", None),
        ("guest-sarah", "cp-demo-main",   "check_out", "success", None),
        ("guest-sarah", "cp-demo-conf",   "check_in",  "success", None),
        ("guest-sarah", "cp-demo-conf",   "check_out", "success", None),
        ("guest-john",  "cp-demo-main",   "check_in",  "success", None),
        ("guest-john",  "cp-demo-main",   "check_out", "success", None),
        ("guest-john",  "cp-demo-lounge", "check_in",  "success", None),
        ("guest-john",  "cp-demo-lounge", "check_out", "success", None),
        ("guest-alex",  "cp-demo-main",   "check_in",  "success", None),
        ("guest-alex",  "cp-demo-main",   "check_out", "success", None),
        ("guest-john",  "cp-demo-conf",   "check_in",  "failure", "Outside allowed hours"),
        ("guest-alex",  "cp-demo-conf",   "check_in",  "failure", "Not authorized for this checkpoint"),
    ]

    log_id = 0
    for day_offset in range(7, -1, -1):
        day = now - timedelta(days=day_offset)
        random.seed(42 + day_offset)  # deterministic per day
        num_activities = random.randint(4, 10)

        for _ in range(num_activities):
            tpl = random.choice(action_templates)
            hour = random.randint(8, 19)
            minute = random.randint(0, 59)
            ts = day.replace(hour=hour, minute=minute, second=random.randint(0, 59))

            log_id += 1
            logs.append({
                "id": f"log-{log_id}",
                "timestamp": ts.isoformat(),
                "checkpoint_id": tpl[1],
                "guest_id": tpl[0],
                "action": tpl[2],
                "status": tpl[3],
                "qr_code_used": "demo_qr_content",
                "failure_reason": tpl[4],
                "metadata": {"scanned_at": ts.isoformat()},
            })

    logs.sort(key=lambda x: x["timestamp"])

    # Write all JSON files
    files = {
        "admin_credentials": [admin_creds],
        "admin_settings": [admin_settings],
        "checkpoints": checkpoints,
        "guests": guests,
        "activity_logs": logs,
    }
    for name, data in files.items():
        with open(os.path.join(DATA_DIR, f"{name}.json"), "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[SEED] {len(checkpoints)} checkpoints, {len(guests)} guests, {len(logs)} logs")


# ── Streamlit Server ──────────────────────────────────────────────────────────

def run_streamlit():
    print(f"[SERVER] Starting Streamlit on port {PORT}...")
    env = os.environ.copy()
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    process = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", str(PORT),
            "--server.headless", "true",
        ],
        env=env,
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return process


def kill_streamlit(process):
    if process and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


# ── Playwright Helpers ────────────────────────────────────────────────────────

def wait_for_app(page: Page) -> bool:
    """Wait for Streamlit to fully load."""
    print("[WAIT] Waiting for Streamlit to start...")
    for attempt in range(60):
        try:
            page.goto(BASE_URL, timeout=5000)
            page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=5000)
            print(f"[WAIT] Ready (attempt {attempt + 1})")
            return True
        except Exception:
            time.sleep(1)
    print("[WAIT] Timed out!")
    return False


def settle(page: Page, extra: float = 1.0):
    """Wait for Streamlit to finish re-rendering.

    TimeService makes external HTTP calls (timeout=5s each, 2 sources)
    so pages calling it can take up to ~12s to render.
    """
    try:
        page.wait_for_selector(
            '[data-testid="stStatusWidget"]', state="hidden", timeout=20000
        )
    except Exception:
        pass
    time.sleep(extra)


def wait_for_element(page: Page, text: str, timeout: int = 20000) -> bool:
    """Wait for text to appear on the page."""
    try:
        page.get_by_text(text, exact=False).first.wait_for(
            state="visible", timeout=timeout
        )
        return True
    except Exception:
        return False


def screenshot(page: Page, name: str, full_page: bool = False):
    path = os.path.join(ASSETS_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=full_page)
    print(f"  -> {name}.png")


def click_sidebar_page(page: Page, page_text: str):
    """Click a page link in the Streamlit sidebar navigation."""
    try:
        nav = page.locator('[data-testid="stSidebarNav"]')
        nav.get_by_text(page_text, exact=False).first.click()
    except Exception:
        # Fallback: click any sidebar link containing the text
        page.locator(f'a:has-text("{page_text}")').first.click()
    settle(page)


def click_sidebar_radio(page: Page, label: str):
    """Click a radio option in the sidebar (Admin menu navigation)."""
    sidebar = page.locator('[data-testid="stSidebar"]')
    sidebar.get_by_text(label, exact=True).click()
    settle(page)


# ── Main Capture Sequence ────────────────────────────────────────────────────

def capture_all(process):
    streamlit_proc = process
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                device_scale_factor=2,
            )
            page = context.new_page()

            if not wait_for_app(page):
                return

            print("\n========== Screenshot Capture ==========\n")

            # ── 1. Home ──────────────────────────────────────────────
            print("[1/11] Home Page")
            page.goto(BASE_URL)
            settle(page)
            screenshot(page, "01_home")

            # ── 2. Admin Login ────────────────────────────────────────
            print("[2/11] Admin Login")
            click_sidebar_page(page, "Admin")
            settle(page)
            screenshot(page, "02_admin_login")

            # ── 3. Admin → Checkpoint Management ─────────────────────
            print("[3/11] Admin - Checkpoint Management")
            page.locator('input[aria-label="Username"]').fill(ADMIN_USERNAME)
            page.locator('input[aria-label="Password"]').fill(ADMIN_PASSWORD)
            page.get_by_role("button", name="Log In").click()
            settle(page, 2)
            # Default menu is "Checkpoint Management"
            screenshot(page, "03_admin_checkpoints")

            # ── 4. Admin → Guest Management ──────────────────────────
            print("[4/11] Admin - Guest Management")
            click_sidebar_radio(page, "Guest Management")
            screenshot(page, "04_admin_guests")

            # ── 5. Admin → Activity Logs ─────────────────────────────
            print("[5/11] Admin - Activity Logs")
            click_sidebar_radio(page, "Activity Logs")
            screenshot(page, "05_admin_logs")

            # ── 6. Admin → Statistics Dashboard ──────────────────────
            print("[6/11] Admin - Statistics Dashboard")
            click_sidebar_radio(page, "Statistics Dashboard")
            screenshot(page, "06_admin_statistics")

            # ── 7. Host Login ────────────────────────────────────────
            print("[7/11] Host Login")
            click_sidebar_page(page, "Host")
            settle(page)
            screenshot(page, "07_host_login")

            # ── 8. Host QR Display ───────────────────────────────────
            print("[8/11] Host QR Display")
            # First checkpoint (Main Entrance Lobby, static) is pre-selected
            page.locator('input[aria-label="Admin Password"]').fill(HOST_PASSWORD)
            page.get_by_role("button", name="Start Display").click()
            # Host page calls TimeService (external API, up to ~12s) then renders QR
            wait_for_element(page, "Static Mode", timeout=25000)
            settle(page, 1)
            # Use taller viewport to fit header + status + QR in one frame
            page.set_viewport_size({"width": 1280, "height": 1200})
            time.sleep(0.5)
            screenshot(page, "08_host_qr_display")
            page.set_viewport_size({"width": 1280, "height": 800})

            # ── 9. Guest Login ───────────────────────────────────────
            print("[9/11] Guest Login")
            click_sidebar_page(page, "Guest")
            settle(page)
            screenshot(page, "09_guest_login")

            # ── 10. Guest → Scan Tab ─────────────────────────────────
            print("[10/11] Guest - Scan Tab")
            page.locator('input[aria-label="Name"]').fill(GUEST_NAME)
            page.locator('input[aria-label="Email"]').fill(GUEST_EMAIL)
            page.get_by_role("button", name="Login").click()
            settle(page, 2)
            screenshot(page, "10_guest_scan")

            # ── 11. Guest → History Tab ──────────────────────────────
            print("[11/11] Guest - History Tab")
            page.get_by_text("My History", exact=False).click()
            settle(page, 1)
            screenshot(page, "11_guest_history")

            print(f"\n========== Done! {ASSETS_DIR} ==========\n")
            browser.close()

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        kill_streamlit(streamlit_proc)


# ── Entry Point ───────────────────────────────────────────────────────────────

def main():
    setup_directories()
    backup_data()
    try:
        seed_data()
        process = run_streamlit()
        capture_all(process)
    except KeyboardInterrupt:
        print("\n[INTERRUPTED]")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        restore_data()
        print("[DONE]")


if __name__ == "__main__":
    main()
