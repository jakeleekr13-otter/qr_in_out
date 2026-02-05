---
document_type: "Product Requirements Document - Guest Page"
project: "QR In/Out"
version: "1.1"
author: "Jake"
date: "2026-02-05"
status: "Active"
language: "Korean"
purpose: "게스트 페이지 상세 기능 명세"
parent_doc: "PRD-Overview.md"
related_docs:
  - "PRD-Admin.md"
  - "PRD-Host.md"
---

# PRD: Guest Page (게스트 페이지)

> **참고**: 이 문서는 게스트 페이지의 상세 명세입니다. 시스템 개요와 공통 모듈은 [PRD-Overview.md](PRD-Overview.md)를 참조하세요.

## Table of Contents
1. [Page Overview](#page-overview)
2. [Features](#features)
3. [UI Specifications](#ui-specifications)
4. [User Stories](#user-stories)
5. [Testing](#testing)

---

## 1. Page Overview

### 1.1 Purpose
방문객이 본인 정보를 입력하여 인증하고, QR 코드를 스캔하여 체크인/체크아웃을 수행하며, 본인의 방문 기록을 조회하는 페이지입니다.

### 1.2 Access
- **URL**: `/Guest` (Streamlit multi-page)
- **인증**: 이름 + 이메일
- **아이콘**: 👋

### 1.3 Main Functions

| 기능 | 설명 | 우선순위 |
|------|------|----------|
| 방문자 인증 | 이름 + 이메일로 인증 | 🔴 필수 |
| QR 스캔 (카메라) | 실시간 카메라로 QR 스캔 | 🔴 필수 |
| QR 스캔 (업로드) | 이미지 파일 업로드로 스캔 | 🟡 중요 |
| 성공/실패 피드백 | 즉시 결과 표시 | 🔴 필수 |
| 방문 기록 조회 | 본인의 체크인/아웃 기록 | 🔴 필수 |
| CSV 다운로드 | 본인 기록 다운로드 | 🟢 선택 |

---

## 2. Features

### 2.1 방문자 인증

**User Story**:
```
As a guest,
I want to authenticate with my name and email,
So that I can scan QR codes at authorized checkpoints.
```

**UI Layout (Unauthenticated)**:
```
┌─────────────────────────────────────────┐
│ 👋 게스트 페이지 - 체크인/체크아웃     │
├─────────────────────────────────────────┤
│                                         │
│ 📋 방문자 정보 입력                     │
│                                         │
│ ℹ️ 관리자에게 등록된 이름과 이메일을    │
│    정확히 입력하세요                    │
│                                         │
│ 이름   * : [홍길동__________]           │
│ 이메일 * : [hong@example.com_______]    │
│                                         │
│ [      확인      ]                      │
│                                         │
└─────────────────────────────────────────┘
```

**Streamlit Code**:
```python
st.title("👋 게스트 페이지")
st.subheader("체크인/체크아웃")

# Session state for guest authentication
if "guest_authenticated" not in st.session_state:
    st.session_state.guest_authenticated = False
    st.session_state.current_guest = None

if not st.session_state.guest_authenticated:
    st.write("### 📋 방문자 정보 입력")
    st.info("관리자에게 등록된 **이름**과 **이메일**을 정확히 입력하세요.")

    with st.form("guest_auth_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("이름 *", placeholder="홍길동")
        with col2:
            email = st.text_input("이메일 *", placeholder="hong@example.com")

        submitted = st.form_submit_button("확인", type="primary")

        if submitted:
            if not name or not email:
                st.error("❌ 이름과 이메일을 모두 입력하세요")
            else:
                # Verify guest identity
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
    guests = storage.load("guests")

    name_lower = name.lower().strip()
    email_lower = email.lower().strip()

    for guest in guests:
        if (guest["name"].lower().strip() == name_lower and
            guest["email"].lower().strip() == email_lower):
            return guest

    return None
```

**Acceptance Criteria**:
- [ ] 이름과 이메일 필수 입력
- [ ] Case-insensitive 검증
- [ ] 등록된 방문객만 통과
- [ ] 삭제된 방문객 차단
- [ ] 인증 성공 시 QR 스캔 화면으로 전환
- [ ] 인증 실패 시 명확한 에러 메시지

---

### 2.2 QR 코드 스캔 (카메라)

**User Story**:
```
As an authenticated guest,
I want to scan a QR code with my camera,
So that I can check in or check out at a checkpoint.
```

**UI Layout (Authenticated)**:
```
┌─────────────────────────────────────────┐
│ 👋 홍길동님                             │
│ 🌍 타임존: Asia/Seoul                   │
│ ⏰ 2026-02-05 14:30:45 (동기화됨)       │
├─────────────────────────────────────────┤
│                                         │
│ 활동 선택: (●) 체크인  ( ) 체크아웃    │
│                                         │
│ 📸 QR 코드 스캔                         │
│                                         │
│ ┌─────────────────────────────────┐    │
│ │                                 │    │
│ │      [카메라 미리보기]          │    │
│ │                                 │    │
│ └─────────────────────────────────┘    │
│                                         │
│ [📷 QR 코드 스캔]                       │
│                                         │
│ --- 또는 ---                            │
│                                         │
│ [📁 이미지 파일 업로드]                 │
│                                         │
│ [🚪 로그아웃]                           │
│                                         │
└─────────────────────────────────────────┘
```

**Streamlit Code**:
```python
if st.session_state.guest_authenticated:
    guest = st.session_state.current_guest

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header(f"👋 {guest['name']}님")
        st.caption(f"🌍 타임존: {guest['timezone']}")

        # Get current time
        from core.time_service import time_service
        current_time, is_synced = time_service.get_current_time(guest["timezone"])
        time_service.show_time_sync_status(is_synced, current_time)

    with col2:
        if st.button("🚪 로그아웃"):
            st.session_state.guest_authenticated = False
            st.session_state.current_guest = None
            st.rerun()

    st.divider()

    # Action selector
    action = st.radio(
        "활동 선택",
        options=["체크인", "체크아웃"],
        horizontal=True,
        key="action_select"
    )

    st.write("### 📸 QR 코드 스캔")

    # Camera input for QR scanning
    from streamlit_camera_input import camera_input

    camera_image = camera_input("카메라로 QR 코드를 스캔하세요")

    if camera_image:
        # Process QR code
        process_qr_scan(camera_image, guest, action, current_time, is_synced)

    st.write("--- **또는** ---")

    # File upload alternative
    uploaded_file = st.file_uploader(
        "QR 코드 이미지 업로드",
        type=["png", "jpg", "jpeg"],
        help="카메라가 작동하지 않을 경우 스크린샷을 업로드할 수 있습니다"
    )

    if uploaded_file:
        process_qr_scan(uploaded_file, guest, action, current_time, is_synced)

def process_qr_scan(image_source, guest, action, current_time, is_time_synced):
    """Process QR code scan from camera or file"""
    from PIL import Image
    from pyzbar.pyzbar import decode
    from core.qr_manager import qr_manager
    from core.storage import storage

    # Load image
    image = Image.open(image_source)

    # Decode QR code
    decoded_objects = decode(image)

    if not decoded_objects:
        st.error("❌ QR 코드를 인식할 수 없습니다. 다시 시도하세요.")
        return

    # Get QR content
    qr_content = decoded_objects[0].data.decode('utf-8')
    st.success("✅ QR 코드 인식 성공!")

    # Parse QR content
    qr_data = qr_manager.parse_qr_content(qr_content)

    if not qr_data:
        st.error("❌ 잘못된 QR 코드 형식입니다")
        return

    # Validate QR code
    action_type = "check_in" if action == "체크인" else "check_out"
    validation_result = validate_qr_scan(
        qr_data=qr_data,
        guest=guest,
        action=action_type,
        current_time=current_time,
        is_time_synced=is_time_synced
    )

    if validation_result["valid"]:
        # Record activity (success)
        activity_log = ActivityLog.create_new(
            checkpoint_id=qr_data["checkpoint_id"],
            guest_id=guest["id"],
            action=action_type,
            qr_code_used=qr_content,
            status="success",
            metadata={
                "time_synced": is_time_synced,
                "qr_sequence": qr_data.get("sequence")
            }
        )

        storage.add("activity_logs", activity_log.to_dict())

        # Show success message
        checkpoint = storage.get_by_id("checkpoints", qr_data["checkpoint_id"])
        st.success(f"✅ {action} 성공!")
        st.balloons()

        # Show details
        with st.container():
            st.info(f"""
            **체크포인트**: {checkpoint['name']}
            **위치**: {checkpoint['location']}
            **시간**: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
            """)

    else:
        # Record activity (failure)
        activity_log = ActivityLog.create_new(
            checkpoint_id=qr_data.get("checkpoint_id"),
            guest_id=guest["id"],
            action=action_type,
            qr_code_used=qr_content,
            status="failure",
            failure_reason=validation_result['reason'],
            metadata={
                "time_synced": is_time_synced
            }
        )

        storage.add("activity_logs", activity_log.to_dict())

        # Show failure message
        st.error(f"❌ {action} 실패: {validation_result['reason']}")

def validate_qr_scan(qr_data, guest, action, current_time, is_time_synced):
    """
    Comprehensive QR validation

    Returns: {"valid": bool, "reason": str or None}
    """
    from core.qr_manager import qr_manager
    from core.time_validator import time_validator
    from core.storage import storage

    # 1. Check checkpoint exists
    checkpoint = storage.get_by_id("checkpoints", qr_data.get("checkpoint_id"))
    if not checkpoint:
        return {"valid": False, "reason": "존재하지 않는 체크포인트입니다"}

    # 2. Check if checkpoint is deleted
    if checkpoint.get("deleted_at"):
        return {"valid": False, "reason": "삭제된 체크포인트입니다"}

    # 3. Verify HMAC signature (for dynamic QR)
    if qr_data.get("qr_mode") == "dynamic":
        if not qr_manager.verify_signature(qr_data):
            return {"valid": False, "reason": "QR 코드 서명이 유효하지 않습니다 (위조 가능성)"}

    # 4. Check sequence number (for dynamic QR)
    if qr_data.get("qr_mode") == "dynamic":
        qr_sequence = qr_data.get("sequence", 0)
        current_sequence = checkpoint.get("current_qr_sequence", 0)

        if qr_sequence < current_sequence:
            return {"valid": False, "reason": f"만료된 QR 코드입니다 (이전 버전). 최신 QR 코드를 스캔하세요."}

    # 5. Check time expiration (for dynamic QR)
    if qr_data.get("qr_mode") == "dynamic":
        is_valid, reason = qr_manager.validate_dynamic_qr(
            qr_data, checkpoint, current_time, is_time_synced
        )
        if not is_valid:
            return {"valid": False, "reason": reason}

    # 6. Check guest authorization
    if guest["id"] not in checkpoint["allowed_guests"]:
        return {"valid": False, "reason": "이 체크포인트에 대한 권한이 없습니다"}

    # 7. Check checkpoint allowed hours
    is_allowed, message = time_validator.is_within_allowed_hours(
        current_time, checkpoint["allowed_hours"]
    )
    if not is_allowed:
        return {"valid": False, "reason": f"체크포인트 허용 시간이 아닙니다 ({checkpoint['allowed_hours']['start_time']} - {checkpoint['allowed_hours']['end_time']})"}

    # 8. Check guest allowed hours (if set)
    if guest.get("allowed_hours"):
        is_allowed, message = time_validator.is_within_allowed_hours(
            current_time, guest["allowed_hours"]
        )
        if not is_allowed:
            return {"valid": False, "reason": f"귀하의 허용 시간이 아닙니다 ({guest['allowed_hours']['start_time']} - {guest['allowed_hours']['end_time']})"}

    # 9. Check action consistency (can't check out without checking in)
    if action == "check_out":
        last_activity = get_last_activity(guest["id"], checkpoint["id"])
        if not last_activity or last_activity["action"] == "check_out":
            return {"valid": False, "reason": "체크인하지 않았습니다. 먼저 체크인하세요."}

    # All checks passed
    return {"valid": True, "reason": None}

def get_last_activity(guest_id: str, checkpoint_id: str) -> Optional[Dict]:
    """Get the last activity for a guest at a checkpoint"""
    logs = storage.load("activity_logs")
    filtered = [
        log for log in logs
        if log["guest_id"] == guest_id and log["checkpoint_id"] == checkpoint_id and log["status"] == "success"
    ]

    if not filtered:
        return None

    # Sort by timestamp descending
    filtered.sort(key=lambda x: x["timestamp"], reverse=True)
    return filtered[0]
```

**Acceptance Criteria**:
- [ ] 카메라 접근 권한 요청
- [ ] 실시간 QR 디코딩 (pyzbar)
- [ ] 파일 업로드 대체 방법
- [ ] 9단계 검증 로직 실행
- [ ] 성공 시 balloons 애니메이션
- [ ] 실패 시 명확한 사유 표시
- [ ] 모든 시도 기록 (성공/실패)
- [ ] 체크아웃 시 체크인 여부 확인

---

### 2.3 방문 기록 조회

**User Story**:
```
As an authenticated guest,
I want to view my visit history,
So that I can track where and when I checked in/out.
```

**UI Layout**:
```
┌─────────────────────────────────────────┐
│ 📊 내 활동 기록                         │
├─────────────────────────────────────────┤
│ 기간: [2026-01-29] ~ [2026-02-05]       │
│                                         │
│ 총 12개의 기록                          │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ 본관 입구                           │ │
│ │ 서울시 강남구...                    │ │
│ │ 2026-02-05 10:30:00                 │ │
│ │                          ✅ IN      │ │
│ ├─────────────────────────────────────┤ │
│ │ 본관 입구                           │ │
│ │ 서울시 강남구...                    │ │
│ │ 2026-02-05 12:00:00                 │ │
│ │                          🚪 OUT     │ │
│ ├─────────────────────────────────────┤ │
│ │ 2층 회의실                          │ │
│ │ 서울시 강남구...                    │ │
│ │ 2026-02-05 14:30:00                 │ │
│ │                          ❌ 실패    │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [📥 내 기록 다운로드 (CSV)]             │
└─────────────────────────────────────────┘
```

**Streamlit Code**:
```python
st.write("### 📊 내 활동 기록")

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
    st.write(f"총 **{len(logs)}개**의 기록")

    # Display as timeline
    for log in sorted(logs, key=lambda x: x["timestamp"], reverse=True):
        checkpoint = storage.get_by_id("checkpoints", log["checkpoint_id"])

        with st.container():
            col1, col2 = st.columns([4, 1])

            with col1:
                if checkpoint:
                    st.write(f"**{checkpoint['name']}**")
                    if checkpoint.get("location"):
                        st.caption(checkpoint['location'])
                    if checkpoint.get("deleted_at"):
                        st.caption("(삭제된 체크포인트)")
                else:
                    st.write("**알 수 없는 체크포인트**")

                st.caption(log["timestamp"])

            with col2:
                if log["status"] == "success":
                    if log["action"] == "check_in":
                        st.success("✅ IN")
                    else:
                        st.info("🚪 OUT")
                else:
                    st.error("❌ 실패")
                    if log.get("failure_reason"):
                        st.caption(log["failure_reason"])

            st.divider()

    # Export personal logs
    if st.button("📥 내 기록 다운로드 (CSV)"):
        df = pd.DataFrame(logs)

        # Enrich with checkpoint names
        df["checkpoint_name"] = df["checkpoint_id"].apply(
            lambda x: get_checkpoint_name(x) if storage.get_by_id("checkpoints", x) else "알 수 없음"
        )

        # Select columns
        df = df[["timestamp", "checkpoint_name", "action", "status", "failure_reason"]]

        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"my_activity_{guest['name']}_{date.today()}.csv",
            mime="text/csv"
        )
else:
    st.info("선택한 기간에 기록이 없습니다.")
```

**Acceptance Criteria**:
- [ ] 본인의 기록만 조회 가능
- [ ] 날짜 범위 필터링
- [ ] 시간순 정렬 (최신순)
- [ ] 체크포인트 정보와 함께 표시
- [ ] 삭제된 체크포인트 표시
- [ ] 성공/실패 상태 표시
- [ ] 실패 사유 표시
- [ ] CSV 다운로드 기능

---

## 3. UI Specifications

### 3.1 Mobile-First Design

**목표**: 모바일 디바이스에서 사용하기 쉽게

**Responsive Layout**:
- 큰 터치 버튼 (최소 44x44px)
- 명확한 텍스트 (최소 16px)
- 충분한 여백

**Streamlit CSS**:
```python
st.markdown("""
<style>
    /* Mobile-friendly buttons */
    .stButton > button {
        width: 100%;
        height: 60px;
        font-size: 1.2rem;
    }

    /* Large input fields */
    .stTextInput > div > input {
        font-size: 1.2rem;
        padding: 15px;
    }

    /* Camera preview */
    .stCameraInput {
        border: 3px solid #4CAF50;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)
```

### 3.2 Color Coding

| 상태 | 색상 | 아이콘 |
|------|------|--------|
| 체크인 성공 | Green | ✅ IN |
| 체크아웃 성공 | Blue | 🚪 OUT |
| 실패 | Red | ❌ 실패 |

---

## 4. User Stories & Acceptance Criteria

### Story 1: 방문자 인증
**As a** guest
**I want to** authenticate with name and email
**So that** I can access QR scanning features

**Acceptance Criteria**:
- [ ] 이름 + 이메일 입력
- [ ] Case-insensitive 검증
- [ ] 등록된 방문객만 통과
- [ ] 삭제된 방문객 차단

### Story 2: QR 스캔
**As an** authenticated guest
**I want to** scan QR codes with camera
**So that** I can check in/out at checkpoints

**Acceptance Criteria**:
- [ ] 카메라 접근
- [ ] 실시간 QR 디코딩
- [ ] 파일 업로드 대체
- [ ] 9단계 검증
- [ ] 성공/실패 피드백
- [ ] 모든 시도 기록

### Story 3: 방문 기록 조회
**As an** authenticated guest
**I want to** view my visit history
**So that** I can track my activities

**Acceptance Criteria**:
- [ ] 본인 기록만 조회
- [ ] 날짜 필터링
- [ ] 시간순 정렬
- [ ] CSV 다운로드

---

## 5. Testing

### 5.1 Manual Testing Checklist

#### 인증
- [ ] 올바른 이름 + 이메일로 인증 성공
- [ ] 잘못된 정보로 인증 실패
- [ ] 삭제된 방문객 차단
- [ ] Case-insensitive 동작

#### QR 스캔
- [ ] 카메라로 Static QR 스캔 성공
- [ ] 카메라로 Dynamic QR 스캔 성공
- [ ] 파일 업로드로 QR 스캔 성공
- [ ] 만료된 Dynamic QR 거부
- [ ] 허용 시간 외 거부
- [ ] 권한 없는 체크포인트 거부
- [ ] 체크아웃 전 체크인 확인

#### 방문 기록
- [ ] 본인 기록 조회
- [ ] 날짜 필터링
- [ ] 삭제된 체크포인트 표시
- [ ] CSV 다운로드

#### Time Sync
- [ ] Time API 성공 시 동기화 메시지
- [ ] Time API 실패 시 경고
- [ ] 시간 조작 감지

---

## Document Metadata

- **문서 타입**: PRD - Guest Page
- **프로젝트**: QR In/Out
- **버전**: 1.1
- **작성자**: Jake
- **작성일**: 2026-02-05
- **언어**: 한국어
- **상태**: Active
- **관련 문서**:
  - [PRD-Overview.md](PRD-Overview.md) - 시스템 개요
  - [PRD-Admin.md](PRD-Admin.md) - 관리자 페이지
  - [PRD-Host.md](PRD-Host.md) - 호스트 페이지

---

**End of PRD - Guest Page**
