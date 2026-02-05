# Security Analysis & Recommendations
## QR In/Out System - Static Code Analysis Report

**Analysis Date**: 2026-02-05
**Version**: 1.0
**Analyzed Files**: All implementation files in `pages/`, `core/`, and `utils/`

---

## Executive Summary

This document provides a comprehensive security analysis of the QR In/Out system. The analysis identifies **critical security vulnerabilities** that must be addressed before production deployment, along with recommendations for remediation.

**Overall Security Status**: ⚠️ **NOT PRODUCTION-READY**

**Key Findings**:
- 🔴 **3 Critical Vulnerabilities** requiring immediate attention
- 🟠 **6 High-Priority Issues** that should be fixed before production
- 🟡 **4 Medium-Priority Issues** recommended for improvement

---

## Critical Security Vulnerabilities

### 1. Weak Password Hashing (SHA-256)

**File**: `core/auth.py`
**Severity**: 🔴 **CRITICAL**
**CVSS Score**: 8.1 (High)

#### Current Implementation

```python
def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()
```

#### Problems

1. **No Salt**: SHA-256 without salt is vulnerable to rainbow table attacks
2. **Fast Hashing**: Designed for speed, not security - enables brute force attacks
3. **No Work Factor**: Cannot adjust computational cost as hardware improves
4. **Predictable**: Same password always produces same hash

#### Attack Scenario

```
1. Attacker gains access to data/admin_settings.json
2. Extracts password hash: "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"
3. Uses rainbow table or GPU-accelerated cracking
4. Cracks weak password ("admin") in < 1 second
5. Full system compromise
```

#### Remediation

**Option 1: Use bcrypt (Recommended)**

```python
import bcrypt

def hash_password(password: str) -> str:
    """Hash a password using bcrypt with automatic salt."""
    salt = bcrypt.gensalt(rounds=12)  # Work factor: 2^12 iterations
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(password.encode(), password_hash.encode())
```

**Option 2: Use argon2 (More Secure)**

```python
from argon2 import PasswordHasher

ph = PasswordHasher()

def hash_password(password: str) -> str:
    """Hash a password using Argon2id."""
    return ph.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its Argon2 hash."""
    try:
        ph.verify(password_hash, password)
        return True
    except:
        return False
```

**Migration Steps**:

1. Install: `pip install bcrypt` or `pip install argon2-cffi`
2. Replace `core/auth.py` with new implementation
3. Add migration script to rehash existing passwords on first login
4. Update `requirements.txt`

**Priority**: P0 - **MUST FIX BEFORE PRODUCTION**

---

### 2. Hardcoded Secret Key

**File**: `core/qr_manager.py:12`
**Severity**: 🔴 **CRITICAL**
**CVSS Score**: 9.1 (Critical)

#### Current Implementation

```python
class QRManager:
    SECRET_KEY = "qr-in-out-secret-key"  # In production, load from environment variable
```

#### Problems

1. **Visible in Source**: Anyone with repository access knows the secret
2. **Version Control**: Committed to git history, cannot be changed retroactively
3. **Forgery**: Attacker can generate valid HMAC signatures
4. **No Rotation**: Cannot change key without breaking all existing QR codes

#### Attack Scenario

```
1. Attacker views public GitHub repository
2. Extracts SECRET_KEY from core/qr_manager.py
3. Generates forged dynamic QR codes with valid signatures:
   {
     "checkpoint_id": "target_checkpoint",
     "sequence": 999,
     "expires_at": "2099-12-31T23:59:59",
     "signature": "valid_hmac_using_known_secret"
   }
4. Bypasses all time and sequence validations
5. Unauthorized access to all checkpoints
```

#### Remediation

**Step 1: Use Environment Variables**

```python
import os
from secrets import token_hex

class QRManager:
    SECRET_KEY = os.getenv("QR_SECRET_KEY")

    @classmethod
    def _get_secret_key(cls):
        if not cls.SECRET_KEY:
            raise ValueError("QR_SECRET_KEY environment variable not set!")
        if len(cls.SECRET_KEY) < 32:
            raise ValueError("QR_SECRET_KEY must be at least 32 characters")
        return cls.SECRET_KEY
```

**Step 2: Generate Secure Key**

```bash
# Generate a secure random key
python3 -c "import secrets; print(secrets.token_hex(32))"
# Output: 8f3e9d2a1b4c5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1
```

**Step 3: Set Environment Variable**

Create `.env` file (add to `.gitignore`):

```env
QR_SECRET_KEY=8f3e9d2a1b4c5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1
```

**Step 4: Load in Application**

```python
# At app startup (app.py)
from dotenv import load_dotenv
load_dotenv()
```

**Step 5: Update .gitignore**

```gitignore
.env
*.env
.env.local
.env.production
```

**Priority**: P0 - **MUST FIX BEFORE PRODUCTION**

---

### 3. Deleted Guest Authentication Bypass

**File**: `pages/3_👋_Guest.py:79-88`
**Severity**: 🔴 **CRITICAL**
**CVSS Score**: 7.5 (High)

#### Current Implementation

```python
def verify_guest(name: str, email: str):
    """Verify guest credentials case-insensitively."""
    guests = storage.get_active_guests()  # ← Misleading function name
    name_clean = name.strip().lower()
    email_clean = email.strip().lower()

    for g in guests:
        if (g["name"].strip().lower() == name_clean and
            g["email"].strip().lower() == email_clean):
            return g  # ← Returns guest even if deleted_at is set!
    return None
```

#### Problems

1. **No Deleted Check**: Function doesn't actually filter deleted guests
2. **Misleading Name**: `get_active_guests()` suggests filtering, but verification doesn't use it properly
3. **Access Control Bypass**: Terminated employees/contractors can still check in

#### Attack Scenario

```
1. Employee "John Doe" is fired on Monday
2. Admin soft-deletes John's guest account (deleted_at = "2026-02-03T09:00:00Z")
3. John still has credentials (name + email)
4. Tuesday, John arrives at checkpoint
5. System authenticates John (deleted_at field ignored)
6. John gains unauthorized access
```

#### Remediation

**Fix 1: Check deleted_at in verify_guest**

```python
def verify_guest(name: str, email: str):
    """Verify guest credentials case-insensitively."""
    guests = storage.load("guests")
    name_clean = name.strip().lower()
    email_clean = email.strip().lower()

    for g in guests:
        # ✅ FIX: Check if guest is deleted
        if g.get("deleted_at") is not None:
            continue  # Skip deleted guests

        if (g["name"].strip().lower() == name_clean and
            g["email"].strip().lower() == email_clean):
            return g
    return None
```

**Fix 2: Show Clear Error Message**

```python
# After authentication attempt
if not guest:
    st.error("인증 실패: 이름 또는 이메일이 일치하지 않거나, 삭제된 계정입니다.")
```

**Priority**: P0 - **MUST FIX BEFORE PRODUCTION**

---

## High-Priority Security Issues

### 4. No Input Validation on QR Content

**File**: `pages/3_👋_Guest.py:245`
**Severity**: 🟠 **HIGH**
**CVSS Score**: 6.5 (Medium)

#### Current Implementation

```python
qr_data_obj = QRManager.parse_qr_content(qr_str)

if qr_data_obj and qr_data_obj.get("type") == "qr_in_out":
    # Accepts any JSON structure without schema validation
```

#### Problems

- No validation of required fields
- Missing fields don't cause errors
- Malicious JSON could contain unexpected data
- No type checking on values

#### Remediation

```python
from typing import Optional

def validate_qr_schema(qr_data: dict) -> tuple[bool, Optional[str]]:
    """Validate QR code data structure."""
    required_fields = ["type", "version", "checkpoint_id", "qr_mode"]

    # Check required fields
    for field in required_fields:
        if field not in qr_data:
            return False, f"Missing required field: {field}"

    # Validate type
    if qr_data["type"] != "qr_in_out":
        return False, "Invalid QR type"

    # Validate qr_mode
    if qr_data["qr_mode"] not in ["static", "dynamic"]:
        return False, "Invalid QR mode"

    # Dynamic QR requires additional fields
    if qr_data["qr_mode"] == "dynamic":
        dynamic_fields = ["sequence", "issued_at", "expires_at", "signature"]
        for field in dynamic_fields:
            if field not in qr_data:
                return False, f"Dynamic QR missing field: {field}"

    return True, None

# Usage
valid, error = validate_qr_schema(qr_data_obj)
if not valid:
    st.error(f"Invalid QR code: {error}")
    return
```

**Priority**: P1

---

### 5. Time Sync Requirement Not Enforced

**File**: `core/qr_manager.py:117-120`
**Severity**: 🟠 **HIGH**

#### Current Implementation

```python
# 3. Time Sync Requirement (Policy Check)
if not is_synced:
    # If system requires strict sync, this might be a failure.
    # However, logic is usually handled by caller using settings["require_time_sync"]
    pass  # ← NO ENFORCEMENT!
```

#### Problems

- Admin can set `require_time_sync = true` but it's not enforced
- Validation continues even when time is not synchronized
- Allows time manipulation attacks when API is unavailable

#### Remediation

```python
def validate_dynamic_qr(qr_content: Dict, checkpoint: Dict,
                         current_time: datetime, is_synced: bool,
                         settings: Dict) -> Tuple[bool, str]:
    """Validate dynamic QR logic with settings enforcement."""

    # 1. Signature
    if not QRManager.verify_signature(qr_content):
        return False, "Invalid signature"

    # 2. Time Sync Requirement
    if settings.get("require_time_sync", True) and not is_synced:
        return False, "Time synchronization required but not available"

    # 3. Expiration
    if QRManager.is_qr_expired(qr_content, current_time):
         return False, "QR code expired"

    return True, "Valid"
```

**Priority**: P1

---

### 6. No Rate Limiting on Authentication

**Files**: `pages/1_👤_Admin.py`, `pages/2_🖥️_Host.py`, `pages/3_👋_Guest.py`
**Severity**: 🟠 **HIGH**

#### Problems

- Unlimited login attempts allowed
- No delay between failed attempts
- No account lockout mechanism
- Enables brute force password attacks

#### Remediation

```python
import time
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self):
        self.attempts = {}  # {identifier: [(timestamp, success), ...]}

    def check_rate_limit(self, identifier: str, max_attempts: int = 5,
                         window_minutes: int = 15) -> tuple[bool, str]:
        """Check if rate limit exceeded."""
        now = datetime.now()
        cutoff = now - timedelta(minutes=window_minutes)

        # Get recent attempts
        if identifier in self.attempts:
            recent = [t for t, success in self.attempts[identifier]
                     if t > cutoff and not success]
        else:
            recent = []

        if len(recent) >= max_attempts:
            return False, f"Too many failed attempts. Try again in {window_minutes} minutes."

        return True, ""

    def record_attempt(self, identifier: str, success: bool):
        """Record authentication attempt."""
        if identifier not in self.attempts:
            self.attempts[identifier] = []
        self.attempts[identifier].append((datetime.now(), success))

        # Keep only last 100 attempts per identifier
        self.attempts[identifier] = self.attempts[identifier][-100:]

# Usage in Admin page
rate_limiter = RateLimiter()

# Before authentication
allowed, message = rate_limiter.check_rate_limit(f"admin_{username}")
if not allowed:
    st.error(message)
    return

# After authentication attempt
rate_limiter.record_attempt(f"admin_{username}", success=is_valid)

if not is_valid:
    st.error("Invalid credentials")
    time.sleep(2)  # Exponential backoff
```

**Priority**: P1

---

### 7. XSS via User-Controlled Names

**Files**: `pages/1_👤_Admin.py:107`, `pages/3_👋_Guest.py:multiple`
**Severity**: 🟠 **HIGH**

#### Current Implementation

```python
st.header(f"📍 {checkpoint['name']}")  # Direct interpolation
```

#### Problems

- Checkpoint/guest names not sanitized
- Could contain HTML/JavaScript
- Streamlit auto-escapes in most cases but not guaranteed

#### Attack Scenario

```
1. Admin creates checkpoint named: <script>alert('XSS')</script>
2. Name stored in database
3. When displayed, JavaScript could execute
4. Session hijacking, credential theft possible
```

#### Remediation

```python
import html

def sanitize_user_input(text: str) -> str:
    """Sanitize user input to prevent XSS."""
    return html.escape(text)

# Usage
st.header(f"📍 {sanitize_user_input(checkpoint['name'])}")

# Or use st.write with plaintext
st.write(f"📍 {checkpoint['name']}")  # Streamlit handles escaping
```

**Priority**: P1

---

### 8. Plaintext Data Storage (No Encryption)

**File**: `core/storage.py`
**Severity**: 🟠 **MEDIUM-HIGH**

#### Current Implementation

```python
def save(self, entity_type: str, data: List[Dict[str, Any]]):
    file_path = self._get_file_path(entity_type)
    with self.lock:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
```

#### Problems

- All data stored in plaintext JSON
- Password hashes readable on disk
- Activity logs contain sensitive information
- No file permissions set
- No encryption at rest

#### Remediation

**Option 1: Encrypt Sensitive Fields**

```python
from cryptography.fernet import Fernet

class EncryptedStorage(JSONStorage):
    def __init__(self, data_dir: str, encryption_key: bytes):
        super().__init__(data_dir)
        self.cipher = Fernet(encryption_key)

    def encrypt_field(self, value: str) -> str:
        """Encrypt a field value."""
        return self.cipher.encrypt(value.encode()).decode()

    def decrypt_field(self, value: str) -> str:
        """Decrypt a field value."""
        return self.cipher.decrypt(value.encode()).decode()

# Encrypt password hashes before storing
checkpoint["admin_password_hash"] = storage.encrypt_field(password_hash)
```

**Option 2: Set File Permissions**

```python
import os

def save(self, entity_type: str, data: List[Dict[str, Any]]):
    file_path = self._get_file_path(entity_type)
    with self.lock:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Set restrictive permissions (owner read/write only)
        os.chmod(file_path, 0o600)
```

**Priority**: P2

---

### 9. No CSRF Protection

**All Pages**
**Severity**: 🟠 **MEDIUM**

#### Current State

- Streamlit provides some built-in CSRF protection
- No explicit token validation visible
- No SameSite cookie configuration seen

#### Remediation

**Verify Streamlit's Protection**:

Streamlit handles CSRF internally through session state. Verify by:

1. Checking Streamlit documentation for current version
2. Confirming session state is properly isolated
3. Adding explicit checks if needed:

```python
import secrets

if "csrf_token" not in st.session_state:
    st.session_state.csrf_token = secrets.token_hex(32)

# Include in forms
if form_csrf != st.session_state.csrf_token:
    st.error("Invalid request")
    return
```

**Priority**: P2

---

## Medium-Priority Issues

### 10. Case-Sensitive Email Duplicates

**File**: `utils/helpers.py:30-35`
**Severity**: 🟡 **MEDIUM**

#### Problem

Email validation is case-insensitive in input but case-sensitive in storage:

```python
def guest_email_exists(email: str, exclude_id: str = None) -> bool:
    guests = storage.load("guests")
    for g in guests:
        if g["email"] == email and ...  # ← Case-sensitive
```

Allows: `John@example.com` and `john@example.com` as separate accounts

#### Remediation

```python
def guest_email_exists(email: str, exclude_id: str = None) -> bool:
    guests = storage.load("guests")
    email_lower = email.strip().lower()
    for g in guests:
        if g["email"].strip().lower() == email_lower and g["id"] != exclude_id:
            return True
    return False
```

**Priority**: P2

---

### 11. Missing Time Range Validation

**File**: `pages/1_👤_Admin.py:188-201`
**Severity**: 🟡 **MEDIUM**

#### Problem

No validation that `start_time < end_time` for allowed hours

#### Remediation

```python
from datetime import time

def validate_time_range(start_str: str, end_str: str) -> tuple[bool, str]:
    """Validate time range."""
    try:
        start = time.fromisoformat(start_str)
        end = time.fromisoformat(end_str)

        # Allow overnight shifts (22:00 - 06:00)
        # So we only check if they're equal
        if start == end:
            return False, "Start and end time cannot be the same"

        return True, ""
    except ValueError:
        return False, "Invalid time format (use HH:MM)"

# Usage
valid, msg = validate_time_range(start_time, end_time)
if not valid:
    errors.append(msg)
```

**Priority**: P2

---

### 12. Generic Exception Handling

**Multiple Files**
**Severity**: 🟡 **MEDIUM**

#### Current Implementation

```python
try:
    url = f"http://worldtimeapi.org/api/timezone/{timezone_str}"
    response = requests.get(url, timeout=5)
except Exception:  # Too broad!
    pass
```

#### Problems

- Catches all exceptions including system errors
- Hides bugs and unexpected failures
- No logging or error context

#### Remediation

```python
import logging

logger = logging.getLogger(__name__)

try:
    url = f"http://worldtimeapi.org/api/timezone/{timezone_str}"
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
        data = response.json()
        return datetime.fromisoformat(data["datetime"]), True
except requests.Timeout:
    logger.warning(f"Time API timeout for {timezone_str}")
except requests.ConnectionError:
    logger.warning(f"Time API connection failed for {timezone_str}")
except (ValueError, KeyError) as e:
    logger.error(f"Time API response parsing error: {e}")
except Exception as e:
    logger.error(f"Unexpected error in time sync: {e}", exc_info=True)
```

**Priority**: P3

---

### 13. No Admin Action Logging

**File**: `pages/1_👤_Admin.py`
**Severity**: 🟡 **MEDIUM**

#### Problem

Admin actions (create/edit/delete checkpoints and guests) are not logged

#### Remediation

Create admin audit log:

```python
@dataclass
class AdminAuditLog:
    id: str
    timestamp: str
    admin_user: str  # Always "admin" for now
    action: str  # "create_checkpoint", "edit_guest", etc.
    entity_type: str  # "checkpoint", "guest", "settings"
    entity_id: str
    changes: Dict[str, Any]  # {"field": {"old": value, "new": value}}

# Log all admin actions
audit_log = AdminAuditLog.create_new(
    admin_user="admin",
    action="create_checkpoint",
    entity_type="checkpoint",
    entity_id=checkpoint.id,
    changes={"checkpoint": checkpoint.to_dict()}
)
storage.add("admin_audit_logs", audit_log.to_dict())
```

**Priority**: P3

---

## Security Best Practices Checklist

### Deployment Checklist

Before deploying to production, ensure:

- [ ] Replace SHA-256 with bcrypt/argon2 password hashing
- [ ] Move SECRET_KEY to environment variable
- [ ] Fix deleted guest authentication bypass
- [ ] Add QR content schema validation
- [ ] Enforce time sync requirement
- [ ] Implement rate limiting on authentication
- [ ] Sanitize user input for XSS prevention
- [ ] Set restrictive file permissions on data files
- [ ] Change default admin password
- [ ] Enable HTTPS (via reverse proxy)
- [ ] Configure secure session cookies
- [ ] Add comprehensive logging
- [ ] Set up monitoring and alerts
- [ ] Perform penetration testing
- [ ] Create incident response plan

### Configuration Hardening

**1. Streamlit Configuration** (`.streamlit/config.toml`):

```toml
[server]
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 5  # MB

[browser]
gatherUsageStats = false
```

**2. Environment Variables** (`.env`):

```env
QR_SECRET_KEY=<64-char-hex-string>
ADMIN_SESSION_TIMEOUT=3600
REQUIRE_HTTPS=true
LOG_LEVEL=INFO
```

**3. File Permissions**:

```bash
chmod 700 data/
chmod 600 data/*.json
chmod 600 .env
```

---

## Incident Response

### If Breach Detected

1. **Immediate Actions**:
   - Take system offline
   - Preserve logs and evidence
   - Notify affected users

2. **Investigation**:
   - Review activity logs
   - Identify attack vector
   - Determine scope of compromise

3. **Remediation**:
   - Patch vulnerabilities
   - Rotate all secrets (SECRET_KEY, passwords)
   - Reset all user credentials
   - Restore from clean backup if needed

4. **Post-Incident**:
   - Conduct root cause analysis
   - Update security controls
   - Document lessons learned

---

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [Streamlit Security](https://docs.streamlit.io/)
- [NIST Password Guidelines](https://pages.nist.gov/800-63-3/sp800-63b.html)

---

## Contact

For security concerns or to report vulnerabilities:

- **Email**: security@yourdomain.com
- **Response Time**: 48 hours
- **PGP Key**: [Link to public key]

**Responsible Disclosure**: We appreciate responsible disclosure of security vulnerabilities. Please allow us reasonable time to address issues before public disclosure.

---

**Document Version**: 1.0
**Last Updated**: 2026-02-05
**Next Review**: 2026-03-05
