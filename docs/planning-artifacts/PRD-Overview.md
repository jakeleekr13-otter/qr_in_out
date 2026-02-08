---
document_type: "Product Requirements Document - Overview"
project: "QR In/Out"
version: "1.2"
author: "Jake"
date: "2026-02-08"
status: "Active"
language: "Korean"
purpose: "시스템 개요, 아키텍처, 공통 모듈 명세"
related_docs:
  - "PRD-Admin.md"
  - "PRD-Host.md"
  - "PRD-Guest.md"
  - "product-brief-qr-in-out.md"
---

# PRD Overview: QR In/Out

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Product Overview](#product-overview)
3. [System Architecture](#system-architecture)
4. [Data Models](#data-models)
5. [Core Modules](#core-modules)
6. [Security](#security)
7. [Performance](#performance)
8. [Testing](#testing)
9. [Deployment](#deployment)

---

## Executive Summary

QR In/Out은 **Streamlit 기반의 QR 코드 체크포인트 관리 시스템**입니다. 로컬 파일 저장소를 사용하여 호스팅이나 데이터베이스 없이 동작하며, Python 환경에서 간단히 실행 가능합니다.

### 핵심 특징

| 카테고리 | 내용 |
|---------|------|
| **프레임워크** | Streamlit (Python 기반) |
| **배포 방식** | 로컬 실행 (`streamlit run app.py`) |
| **데이터 저장** | JSON 파일 또는 SQLite (로컬) |
| **QR 스캔** | 실시간 카메라 스캔 (streamlit-camera-input) |
| **Multi-page** | 3개 독립 페이지 (Admin/Host/Guest) |
| **시간 동기화** | World Time API (로컬 시간 조작 방지) |
| **보안** | Sequence Number + HMAC Signature (Static/Dynamic 공통) |
| **데이터 보존** | Soft Delete (삭제 이력 보존) |

### 문서 구조

```
PRD-Overview.md    (현재 문서) ← 아키텍처, 공통 모듈
├── PRD-Admin.md   ← 관리자 페이지 상세 명세
├── PRD-Host.md    ← 호스트 페이지 상세 명세
└── PRD-Guest.md   ← 게스트 페이지 상세 명세
```

---

## 1. Product Overview

### 1.1 Product Vision
체크포인트 출입 관리를 위한 간단하고 효율적인 QR 코드 시스템을 제공합니다.

### 1.2 Target Users

| 사용자 | 역할 | 주요 활동 |
|-------|------|----------|
| **관리자** | 시스템 관리 | 체크포인트/방문객 생성, 로그 조회 |
| **호스트** | QR 디스플레이 | QR 코드 표시, 자동 갱신 |
| **방문객** | 체크인/아웃 | QR 스캔, 기록 조회 |

### 1.3 Key Goals
- ✅ 로컬 환경에서 독립적으로 실행 가능
- ✅ 외부 의존성 최소화 (호스팅, DB 불필요)
- ✅ 빠른 프로토타이핑 및 테스트
- ✅ 시간 조작 방지 (World Time API)
- ✅ 데이터 이력 보존 (Soft Delete)

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────┐
│         Streamlit Web Server            │
│         (localhost:8501)                │
└─────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
   ┌────▼───┐  ┌───▼────┐  ┌──▼─────┐
   │ Admin  │  │  Host  │  │ Guest  │
   │  Page  │  │  Page  │  │  Page  │
   └────┬───┘  └───┬────┘  └──┬─────┘
        │          │           │
        └──────────┼───────────┘
                   │
         ┌─────────▼──────────┐
         │   Core Modules     │
         │ ┌────────────────┐ │
         │ │ Storage Layer  │ │
         │ │ QR Manager     │ │
         │ │ Time Service   │ │
         │ │ Auth Manager   │ │
         │ │ Time Validator │ │
         │ └────────────────┘ │
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────┐
         │   Data Storage     │
         │ ┌────────────────┐ │
         │ │ checkpoints    │ │
         │ │ guests         │ │
         │ │ activity_logs  │ │
         │ │ admin_settings │ │
         │ └────────────────┘ │
         └────────────────────┘
                   │
         ┌─────────▼──────────┐
         │  External Services │
         │ ┌────────────────┐ │
         │ │ World Time API │ │
         │ └────────────────┘ │
         └────────────────────┘
```

### 2.2 Technology Stack

#### Core Framework
```
Python 3.10+
Streamlit 1.30+
```

#### Required Libraries
```python
# Web Framework
streamlit>=1.30.0
streamlit-camera-input>=0.1.0

# QR Code
qrcode[pil]>=7.4.0
pyzbar>=0.1.9
pillow>=10.0.0

# Utilities
pytz>=2023.3
pandas>=2.0.0
requests>=2.31.0  # For World Time API

# Optional
opencv-python>=4.8.0  # For advanced image processing
```

### 2.3 Directory Structure

```
qr_in_out/
├── app.py                          # Main entry point
├── requirements.txt                # Python dependencies
├── README.md                       # Public documentation
├── .streamlit/
│   └── config.toml                # Streamlit configuration
├── config/
│   ├── __init__.py
│   └── settings.py                # Application settings
├── core/
│   ├── __init__.py
│   ├── models.py                  # Data models
│   ├── storage.py                 # Storage layer (JSON/SQLite)
│   ├── qr_manager.py              # QR generation & validation
│   ├── time_service.py            # Time synchronization (World Time API)
│   ├── time_validator.py          # Time-based access control
│   ├── auth.py                    # Password management
│   └── connection_health.py       # Connection health monitoring
├── pages/
│   ├── 1_👤_Admin.py              # Admin page
│   ├── 2_🖥️_Host.py               # Host page
│   └── 3_👋_Guest.py              # Guest page
├── utils/
│   ├── __init__.py
│   └── helpers.py                 # Helper functions
├── assets/                        # Static assets
│   └── sounds/
│       ├── success.mp3           # Success sound (check-in/out)
│       └── error.mp3             # Error sound (scan failure)
├── data/                          # Data directory (gitignored)
│   ├── checkpoints.json
│   ├── guests.json
│   ├── activity_logs.json
│   └── admin_settings.json
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_storage.py
│   ├── test_qr_manager.py
│   ├── test_time_service.py
│   └── test_integration.py
└── docs/
    └── planning-artifacts/
        ├── PRD-Overview.md (this file)
        ├── PRD-Admin.md
        ├── PRD-Host.md
        └── PRD-Guest.md
```

---

## 3. Data Models

### 3.1 Checkpoint

**설명**: QR 코드가 설치된 체크포인트

```python
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
    wifi_ssid: Optional[str] = None     # WiFi 네트워크 이름 (Host 화면 표시용)
    wifi_password: Optional[str] = None # WiFi 비밀번호 (Host 화면 표시용)
    deleted_at: Optional[datetime] = None  # Soft delete 타임스탬프
    created_at: datetime
    updated_at: datetime
```

**JSON Example**:
```json
{
  "id": "cp-123e4567-e89b-12d3-a456-426614174000",
  "name": "본관 입구",
  "location": "서울시 강남구 테헤란로 123",
  "allowed_hours": {
    "start_time": "09:00",
    "end_time": "18:00"
  },
  "qr_mode": "dynamic",
  "admin_password_hash": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
  "allowed_guests": ["guest-uuid-1", "guest-uuid-2"],
  "current_qr_sequence": 42,
  "wifi_ssid": "Guest_Network",
  "wifi_password": "welcome2024",
  "deleted_at": null,
  "created_at": "2026-02-05T09:00:00+09:00",
  "updated_at": "2026-02-05T10:30:00+09:00"
}
```

### 3.2 Guest

**설명**: 등록된 방문객

```python
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
    deleted_at: Optional[datetime] = None  # Soft delete 타임스탬프
    created_at: datetime
    updated_at: datetime
```

**JSON Example**:
```json
{
  "id": "guest-456e7890-a12b-34c5-d678-901234567890",
  "name": "홍길동",
  "email": "hong@example.com",
  "phone": "010-1234-5678",
  "timezone": "Asia/Seoul",
  "allowed_checkpoints": ["cp-123e4567-e89b-12d3-a456-426614174000"],
  "additional_info": {
    "company": "ABC Corp",
    "department": "Engineering"
  },
  "allowed_hours": {
    "start_time": "08:00",
    "end_time": "20:00"
  },
  "deleted_at": null,
  "created_at": "2026-02-05T08:00:00+09:00",
  "updated_at": "2026-02-05T08:00:00+09:00"
}
```

### 3.3 AllowedHours

**설명**: 시간대 설정

```python
@dataclass
class AllowedHours:
    start_time: str  # "HH:MM" format (e.g., "09:00")
    end_time: str    # "HH:MM" format (e.g., "18:00")
```

**참고**: `start_time`이 `end_time`보다 크면 overnight hours (예: 22:00 - 06:00)

### 3.4 ActivityLog

**설명**: 체크인/체크아웃 활동 기록

```python
@dataclass
class ActivityLog:
    id: str                             # UUID
    timestamp: datetime                 # 활동 시간
    checkpoint_id: str                  # 체크포인트 ID
    guest_id: str                       # 방문객 ID
    action: Literal["check_in", "check_out"]  # 활동 타입
    qr_code_used: str                   # 스캔한 QR 코드 내용
    status: Literal["success", "failure"]  # 성공/실패
    failure_reason: Optional[str] = None  # 실패 사유
    metadata: Dict[str, Any] = field(default_factory=dict)  # 추가 메타데이터
```

**JSON Example**:
```json
{
  "id": "log-789a0123-b45c-67d8-e901-234567890abc",
  "timestamp": "2026-02-05T10:30:45+09:00",
  "checkpoint_id": "cp-123e4567-e89b-12d3-a456-426614174000",
  "guest_id": "guest-456e7890-a12b-34c5-d678-901234567890",
  "action": "check_in",
  "qr_code_used": "{\"type\":\"qr_in_out\",\"checkpoint_id\":\"cp-123...\"}",
  "status": "success",
  "failure_reason": null,
  "metadata": {
    "time_synced": true,
    "qr_sequence": 42
  }
}
```

### 3.5 AdminSettings

**설명**: 시스템 전역 설정 (Singleton)

```python
@dataclass
class AdminSettings:
    id: str = "admin_settings"          # Fixed ID (Singleton)
    admin_timezone: str = "Asia/Seoul"  # 관리자 타임존
    default_guest_timezone: str = "Asia/Seoul"  # 기본 방문객 타임존
    qr_refresh_interval: int = 1800     # QR 갱신 주기 (초)
    require_time_sync: bool = True      # 시간 동기화 필수 여부
    created_at: datetime
    updated_at: datetime
```

---

## 4. Core Modules

### 4.1 Storage Layer (`core/storage.py`)

**책임**: 데이터 CRUD 및 영속성 관리

**주요 메서드**:
```python
class JSONStorage:
    def load(entity_type: str) -> List[Dict[str, Any]]
    def save(entity_type: str, data: List[Dict[str, Any]])
    def add(entity_type: str, entity: Dict[str, Any])
    def update(entity_type: str, entity_id: str, updates: Dict[str, Any])
    def delete(entity_type: str, entity_id: str)
    def get_by_id(entity_type: str, entity_id: str) -> Optional[Dict]

    # Soft Delete
    def soft_delete_checkpoint(checkpoint_id: str)
    def soft_delete_guest(guest_id: str)
    def get_active_checkpoints() -> List[Dict]
    def get_active_guests() -> List[Dict]
```

**특징**:
- Thread-safe (file locking)
- UTF-8 encoding
- ISO datetime serialization

### 4.2 QR Manager (`core/qr_manager.py`)

**책임**: QR 코드 생성, 검증, 암호화

**주요 메서드**:
```python
class QRManager:
    def generate_static_qr_content(checkpoint_id: str) -> str
    def generate_dynamic_qr_content(checkpoint_id: str, current_sequence: int,
                                     timestamp: datetime) -> Tuple[str, int]
    def generate_qr_image(content: str, size: int) -> Image
    def qr_image_to_bytes(img: Image) -> bytes

    def parse_qr_content(qr_string: str) -> Optional[Dict]
    def verify_signature(qr_content: Dict) -> bool
    def validate_dynamic_qr(qr_content: Dict, checkpoint: Dict,
                            current_time: datetime, is_time_synced: bool) -> Tuple[bool, Optional[str]]
    def is_qr_expired(qr_content: Dict) -> bool
```

**QR Content Format**:

Static QR:
```json
{
  "type": "qr_in_out",
  "version": "1.0",
  "checkpoint_id": "cp-uuid",
  "qr_mode": "static",
  "sequence": 42,
  "created_at": "2026-02-05T10:00:00Z",
  "signature": "hmac-sha256-signature"
}
```

Dynamic QR:
```json
{
  "type": "qr_in_out",
  "version": "1.0",
  "checkpoint_id": "cp-uuid",
  "qr_mode": "dynamic",
  "sequence": 42,
  "issued_at": "2026-02-05T10:00:00Z",
  "expires_at": "2026-02-05T10:30:00Z",
  "refresh_interval": 1800,
  "signature": "hmac-sha256-signature"
}
```

### 4.3 Time Service (`core/time_service.py`)

**책임**: 시간 동기화 (World Time API)

**주요 메서드**:
```python
class TimeService:
    @staticmethod
    @st.cache_data(ttl=60)
    def get_current_time(timezone: str) -> Tuple[datetime, bool]

    @staticmethod
    def show_time_sync_status(is_synced: bool, current_time: datetime)

    @staticmethod
    def format_time_for_display(dt: datetime) -> str
```

**특징**:
- World Time API 사용 (worldtimeapi.org)
- 60초 캐싱 (성능)
- Fallback to local time
- UI에 동기화 상태 표시

**API Endpoint**:
```
GET http://worldtimeapi.org/api/timezone/{timezone}
```

**Response Example**:
```json
{
  "datetime": "2026-02-05T10:30:45.123456+09:00",
  "timezone": "Asia/Seoul",
  "utc_offset": "+09:00"
}
```

### 4.4 Time Validator (`core/time_validator.py`)

**책임**: 시간 기반 접근 제어 검증

**주요 메서드**:
```python
class TimeValidator:
    @staticmethod
    def parse_time_string(time_str: str) -> time

    @staticmethod
    def is_within_allowed_hours(current_time: datetime,
                                  allowed_hours: Dict) -> bool

    @staticmethod
    def check_checkpoint_access(checkpoint: Dict, guest: Dict) -> Tuple[bool, str]

    @staticmethod
    def format_countdown(seconds: float) -> str
```

**검증 로직**:
```python
# 이중 시간 제어
접근 허용 = (
    체크포인트 허용 시간 내
    AND
    (방문객 허용 시간 내 OR 방문객 허용 시간 미설정)
)
```

### 4.5 Auth Manager (`core/auth.py`)

**책임**: 비밀번호 해싱 및 검증

**주요 메서드**:
```python
class AuthManager:
    @staticmethod
    def hash_password(password: str) -> str

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool

    @staticmethod
    def generate_guest_token() -> str
```

**해싱 알고리즘**:
- SHA-256 (간단한 구현)
- 프로덕션 권장: bcrypt 또는 argon2

### 4.6 Connection Health Check (`core/connection_health.py`)

**책임**: 서버 및 외부 서비스 연결 상태 모니터링

**주요 메서드**:
```python
@dataclass
class ConnectionStatus:
    server_connected: bool          # Streamlit 서버 연결 상태
    time_api_connected: bool        # World Time API 연결 상태
    last_check: datetime            # 마지막 확인 시간
    latency_ms: Optional[int]       # 응답 시간 (ms)
    error_message: Optional[str]    # 에러 메시지 (있을 경우)

class ConnectionHealthCheck:
    @staticmethod
    @st.cache_data(ttl=30)
    def check_time_api() -> Tuple[bool, Optional[int], Optional[str]]
        """
        World Time API 연결 확인
        Returns: (connected, latency_ms, error_message)
        """

    @staticmethod
    def get_connection_status() -> ConnectionStatus
        """
        전체 연결 상태 반환
        """

    @staticmethod
    def render_status_badge(status: ConnectionStatus)
        """
        Streamlit UI에 연결 상태 배지 렌더링
        - ✅ 정상: 초록색
        - ⚠️ 부분 오류: 노란색
        - ❌ 연결 끊김: 빨간색
        """
```

**UI 표시 형식**:
```
# 정상
📶 ✅ 연결 정상 (45ms)

# Time API 오류
📶 ⚠️ 시간 동기화 불가 - 로컬 시간 사용 중

# 서버 연결 끊김
📶 ❌ 서버 연결 끊김 - 네트워크를 확인하세요
```

**특징**:
- 30초 캐싱 (과도한 API 호출 방지)
- Graceful degradation (Time API 실패 시 로컬 시간 사용)
- 사용자 친화적 에러 메시지

---

## 5. Security

### 5.1 Security Architecture

```
┌────────────────────────────────────────────┐
│          Security Layers                   │
├────────────────────────────────────────────┤
│ 1. Time Synchronization (World Time API)  │
│    - Prevents local time manipulation      │
│    - Falls back to local time with warning │
├────────────────────────────────────────────┤
│ 2. Sequence Number System                  │
│    - Prevents QR code reuse                │
│    - Incremental counter per checkpoint    │
├────────────────────────────────────────────┤
│ 3. HMAC Signature (SHA-256)                │
│    - Prevents QR code forgery              │
│    - Secret key based                      │
├────────────────────────────────────────────┤
│ 4. Password Hashing (SHA-256)              │
│    - Admin passwords never stored plaintext│
│    - Minimum 4 characters                  │
├────────────────────────────────────────────┤
│ 5. Soft Delete                             │
│    - Preserves data history                │
│    - Audit trail maintained                │
└────────────────────────────────────────────┘
```

### 5.2 Threat Model & Mitigations

| 위협 | 설명 | 완화 방안 | 보안 수준 |
|------|------|----------|----------|
| **로컬 시간 조작** | 게스트가 로컬 시간을 과거로 설정하여 만료된 QR 스캔 시도 | World Time API 사용 | ✅ 높음 |
| **QR 재사용 공격** | 이전 QR 코드를 캡처하여 재사용 | Sequence Number 검증 | ✅ 높음 |
| **QR 위조** | QR 코드 내용을 임의로 생성 | HMAC-SHA256 서명 검증 | ✅ 높음 |
| **Replay Attack** | 네트워크에서 QR 내용을 가로채서 재전송 | Sequence + Time 이중 검증 | ✅ 높음 |
| **비밀번호 유출** | 평문 비밀번호 노출 | SHA-256 해싱 (bcrypt 권장) | ⚠️ 중간 |
| **데이터 손실** | 실수로 삭제 | Soft Delete (_removed suffix) | ✅ 높음 |
| **Time API 장애** | World Time API 접근 불가 | Fallback to local + 경고 | ⚠️ 낮음 |

### 5.3 QR Code Validation Flow

```
┌─────────────────────────────────────────────┐
│  Guest scans QR code                        │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  1. Parse QR content (JSON)                 │
│     ✓ Valid JSON?                           │
│     ✓ type == "qr_in_out"?                  │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  2. Verify HMAC signature                   │
│     ✓ Signature matches?                    │
│     ✗ Reject: "위조된 QR 코드"             │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  3. Check Sequence Number                   │
│     ✓ QR.sequence >= Checkpoint.sequence?   │
│     ✗ Reject: "만료된 QR (이전 버전)"       │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  4. Get current time (World Time API)       │
│     ✓ API success: Use API time             │
│     ✗ API fail: Use local time + warning    │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  5. Check time expiration (dynamic only)    │
│     ✓ current_time <= expires_at?           │
│     ✗ Reject: "만료된 QR (시간 초과)"       │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  6. Check checkpoint allowed hours          │
│     ✓ Within checkpoint hours?              │
│     ✗ Reject: "체크포인트 허용 시간 아님"   │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  7. Check guest allowed hours (if set)      │
│     ✓ Within guest hours OR not set?        │
│     ✗ Reject: "방문객 허용 시간 아님"       │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  8. Check guest authorization               │
│     ✓ Guest in checkpoint.allowed_guests?   │
│     ✗ Reject: "권한 없음"                   │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  ✅ All checks passed - Allow check-in      │
│     Record activity log (success)           │
└─────────────────────────────────────────────┘
```

---

## 6. Performance

### 6.1 Performance Targets

| 작업 | 목표 | 측정 방법 |
|------|------|----------|
| QR 생성 | < 100ms | Time from function call to image ready |
| QR 스캔 | < 2 seconds | Time from camera capture to result |
| JSON 로드 | < 50ms | For < 1000 records |
| SQLite 쿼리 | < 100ms | With proper indexing |
| 페이지 로드 | < 2 seconds | Initial Streamlit page load |
| Time API 호출 | < 5 seconds | With 60s caching |

### 6.2 Optimization Strategies

| 영역 | 전략 | 효과 |
|------|------|------|
| **Time API** | Streamlit @st.cache_data(ttl=60) | API 호출 60배 감소 |
| **QR 생성** | 이미지 크기 최적화 (box_size=10) | 메모리 사용량 감소 |
| **JSON 로드** | 필요한 entity만 로드 | I/O 시간 단축 |
| **UI 렌더링** | st.columns(), st.expander() 활용 | 렌더링 속도 향상 |

### 6.3 Scalability Limits

| 리소스 | 제한 | 권장 최대 |
|--------|------|----------|
| Checkpoints | JSON 파일 크기 | ~100개 |
| Guests | JSON 파일 크기 | ~1,000명 |
| Activity Logs | JSON 파일 크기 | ~10,000개 |
| Concurrent Users | Streamlit 단일 프로세스 | 1-5명 |

**확장 방안**:
- JSON → SQLite 마이그레이션
- Pagination 구현
- 오래된 로그 아카이빙

---

## 7. Testing

### 7.1 Test Strategy

```
┌─────────────────────────────────────┐
│          Test Pyramid               │
├─────────────────────────────────────┤
│  Manual Testing (E2E)         10%   │
│  ────────────────────────────       │
│  Integration Tests            20%   │
│  ────────────────────────────       │
│  Unit Tests                   70%   │
└─────────────────────────────────────┘
```

### 7.2 Unit Tests

**Coverage Target**: 80%+

**Key Test Files**:
- `tests/test_models.py` - Data model validation
- `tests/test_storage.py` - CRUD operations
- `tests/test_qr_manager.py` - QR generation & validation
- `tests/test_time_service.py` - Time synchronization
- `tests/test_time_validator.py` - Time-based access control

**Example**:
```python
def test_generate_static_qr():
    content = qr_manager.generate_static_qr_content("cp-123")
    parsed = qr_manager.parse_qr_content(content)

    assert parsed["type"] == "qr_in_out"
    assert parsed["checkpoint_id"] == "cp-123"
    assert parsed["qr_mode"] == "static"

def test_sequence_number_validation():
    # QR with sequence 1, checkpoint current sequence 2
    qr_content = {"sequence": 1}
    checkpoint = {"current_qr_sequence": 2}

    is_valid, reason = qr_manager.validate_dynamic_qr(qr_content, checkpoint, ...)
    assert is_valid == False
    assert "만료" in reason
```

### 7.3 Integration Tests

**Scenarios**:
1. Full checkpoint creation → QR generation → QR scan workflow
2. Guest registration → Authentication → QR scan
3. Soft delete → Activity log preservation
4. Time API failure → Fallback to local time

### 7.4 Manual Testing Checklist

See individual page PRDs:
- [PRD-Admin.md](PRD-Admin.md#testing) - Admin page tests
- [PRD-Host.md](PRD-Host.md#testing) - Host page tests
- [PRD-Guest.md](PRD-Guest.md#testing) - Guest page tests

---

## 8. Network Architecture

### 8.1 Network Requirements

#### 필수 요구사항

| 구성요소 | 필요한 연결 | 포트 | 설명 |
|---------|-----------|-----|------|
| **Streamlit 서버** | Inbound HTTP/HTTPS | 8501 (기본) | 클라이언트 접속용 |
| **모든 클라이언트** | Outbound HTTPS | 443 | World Time API 접근 |
| **Admin** | 서버 접근 | 8501 | 체크포인트/게스트 관리 |
| **Host** | 서버 접근 | 8501 | QR 코드 표시 |
| **Guest** | 서버 접근 | 8501 | QR 스캔 및 체크인 |

#### 방화벽 설정

```
# Inbound Rules (서버)
┌────────────────────────────────────────────┐
│ Port 8501/TCP  │ Allow │ 모든 클라이언트   │
└────────────────────────────────────────────┘

# Outbound Rules (모든 디바이스)
┌────────────────────────────────────────────┐
│ Port 443/TCP   │ Allow │ worldtimeapi.org │
└────────────────────────────────────────────┘
```

### 8.2 Deployment Scenarios

#### 시나리오 A: 동일 LAN (가장 단순)

**적합한 환경**: 소규모 사무실, 단일 건물

```
┌─────────────────────────────────────────────────────┐
│              Local Network (192.168.x.x)            │
│                                                     │
│  ┌──────────────┐  ┌──────────┐  ┌──────────┐      │
│  │   Server     │  │   Host   │  │  Guest   │      │
│  │ 192.168.1.10 │  │ (태블릿) │  │  (폰)    │      │
│  │    :8501     │  │          │  │          │      │
│  └──────────────┘  └──────────┘  └──────────┘      │
│         │                │             │            │
│  ───────┴────────────────┴─────────────┴────────   │
│                    WiFi Router                      │
│                  (인터넷 연결)                      │
└─────────────────────────────────────────────────────┘

설정 방법:
1. 서버 실행: streamlit run app.py --server.address 0.0.0.0
2. Host/Guest 접속: http://192.168.1.10:8501
```

#### 시나리오 B: 클라우드 배포 (원격 체크포인트 지원)

**적합한 환경**: 다중 지점, 원격 체크포인트

```
                    ┌─────────────────────┐
                    │   Cloud Server      │
                    │  (AWS/GCP/Azure)    │
                    │   Public IP/DNS     │
                    │  qr.company.com     │
                    └──────────┬──────────┘
                               │ HTTPS (443)
           ┌───────────────────┼───────────────────┐
           │                   │                   │
      ┌────▼────┐        ┌────▼────┐        ┌────▼────┐
      │  Admin  │        │  Host   │        │  Guest  │
      │ (본사)  │        │ (지점A) │        │ (모바일)│
      │ 서울    │        │ 부산    │        │ 어디서든│
      └─────────┘        └─────────┘        └─────────┘

설정 방법:
1. 클라우드에 Docker/VM 배포
2. Nginx/Caddy로 HTTPS 설정
3. 도메인 연결 (qr.company.com)
4. 모든 디바이스에서 https://qr.company.com 접속
```

#### 시나리오 C: VPN/터널 (보안 강화)

**적합한 환경**: 보안 요구사항이 높은 환경

```
┌─────────────────────────────────────────────────────┐
│                    본사 네트워크                     │
│  ┌──────────────┐      ┌──────────────┐            │
│  │   Server     │      │ VPN Gateway  │            │
│  │ (Private IP) │      │              │            │
│  └──────────────┘      └──────┬───────┘            │
└──────────────────────────────┼──────────────────────┘
                               │ VPN Tunnel
                               │ (암호화)
┌──────────────────────────────┼──────────────────────┐
│                    원격 지점                         │
│                      ┌───────▼───────┐              │
│                      │  VPN Client   │              │
│                      └───────┬───────┘              │
│                              │                      │
│  ┌──────────────┐    ┌──────▼───────┐              │
│  │    Host      │    │   Guest      │              │
│  │  (태블릿)    │    │   (모바일)   │              │
│  └──────────────┘    └──────────────┘              │
└─────────────────────────────────────────────────────┘

설정 방법:
1. 본사에 VPN 서버 설정 (WireGuard/OpenVPN)
2. 원격 지점에 VPN 클라이언트 설정
3. VPN 연결 후 Private IP로 서버 접속
```

### 8.3 HTTPS 설정 (프로덕션 필수)

#### 왜 HTTPS가 필요한가?

| 기능 | HTTP | HTTPS |
|------|------|-------|
| 카메라 접근 | ❌ 차단됨 (localhost 제외) | ✅ 허용 |
| 데이터 암호화 | ❌ 평문 전송 | ✅ 암호화 |
| 중간자 공격 방지 | ❌ 취약 | ✅ 보호 |

#### Nginx + Let's Encrypt 설정 예시

```nginx
# /etc/nginx/sites-available/qr-in-out
server {
    listen 80;
    server_name qr.company.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name qr.company.com;

    ssl_certificate /etc/letsencrypt/live/qr.company.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/qr.company.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Caddy 설정 예시 (더 간단)

```
# Caddyfile
qr.company.com {
    reverse_proxy localhost:8501
}
```

### 8.4 Connection Health Check

#### 연결 상태 모니터링

시스템은 다음 연결 상태를 실시간으로 모니터링합니다:

```python
@dataclass
class ConnectionStatus:
    server_connected: bool      # Streamlit 서버 연결
    time_api_connected: bool    # World Time API 연결
    last_check: datetime        # 마지막 확인 시간
    latency_ms: Optional[int]   # 응답 시간 (ms)
```

#### UI 표시

```
# 정상 상태
📶 연결 상태: ✅ 정상 (응답: 45ms)

# Time API 오류
📶 연결 상태: ⚠️ 시간 동기화 불가 (로컬 시간 사용)

# 서버 연결 끊김
📶 연결 상태: ❌ 서버 연결 끊김 - 네트워크를 확인하세요
```

---

## 9. Deployment

### 9.1 Installation

**Prerequisites**:
- Python 3.10+
- pip

**Steps**:
```bash
# 1. Clone/download project
cd qr_in_out

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run application
streamlit run app.py
```

**First Run**:
- Opens browser at `http://localhost:8501`
- Shows initial setup wizard
- Configure admin timezone
- Creates data/ directory

### 8.2 Configuration

**Environment Variables** (optional):
```bash
# .env file
QR_SECRET_KEY=your-secret-key-here
DEFAULT_TIMEZONE=Asia/Seoul
DATA_DIR=./data
```

**Streamlit Configuration** (`.streamlit/config.toml`):
```toml
[theme]
primaryColor = "#4CAF50"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"

[server]
port = 8501
headless = false

[browser]
gatherUsageStats = false
```

### 8.3 Data Backup

**Manual Backup**:
```bash
# Backup data directory
cp -r data/ backups/data-$(date +%Y%m%d-%H%M%S)/
```

**Scheduled Backup** (cron):
```bash
# Run daily at 2 AM
0 2 * * * cd /path/to/qr_in_out && ./backup.sh
```

---

## 9. Known Limitations

### 9.1 Streamlit Limitations

| 제약 | 영향 | 해결 방안 |
|------|------|----------|
| **Page Refresh** | 모든 상호작용 시 페이지 새로고침 | st.session_state 활용 |
| **No WebSocket** | 실시간 푸시 불가 | 수동 새로고침 필요 |
| **Single Thread** | 동시 사용자 제한 | 로컬 사용에는 충분 |
| **Camera Access** | HTTPS 필요 (localhost는 OK) | 로컬에서는 문제 없음 |

### 9.2 Storage Limitations

| 제약 | 영향 | 해결 방안 |
|------|------|----------|
| **JSON File Size** | > 10,000 records 시 느림 | SQLite로 마이그레이션 |
| **No Transaction** | Race condition 가능 | File locking 구현 |
| **No Indexing** | 검색 느림 | SQLite 사용 권장 |

### 9.3 Security Limitations

| 제약 | 영향 | 해결 방안 |
|------|------|----------|
| **Time API 의존** | API 장애 시 보안 취약 | Fallback + 경고 표시 |
| **SHA-256 해싱** | bcrypt보다 약함 | bcrypt로 업그레이드 권장 |
| **No HTTPS** | 로컬 네트워크에서만 안전 | 공개 배포 시 HTTPS 필수 |

---

## 10. Future Enhancements (Out of Scope)

### Phase 2
- Cloud-based data synchronization (optional)
- Export to PDF, Excel
- Email notifications
- Multi-language support (i18n)

### Phase 3
- REST API for external integrations
- Webhook support
- Mobile native apps (iOS/Android)
- Geolocation validation

### Phase 4
- Multi-tenancy
- Role-based access control (RBAC)
- Advanced analytics dashboard
- SSO integration

---

## Document Metadata

- **문서 타입**: PRD Overview
- **프로젝트**: QR In/Out
- **버전**: 1.2
- **작성자**: Jake
- **작성일**: 2026-02-08
- **언어**: 한국어
- **상태**: Active
- **변경 이력**:
  - v1.2 (2026-02-08): 네트워크 아키텍처, WiFi 정보 필드, 연결 상태 모니터링 추가
  - v1.1 (2026-02-05): 초기 버전
- **관련 문서**:
  - [PRD-Admin.md](PRD-Admin.md) - 관리자 페이지 명세
  - [PRD-Host.md](PRD-Host.md) - 호스트 페이지 명세
  - [PRD-Guest.md](PRD-Guest.md) - 게스트 페이지 명세
  - [Product Brief (한글)](product-brief-qr-in-out.md)
  - [Product Brief (영문)](product-brief-qr-in-out-en.md)

---

**End of PRD Overview**
