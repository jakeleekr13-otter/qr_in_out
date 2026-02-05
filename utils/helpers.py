from core.storage import JSONStorage
import re

storage = JSONStorage()

def get_checkpoint_name(checkpoint_id: str) -> str:
    checkpoint = storage.get_by_id("checkpoints", checkpoint_id)
    return checkpoint["name"] if checkpoint else "Unknown Checkpoint"

def get_guest_name(guest_id: str) -> str:
    guest = storage.get_by_id("guests", guest_id)
    return guest["name"] if guest else "Unknown Guest"

def get_guest_email(guest_id: str) -> str:
    guest = storage.get_by_id("guests", guest_id)
    return guest["email"] if guest else "Unknown Email"

def is_valid_email(email: str) -> bool:
    """Simple email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def checkpoint_name_exists(name: str, exclude_id: str = None) -> bool:
    checkpoints = storage.load("checkpoints")
    for cp in checkpoints:
        if cp["name"] == name and cp["id"] != exclude_id and cp.get('deleted_at') is None:
            return True
    return False

def guest_email_exists(email: str, exclude_id: str = None) -> bool:
    guests = storage.load("guests")
    for g in guests:
        if g["email"] == email and g["id"] != exclude_id and g.get('deleted_at') is None:
            return True
    return False

def get_checkpoint_location(checkpoint_id: str) -> str:
    """Get checkpoint location by ID."""
    checkpoint = storage.get_by_id("checkpoints", checkpoint_id)
    return checkpoint["location"] if checkpoint else "Unknown Location"
