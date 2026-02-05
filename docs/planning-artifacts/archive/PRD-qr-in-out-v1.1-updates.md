---
document_type: "PRD Update Document"
project: "QR In/Out"
version: "1.1"
author: "Jake"
date: "2026-02-05"
status: "Active"
language: "Korean"
purpose: "v1.0에서 v1.1로의 변경사항 및 추가 명세"
parent_doc: "PRD-qr-in-out.md"
---

# PRD v1.1 Updates: QR In/Out

## 변경 이력

### v1.1 (2026-02-05)
- ✅ Time Synchronization (World Time API)
- ✅ Sequence Number System (Expired QR 검증)
- ✅ Soft Delete Mechanism (데이터 이력 보존)
- ✅ Admin Settings (관리자 타임존 설정)
- ✅ Updated Guest Authentication (이름 + 이메일)
- ✅ Required Guest Fields (이메일 필수)

---

## 1. Time Synchronization Module

### 1.1 개요
로컬 시스템 시간 조작을 방지하기 위해 World Time API를 사용하여 시간을 동기화합니다.

### 1.2 구현: Time Service Module

**파일**: `core/time_service.py`

```python
import requests
from datetime import datetime
import pytz
from typing import Optional, Tuple
import streamlit as st

class TimeService:
    """
    Time synchronization service using World Time API

    Features:
    - Fetch current time from World Time API
    - Fallback to local time if API fails
    - Cache results for 60 seconds (performance)
    - Display sync status to user
    """

    API_URL = "http://worldtimeapi.org/api/timezone/{timezone}"
    CACHE_DURATION = 60  # seconds

    @staticmethod
    @st.cache_data(ttl=60)  # Streamlit cache
    def get_current_time(timezone: str = "Asia/Seoul") -> Tuple[datetime, bool]:
        """
        Get current time from World Time API with fallback

        Args:
            timezone: IANA timezone string (e.g., "Asia/Seoul")

        Returns:
            (datetime, is_synced): Current time and whether it's from API
        """
        try:
            response = requests.get(
                TimeService.API_URL.format(timezone=timezone),
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                # Parse ISO datetime from API
                dt_str = data["datetime"]
                # Handle timezone offset
                if dt_str.endswith("Z"):
                    dt_str = dt_str.replace("Z", "+00:00")

                dt = datetime.fromisoformat(dt_str)
                # Convert to requested timezone
                tz = pytz.timezone(timezone)
                dt = dt.astimezone(tz)

                return dt, True  # Successfully synced

        except Exception as e:
            print(f"⚠️ Time API error: {e}")

        # Fallback to local time
        local_time = datetime.now(pytz.timezone(timezone))
        return local_time, False  # Not synced

    @staticmethod
    def show_time_sync_status(is_synced: bool, current_time: datetime):
        """Display time sync status in UI"""
        if is_synced:
            st.success(f"✅ 시간 동기화됨 (World Time API) - {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        else:
            st.warning("⚠️ 시간 동기화 실패 - 로컬 시간 사용 중")
            st.caption("⚠️ 보안 경고: 인터넷 연결을 확인하세요. 로컬 시간이 정확하지 않으면 QR 스캔이 실패할 수 있습니다.")

    @staticmethod
    def format_time_for_display(dt: datetime) -> str:
        """Format datetime for display"""
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")

# Global time service instance
time_service = TimeService()
```

### 1.3 사용법

**Host Page에서**:
```python
# Get current time with sync
checkpoint = get_checkpoint(st.session_state.selected_checkpoint)
current_time, is_synced = time_service.get_current_time(checkpoint.get("timezone", "UTC"))

# Show sync status
time_service.show_time_sync_status(is_synced, current_time)

# Use current_time for QR generation
qr_content, new_sequence = qr_manager.generate_dynamic_qr_content(
    checkpoint_id=checkpoint["id"],
    current_sequence=checkpoint["current_qr_sequence"],
    timestamp=current_time
)
```

**Guest Page에서**:
```python
# Get current time with guest's timezone
guest = st.session_state.current_guest
current_time, is_synced = time_service.get_current_time(guest["timezone"])

# Show sync status
time_service.show_time_sync_status(is_synced, current_time)

# Validate QR code with synced time
validation_result = validate_qr_code(
    qr_data=qr_data,
    guest=guest,
    current_time=current_time,
    is_time_synced=is_synced
)
```

### 1.4 의존성 추가

**requirements.txt**에 추가:
```txt
requests>=2.31.0
```

### 1.5 보안 고려사항

| 시나리오 | 동작 | 보안 수준 |
|---------|------|----------|
| API 성공 | API 시간 사용 | ✅ 높음 |
| API 실패 | 로컬 시간 + 경고 | ⚠️ 중간 (경고 표시) |
| 로컬 시간 조작 | API로 감지 가능 | ✅ 높음 |
| 네트워크 차단 | Fallback (제한적) | ⚠️ 낮음 |

---

## 2. Sequence Number System

### 2.1 개요
Dynamic QR 코드에 순차 번호를 부여하여 이전 QR 코드의 재사용을 방지합니다.

### 2.2 동작 원리

```
초기 상태: Checkpoint.current_qr_sequence = 0

30분 후 첫 갱신:
- QR 생성: sequence = 1
- Checkpoint.current_qr_sequence = 1 (저장)

30분 후 두 번째 갱신:
- QR 생성: sequence = 2
- Checkpoint.current_qr_sequence = 2 (저장)

스캔 시 검증:
- QR.sequence >= Checkpoint.current_qr_sequence → ✅ 허용
- QR.sequence < Checkpoint.current_qr_sequence → ❌ 거부 (만료)
```

### 2.3 Updated Data Model: Checkpoint

```python
@dataclass
class Checkpoint:
    id: str
    name: str
    location: str
    allowed_hours: AllowedHours
    qr_mode: Literal["static", "dynamic"]
    admin_password_hash: str
    allowed_guests: List[str]
    current_qr_sequence: int = 0  # 🆕 NEW: Sequence number for dynamic QR
    deleted_at: Optional[datetime] = None  # 🆕 NEW: Soft delete timestamp
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
```

### 2.4 Updated QR Manager

**파일**: `core/qr_manager.py` (업데이트)

```python
def generate_dynamic_qr_content(
    self,
    checkpoint_id: str,
    current_sequence: int,
    timestamp: Optional[datetime] = None
) -> Tuple[str, int]:
    """
    Generate dynamic QR code content with sequence number

    Args:
        checkpoint_id: Checkpoint ID
        current_sequence: Current sequence number from checkpoint
        timestamp: Current time (from Time API)

    Returns:
        (qr_content_json, new_sequence_number)
    """
    if timestamp is None:
        from core.time_service import time_service
        timestamp, _ = time_service.get_current_time()

    # Calculate expiration (next 30-minute mark)
    expires_at = self._calculate_next_refresh_time(timestamp)

    # Increment sequence number
    new_sequence = current_sequence + 1

    content = {
        "type": "qr_in_out",
        "version": "1.0",
        "checkpoint_id": checkpoint_id,
        "qr_mode": "dynamic",
        "sequence": new_sequence,  # 🆕 NEW
        "issued_at": timestamp.isoformat(),
        "expires_at": expires_at.isoformat(),
        "refresh_interval": self.refresh_interval
    }

    # Add HMAC signature
    signature = self._generate_signature(content)
    content["signature"] = signature

    return json.dumps(content), new_sequence

def validate_dynamic_qr(
    self,
    qr_content: Dict[str, Any],
    checkpoint: Dict[str, Any],
    current_time: datetime,
    is_time_synced: bool
) -> Tuple[bool, Optional[str]]:
    """
    Validate dynamic QR code with sequence number and time check

    Args:
        qr_content: Parsed QR code data
        checkpoint: Checkpoint data
        current_time: Current time (from Time API)
        is_time_synced: Whether time is synced with API

    Returns:
        (is_valid, failure_reason)
    """
    # 1. Verify signature
    if not self.verify_signature(qr_content):
        return False, "QR 코드 서명이 유효하지 않습니다 (위조 가능성)"

    # 2. Check sequence number
    qr_sequence = qr_content.get("sequence", 0)
    current_sequence = checkpoint.get("current_qr_sequence", 0)

    if qr_sequence < current_sequence:
        return False, f"만료된 QR 코드입니다 (이전 버전: {qr_sequence}, 현재: {current_sequence}). 최신 QR 코드를 스캔하세요."

    # 3. Check time-based expiration
    if not is_time_synced:
        # Warning but still allow (with reduced security)
        pass

    expires_at_str = qr_content.get("expires_at")
    if not expires_at_str:
        return False, "QR 코드에 만료 시간이 없습니다"

    expires_at = datetime.fromisoformat(expires_at_str)

    if current_time > expires_at:
        # Check if this is a newer QR (just refreshed)
        if qr_sequence > current_sequence:
            # This is a newer QR, accept it
            return True, None
        else:
            return False, f"만료된 QR 코드입니다 (시간 초과). 갱신된 QR 코드를 스캔하세요."

    return True, None  # Valid!
```

### 2.5 Host Page: QR Refresh Logic

```python
def refresh_qr_code(checkpoint_id: str):
    """
    Refresh QR code and update sequence number
    Called every 30 minutes automatically
    """
    from core.storage import storage
    from core.qr_manager import qr_manager
    from core.time_service import time_service

    # Load checkpoint
    checkpoint = storage.get_by_id("checkpoints", checkpoint_id)

    # Get current time from Time API
    current_time, is_synced = time_service.get_current_time(
        checkpoint.get("timezone", "UTC")
    )

    # Generate new QR with incremented sequence
    qr_content, new_sequence = qr_manager.generate_dynamic_qr_content(
        checkpoint_id=checkpoint_id,
        current_sequence=checkpoint["current_qr_sequence"],
        timestamp=current_time
    )

    # Update checkpoint with new sequence
    storage.update("checkpoints", checkpoint_id, {
        "current_qr_sequence": new_sequence
    })

    return qr_content, new_sequence, is_synced
```

---

## 3. Soft Delete Mechanism

### 3.1 개요
체크포인트와 방문객을 삭제할 때 완전히 제거하지 않고 `_removed` suffix를 추가하여 이력을 보존합니다.

### 3.2 이유
- **Activity Log 참조 보존**: 삭제된 체크포인트/방문객의 과거 기록 유지
- **감사 추적**: 누가 언제 어디에 방문했는지 추적 가능
- **데이터 복구**: 실수로 삭제한 경우 복구 가능

### 3.3 구현

#### Updated Data Models

```python
@dataclass
class Checkpoint:
    # ... (existing fields)
    deleted_at: Optional[datetime] = None  # 🆕 Soft delete timestamp

    def is_deleted(self) -> bool:
        """Check if checkpoint is deleted"""
        return self.deleted_at is not None

    def mark_as_deleted(self):
        """Mark checkpoint as deleted (soft delete)"""
        self.deleted_at = datetime.now()
        self.name = f"{self.name}_removed"
        self.updated_at = datetime.now()

@dataclass
class Guest:
    # ... (existing fields)
    deleted_at: Optional[datetime] = None  # 🆕 Soft delete timestamp

    def is_deleted(self) -> bool:
        """Check if guest is deleted"""
        return self.deleted_at is not None

    def mark_as_deleted(self):
        """Mark guest as deleted (soft delete)"""
        self.deleted_at = datetime.now()
        self.name = f"{self.name}_removed"
        self.updated_at = datetime.now()
```

#### Storage Layer: Soft Delete Methods

**파일**: `core/storage.py` (추가)

```python
def soft_delete_checkpoint(self, checkpoint_id: str):
    """Soft delete a checkpoint by adding _removed suffix"""
    checkpoint = self.get_by_id("checkpoints", checkpoint_id)

    if not checkpoint:
        raise ValueError(f"Checkpoint {checkpoint_id} not found")

    # Add _removed suffix to name
    if not checkpoint["name"].endswith("_removed"):
        checkpoint["name"] = f"{checkpoint['name']}_removed"

    # Set deleted_at timestamp
    checkpoint["deleted_at"] = datetime.now().isoformat()
    checkpoint["updated_at"] = datetime.now().isoformat()

    # Update in storage
    data = self.load("checkpoints")
    for i, item in enumerate(data):
        if item["id"] == checkpoint_id:
            data[i] = checkpoint
            break

    self.save("checkpoints", data)

    print(f"✅ Checkpoint {checkpoint_id} soft-deleted")

def soft_delete_guest(self, guest_id: str):
    """Soft delete a guest by adding _removed suffix"""
    guest = self.get_by_id("guests", guest_id)

    if not guest:
        raise ValueError(f"Guest {guest_id} not found")

    # Add _removed suffix to name
    if not guest["name"].endswith("_removed"):
        guest["name"] = f"{guest['name']}_removed"

    # Set deleted_at timestamp
    guest["deleted_at"] = datetime.now().isoformat()
    guest["updated_at"] = datetime.now().isoformat()

    # Update in storage
    data = self.load("guests")
    for i, item in enumerate(data):
        if item["id"] == guest_id:
            data[i] = guest
            break

    self.save("guests", data)

    print(f"✅ Guest {guest_id} soft-deleted")

def get_active_checkpoints(self) -> List[Dict[str, Any]]:
    """Get only active (non-deleted) checkpoints"""
    all_checkpoints = self.load("checkpoints")
    return [c for c in all_checkpoints if not c.get("deleted_at")]

def get_active_guests(self) -> List[Dict[str, Any]]:
    """Get only active (non-deleted) guests"""
    all_guests = self.load("guests")
    return [g for g in all_guests if not g.get("deleted_at")]
```

#### Admin Page: Soft Delete UI

```python
# In Admin Page - Checkpoint deletion
with st.expander("⚠️ 위험 구역: 체크포인트 삭제"):
    st.warning("체크포인트를 삭제하면 이름에 '_removed'가 추가되고 더 이상 사용할 수 없습니다. 과거 기록은 보존됩니다.")

    if st.button("체크포인트 삭제", type="secondary"):
        if st.session_state.get("confirm_delete_checkpoint"):
            storage.soft_delete_checkpoint(selected_checkpoint)
            st.success("체크포인트가 삭제되었습니다 (이름에 _removed 추가)")
            st.session_state.confirm_delete_checkpoint = False
            st.rerun()
        else:
            st.session_state.confirm_delete_checkpoint = True
            st.error("⚠️ 다시 한 번 클릭하여 삭제를 확인하세요.")

# In Admin Page - Guest deletion
with st.expander("⚠️ 위험 구역: 방문객 삭제"):
    st.warning("방문객을 삭제하면 이름에 '_removed'가 추가되고 더 이상 체크인할 수 없습니다. 과거 기록은 보존됩니다.")

    if st.button("방문객 삭제", type="secondary"):
        if st.session_state.get("confirm_delete_guest"):
            storage.soft_delete_guest(selected_guest)
            st.success("방문객이 삭제되었습니다 (이름에 _removed 추가)")
            st.session_state.confirm_delete_guest = False
            st.rerun()
        else:
            st.session_state.confirm_delete_guest = True
            st.error("⚠️ 다시 한 번 클릭하여 삭제를 확인하세요.")
```

### 3.4 Activity Log에서 삭제된 항목 표시

```python
# When displaying activity logs
def display_activity_log(log: Dict[str, Any]):
    checkpoint = storage.get_by_id("checkpoints", log["checkpoint_id"])
    guest = storage.get_by_id("guests", log["guest_id"])

    checkpoint_name = checkpoint["name"] if checkpoint else "알 수 없음"
    guest_name = guest["name"] if guest else "알 수 없음"

    # Highlight deleted items
    if checkpoint and checkpoint.get("deleted_at"):
        st.caption(f"📍 {checkpoint_name} (삭제됨)")
    else:
        st.write(f"📍 {checkpoint_name}")

    if guest and guest.get("deleted_at"):
        st.caption(f"👤 {guest_name} (삭제됨)")
    else:
        st.write(f"👤 {guest_name}")
```

---

## 4. Admin Settings (시스템 설정)

### 4.1 개요
관리자가 시스템 전역 설정을 관리할 수 있도록 합니다.

### 4.2 Data Model: AdminSettings

```python
@dataclass
class AdminSettings:
    """System-wide admin settings"""
    id: str = "admin_settings"  # Singleton
    admin_timezone: str = "Asia/Seoul"  # 관리자 타임존
    default_guest_timezone: str = "Asia/Seoul"  # 기본 방문객 타임존
    qr_refresh_interval: int = 1800  # QR 갱신 주기 (초)
    require_time_sync: bool = True  # 시간 동기화 필수 여부
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AdminSettings":
        data = data.copy()
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)

    @classmethod
    def load_or_create_default(cls) -> "AdminSettings":
        """Load settings from storage or create default"""
        from core.storage import storage

        settings_data = storage.get_by_id("admin_settings", "admin_settings")

        if settings_data:
            return cls.from_dict(settings_data)
        else:
            # Create default settings
            default_settings = cls()
            storage.add("admin_settings", default_settings.to_dict())
            return default_settings
```

### 4.3 Admin Page: Settings UI

```python
st.title("⚙️ 시스템 설정")

# Load current settings
settings = AdminSettings.load_or_create_default()

with st.form("admin_settings_form"):
    st.subheader("관리자 설정")

    admin_timezone = st.selectbox(
        "관리자 타임존",
        options=pytz.all_timezones,
        index=pytz.all_timezones.index(settings.admin_timezone),
        help="관리자 페이지에서 사용할 기본 타임존"
    )

    default_guest_timezone = st.selectbox(
        "기본 방문객 타임존",
        options=pytz.all_timezones,
        index=pytz.all_timezones.index(settings.default_guest_timezone),
        help="방문객 등록 시 기본 타임존"
    )

    st.subheader("QR 코드 설정")

    qr_refresh_interval = st.number_input(
        "QR 갱신 주기 (분)",
        min_value=5,
        max_value=120,
        value=settings.qr_refresh_interval // 60,
        step=5,
        help="Dynamic QR 코드 갱신 주기"
    )

    require_time_sync = st.checkbox(
        "시간 동기화 필수",
        value=settings.require_time_sync,
        help="Time API 동기화 실패 시 QR 스캔 차단"
    )

    submitted = st.form_submit_button("설정 저장")

    if submitted:
        settings.admin_timezone = admin_timezone
        settings.default_guest_timezone = default_guest_timezone
        settings.qr_refresh_interval = qr_refresh_interval * 60
        settings.require_time_sync = require_time_sync
        settings.updated_at = datetime.now()

        storage.update("admin_settings", "admin_settings", settings.to_dict())
        st.success("✅ 설정이 저장되었습니다!")
        st.rerun()
```

### 4.4 첫 실행 시 설정 마법사

```python
# In app.py (Main entry point)
def show_initial_setup_wizard():
    """Show setup wizard on first run"""
    st.title("🎉 QR In/Out 초기 설정")
    st.write("환영합니다! 시스템을 처음 사용하시는군요. 기본 설정을 해주세요.")

    with st.form("initial_setup"):
        st.subheader("관리자 정보")

        admin_timezone = st.selectbox(
            "타임존 선택",
            options=pytz.all_timezones,
            index=pytz.all_timezones.index("Asia/Seoul"),
            help="귀하의 현재 위치 타임존을 선택하세요"
        )

        submitted = st.form_submit_button("설정 완료")

        if submitted:
            # Create admin settings
            settings = AdminSettings()
            settings.admin_timezone = admin_timezone
            settings.default_guest_timezone = admin_timezone

            from core.storage import storage
            storage.add("admin_settings", settings.to_dict())

            st.success("✅ 초기 설정이 완료되었습니다!")
            time.sleep(2)
            st.rerun()

# Check if initial setup is needed
if not storage.get_by_id("admin_settings", "admin_settings"):
    show_initial_setup_wizard()
    st.stop()
```

---

## 5. Updated Guest Authentication

### 5.1 개요
방문객 인증 시 **이름 + 이메일**을 필수로 입력하도록 변경합니다.

### 5.2 Updated Data Model: Guest

```python
@dataclass
class Guest:
    id: str
    name: str
    email: str  # 🆕 REQUIRED: Email is now mandatory
    phone: Optional[str] = None  # 🆕 OPTIONAL: Phone number
    timezone: str = "Asia/Seoul"
    allowed_checkpoints: List[str] = field(default_factory=list)
    additional_info: Dict[str, Any] = field(default_factory=dict)
    allowed_hours: Optional[AllowedHours] = None
    deleted_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def create_new(cls, name: str, email: str, timezone: str,
                   allowed_checkpoints: List[str], phone: Optional[str] = None,
                   additional_info: Optional[Dict[str, Any]] = None,
                   allowed_hours: Optional[AllowedHours] = None) -> "Guest":
        """Create a new guest with required fields"""
        if not name:
            raise ValueError("이름은 필수입니다")
        if not email:
            raise ValueError("이메일은 필수입니다")

        return cls(
            id=str(uuid.uuid4()),
            name=name,
            email=email,
            phone=phone,
            timezone=timezone,
            allowed_checkpoints=allowed_checkpoints,
            additional_info=additional_info or {},
            allowed_hours=allowed_hours
        )
```

### 5.3 Admin Page: Guest Registration (Updated)

```python
st.title("방문객 관리")
st.subheader("새 방문객 등록")

with st.form("create_guest"):
    st.write("**필수 정보**")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("이름 *", placeholder="홍길동")
    with col2:
        email = st.text_input("이메일 *", placeholder="hong@example.com")

    st.write("**선택 정보**")
    phone = st.text_input("전화번호", placeholder="010-1234-5678")

    st.write("**타임존 및 권한 설정**")

    # Load default timezone from admin settings
    settings = AdminSettings.load_or_create_default()

    timezone = st.selectbox(
        "타임존",
        options=pytz.all_timezones,
        index=pytz.all_timezones.index(settings.default_guest_timezone)
    )

    # Optional: Allowed hours for this guest
    use_custom_hours = st.checkbox("방문객별 허용 시간 설정")
    guest_allowed_hours = None
    if use_custom_hours:
        col1, col2 = st.columns(2)
        with col1:
            guest_start_time = st.time_input("허용 시작 시간")
        with col2:
            guest_end_time = st.time_input("허용 종료 시간")

        guest_allowed_hours = AllowedHours(
            start_time=guest_start_time.strftime("%H:%M"),
            end_time=guest_end_time.strftime("%H:%M")
        )

    # Multi-select for allowed checkpoints
    checkpoints = storage.get_active_checkpoints()
    allowed_checkpoints = st.multiselect(
        "허가 체크포인트 (0개 이상 선택)",
        options=[c["id"] for c in checkpoints],
        format_func=lambda x: get_checkpoint_name(x),
        help="0개를 선택하면 어떤 체크포인트에도 접근할 수 없습니다"
    )

    submitted = st.form_submit_button("등록")

    if submitted:
        # Validation
        if not name:
            st.error("❌ 이름은 필수입니다")
        elif not email:
            st.error("❌ 이메일은 필수입니다")
        elif not is_valid_email(email):
            st.error("❌ 유효한 이메일 주소를 입력하세요")
        else:
            try:
                guest = Guest.create_new(
                    name=name,
                    email=email,
                    phone=phone if phone else None,
                    timezone=timezone,
                    allowed_checkpoints=allowed_checkpoints,
                    allowed_hours=guest_allowed_hours
                )

                storage.add("guests", guest.to_dict())
                st.success(f"✅ 방문객 '{name}'이(가) 등록되었습니다!")

                # Show warning if no checkpoints selected
                if len(allowed_checkpoints) == 0:
                    st.warning("⚠️ 허가된 체크포인트가 없어 이 방문객은 어떤 체크포인트에도 접근할 수 없습니다.")

            except ValueError as e:
                st.error(f"❌ {str(e)}")

def is_valid_email(email: str) -> bool:
    """Simple email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
```

### 5.4 Guest Page: Authentication (Updated)

```python
st.title("게스트 페이지 - 체크인/체크아웃")

# Session state for guest authentication
if "guest_authenticated" not in st.session_state:
    st.session_state.guest_authenticated = False
    st.session_state.current_guest = None

if not st.session_state.guest_authenticated:
    st.subheader("방문자 정보 입력")
    st.info("관리자에게 등록된 **이름**과 **이메일**을 정확히 입력하세요.")

    with st.form("guest_auth_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("이름 *", placeholder="홍길동")
        with col2:
            email = st.text_input("이메일 *", placeholder="hong@example.com")

        submitted = st.form_submit_button("확인")

        if submitted:
            if not name or not email:
                st.error("❌ 이름과 이메일을 모두 입력하세요")
            else:
                # Verify guest identity with name + email
                guest = verify_guest_by_name_and_email(name, email)

                if guest:
                    # Check if guest is deleted
                    if guest.get("deleted_at"):
                        st.error("❌ 삭제된 방문객입니다. 관리자에게 문의하세요.")
                    else:
                        st.session_state.guest_authenticated = True
                        st.session_state.current_guest = guest
                        st.success(f"✅ 환영합니다, {guest['name']}님!")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error("❌ 등록되지 않은 방문객입니다. 이름과 이메일을 확인하거나 관리자에게 문의하세요.")

def verify_guest_by_name_and_email(name: str, email: str) -> Optional[Dict[str, Any]]:
    """Verify guest identity by name and email (case-insensitive)"""
    from core.storage import storage

    guests = storage.load("guests")

    name_lower = name.lower().strip()
    email_lower = email.lower().strip()

    for guest in guests:
        if (guest["name"].lower().strip() == name_lower and
            guest["email"].lower().strip() == email_lower):
            return guest

    return None
```

---

## 6. Summary of Changes

### 6.1 New Modules

| 모듈 | 파일 | 설명 |
|-----|------|------|
| Time Service | `core/time_service.py` | World Time API 통합 |
| Admin Settings | `core/models.py` (AdminSettings) | 시스템 전역 설정 |

### 6.2 Updated Modules

| 모듈 | 변경사항 |
|-----|---------|
| `core/models.py` | Checkpoint, Guest에 deleted_at, current_qr_sequence 추가 |
| `core/storage.py` | soft_delete_*, get_active_* 메서드 추가 |
| `core/qr_manager.py` | Sequence number 로직 추가, Time API 통합 |
| `pages/1_Admin.py` | 설정 페이지, Soft delete UI, Email 필수 |
| `pages/2_Host.py` | Time sync 표시, Sequence number 저장 |
| `pages/3_Guest.py` | 이름 + 이메일 인증 |

### 6.3 New Dependencies

```txt
requests>=2.31.0  # For World Time API
```

### 6.4 Security Improvements

| 개선사항 | 설명 |
|---------|------|
| ✅ Time Sync | World Time API로 로컬 시간 조작 방지 |
| ✅ Sequence Number | Expired QR 재사용 방지 |
| ✅ HMAC Signature | QR 위조 방지 (기존) |
| ✅ Soft Delete | 데이터 이력 보존 |
| ✅ Email Auth | 이메일로 방문객 인증 강화 |

---

## 7. Implementation Checklist

### Phase 1: Core Security (우선순위 높음)
- [ ] Time Service Module 구현
- [ ] Sequence Number System 구현
- [ ] QR Manager 업데이트 (Sequence + Time)
- [ ] Host Page: QR 갱신 로직 업데이트
- [ ] Guest Page: QR 검증 로직 업데이트

### Phase 2: Data Management
- [ ] Soft Delete 메커니즘 구현
- [ ] Storage Layer 업데이트
- [ ] Admin Page: Soft Delete UI
- [ ] Activity Log: 삭제된 항목 표시

### Phase 3: Admin Features
- [ ] AdminSettings 모델 구현
- [ ] Admin Page: 설정 UI
- [ ] 첫 실행 설정 마법사

### Phase 4: Guest Features
- [ ] Guest 모델 업데이트 (email 필수)
- [ ] Admin Page: Guest 등록 UI 업데이트
- [ ] Guest Page: 이름 + 이메일 인증

### Phase 5: Testing
- [ ] Time Service 테스트
- [ ] Sequence Number 테스트
- [ ] Soft Delete 테스트
- [ ] Guest Authentication 테스트
- [ ] End-to-end 통합 테스트

---

## 8. Testing Scenarios

### 8.1 Time Synchronization Tests

| 시나리오 | 기대 결과 |
|---------|----------|
| Time API 성공 | ✅ API 시간 사용, 성공 메시지 |
| Time API 실패 | ⚠️ 로컬 시간 사용, 경고 메시지 |
| 로컬 시간 조작 | ✅ API로 감지, QR 검증 실패 |
| 네트워크 차단 | ⚠️ Fallback, 경고 표시 |

### 8.2 Sequence Number Tests

| 시나리오 | 기대 결과 |
|---------|----------|
| 최신 QR 스캔 | ✅ 성공 |
| 이전 QR 스캔 (seq=1, current=2) | ❌ "만료된 QR 코드" |
| 미래 QR 스캔 (seq=3, current=2) | ✅ 성공 (새로 갱신됨) |
| Sequence 조작 | ❌ HMAC 서명 검증 실패 |

### 8.3 Soft Delete Tests

| 시나리오 | 기대 결과 |
|---------|----------|
| 체크포인트 삭제 | ✅ "_removed" suffix 추가 |
| 삭제된 체크포인트 조회 | ✅ 과거 로그에 표시 |
| 삭제된 체크포인트에 QR 스캔 | ❌ "삭제된 체크포인트" |
| 방문객 삭제 | ✅ "_removed" suffix 추가 |
| 삭제된 방문객 인증 | ❌ "삭제된 방문객" |

### 8.4 Guest Authentication Tests

| 시나리오 | 기대 결과 |
|---------|----------|
| 올바른 이름 + 이메일 | ✅ 인증 성공 |
| 잘못된 이름 | ❌ "등록되지 않은 방문객" |
| 잘못된 이메일 | ❌ "등록되지 않은 방문객" |
| 삭제된 방문객 | ❌ "삭제된 방문객" |
| 허가 체크포인트 0개 | ⚠️ 인증 성공, QR 스캔 시 차단 |

---

## Document Metadata

- **문서 타입**: PRD Update Document
- **프로젝트**: QR In/Out
- **버전**: 1.1
- **작성자**: Jake
- **작성일**: 2026-02-05
- **언어**: 한국어
- **용도**: v1.0에서 v1.1로의 변경사항 상세 명세
- **상태**: Active
- **부모 문서**: PRD-qr-in-out.md

---

**End of PRD v1.1 Updates**
