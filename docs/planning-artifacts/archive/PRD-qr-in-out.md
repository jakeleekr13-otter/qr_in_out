---
document_type: "Product Requirements Document"
project: "QR In/Out"
version: "1.1"
author: "Jake"
date: "2026-02-05"
updated: "2026-02-05"
status: "Draft"
language: "Korean"
purpose: "개인 개발용 상세 기능 명세"
changelog: "Added Time Sync, Sequence Number, Soft Delete, Admin Settings"
related_docs:
  - "product-brief-qr-in-out.md"
---

# PRD: QR In/Out

## Executive Summary

QR In/Out은 Streamlit 기반의 QR 코드 체크포인트 관리 시스템입니다. 로컬 파일 저장소를 사용하여 호스팅이나 데이터베이스 없이 동작하며, Python 환경에서 간단히 실행 가능합니다.

### 핵심 특징
- **프레임워크**: Streamlit (Python 기반)
- **배포 방식**: 로컬 실행 (`streamlit run app.py`)
- **데이터 저장**: JSON 파일 또는 SQLite (로컬)
- **QR 스캔**: 실시간 카메라 스캔 (streamlit-camera-input)
- **Multi-page**: 3개 독립 페이지 (Admin/Host/Guest)
- **시간 동기화**: World Time API (로컬 시간 조작 방지)
- **보안**: Sequence Number + HMAC Signature (Expired QR 검증)
- **데이터 보존**: Soft Delete (삭제 이력 보존)

---

## 1. Product Overview

### 1.1 Product Vision
체크포인트 출입 관리를 위한 간단하고 효율적인 QR 코드 시스템을 제공합니다.

### 1.2 Target Users
- **관리자**: 체크포인트 및 방문객 관리
- **호스트**: QR 코드 디스플레이 운영
- **방문객**: QR 코드 스캔 및 기록 조회

### 1.3 Key Goals
- 로컬 환경에서 독립적으로 실행 가능
- 외부 의존성 최소화 (호스팅, DB 불필요)
- 빠른 프로토타이핑 및 테스트

---

## 2. System Architecture

### 2.1 Technology Stack

#### Core Framework
```
Streamlit 1.30+
Python 3.10+
```

#### Required Libraries
```python
streamlit              # Web framework
streamlit-camera-input # Camera access for QR scanning
qrcode                # QR code generation
pillow                # Image processing
pyzbar                # QR code decoding
opencv-python         # Image processing (optional, for advanced scanning)
python-dotenv         # Configuration management
pytz                  # Timezone support
```

#### Data Storage
```
Option 1: JSON files (simple, human-readable)
Option 2: SQLite (better for large datasets)
```

### 2.2 Application Structure

```
qr_in_out/
├── app.py                    # Main entry point
├── pages/
│   ├── 1_👤_Admin.py        # Admin page
│   ├── 2_🖥️_Host.py         # Host page
│   └── 3_👋_Guest.py        # Guest page
├── core/
│   ├── __init__.py
│   ├── models.py            # Data models
│   ├── storage.py           # Storage layer
│   ├── qr_manager.py        # QR generation/validation
│   ├── time_validator.py    # Time-based access control
│   └── auth.py              # Password management
├── data/
│   ├── checkpoints.json     # Checkpoint data
│   ├── guests.json          # Guest data
│   └── activity_logs.json   # Activity logs
├── config/
│   └── settings.py          # Configuration
├── utils/
│   ├── __init__.py
│   └── helpers.py           # Helper functions
├── tests/
│   ├── test_models.py
│   ├── test_qr_manager.py
│   └── test_time_validator.py
├── requirements.txt
├── README.md
└── .streamlit/
    └── config.toml          # Streamlit configuration
```

### 2.3 Data Flow

```
[Admin Page]
    ↓ (Create/Edit)
[Local Storage: checkpoints.json, guests.json]
    ↓ (Read)
[Host Page] → Generate QR → Display
    ↓ (Scan)
[Guest Page] → Validate → Record
    ↓ (Save)
[Local Storage: activity_logs.json]
```

---

## 3. Detailed Feature Specifications

### 3.1 Admin Page (관리자 페이지)

#### 3.1.1 페이지 개요
- **URL**: `/Admin` (Streamlit multi-page)
- **접근 제어**: 없음 (로컬 실행이므로)
- **주요 기능**: 체크포인트 관리, 방문객 관리, 로그 조회

#### 3.1.2 체크포인트 관리

##### 기능: 체크포인트 생성
**User Story**:
```
As an admin,
I want to create a new checkpoint,
So that I can control access to a specific location.
```

**UI Components**:
```python
st.title("체크포인트 관리")
st.subheader("새 체크포인트 생성")

with st.form("create_checkpoint"):
    name = st.text_input("체크포인트 이름", placeholder="예: 본관 입구")
    location = st.text_input("위치", placeholder="예: 서울시 강남구...")

    col1, col2 = st.columns(2)
    with col1:
        start_time = st.time_input("허용 시작 시간", value=time(9, 0))
    with col2:
        end_time = st.time_input("허용 종료 시간", value=time(18, 0))

    qr_mode = st.selectbox("QR 코드 방식", ["static", "dynamic"])
    admin_password = st.text_input("관리 비밀번호", type="password")

    # Multi-select for allowed guests
    guests = load_guests()
    allowed_guests = st.multiselect(
        "허용 방문객",
        options=[g["id"] for g in guests],
        format_func=lambda x: get_guest_name(x)
    )

    submitted = st.form_submit_button("생성")
    if submitted:
        create_checkpoint(...)
        st.success("체크포인트가 생성되었습니다!")
```

**Data Model**:
```python
@dataclass
class Checkpoint:
    id: str
    name: str
    location: str
    allowed_hours: AllowedHours
    qr_mode: Literal["static", "dynamic"]
    admin_password_hash: str
    allowed_guests: List[str]  # guest IDs
    created_at: datetime
    updated_at: datetime

@dataclass
class AllowedHours:
    start_time: str  # "HH:MM" format
    end_time: str    # "HH:MM" format
```

**Acceptance Criteria**:
- [ ] 모든 필드가 입력되어야 생성 가능
- [ ] 체크포인트 이름은 고유해야 함
- [ ] 허용 시간은 시작 < 종료 검증
- [ ] 비밀번호는 최소 4자 이상
- [ ] 생성 후 checkpoints.json에 저장
- [ ] 성공 메시지 표시

##### 기능: 체크포인트 수정

**UI Components**:
```python
st.subheader("기존 체크포인트 수정")

checkpoints = load_checkpoints()
selected_checkpoint = st.selectbox(
    "수정할 체크포인트 선택",
    options=[c["id"] for c in checkpoints],
    format_func=lambda x: get_checkpoint_name(x)
)

if selected_checkpoint:
    checkpoint = get_checkpoint(selected_checkpoint)

    with st.form("edit_checkpoint"):
        name = st.text_input("이름", value=checkpoint["name"])
        location = st.text_input("위치", value=checkpoint["location"])
        # ... (생성과 동일한 필드들)

        submitted = st.form_submit_button("수정")
        if submitted:
            update_checkpoint(...)
            st.success("체크포인트가 수정되었습니다!")
```

**Acceptance Criteria**:
- [ ] 기존 데이터가 폼에 pre-filled
- [ ] 수정 시 updated_at 타임스탬프 갱신
- [ ] 변경사항이 즉시 저장

##### 기능: 체크포인트 삭제

**UI Components**:
```python
with st.expander("⚠️ 위험 구역"):
    st.warning("체크포인트를 삭제하면 관련된 모든 로그도 삭제됩니다.")

    if st.button("체크포인트 삭제", type="secondary"):
        if st.session_state.get("confirm_delete"):
            delete_checkpoint(selected_checkpoint)
            st.success("삭제되었습니다.")
            st.session_state.confirm_delete = False
        else:
            st.session_state.confirm_delete = True
            st.error("다시 한 번 클릭하여 삭제를 확인하세요.")
```

**Acceptance Criteria**:
- [ ] 이중 확인 메커니즘 (실수 방지)
- [ ] 연관된 activity logs도 함께 삭제
- [ ] 삭제 후 리스트에서 제거

#### 3.1.3 방문객 관리

##### 기능: 방문객 등록

**User Story**:
```
As an admin,
I want to register a new guest,
So that they can scan QR codes at authorized checkpoints.
```

**UI Components**:
```python
st.title("방문객 관리")
st.subheader("새 방문객 등록")

with st.form("create_guest"):
    name = st.text_input("이름", placeholder="홍길동")

    # Additional info as JSON or key-value pairs
    st.write("추가 정보 (선택사항)")
    col1, col2 = st.columns(2)
    with col1:
        email = st.text_input("이메일")
    with col2:
        phone = st.text_input("전화번호")

    # Timezone
    timezone = st.selectbox(
        "타임존",
        options=pytz.all_timezones,
        index=pytz.all_timezones.index("Asia/Seoul")
    )

    # Optional: Allowed hours for this guest
    use_custom_hours = st.checkbox("방문객별 허용 시간 설정")
    if use_custom_hours:
        col1, col2 = st.columns(2)
        with col1:
            guest_start_time = st.time_input("허용 시작 시간")
        with col2:
            guest_end_time = st.time_input("허용 종료 시간")

    # Multi-select for allowed checkpoints
    checkpoints = load_checkpoints()
    allowed_checkpoints = st.multiselect(
        "허가 체크포인트",
        options=[c["id"] for c in checkpoints],
        format_func=lambda x: get_checkpoint_name(x)
    )

    submitted = st.form_submit_button("등록")
    if submitted:
        create_guest(...)
        st.success("방문객이 등록되었습니다!")
```

**Data Model**:
```python
@dataclass
class Guest:
    id: str
    name: str
    additional_info: Dict[str, Any]  # email, phone, etc.
    timezone: str  # IANA timezone
    allowed_hours: Optional[AllowedHours]  # Optional per-guest restrictions
    allowed_checkpoints: List[str]  # checkpoint IDs
    created_at: datetime
    updated_at: datetime
```

**Acceptance Criteria**:
- [ ] 이름은 필수 입력
- [ ] 타임존 선택 가능 (기본값: Asia/Seoul)
- [ ] 허용 시간은 선택사항
- [ ] 최소 1개 이상의 체크포인트 선택 필요
- [ ] guests.json에 저장
- [ ] 고유 ID 자동 생성 (UUID)

##### 기능: 방문객 수정/삭제

**UI Components**:
```python
st.subheader("기존 방문객 관리")

guests = load_guests()
selected_guest = st.selectbox(
    "방문객 선택",
    options=[g["id"] for g in guests],
    format_func=lambda x: get_guest_name(x)
)

if selected_guest:
    tab1, tab2 = st.tabs(["수정", "삭제"])

    with tab1:
        # Similar form as create_guest with pre-filled values
        pass

    with tab2:
        st.warning("방문객을 삭제하면 관련 로그는 유지되지만 더 이상 체크인할 수 없습니다.")
        if st.button("방문객 삭제"):
            delete_guest(selected_guest)
            st.success("삭제되었습니다.")
```

**Acceptance Criteria**:
- [ ] 수정 시 기존 데이터 pre-fill
- [ ] 삭제 시 activity logs는 유지 (히스토리 보존)
- [ ] 삭제된 방문객은 QR 스캔 불가

#### 3.1.4 모니터링 및 리포팅

##### 기능: 체크포인트별 로그 조회

**UI Components**:
```python
st.title("활동 로그")

view_mode = st.radio("조회 방식", ["체크포인트별", "방문객별", "전체"])

if view_mode == "체크포인트별":
    checkpoint_id = st.selectbox(
        "체크포인트 선택",
        options=[c["id"] for c in load_checkpoints()],
        format_func=lambda x: get_checkpoint_name(x)
    )

    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("시작일", value=date.today() - timedelta(days=7))
    with col2:
        end_date = st.date_input("종료일", value=date.today())

    # Load and filter logs
    logs = load_activity_logs(
        checkpoint_id=checkpoint_id,
        start_date=start_date,
        end_date=end_date
    )

    # Display as dataframe
    df = pd.DataFrame(logs)
    st.dataframe(
        df,
        column_config={
            "timestamp": st.column_config.DatetimeColumn("시간"),
            "guest_name": "방문객",
            "action": st.column_config.SelectboxColumn("활동", options=["check_in", "check_out"]),
            "status": st.column_config.SelectboxColumn("상태", options=["success", "failure"])
        }
    )

    # Export functionality
    if st.button("CSV 다운로드"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"checkpoint_{checkpoint_id}_logs.csv",
            mime="text/csv"
        )

elif view_mode == "방문객별":
    # Similar implementation for guest view
    pass

else:  # 전체
    # Show all logs with filters
    pass
```

**Data Model**:
```python
@dataclass
class ActivityLog:
    id: str
    timestamp: datetime
    checkpoint_id: str
    guest_id: str
    action: Literal["check_in", "check_out"]
    qr_code_used: str  # The QR code content that was scanned
    status: Literal["success", "failure"]
    failure_reason: Optional[str]
    metadata: Dict[str, Any]  # Additional context
```

**Acceptance Criteria**:
- [ ] 체크포인트별, 방문객별, 전체 조회 지원
- [ ] 날짜 범위 필터링
- [ ] 테이블 형태로 표시 (정렬 가능)
- [ ] CSV 다운로드 기능
- [ ] 실시간 업데이트 (페이지 새로고침 시)

##### 기능: 통계 대시보드

**UI Components**:
```python
st.title("통계 대시보드")

# Date range selector
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("시작일")
with col2:
    end_date = st.date_input("종료일")

logs = load_activity_logs(start_date=start_date, end_date=end_date)

# Metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("총 체크인", count_check_ins(logs))
with col2:
    st.metric("총 체크아웃", count_check_outs(logs))
with col3:
    st.metric("성공률", f"{success_rate(logs):.1f}%")
with col4:
    st.metric("활성 방문객", active_guests_count(logs))

# Charts
st.subheader("시간대별 활동")
chart_data = get_hourly_activity(logs)
st.line_chart(chart_data)

st.subheader("체크포인트별 활동")
checkpoint_data = get_checkpoint_activity(logs)
st.bar_chart(checkpoint_data)
```

**Acceptance Criteria**:
- [ ] 주요 지표 표시 (체크인/아웃, 성공률 등)
- [ ] 시간대별 활동 차트
- [ ] 체크포인트별 활동 차트
- [ ] 날짜 범위 필터링

---

### 3.2 Host Page (호스트 페이지)

#### 3.2.1 페이지 개요
- **URL**: `/Host` (Streamlit multi-page)
- **주요 기능**: QR 코드 표시, 자동 갱신, 화면 잠금

#### 3.2.2 체크포인트 선택 및 인증

##### 기능: 체크포인트 선택

**UI Components**:
```python
st.title("호스트 페이지 - QR 코드 디스플레이")

# Session state for authentication
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.selected_checkpoint = None

if not st.session_state.authenticated:
    st.subheader("체크포인트 선택")

    checkpoints = load_checkpoints()
    selected = st.selectbox(
        "디스플레이할 체크포인트",
        options=[c["id"] for c in checkpoints],
        format_func=lambda x: get_checkpoint_name(x)
    )

    password = st.text_input("관리 비밀번호", type="password")

    if st.button("시작"):
        checkpoint = get_checkpoint(selected)
        if verify_password(password, checkpoint["admin_password_hash"]):
            st.session_state.authenticated = True
            st.session_state.selected_checkpoint = selected
            st.rerun()
        else:
            st.error("비밀번호가 올바르지 않습니다.")
```

**Acceptance Criteria**:
- [ ] 체크포인트 리스트 표시
- [ ] 비밀번호 입력 및 검증
- [ ] 인증 성공 시 QR 코드 화면으로 전환
- [ ] 인증 실패 시 에러 메시지

#### 3.2.3 QR 코드 표시

##### 기능: Static QR 코드 표시

**UI Components**:
```python
if st.session_state.authenticated:
    checkpoint = get_checkpoint(st.session_state.selected_checkpoint)

    # Header with checkpoint info
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header(f"📍 {checkpoint['name']}")
        st.caption(checkpoint['location'])
    with col2:
        if st.button("🔒 잠금"):
            st.session_state.authenticated = False
            st.rerun()

    # Check if within allowed hours
    is_allowed, message = check_allowed_hours(checkpoint)

    if is_allowed:
        st.success("✅ 현재 허용 시간 내입니다")

        # Generate QR code
        if checkpoint["qr_mode"] == "static":
            qr_content = generate_static_qr_content(checkpoint["id"])
            qr_image = generate_qr_image(qr_content)

            # Display QR code (large)
            st.image(qr_image, use_column_width=True)

            st.info(f"QR 코드 타입: 고정형 (프린트 가능)")

            # Print button
            if st.button("🖨️ 프린트용 다운로드"):
                st.download_button(
                    label="QR 코드 이미지 다운로드",
                    data=qr_image_to_bytes(qr_image),
                    file_name=f"qr_{checkpoint['name']}.png",
                    mime="image/png"
                )
    else:
        st.error(f"🚫 허용 시간 외: {message}")
        st.info("QR 코드가 비활성화되었습니다.")
```

**QR Content Format (Static)**:
```json
{
  "type": "qr_in_out",
  "version": "1.0",
  "checkpoint_id": "uuid-here",
  "qr_mode": "static",
  "created_at": "2026-02-05T10:30:00Z"
}
```

**Acceptance Criteria**:
- [ ] 체크포인트 정보 표시
- [ ] 허용 시간 체크
- [ ] QR 코드 생성 및 표시 (큰 사이즈)
- [ ] 프린트용 다운로드 버튼
- [ ] 잠금 버튼으로 화면 보호

##### 기능: Dynamic QR 코드 표시 및 자동 갱신

**UI Components**:
```python
if checkpoint["qr_mode"] == "dynamic":
    # Calculate next refresh time
    current_time = datetime.now(pytz.timezone(checkpoint.get("timezone", "UTC")))
    next_refresh = calculate_next_refresh_time(current_time)
    time_until_refresh = (next_refresh - current_time).total_seconds()

    # Generate current QR code
    qr_content = generate_dynamic_qr_content(
        checkpoint_id=checkpoint["id"],
        timestamp=current_time
    )
    qr_image = generate_qr_image(qr_content)

    # Display QR code
    st.image(qr_image, use_column_width=True)

    # Countdown timer
    st.info(f"QR 코드 타입: 갱신형 (30분 주기)")
    st.warning(f"⏱️ 다음 갱신까지: {format_countdown(time_until_refresh)}")

    # Progress bar for visual feedback
    progress = 1 - (time_until_refresh / 1800)  # 1800 seconds = 30 minutes
    st.progress(progress)

    # Auto-refresh using st.rerun() with timer
    if time_until_refresh <= 0:
        st.rerun()
    else:
        time.sleep(1)  # Check every second
        st.rerun()
```

**QR Content Format (Dynamic)**:
```json
{
  "type": "qr_in_out",
  "version": "1.0",
  "checkpoint_id": "uuid-here",
  "qr_mode": "dynamic",
  "issued_at": "2026-02-05T10:30:00Z",
  "expires_at": "2026-02-05T11:00:00Z",
  "refresh_interval": 1800,
  "signature": "hmac-signature-here"
}
```

**Acceptance Criteria**:
- [ ] 30분 주기로 QR 코드 자동 갱신
- [ ] 다음 갱신까지 카운트다운 표시
- [ ] Progress bar로 시각적 피드백
- [ ] 만료된 QR 코드는 스캔 불가
- [ ] 프린트 버튼 비활성화 (동적이므로)

#### 3.2.4 화면 잠금

**UI Components**:
```python
# Lock button in the corner
if st.button("🔒 잠금", key="lock_screen"):
    st.session_state.authenticated = False
    st.session_state.show_lock_confirmation = True
    st.rerun()

# Lock confirmation overlay
if st.session_state.get("show_lock_confirmation"):
    st.success("화면이 잠겼습니다. 다시 시작하려면 비밀번호를 입력하세요.")
    time.sleep(2)
    st.session_state.show_lock_confirmation = False
    st.rerun()
```

**Acceptance Criteria**:
- [ ] 잠금 버튼 클릭 시 인증 세션 종료
- [ ] 다시 시작하려면 비밀번호 재입력 필요
- [ ] 잠금 확인 메시지 표시

---

### 3.3 Guest Page (게스트 페이지)

#### 3.3.1 페이지 개요
- **URL**: `/Guest` (Streamlit multi-page)
- **주요 기능**: 방문자 정보 입력, QR 코드 스캔, 기록 조회

#### 3.3.2 방문자 인증

##### 기능: 방문자 정보 입력

**UI Components**:
```python
st.title("게스트 페이지 - 체크인/체크아웃")

# Session state for guest authentication
if "guest_authenticated" not in st.session_state:
    st.session_state.guest_authenticated = False
    st.session_state.current_guest = None

if not st.session_state.guest_authenticated:
    st.subheader("방문자 정보 입력")

    st.info("관리자에게 등록된 정보를 입력하세요.")

    name = st.text_input("이름", placeholder="홍길동")

    # Additional verification fields (optional)
    with st.expander("추가 정보 (선택사항)"):
        email = st.text_input("이메일")
        phone = st.text_input("전화번호")

    if st.button("확인"):
        guest = verify_guest_identity(name, email, phone)
        if guest:
            st.session_state.guest_authenticated = True
            st.session_state.current_guest = guest
            st.success(f"환영합니다, {guest['name']}님!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("등록되지 않은 방문객입니다. 관리자에게 문의하세요.")
```

**Acceptance Criteria**:
- [ ] 이름 입력 필수
- [ ] 추가 정보로 검증 강화 (선택사항)
- [ ] 등록된 방문객만 통과
- [ ] 인증 성공 시 세션에 guest 정보 저장

#### 3.3.3 QR 코드 스캔

##### 기능: 카메라로 QR 코드 스캔

**UI Components**:
```python
if st.session_state.guest_authenticated:
    guest = st.session_state.current_guest

    st.header(f"👋 {guest['name']}님")
    st.caption(f"타임존: {guest['timezone']}")

    # Action selector
    action = st.radio("활동 선택", ["체크인", "체크아웃"], horizontal=True)

    st.subheader("QR 코드 스캔")

    # Camera input for QR scanning
    camera_image = st.camera_input("카메라로 QR 코드를 스캔하세요")

    if camera_image:
        # Decode QR code from image
        image = Image.open(camera_image)
        qr_content = decode_qr_from_image(image)

        if qr_content:
            st.success("✅ QR 코드 인식 성공!")

            # Parse QR content
            qr_data = parse_qr_content(qr_content)

            # Validate QR code
            validation_result = validate_qr_code(
                qr_data=qr_data,
                guest=guest,
                action=action.lower().replace("체크", "check_")
            )

            if validation_result["valid"]:
                # Record activity
                activity_log = record_activity(
                    checkpoint_id=qr_data["checkpoint_id"],
                    guest_id=guest["id"],
                    action=action.lower().replace("체크", "check_"),
                    qr_code_used=qr_content,
                    status="success"
                )

                st.success(f"✅ {action} 성공!")
                st.balloons()

                # Show activity details
                checkpoint = get_checkpoint(qr_data["checkpoint_id"])
                st.info(f"📍 {checkpoint['name']}\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            else:
                # Show failure reason
                st.error(f"❌ {action} 실패: {validation_result['reason']}")

                # Record failed attempt
                record_activity(
                    checkpoint_id=qr_data.get("checkpoint_id"),
                    guest_id=guest["id"],
                    action=action.lower().replace("체크", "check_"),
                    qr_code_used=qr_content,
                    status="failure",
                    failure_reason=validation_result['reason']
                )
        else:
            st.error("❌ QR 코드를 인식할 수 없습니다. 다시 시도하세요.")
```

**QR Validation Logic**:
```python
def validate_qr_code(qr_data, guest, action):
    """
    Validate QR code scan attempt

    Checks:
    1. QR code format is correct
    2. Checkpoint exists
    3. Guest is allowed at this checkpoint
    4. Current time is within checkpoint allowed hours
    5. Current time is within guest allowed hours (if set)
    6. QR code is not expired (for dynamic QR)
    7. Action is consistent (can't check out without checking in)
    """

    # 1. Check QR format
    if not is_valid_qr_format(qr_data):
        return {"valid": False, "reason": "잘못된 QR 코드 형식"}

    # 2. Check checkpoint exists
    checkpoint = get_checkpoint(qr_data["checkpoint_id"])
    if not checkpoint:
        return {"valid": False, "reason": "존재하지 않는 체크포인트"}

    # 3. Check guest authorization
    if guest["id"] not in checkpoint["allowed_guests"]:
        return {"valid": False, "reason": "이 체크포인트에 대한 권한이 없습니다"}

    # 4. Check checkpoint allowed hours
    current_time = datetime.now(pytz.timezone(guest["timezone"]))
    if not is_within_allowed_hours(current_time, checkpoint["allowed_hours"]):
        return {"valid": False, "reason": "체크포인트 허용 시간이 아닙니다"}

    # 5. Check guest allowed hours (if set)
    if guest.get("allowed_hours"):
        if not is_within_allowed_hours(current_time, guest["allowed_hours"]):
            return {"valid": False, "reason": "귀하의 허용 시간이 아닙니다"}

    # 6. Check QR expiration (for dynamic QR)
    if qr_data.get("qr_mode") == "dynamic":
        if is_qr_expired(qr_data):
            return {"valid": False, "reason": "만료된 QR 코드입니다. 갱신된 코드를 스캔하세요"}

    # 7. Check action consistency
    last_activity = get_last_activity(guest["id"], checkpoint["id"])
    if action == "check_out" and (not last_activity or last_activity["action"] == "check_out"):
        return {"valid": False, "reason": "체크인하지 않았습니다"}

    return {"valid": True, "reason": None}
```

**Acceptance Criteria**:
- [ ] 카메라 접근 권한 요청
- [ ] QR 코드 실시간 디코딩
- [ ] 다중 검증 로직 실행
- [ ] 성공 시 balloons 애니메이션
- [ ] 실패 시 명확한 사유 표시
- [ ] 모든 시도 기록 (성공/실패)

##### 기능: 파일 업로드로 QR 스캔 (대체 방법)

**UI Components**:
```python
st.subheader("또는 QR 코드 이미지 업로드")

uploaded_file = st.file_uploader(
    "QR 코드 이미지를 업로드하세요",
    type=["png", "jpg", "jpeg"],
    help="카메라가 작동하지 않을 경우 스크린샷을 업로드할 수 있습니다"
)

if uploaded_file:
    # Same logic as camera input
    image = Image.open(uploaded_file)
    qr_content = decode_qr_from_image(image)
    # ... (validation logic)
```

**Acceptance Criteria**:
- [ ] PNG, JPG 형식 지원
- [ ] 카메라 입력과 동일한 검증 로직

#### 3.3.4 방문 기록 조회

##### 기능: 개인 활동 기록 보기

**UI Components**:
```python
st.subheader("내 활동 기록")

# Date range filter
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input(
        "시작일",
        value=date.today() - timedelta(days=7)
    )
with col2:
    end_date = st.date_input("종료일", value=date.today())

# Load guest's activity logs
logs = load_activity_logs(
    guest_id=guest["id"],
    start_date=start_date,
    end_date=end_date
)

if logs:
    # Group by checkpoint and date
    st.write(f"총 {len(logs)}개의 기록")

    # Display as timeline
    for log in sorted(logs, key=lambda x: x["timestamp"], reverse=True):
        checkpoint = get_checkpoint(log["checkpoint_id"])

        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:
                st.write(f"**{checkpoint['name']}**")
                st.caption(checkpoint['location'])

            with col2:
                st.write(log["timestamp"].strftime("%Y-%m-%d %H:%M:%S"))

            with col3:
                if log["action"] == "check_in":
                    st.success("✅ IN")
                else:
                    st.info("🚪 OUT")

            st.divider()

    # Export personal logs
    if st.button("내 기록 다운로드 (CSV)"):
        df = pd.DataFrame(logs)
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"my_activity_{guest['name']}.csv",
            mime="text/csv"
        )
else:
    st.info("기록이 없습니다.")
```

**Acceptance Criteria**:
- [ ] 본인의 기록만 조회 가능
- [ ] 날짜 범위 필터링
- [ ] 시간순 정렬 (최신순)
- [ ] 체크포인트 정보와 함께 표시
- [ ] CSV 다운로드 기능

---

## 4. Data Storage Implementation

### 4.1 Storage Architecture

#### Option 1: JSON Files (Recommended for V1)

**Directory Structure**:
```
data/
├── checkpoints.json
├── guests.json
└── activity_logs.json
```

**Storage Module** (`core/storage.py`):
```python
import json
import os
from typing import List, Optional, Dict, Any
from pathlib import Path
import threading

class JSONStorage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self._lock = threading.Lock()

    def _get_file_path(self, entity_type: str) -> Path:
        return self.data_dir / f"{entity_type}.json"

    def load(self, entity_type: str) -> List[Dict[str, Any]]:
        """Load all entities of a given type"""
        file_path = self._get_file_path(entity_type)

        if not file_path.exists():
            return []

        with self._lock:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)

    def save(self, entity_type: str, data: List[Dict[str, Any]]):
        """Save all entities of a given type"""
        file_path = self._get_file_path(entity_type)

        with self._lock:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def add(self, entity_type: str, entity: Dict[str, Any]):
        """Add a new entity"""
        data = self.load(entity_type)
        data.append(entity)
        self.save(entity_type, data)

    def update(self, entity_type: str, entity_id: str, updates: Dict[str, Any]):
        """Update an existing entity"""
        data = self.load(entity_type)

        for item in data:
            if item["id"] == entity_id:
                item.update(updates)
                item["updated_at"] = datetime.now().isoformat()
                break

        self.save(entity_type, data)

    def delete(self, entity_type: str, entity_id: str):
        """Delete an entity"""
        data = self.load(entity_type)
        data = [item for item in data if item["id"] != entity_id]
        self.save(entity_type, data)

    def get_by_id(self, entity_type: str, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get a single entity by ID"""
        data = self.load(entity_type)
        for item in data:
            if item["id"] == entity_id:
                return item
        return None

# Global storage instance
storage = JSONStorage()
```

**Acceptance Criteria**:
- [ ] Thread-safe file operations
- [ ] Automatic directory creation
- [ ] UTF-8 encoding support
- [ ] ISO datetime serialization
- [ ] CRUD operations support

#### Option 2: SQLite (Alternative)

**Schema**:
```sql
CREATE TABLE checkpoints (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT,
    allowed_hours_start TEXT,
    allowed_hours_end TEXT,
    qr_mode TEXT CHECK(qr_mode IN ('static', 'dynamic')),
    admin_password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE guests (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    additional_info TEXT,  -- JSON blob
    timezone TEXT NOT NULL,
    allowed_hours_start TEXT,
    allowed_hours_end TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE checkpoint_guests (
    checkpoint_id TEXT,
    guest_id TEXT,
    PRIMARY KEY (checkpoint_id, guest_id),
    FOREIGN KEY (checkpoint_id) REFERENCES checkpoints(id) ON DELETE CASCADE,
    FOREIGN KEY (guest_id) REFERENCES guests(id) ON DELETE CASCADE
);

CREATE TABLE activity_logs (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    checkpoint_id TEXT,
    guest_id TEXT,
    action TEXT CHECK(action IN ('check_in', 'check_out')),
    qr_code_used TEXT,
    status TEXT CHECK(status IN ('success', 'failure')),
    failure_reason TEXT,
    metadata TEXT,  -- JSON blob
    FOREIGN KEY (checkpoint_id) REFERENCES checkpoints(id),
    FOREIGN KEY (guest_id) REFERENCES guests(id)
);

CREATE INDEX idx_logs_timestamp ON activity_logs(timestamp);
CREATE INDEX idx_logs_checkpoint ON activity_logs(checkpoint_id);
CREATE INDEX idx_logs_guest ON activity_logs(guest_id);
```

### 4.2 Data Models

**Complete Type Definitions** (`core/models.py`):
```python
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
import uuid

@dataclass
class AllowedHours:
    start_time: str  # "HH:MM" format
    end_time: str    # "HH:MM" format

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "AllowedHours":
        return cls(**data)

@dataclass
class Checkpoint:
    id: str
    name: str
    location: str
    allowed_hours: AllowedHours
    qr_mode: Literal["static", "dynamic"]
    admin_password_hash: str
    allowed_guests: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["allowed_hours"] = self.allowed_hours.to_dict()
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Checkpoint":
        data = data.copy()
        data["allowed_hours"] = AllowedHours.from_dict(data["allowed_hours"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)

    @classmethod
    def create_new(cls, name: str, location: str, allowed_hours: AllowedHours,
                   qr_mode: str, admin_password: str, allowed_guests: List[str]) -> "Checkpoint":
        from core.auth import hash_password

        return cls(
            id=str(uuid.uuid4()),
            name=name,
            location=location,
            allowed_hours=allowed_hours,
            qr_mode=qr_mode,
            admin_password_hash=hash_password(admin_password),
            allowed_guests=allowed_guests
        )

@dataclass
class Guest:
    id: str
    name: str
    timezone: str
    allowed_checkpoints: List[str] = field(default_factory=list)
    additional_info: Dict[str, Any] = field(default_factory=dict)
    allowed_hours: Optional[AllowedHours] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.allowed_hours:
            data["allowed_hours"] = self.allowed_hours.to_dict()
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Guest":
        data = data.copy()
        if data.get("allowed_hours"):
            data["allowed_hours"] = AllowedHours.from_dict(data["allowed_hours"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        return cls(**data)

    @classmethod
    def create_new(cls, name: str, timezone: str, allowed_checkpoints: List[str],
                   additional_info: Dict[str, Any], allowed_hours: Optional[AllowedHours] = None) -> "Guest":
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            timezone=timezone,
            allowed_checkpoints=allowed_checkpoints,
            additional_info=additional_info,
            allowed_hours=allowed_hours
        )

@dataclass
class ActivityLog:
    id: str
    timestamp: datetime
    checkpoint_id: str
    guest_id: str
    action: Literal["check_in", "check_out"]
    qr_code_used: str
    status: Literal["success", "failure"]
    failure_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActivityLog":
        data = data.copy()
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)

    @classmethod
    def create_new(cls, checkpoint_id: str, guest_id: str, action: str,
                   qr_code_used: str, status: str, failure_reason: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> "ActivityLog":
        return cls(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            checkpoint_id=checkpoint_id,
            guest_id=guest_id,
            action=action,
            qr_code_used=qr_code_used,
            status=status,
            failure_reason=failure_reason,
            metadata=metadata or {}
        )
```

---

## 5. Core Modules Implementation

### 5.1 QR Code Manager (`core/qr_manager.py`)

```python
import qrcode
import json
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from PIL import Image
import io
import pytz

class QRManager:
    def __init__(self, secret_key: str = "your-secret-key-here"):
        self.secret_key = secret_key
        self.refresh_interval = 1800  # 30 minutes in seconds

    def generate_static_qr_content(self, checkpoint_id: str) -> str:
        """Generate static QR code content"""
        content = {
            "type": "qr_in_out",
            "version": "1.0",
            "checkpoint_id": checkpoint_id,
            "qr_mode": "static",
            "created_at": datetime.now(pytz.UTC).isoformat()
        }
        return json.dumps(content)

    def generate_dynamic_qr_content(self, checkpoint_id: str,
                                     timestamp: Optional[datetime] = None) -> str:
        """Generate dynamic QR code content with expiration"""
        if timestamp is None:
            timestamp = datetime.now(pytz.UTC)

        # Calculate expiration (next 30-minute mark)
        expires_at = self._calculate_next_refresh_time(timestamp)

        content = {
            "type": "qr_in_out",
            "version": "1.0",
            "checkpoint_id": checkpoint_id,
            "qr_mode": "dynamic",
            "issued_at": timestamp.isoformat(),
            "expires_at": expires_at.isoformat(),
            "refresh_interval": self.refresh_interval
        }

        # Add HMAC signature to prevent tampering
        signature = self._generate_signature(content)
        content["signature"] = signature

        return json.dumps(content)

    def _calculate_next_refresh_time(self, current_time: datetime) -> datetime:
        """Calculate the next 30-minute refresh time"""
        # Round up to next 30-minute mark
        minutes = current_time.minute
        if minutes < 30:
            next_time = current_time.replace(minute=30, second=0, microsecond=0)
        else:
            next_time = (current_time + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

        return next_time

    def _generate_signature(self, content: Dict[str, Any]) -> str:
        """Generate HMAC signature for QR content"""
        # Create canonical string from content (excluding signature field)
        content_copy = {k: v for k, v in content.items() if k != "signature"}
        canonical = json.dumps(content_copy, sort_keys=True)

        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            self.secret_key.encode(),
            canonical.encode(),
            hashlib.sha256
        ).hexdigest()

        return signature

    def verify_signature(self, qr_content: Dict[str, Any]) -> bool:
        """Verify HMAC signature of QR content"""
        if "signature" not in qr_content:
            return False

        provided_signature = qr_content["signature"]
        expected_signature = self._generate_signature(qr_content)

        return hmac.compare_digest(provided_signature, expected_signature)

    def generate_qr_image(self, content: str, size: int = 10) -> Image.Image:
        """Generate QR code image from content"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=4,
        )
        qr.add_data(content)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        return img

    def qr_image_to_bytes(self, img: Image.Image) -> bytes:
        """Convert QR image to bytes for download"""
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf.getvalue()

    def parse_qr_content(self, qr_string: str) -> Optional[Dict[str, Any]]:
        """Parse QR code content from string"""
        try:
            content = json.loads(qr_string)

            # Validate basic structure
            if content.get("type") != "qr_in_out":
                return None

            return content
        except json.JSONDecodeError:
            return None

    def is_qr_expired(self, qr_content: Dict[str, Any]) -> bool:
        """Check if dynamic QR code has expired"""
        if qr_content.get("qr_mode") != "dynamic":
            return False

        expires_at_str = qr_content.get("expires_at")
        if not expires_at_str:
            return True

        expires_at = datetime.fromisoformat(expires_at_str)
        current_time = datetime.now(pytz.UTC)

        return current_time > expires_at

# Global QR manager instance
qr_manager = QRManager()
```

### 5.2 Time Validator (`core/time_validator.py`)

```python
from datetime import datetime, time
from typing import Dict, Any, Tuple
import pytz

class TimeValidator:
    @staticmethod
    def parse_time_string(time_str: str) -> time:
        """Parse HH:MM string to time object"""
        hours, minutes = map(int, time_str.split(":"))
        return time(hours, minutes)

    @staticmethod
    def is_within_allowed_hours(current_time: datetime,
                                  allowed_hours: Dict[str, str]) -> bool:
        """Check if current time is within allowed hours"""
        start_time = TimeValidator.parse_time_string(allowed_hours["start_time"])
        end_time = TimeValidator.parse_time_string(allowed_hours["end_time"])

        current_time_only = current_time.time()

        # Handle overnight hours (e.g., 22:00 to 06:00)
        if start_time <= end_time:
            return start_time <= current_time_only <= end_time
        else:
            return current_time_only >= start_time or current_time_only <= end_time

    @staticmethod
    def check_checkpoint_access(checkpoint: Dict[str, Any],
                                  guest: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Check if guest can access checkpoint at current time

        Returns:
            (allowed, message)
        """
        # Get current time in guest's timezone
        guest_tz = pytz.timezone(guest["timezone"])
        current_time = datetime.now(guest_tz)

        # Check checkpoint allowed hours
        if not TimeValidator.is_within_allowed_hours(
            current_time,
            checkpoint["allowed_hours"]
        ):
            return False, f"체크포인트 허용 시간이 아닙니다 ({checkpoint['allowed_hours']['start_time']} - {checkpoint['allowed_hours']['end_time']})"

        # Check guest allowed hours (if set)
        if guest.get("allowed_hours"):
            if not TimeValidator.is_within_allowed_hours(
                current_time,
                guest["allowed_hours"]
            ):
                return False, f"귀하의 허용 시간이 아닙니다 ({guest['allowed_hours']['start_time']} - {guest['allowed_hours']['end_time']})"

        return True, "접근 허용"

    @staticmethod
    def format_countdown(seconds: float) -> str:
        """Format seconds to MM:SS string"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

# Global time validator instance
time_validator = TimeValidator()
```

### 5.3 Authentication Module (`core/auth.py`)

```python
import hashlib
import secrets

class AuthManager:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256"""
        # In production, use bcrypt or argon2
        # This is simplified for local use
        salt = "qr_in_out_salt"  # In production, use random salt per password
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return AuthManager.hash_password(password) == password_hash

    @staticmethod
    def generate_guest_token() -> str:
        """Generate a random token for guest session"""
        return secrets.token_urlsafe(32)

# Global auth manager instance
auth_manager = AuthManager()
```

---

## 6. Security Requirements

### 6.1 Password Security
- [ ] Admin passwords hashed using SHA-256 minimum (bcrypt recommended)
- [ ] Minimum 4-character password length
- [ ] No password stored in plaintext

### 6.2 QR Code Security (Dynamic)
- [ ] HMAC-SHA256 signature for tampering detection
- [ ] 30-minute expiration window
- [ ] Expired QR codes rejected with clear message
- [ ] Secret key stored securely (environment variable)

### 6.3 Data Security
- [ ] Local file storage with restricted permissions (600)
- [ ] No sensitive data in QR codes (only IDs)
- [ ] Activity logs preserve privacy (no PII in QR content)

### 6.4 Session Security (Streamlit)
- [ ] Session state cleared on logout
- [ ] No credentials stored in session state
- [ ] Host page requires authentication

---

## 7. Performance Requirements

### 7.1 QR Generation
- Target: < 100ms per QR code
- Constraint: Streamlit's single-threaded nature

### 7.2 QR Scanning
- Target: < 2 seconds from camera capture to result
- Dependency: pyzbar decoding speed

### 7.3 Data Loading
- JSON: < 50ms for < 1000 records
- SQLite: < 100ms with proper indexing

### 7.4 Page Load Time
- Target: < 2 seconds for initial load
- Streamlit overhead: ~1-2 seconds typical

---

## 8. Testing Strategy

### 8.1 Unit Tests

```python
# tests/test_qr_manager.py
import pytest
from core.qr_manager import qr_manager

def test_generate_static_qr():
    content = qr_manager.generate_static_qr_content("checkpoint-123")
    parsed = qr_manager.parse_qr_content(content)

    assert parsed["type"] == "qr_in_out"
    assert parsed["checkpoint_id"] == "checkpoint-123"
    assert parsed["qr_mode"] == "static"

def test_generate_dynamic_qr():
    content = qr_manager.generate_dynamic_qr_content("checkpoint-456")
    parsed = qr_manager.parse_qr_content(content)

    assert parsed["qr_mode"] == "dynamic"
    assert "signature" in parsed
    assert "expires_at" in parsed

def test_verify_signature():
    content = qr_manager.generate_dynamic_qr_content("checkpoint-789")
    parsed = qr_manager.parse_qr_content(content)

    assert qr_manager.verify_signature(parsed) == True

    # Tamper with content
    parsed["checkpoint_id"] = "modified"
    assert qr_manager.verify_signature(parsed) == False

def test_qr_expiration():
    from datetime import datetime, timedelta
    import pytz

    # Generate QR that expired 1 hour ago
    past_time = datetime.now(pytz.UTC) - timedelta(hours=1)
    content = qr_manager.generate_dynamic_qr_content("checkpoint-999", past_time)
    parsed = qr_manager.parse_qr_content(content)

    assert qr_manager.is_qr_expired(parsed) == True
```

```python
# tests/test_time_validator.py
import pytest
from core.time_validator import time_validator
from datetime import datetime, time
import pytz

def test_parse_time_string():
    t = time_validator.parse_time_string("14:30")
    assert t == time(14, 30)

def test_is_within_allowed_hours():
    allowed_hours = {"start_time": "09:00", "end_time": "18:00"}

    # Within hours
    current = datetime(2026, 2, 5, 12, 0, 0, tzinfo=pytz.UTC)
    assert time_validator.is_within_allowed_hours(current, allowed_hours) == True

    # Outside hours
    current = datetime(2026, 2, 5, 20, 0, 0, tzinfo=pytz.UTC)
    assert time_validator.is_within_allowed_hours(current, allowed_hours) == False

def test_overnight_hours():
    allowed_hours = {"start_time": "22:00", "end_time": "06:00"}

    # Late night (within)
    current = datetime(2026, 2, 5, 23, 0, 0, tzinfo=pytz.UTC)
    assert time_validator.is_within_allowed_hours(current, allowed_hours) == True

    # Early morning (within)
    current = datetime(2026, 2, 5, 3, 0, 0, tzinfo=pytz.UTC)
    assert time_validator.is_within_allowed_hours(current, allowed_hours) == True

    # Daytime (outside)
    current = datetime(2026, 2, 5, 12, 0, 0, tzinfo=pytz.UTC)
    assert time_validator.is_within_allowed_hours(current, allowed_hours) == False

def test_check_checkpoint_access():
    checkpoint = {
        "id": "cp1",
        "allowed_hours": {"start_time": "09:00", "end_time": "18:00"}
    }

    guest = {
        "id": "guest1",
        "timezone": "Asia/Seoul",
        "allowed_hours": None  # No guest-specific hours
    }

    # Mock current time (would need proper mocking in real tests)
    # This is a simplified example
    allowed, message = time_validator.check_checkpoint_access(checkpoint, guest)
    # assert allowed == True or False depending on current time
```

### 8.2 Integration Tests

```python
# tests/test_integration.py
import pytest
from core.storage import storage
from core.models import Checkpoint, Guest, AllowedHours
import os
import tempfile

@pytest.fixture
def temp_storage():
    """Create temporary storage for testing"""
    temp_dir = tempfile.mkdtemp()
    test_storage = JSONStorage(temp_dir)
    yield test_storage
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

def test_create_and_retrieve_checkpoint(temp_storage):
    checkpoint = Checkpoint.create_new(
        name="Test Checkpoint",
        location="Test Location",
        allowed_hours=AllowedHours(start_time="09:00", end_time="18:00"),
        qr_mode="static",
        admin_password="test123",
        allowed_guests=[]
    )

    temp_storage.add("checkpoints", checkpoint.to_dict())

    retrieved = temp_storage.get_by_id("checkpoints", checkpoint.id)
    assert retrieved["name"] == "Test Checkpoint"

def test_activity_log_creation(temp_storage):
    log = ActivityLog.create_new(
        checkpoint_id="cp1",
        guest_id="guest1",
        action="check_in",
        qr_code_used="qr_content_here",
        status="success"
    )

    temp_storage.add("activity_logs", log.to_dict())

    logs = temp_storage.load("activity_logs")
    assert len(logs) == 1
    assert logs[0]["action"] == "check_in"
```

### 8.3 Manual Testing Checklist

#### Admin Page
- [ ] Create checkpoint with all fields
- [ ] Edit existing checkpoint
- [ ] Delete checkpoint (with confirmation)
- [ ] Create guest with timezone
- [ ] Create guest with custom allowed hours
- [ ] Edit guest information
- [ ] Delete guest
- [ ] View logs by checkpoint
- [ ] View logs by guest
- [ ] Export logs to CSV
- [ ] View statistics dashboard

#### Host Page
- [ ] Select checkpoint and authenticate
- [ ] Display static QR code
- [ ] Download static QR as PNG
- [ ] Display dynamic QR code
- [ ] Observe 30-minute countdown
- [ ] Verify QR auto-refresh at expiration
- [ ] Test outside allowed hours (QR hidden)
- [ ] Lock screen with password
- [ ] Unlock screen with password

#### Guest Page
- [ ] Enter guest information and authenticate
- [ ] Failed authentication for unregistered guest
- [ ] Scan static QR code (check-in)
- [ ] Scan dynamic QR code (check-in)
- [ ] Scan for check-out
- [ ] Attempt check-out without check-in (should fail)
- [ ] Scan expired dynamic QR (should fail)
- [ ] Scan outside checkpoint hours (should fail)
- [ ] Scan outside guest hours (should fail)
- [ ] Scan unauthorized checkpoint (should fail)
- [ ] View personal activity logs
- [ ] Export personal logs to CSV

---

## 9. Deployment Plan

### 9.1 Local Installation

**Requirements**:
```
Python 3.10+
pip
```

**Installation Steps**:
```bash
# Clone repository (or unzip)
cd qr_in_out

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run application
streamlit run app.py
```

**requirements.txt**:
```
streamlit>=1.30.0
streamlit-camera-input>=0.1.0
qrcode[pil]>=7.4.0
pillow>=10.0.0
pyzbar>=0.1.9
pytz>=2023.3
pandas>=2.0.0
```

### 9.2 Configuration

**config/settings.py**:
```python
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Data directory
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Secret key for QR signing (change this!)
SECRET_KEY = os.getenv("QR_SECRET_KEY", "change-me-in-production")

# QR code settings
QR_REFRESH_INTERVAL = 1800  # 30 minutes

# Default timezone
DEFAULT_TIMEZONE = "Asia/Seoul"

# Streamlit settings
PAGE_TITLE = "QR In/Out"
PAGE_ICON = "🔲"
LAYOUT = "wide"
```

**.streamlit/config.toml**:
```toml
[theme]
primaryColor = "#4CAF50"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
port = 8501
headless = false

[browser]
gatherUsageStats = false
```

### 9.3 First-time Setup

**app.py** (Main entry point):
```python
import streamlit as st
from config.settings import PAGE_TITLE, PAGE_ICON, LAYOUT
from core.storage import storage

# Page configuration
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded"
)

# Initialize data files if they don't exist
def initialize_data():
    for entity_type in ["checkpoints", "guests", "activity_logs"]:
        if not storage._get_file_path(entity_type).exists():
            storage.save(entity_type, [])

initialize_data()

# Landing page
st.title("🔲 QR In/Out")
st.subheader("QR 코드 기반 체크포인트 관리 시스템")

st.markdown("""
## 시작하기

왼쪽 사이드바에서 페이지를 선택하세요:

- **👤 Admin**: 체크포인트 및 방문객 관리
- **🖥️ Host**: QR 코드 디스플레이
- **👋 Guest**: QR 코드 스캔 및 체크인/아웃

---

### 빠른 가이드

1. **관리자**: Admin 페이지에서 체크포인트와 방문객을 등록하세요
2. **호스트**: Host 페이지에서 체크포인트를 선택하고 QR 코드를 표시하세요
3. **방문객**: Guest 페이지에서 본인 정보를 입력하고 QR 코드를 스캔하세요
""")

# System stats
col1, col2, col3 = st.columns(3)

with col1:
    checkpoints = storage.load("checkpoints")
    st.metric("체크포인트", len(checkpoints))

with col2:
    guests = storage.load("guests")
    st.metric("등록된 방문객", len(guests))

with col3:
    logs = storage.load("activity_logs")
    st.metric("총 활동 기록", len(logs))
```

---

## 10. Future Enhancements (Out of V1 Scope)

### 10.1 Phase 2 Features
- [ ] Cloud-based data synchronization (optional)
- [ ] Export to multiple formats (PDF, Excel)
- [ ] Email notifications for check-ins
- [ ] Advanced analytics dashboard
- [ ] Multi-language support (i18n)

### 10.2 Phase 3 Features
- [ ] REST API for external integrations
- [ ] Webhook support
- [ ] Mobile native apps (iOS/Android)
- [ ] Geolocation validation
- [ ] Biometric authentication

---

## 11. Known Limitations

### 11.1 Streamlit Limitations
- **Page Refresh**: Streamlit reruns on every interaction
- **Concurrent Access**: File locking may cause issues with many simultaneous users
- **Real-time Updates**: No push notifications; manual refresh required

### 11.2 Camera Access
- **HTTPS Required**: Camera access requires HTTPS in browsers (okay for localhost)
- **Browser Support**: Not all mobile browsers support camera input
- **Fallback**: File upload available as alternative

### 11.3 Data Storage
- **Scalability**: JSON files not ideal for > 10,000 records
- **Backup**: Manual backup required (no automatic cloud sync)
- **Concurrency**: File-based storage may have race conditions

### 11.4 Workarounds
- For production use, consider migrating to SQLite for better performance
- For multi-user scenarios, implement file locking or use database
- For real-time features, consider WebSocket-based frameworks

---

## 12. Appendices

### 12.1 Glossary

| 용어 | 설명 |
|------|------|
| 체크포인트 | QR 코드가 설치된 출입 지점 |
| 호스트 | QR 코드를 표시하는 디바이스 운영자 |
| 게스트 | QR 코드를 스캔하는 방문객 |
| Static QR | 변경되지 않는 고정형 QR 코드 |
| Dynamic QR | 30분마다 갱신되는 동적 QR 코드 |
| Allowed Hours | 체크인/체크아웃이 허용되는 시간대 |
| Activity Log | 체크인/체크아웃 활동 기록 |
| HMAC | Hash-based Message Authentication Code (위변조 방지) |

### 12.2 File Structure Reference

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
│   ├── models.py                  # Data models (Checkpoint, Guest, ActivityLog)
│   ├── storage.py                 # Storage layer (JSONStorage, SQLiteStorage)
│   ├── qr_manager.py              # QR generation and validation
│   ├── time_validator.py          # Time-based access control
│   └── auth.py                    # Password management
├── pages/
│   ├── 1_👤_Admin.py              # Admin page
│   ├── 2_🖥️_Host.py               # Host page
│   └── 3_👋_Guest.py              # Guest page
├── utils/
│   ├── __init__.py
│   └── helpers.py                 # Helper functions
├── data/                          # Data directory (gitignored)
│   ├── checkpoints.json
│   ├── guests.json
│   └── activity_logs.json
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_storage.py
│   ├── test_qr_manager.py
│   ├── test_time_validator.py
│   └── test_integration.py
└── docs/                          # Private documentation
    ├── planning-artifacts/
    │   ├── product-brief-qr-in-out.md
    │   ├── product-brief-qr-in-out-en.md
    │   └── PRD-qr-in-out.md (this file)
    └── images/                    # Screenshots, diagrams
```

### 12.3 Environment Variables

```bash
# .env file (optional)
QR_SECRET_KEY=your-secret-key-here
DEFAULT_TIMEZONE=Asia/Seoul
DATA_DIR=./data
```

### 12.4 Git Repository Structure

```bash
# .gitignore
venv/
__pycache__/
*.pyc
.env
data/
.streamlit/secrets.toml
*.db
```

---

## Document Metadata

- **문서 타입**: Product Requirements Document (PRD)
- **프로젝트**: QR In/Out
- **버전**: 1.0
- **작성자**: Jake
- **작성일**: 2026-02-05
- **언어**: 한국어
- **용도**: 개인 개발용 상세 기능 명세
- **상태**: Draft
- **다음 단계**: 구현 시작 (Implementation)
- **관련 문서**:
  - Product Brief (한글): `product-brief-qr-in-out.md`
  - Product Brief (영문): `product-brief-qr-in-out-en.md`

---

**End of PRD**
