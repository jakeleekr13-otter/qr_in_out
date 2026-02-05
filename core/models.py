from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Any, Optional, Literal, Tuple
import uuid
import pytz

@dataclass
class AllowedHours:
    start_time: str  # "HH:MM" format (e.g., "09:00")
    end_time: str    # "HH:MM" format (e.g., "18:00")

    def to_dict(self):
        return asdict(self)

@dataclass
class Checkpoint:
    id: str                             # UUID
    name: str                           # 체크포인트 이름
    location: str                       # 위치 정보
    allowed_hours: AllowedHours         # 허용 시간대
    qr_mode: Literal["static", "dynamic"]  # QR 방식
    admin_password_hash: str            # 관리 비밀번호 (해시)
    allowed_guests: List[str]           # 허용 방문객 ID 리스트
    current_qr_sequence: int = 0        # 현재 QR 순차번호 (dynamic only)
    deleted_at: Optional[str] = None    # Soft delete 타임스탬프 (ISO format string)
    created_at: str = field(default_factory=lambda: datetime.now(pytz.UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(pytz.UTC).isoformat())

    @classmethod
    def create_new(cls, name: str, location: str, allowed_hours: AllowedHours, 
                   qr_mode: Literal["static", "dynamic"], admin_password_hash: str, 
                   allowed_guests: List[str]):
        now = datetime.now(pytz.UTC).isoformat()
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            location=location,
            allowed_hours=allowed_hours,
            qr_mode=qr_mode,
            admin_password_hash=admin_password_hash,
            allowed_guests=allowed_guests,
            created_at=now,
            updated_at=now
        )

    def to_dict(self):
        d = asdict(self)
        d['allowed_hours'] = self.allowed_hours.to_dict()
        return d

@dataclass
class Guest:
    id: str                             # UUID
    name: str                           # 이름 (필수)
    email: str                          # 이메일 (필수)
    phone: Optional[str] = None         # 전화번호 (선택)
    timezone: str = "Asia/Seoul"        # IANA 타임존
    allowed_checkpoints: List[str] = field(default_factory=list)  # 허가 체크포인트 ID
    additional_info: Dict[str, Any] = field(default_factory=dict)  # 추가 정보
    allowed_hours: Optional[AllowedHours] = None  # 방문객별 허용 시간 (선택)
    deleted_at: Optional[str] = None    # Soft delete 타임스탬프 (ISO format string)
    created_at: str = field(default_factory=lambda: datetime.now(pytz.UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(pytz.UTC).isoformat())

    @classmethod
    def create_new(cls, name: str, email: str, phone: Optional[str] = None, 
                   timezone: str = "Asia/Seoul", allowed_checkpoints: List[str] = None, 
                   allowed_hours: Optional[AllowedHours] = None):
        now = datetime.now(pytz.UTC).isoformat()
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            email=email,
            phone=phone,
            timezone=timezone,
            allowed_checkpoints=allowed_checkpoints or [],
            allowed_hours=allowed_hours,
            created_at=now,
            updated_at=now
        )

    def to_dict(self):
        d = asdict(self)
        if self.allowed_hours:
            d['allowed_hours'] = self.allowed_hours.to_dict()
        return d

@dataclass
class ActivityLog:
    id: str                             # UUID
    timestamp: str                      # ISO format string
    checkpoint_id: str                  # 체크포인트 ID
    guest_id: str                       # 방문객 ID
    action: Literal["check_in", "check_out"]  # 활동 타입
    qr_code_used: str                   # 스캔한 QR 코드 내용
    status: Literal["success", "failure"]  # 성공/실패
    failure_reason: Optional[str] = None  # 실패 사유
    metadata: Dict[str, Any] = field(default_factory=dict)  # 추가 메타데이터

    @classmethod
    def create_new(cls, checkpoint_id: str, guest_id: str, action: Literal["check_in", "check_out"], 
                   qr_code_used: str, status: Literal["success", "failure"], 
                   failure_reason: Optional[str] = None, metadata: Dict[str, Any] = None):
        return cls(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(pytz.UTC).isoformat(),
            checkpoint_id=checkpoint_id,
            guest_id=guest_id,
            action=action,
            qr_code_used=qr_code_used,
            status=status,
            failure_reason=failure_reason,
            metadata=metadata or {}
        )

    def to_dict(self):
        return asdict(self)

@dataclass
class AdminSettings:
    id: str = "admin_settings"          # Fixed ID (Singleton)
    admin_timezone: str = "Asia/Seoul"  # 관리자 타임존
    default_guest_timezone: str = "Asia/Seoul"  # 기본 방문객 타임존
    qr_refresh_interval: int = 1800     # QR 갱신 주기 (초)
    require_time_sync: bool = True      # 시간 동기화 필수 여부
    created_at: str = field(default_factory=lambda: datetime.now(pytz.UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(pytz.UTC).isoformat())

    @classmethod
    def create_default(cls):
        now = datetime.now(pytz.UTC).isoformat()
        return cls(created_at=now, updated_at=now)

    def to_dict(self):
        return asdict(self)
