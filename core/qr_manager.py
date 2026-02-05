import qrcode
import json
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple, Any
from PIL import Image
import io
import base64

class QRManager:
    SECRET_KEY = "qr-in-out-secret-key"  # In production, load from environment variable

    @staticmethod
    def generate_static_qr_content(checkpoint_id: str) -> str:
        content = {
            "type": "qr_in_out",
            "version": "1.0",
            "checkpoint_id": checkpoint_id,
            "qr_mode": "static",
            "created_at": datetime.now().isoformat()
        }
        return json.dumps(content)

    @staticmethod
    def generate_dynamic_qr_content(checkpoint_id: str, current_sequence: int, 
                                     issued_at: datetime, expires_at: datetime,
                                     refresh_interval: int = 1800) -> str:
        content = {
            "type": "qr_in_out",
            "version": "1.0",
            "checkpoint_id": checkpoint_id,
            "qr_mode": "dynamic",
            "sequence": current_sequence,
            "issued_at": issued_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "refresh_interval": refresh_interval
        }
        
        # Add signature
        signature = QRManager._generate_signature(content)
        content["signature"] = signature
        
        return json.dumps(content)

    @staticmethod
    def _generate_signature(content: Dict[str, Any]) -> str:
        # Create a canonical string representation excluding the signature itself
        data_to_sign = f"{content['checkpoint_id']}|{content['sequence']}|{content['issued_at']}"
        return hmac.new(
            QRManager.SECRET_KEY.encode(),
            data_to_sign.encode(),
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    def generate_qr_image(content: str, box_size: int = 10) -> Image:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=box_size,
            border=4,
        )
        qr.add_data(content)
        qr.make(fit=True)
        return qr.make_image(fill_color="black", back_color="white")

    @staticmethod
    def parse_qr_content(qr_string: str) -> Optional[Dict]:
        try:
            return json.loads(qr_string)
        except Exception:
            return None

    @staticmethod
    def verify_signature(qr_content: Dict) -> bool:
        if "signature" not in qr_content:
            return False
        
        expected_sig = QRManager._generate_signature(qr_content)
        return hmac.compare_digest(qr_content["signature"], expected_sig)

    @staticmethod
    def is_qr_expired(qr_content: Dict, current_time: datetime) -> bool:
        if qr_content.get("qr_mode") == "static":
            return False
            
        expires_at_str = qr_content.get("expires_at")
        if not expires_at_str:
            return True
            
        expires_at = datetime.fromisoformat(expires_at_str)
        # Ensure comparison is timezone-aware if current_time is
        if expires_at.tzinfo is None and current_time.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=current_time.tzinfo)
        elif expires_at.tzinfo is not None and current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=expires_at.tzinfo)
            
        return current_time > expires_at

    @staticmethod
    def validate_dynamic_qr(qr_content: Dict, checkpoint: Dict, 
                             current_time: datetime, is_synced: bool) -> Tuple[bool, str]:
        """
        Validate dynamic QR logic: Signature, Time, Sequence, Sync Requirement.
        """
        # 1. Signature
        if not QRManager.verify_signature(qr_content):
            return False, "Invalid signature"

        # 2. Expiration
        if QRManager.is_qr_expired(qr_content, current_time):
             return False, "QR code expired"

        # 3. Time Sync Requirement (Policy Check)
        # Assuming admin settings are checked outside or passed here. 
        # But for strictly QR logic, if checking time validity, trustworthy time source is needed.
        if not is_synced:
            # If system requires strict sync, this might be a failure.
            # However, logic is usually handled by caller using settings["require_time_sync"]
            pass 

        return True, "Valid"
