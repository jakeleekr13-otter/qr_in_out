---
document_type: "Product Requirements Document - Guest Page"
project: "QR In/Out"
version: "1.2"
author: "Jake"
date: "2026-02-08"
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
| 성공/실패 피드백 | 즉시 결과 표시 + 사운드 | 🔴 필수 |
| 연결 상태 표시 | 서버/Time API 연결 상태 배지 | 🔴 필수 |
| 정보 기억하기 | 이름/이메일 브라우저 저장 | 🟡 중요 |
| 빠른 재스캔 모드 | 연속 스캔 (공용 기기용) | 🟢 선택 |
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
│ 👋 홍길동님                  [🚪 로그아웃]│
│ 🌍 타임존: Asia/Seoul                   │
├─────────────────────────────────────────┤
│ 📶 ✅ 연결 정상 (45ms)                  │
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

    with col2:
        if st.button("🚪 로그아웃"):
            st.session_state.guest_authenticated = False
            st.session_state.current_guest = None
            st.rerun()

    st.divider()

    # Connection status
    from core.connection_health import ConnectionHealthCheck
    status = ConnectionHealthCheck.get_connection_status()

    if status.server_connected and status.time_api_connected:
        latency_text = f" ({status.latency_ms}ms)" if status.latency_ms else ""
        st.success(f"📶 ✅ 연결 정상{latency_text}")
    elif status.server_connected and not status.time_api_connected:
        st.warning("📶 ⚠️ 시간 동기화 불가 - 로컬 시간 사용 중")
    else:
        st.error("📶 ❌ 서버 연결 끊김 - 네트워크를 확인하세요")

    # Get current time
    from core.time_service import time_service
    current_time, is_synced = time_service.get_current_time(guest["timezone"])
    time_service.show_time_sync_status(is_synced, current_time)

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

    # 3. Verify HMAC signature (모든 QR 공통)
    if not qr_manager.verify_signature(qr_data):
        return {"valid": False, "reason": "QR 코드 서명이 유효하지 않습니다 (위조 가능성)"}

    # 4. Check sequence number (모든 QR 공통 - 구버전 무효화용)
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

### 2.3 사운드 피드백

**User Story**:
```
As a guest,
I want to hear a sound when I scan successfully or fail,
So that I get immediate audio feedback without looking at the screen.
```

**Sound Types**:

| 상태 | 사운드 | 설명 |
|------|--------|------|
| 성공 | 🔊 success.mp3 | 밝고 짧은 성공음 (약 0.5초) |
| 실패 | 🔊 error.mp3 | 낮고 짧은 경고음 (약 0.5초) |

**Implementation**:
```python
import streamlit.components.v1 as components

def play_sound(sound_type: str):
    """
    Play sound feedback using HTML5 Audio
    sound_type: "success" or "error"
    """
    sound_files = {
        "success": "assets/sounds/success.mp3",
        "error": "assets/sounds/error.mp3"
    }

    sound_file = sound_files.get(sound_type, sound_files["error"])

    # Use HTML5 Audio for cross-browser compatibility
    components.html(f"""
        <audio autoplay>
            <source src="{sound_file}" type="audio/mpeg">
        </audio>
    """, height=0)

# Usage in QR scan result
if validation_result["valid"]:
    play_sound("success")
    st.success(f"✅ {action} 성공!")
    st.balloons()
else:
    play_sound("error")
    st.error(f"❌ {action} 실패: {validation_result['reason']}")
```

**Alternative: Web Audio API (더 안정적)**:
```python
def play_sound_v2(sound_type: str):
    """
    Play sound using Web Audio API with base64 encoded audio
    """
    import base64

    # Pre-encoded audio data (small beep sounds)
    sounds = {
        "success": "data:audio/wav;base64,UklGRl...",  # Success beep
        "error": "data:audio/wav;base64,UklGRm..."     # Error beep
    }

    components.html(f"""
        <script>
            const audio = new Audio("{sounds[sound_type]}");
            audio.play().catch(e => console.log("Audio play failed:", e));
        </script>
    """, height=0)
```

**UI Enhancement - 결과 표시 개선**:
```
스캔 성공 시:
┌─────────────────────────────────────────┐
│                                         │
│         ✅ 체크인 완료!                 │
│                                         │
│         🔊 (성공 사운드 재생)           │
│                                         │
│    체크포인트: 본관 입구                │
│    시간: 2026-02-05 14:30:45            │
│                                         │
│    ⏳ 3초 후 자동으로 초기화됩니다...   │
│                                         │
└─────────────────────────────────────────┘

스캔 실패 시:
┌─────────────────────────────────────────┐
│                                         │
│         ❌ 체크인 실패                  │
│                                         │
│         🔊 (에러 사운드 재생)           │
│                                         │
│    사유: 허용 시간이 아닙니다           │
│          (09:00 - 18:00)                │
│                                         │
│    [다시 시도]                          │
│                                         │
└─────────────────────────────────────────┘
```

**Auto-reset 기능**:
```python
import time

if validation_result["valid"]:
    play_sound("success")
    st.success(f"✅ {action} 성공!")
    st.balloons()

    # Show result details
    with st.container():
        st.info(f"체크포인트: {checkpoint['name']}")
        st.info(f"시간: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Auto-reset after 3 seconds
    st.caption("⏳ 3초 후 자동으로 초기화됩니다...")

    # Use JavaScript for non-blocking countdown
    components.html("""
        <script>
            setTimeout(() => {
                window.parent.postMessage({type: 'streamlit:rerun'}, '*');
            }, 3000);
        </script>
    """, height=0)
```

**Acceptance Criteria**:
- [ ] 성공 시 성공음 재생
- [ ] 실패 시 에러음 재생
- [ ] 브라우저 오디오 권한 요청 처리
- [ ] 오디오 재생 실패 시 graceful degradation (시각적 피드백만)
- [ ] 성공 후 3초 자동 초기화 (연속 스캔 용이)
- [ ] 사운드 on/off 토글 옵션 (선택)

---

### 2.4 정보 기억하기 (Remember Me)

**User Story**:
```
As a guest,
I want to save my name and email in the browser,
So that I don't have to enter them every time I visit.
```

**UI Layout**:
```
┌─────────────────────────────────────────┐
│ 👋 게스트 페이지 - 체크인/체크아웃     │
├─────────────────────────────────────────┤
│                                         │
│ 📋 방문자 정보 입력                     │
│                                         │
│ 이름   : [홍길동__________]  (자동완성) │
│ 이메일 : [hong@example.com__] (자동완성)│
│                                         │
│ ☑️ 이 정보 기억하기                     │
│    (이 기기에 저장됩니다)               │
│                                         │
│ [      확인      ]                      │
│                                         │
│ ─────────────────────────────────────── │
│ 💡 저장된 정보가 있습니다               │
│    홍길동 (hong@example.com)            │
│    [이 정보로 로그인] [삭제]            │
│                                         │
└─────────────────────────────────────────┘
```

**Implementation using Local Storage**:
```python
import streamlit.components.v1 as components

def get_saved_guest_info() -> dict:
    """
    Retrieve saved guest info from browser localStorage
    Returns: {"name": str, "email": str} or empty dict
    """
    # Use JavaScript to read localStorage and pass to Streamlit
    saved_info = components.html("""
        <script>
            const savedGuest = localStorage.getItem('qr_in_out_guest');
            if (savedGuest) {
                const data = JSON.parse(savedGuest);
                // Send data back to Streamlit via query params or custom event
                window.parent.postMessage({
                    type: 'saved_guest',
                    data: data
                }, '*');
            }
        </script>
    """, height=0)

    return saved_info or {}

def save_guest_info(name: str, email: str):
    """Save guest info to browser localStorage"""
    components.html(f"""
        <script>
            localStorage.setItem('qr_in_out_guest', JSON.stringify({{
                name: "{name}",
                email: "{email}",
                saved_at: new Date().toISOString()
            }}));
        </script>
    """, height=0)

def clear_saved_guest_info():
    """Clear saved guest info from localStorage"""
    components.html("""
        <script>
            localStorage.removeItem('qr_in_out_guest');
        </script>
    """, height=0)
```

**Streamlit Integration**:
```python
# Check for saved info on page load
if "checked_saved_info" not in st.session_state:
    st.session_state.checked_saved_info = False
    st.session_state.saved_guest = None

# Show saved info prompt if available
if st.session_state.saved_guest:
    saved = st.session_state.saved_guest

    st.info(f"💡 저장된 정보: **{saved['name']}** ({saved['email']})")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("이 정보로 로그인", type="primary"):
            # Auto-fill and authenticate
            guest = verify_guest_by_name_and_email(saved["name"], saved["email"])
            if guest and not guest.get("deleted_at"):
                st.session_state.guest_authenticated = True
                st.session_state.current_guest = guest
                st.success(f"✅ 환영합니다, {guest['name']}님!")
                st.rerun()
            else:
                st.error("❌ 저장된 정보로 인증할 수 없습니다. 다시 입력해주세요.")
                clear_saved_guest_info()
                st.session_state.saved_guest = None

    with col2:
        if st.button("삭제", type="secondary"):
            clear_saved_guest_info()
            st.session_state.saved_guest = None
            st.rerun()

    st.divider()

# Regular login form
with st.form("guest_auth_form"):
    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("이름 *", placeholder="홍길동")
    with col2:
        email = st.text_input("이메일 *", placeholder="hong@example.com")

    # Remember me checkbox
    remember_me = st.checkbox(
        "이 정보 기억하기",
        help="이 기기의 브라우저에 이름과 이메일을 저장합니다"
    )

    submitted = st.form_submit_button("확인", type="primary")

    if submitted:
        if not name or not email:
            st.error("❌ 이름과 이메일을 모두 입력하세요")
        else:
            guest = verify_guest_by_name_and_email(name, email)

            if guest and not guest.get("deleted_at"):
                # Save to localStorage if checkbox is checked
                if remember_me:
                    save_guest_info(name, email)

                st.session_state.guest_authenticated = True
                st.session_state.current_guest = guest
                st.success(f"✅ 환영합니다, {guest['name']}님!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ 등록되지 않은 방문객입니다.")
```

**Security Considerations**:
- localStorage에는 민감한 정보(비밀번호 등) 저장 금지
- 이름/이메일만 저장 (인증용 토큰 X)
- 사용자가 명시적으로 "기억하기" 체크해야 저장
- "삭제" 버튼으로 언제든 제거 가능
- 공용 기기에서는 사용하지 않도록 안내

**Acceptance Criteria**:
- [ ] "이 정보 기억하기" 체크박스 제공
- [ ] 체크 시 localStorage에 이름/이메일 저장
- [ ] 재방문 시 저장된 정보 표시
- [ ] "이 정보로 로그인" 원클릭 인증
- [ ] "삭제" 버튼으로 저장 정보 제거
- [ ] 저장 정보로 인증 실패 시 자동 삭제
- [ ] 공용 기기 경고 문구 표시

---

### 2.5 빠른 재스캔 모드 (Kiosk Mode)

**User Story**:
```
As a guest using a shared device,
I want to quickly scan and move on,
So that the next person can use the device immediately.
```

**Use Case**:
- 공용 태블릿/키오스크에서 여러 방문객이 연속으로 체크인
- 이벤트 입장 시 빠른 대량 체크인
- 개인정보 입력 없이 QR 스캔만으로 체크인

**UI Layout (Kiosk Mode)**:
```
┌─────────────────────────────────────────┐
│ 📸 빠른 스캔 모드                       │
│ 🏢 체크포인트: 본관 입구                │
├─────────────────────────────────────────┤
│                                         │
│ ┌─────────────────────────────────┐    │
│ │                                 │    │
│ │      [카메라 미리보기]          │    │
│ │                                 │    │
│ │   QR 코드를 카메라에 대세요     │    │
│ │                                 │    │
│ └─────────────────────────────────┘    │
│                                         │
│ 📊 오늘 스캔: 47회                      │
│                                         │
│ [🔓 일반 모드로 전환]                   │
│                                         │
└─────────────────────────────────────────┘

스캔 성공 후 (2초간 표시):
┌─────────────────────────────────────────┐
│                                         │
│         ✅ 체크인 완료!                 │
│                                         │
│         홍길동님                        │
│         14:30:45                        │
│                                         │
│         🔊 (성공 사운드)                │
│                                         │
│    [2초 후 자동으로 다음 스캔 대기]     │
│                                         │
└─────────────────────────────────────────┘
```

**Implementation**:
```python
# Kiosk mode flag
if "kiosk_mode" not in st.session_state:
    st.session_state.kiosk_mode = False
    st.session_state.kiosk_checkpoint_id = None
    st.session_state.kiosk_scan_count = 0

def enter_kiosk_mode():
    """Enter kiosk mode for continuous scanning"""
    st.title("📸 빠른 스캔 모드")

    # Checkpoint selection (first time only)
    if not st.session_state.kiosk_checkpoint_id:
        checkpoints = storage.get_active_checkpoints()
        selected_id = st.selectbox(
            "체크포인트 선택",
            options=[c["id"] for c in checkpoints],
            format_func=lambda x: get_checkpoint_name(x)
        )

        if st.button("시작", type="primary"):
            st.session_state.kiosk_checkpoint_id = selected_id
            st.rerun()
        return

    checkpoint = storage.get_by_id("checkpoints", st.session_state.kiosk_checkpoint_id)
    st.caption(f"🏢 체크포인트: **{checkpoint['name']}**")

    st.divider()

    # Continuous camera scanning
    from streamlit_camera_input import camera_input

    camera_image = camera_input(
        "QR 코드를 카메라에 대세요",
        key=f"kiosk_camera_{st.session_state.kiosk_scan_count}"
    )

    if camera_image:
        # Process scan without requiring guest login
        process_kiosk_scan(camera_image, checkpoint)

    # Stats
    st.caption(f"📊 오늘 스캔: {st.session_state.kiosk_scan_count}회")

    # Exit kiosk mode
    if st.button("🔓 일반 모드로 전환"):
        st.session_state.kiosk_mode = False
        st.session_state.kiosk_checkpoint_id = None
        st.rerun()

def process_kiosk_scan(image, checkpoint):
    """Process QR scan in kiosk mode - extracts guest from QR"""
    from PIL import Image
    from pyzbar.pyzbar import decode
    from core.qr_manager import qr_manager

    image = Image.open(image)
    decoded_objects = decode(image)

    if not decoded_objects:
        play_sound("error")
        st.error("❌ QR 코드를 인식할 수 없습니다")
        return

    qr_content = decoded_objects[0].data.decode('utf-8')
    qr_data = qr_manager.parse_qr_content(qr_content)

    if not qr_data:
        play_sound("error")
        st.error("❌ 잘못된 QR 코드입니다")
        return

    # In kiosk mode, guest info must be embedded in QR or use a guest lookup
    # Option 1: QR contains guest_id (if guest has their own QR)
    # Option 2: Use checkpoint QR and require guest to type ID quickly

    # For checkpoint QR scan (standard flow):
    # Show quick guest selector or numeric keypad for guest ID

    play_sound("success")
    st.success("✅ QR 인식 성공!")
    st.session_state.kiosk_scan_count += 1

    # Show guest quick-select
    st.write("### 방문객 선택")
    guests = storage.get_active_guests()
    allowed_guests = [g for g in guests if g["id"] in checkpoint.get("allowed_guests", [])]

    if allowed_guests:
        guest_id = st.selectbox(
            "이름 선택",
            options=[g["id"] for g in allowed_guests],
            format_func=lambda x: get_guest_name(x)
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 체크인", type="primary"):
                record_activity(checkpoint["id"], guest_id, "check_in", qr_content)
                st.balloons()
                time.sleep(2)
                st.rerun()
        with col2:
            if st.button("🚪 체크아웃"):
                record_activity(checkpoint["id"], guest_id, "check_out", qr_content)
                time.sleep(2)
                st.rerun()
```

**Kiosk Mode Entry Points**:
```
1. URL 파라미터: /Guest?mode=kiosk&checkpoint=cp-uuid
2. 메뉴 버튼: "빠른 스캔 모드 시작"
3. Admin 설정: 특정 체크포인트를 kiosk 전용으로 설정
```

**Security Considerations**:
- Kiosk 모드에서는 방문 기록 조회 불가 (개인정보 보호)
- 자동 로그아웃: 5분 미활동 시 초기화
- 관리자 비밀번호로 kiosk 모드 해제

**Acceptance Criteria**:
- [ ] Kiosk 모드 진입/종료
- [ ] 연속 QR 스캔 (자동 리셋)
- [ ] 스캔 후 2초 대기 → 자동 초기화
- [ ] 오늘 스캔 횟수 표시
- [ ] 성공/실패 사운드 피드백
- [ ] 5분 미활동 시 자동 종료
- [ ] 방문 기록 조회 비활성화 (kiosk 모드)

---

### 2.6 방문 기록 조회

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

#### 연결 상태 표시
- [ ] 정상 연결 시 초록색 배지 (✅)
- [ ] Time API 오류 시 노란색 경고 (⚠️)
- [ ] 서버 연결 끊김 시 빨간색 에러 (❌)
- [ ] 응답 시간 (latency) 표시
- [ ] 30초마다 상태 갱신

#### 사운드 피드백
- [ ] 스캔 성공 시 성공음 재생
- [ ] 스캔 실패 시 에러음 재생
- [ ] 브라우저 오디오 권한 미허용 시 시각적 피드백만 표시
- [ ] 성공 후 3초 자동 초기화

#### 정보 기억하기
- [ ] "이 정보 기억하기" 체크박스 표시
- [ ] 체크 후 로그인 시 localStorage에 저장
- [ ] 재방문 시 저장된 정보 표시
- [ ] "이 정보로 로그인" 버튼 작동
- [ ] "삭제" 버튼으로 저장 정보 제거
- [ ] 저장 정보로 인증 실패 시 자동 삭제

#### 빠른 재스캔 모드 (Kiosk)
- [ ] Kiosk 모드 진입/종료
- [ ] 체크포인트 선택 후 연속 스캔
- [ ] 스캔 후 2초 대기 → 자동 초기화
- [ ] 오늘 스캔 횟수 표시
- [ ] 5분 미활동 시 자동 종료
- [ ] 방문 기록 조회 비활성화 (개인정보 보호)

---

## Document Metadata

- **문서 타입**: PRD - Guest Page
- **프로젝트**: QR In/Out
- **버전**: 1.2
- **작성자**: Jake
- **작성일**: 2026-02-08
- **언어**: 한국어
- **상태**: Active
- **변경 이력**:
  - v1.2 (2026-02-08): 연결 상태 표시, 사운드 피드백, 정보 기억하기, 빠른 재스캔 모드 추가
  - v1.1 (2026-02-05): 초기 버전
- **관련 문서**:
  - [PRD-Overview.md](PRD-Overview.md) - 시스템 개요
  - [PRD-Admin.md](PRD-Admin.md) - 관리자 페이지
  - [PRD-Host.md](PRD-Host.md) - 호스트 페이지

---

**End of PRD - Guest Page**
