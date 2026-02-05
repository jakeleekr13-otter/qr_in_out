import json
import os
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime
import pytz

class JSONStorage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.lock = threading.Lock()
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _get_file_path(self, entity_type: str) -> str:
        return os.path.join(self.data_dir, f"{entity_type}.json")

    def load(self, entity_type: str) -> List[Dict[str, Any]]:
        file_path = self._get_file_path(entity_type)
        with self.lock:
            if not os.path.exists(file_path):
                return []
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []

    def save(self, entity_type: str, data: List[Dict[str, Any]]):
        file_path = self._get_file_path(entity_type)
        with self.lock:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def add(self, entity_type: str, entity: Dict[str, Any]):
        data = self.load(entity_type)
        data.append(entity)
        self.save(entity_type, data)

    def update(self, entity_type: str, entity_id: str, updates: Dict[str, Any]):
        data = self.load(entity_type)
        updated = False
        for i, item in enumerate(data):
            if item.get('id') == entity_id:
                data[i].update(updates)
                data[i]['updated_at'] = datetime.now(pytz.UTC).isoformat()
                updated = True
                break
        if updated:
            self.save(entity_type, data)

    def delete(self, entity_type: str, entity_id: str):
        # Physical delete - use with caution
        data = self.load(entity_type)
        data = [item for item in data if item.get('id') != entity_id]
        self.save(entity_type, data)

    def get_by_id(self, entity_type: str, entity_id: str) -> Optional[Dict]:
        data = self.load(entity_type)
        for item in data:
            if item.get('id') == entity_id:
                return item
        return None

    # Soft Delete helpers
    def soft_delete_checkpoint(self, checkpoint_id: str):
        checkpoint = self.get_by_id("checkpoints", checkpoint_id)
        if checkpoint:
            updates = {
                "name": f"{checkpoint['name']}_removed",
                "deleted_at": datetime.now(pytz.UTC).isoformat()
            }
            self.update("checkpoints", checkpoint_id, updates)

    def soft_delete_guest(self, guest_id: str):
        guest = self.get_by_id("guests", guest_id)
        if guest:
            updates = {
                "name": f"{guest['name']}_removed",
                "deleted_at": datetime.now(pytz.UTC).isoformat()
            }
            self.update("guests", guest_id, updates)

    def get_active_checkpoints(self) -> List[Dict]:
        data = self.load("checkpoints")
        return [item for item in data if item.get('deleted_at') is None]

    def get_active_guests(self) -> List[Dict]:
        data = self.load("guests")
        return [item for item in data if item.get('deleted_at') is None]

    # Admin Settings Singleton helper
    def load_admin_settings(self) -> Dict[str, Any]:
        data = self.load("admin_settings")
        if not data:
            from core.models import AdminSettings
            default_settings = AdminSettings.create_default().to_dict()
            self.save("admin_settings", [default_settings])
            return default_settings
        return data[0]

    def save_admin_settings(self, settings_dict: Dict[str, Any]):
        settings_dict['updated_at'] = datetime.now(pytz.UTC).isoformat()
        self.save("admin_settings", [settings_dict])

    # Admin Credentials
    def get_admin_credentials(self) -> Optional[Dict[str, str]]:
        data = self.load("admin_credentials")
        return data[0] if data else None

    def save_admin_credentials(self, credentials_dict: Dict[str, str]):
        # credentials_dict should contain 'username' and 'password_hash'
        credentials_dict['updated_at'] = datetime.now(pytz.UTC).isoformat()
        self.save("admin_credentials", [credentials_dict])
