---
document_type: "Product Requirements Document - Host Page"
project: "QR In/Out"
version: "1.1"
author: "Jake"
date: "2026-02-05"
status: "Active"
language: "Korean"
purpose: "호스트 페이지 상세 기능 명세"
parent_doc: "PRD-Overview.md"
related_docs:
  - "PRD-Admin.md"
  - "PRD-Guest.md"
---

# PRD: Host Page (호스트 페이지)

> **참고**: 이 문서는 호스트 페이지의 상세 명세입니다. 시스템 개요와 공통 모듈은 [PRD-Overview.md](PRD-Overview.md)를 참조하세요.

## Table of Contents
1. [Page Overview](#page-overview)
2. [Features](#features)
3. [UI Specifications](#ui-specifications)
4. [User Stories](#user-stories)
5. [Testing](#testing)

---

## 1. Page Overview

### 1.1 Purpose
체크포인트에서 QR 코드를 표시하는 페이지입니다. 디바이스(태블릿, 모니터 등)에 QR 코드를 전체 화면으로 표시하여 방문객이 스캔할 수 있도록 합니다.

### 1.2 Access
- **URL**: `/Host` (Streamlit multi-page)
- **인증**: 체크포인트 비밀번호
- **아이콘**: 🖥️

### 1.3 Main Functions

| 기능 | 설명 | 우선순위 |
|------|------|----------|
| 체크포인트 선택 | Admin에서 생성한 체크포인트 선택 | 🔴 필수 |
| 비밀번호 인증 | 관리 비밀번호로 화면 잠금/해제 | 🔴 필수 |
| Static QR 표시 | 고정형 QR 코드 표시 및 다운로드 | 🔴 필수 |
| Dynamic QR 표시 | 30분 주기 자동 갱신 QR 표시 | 🔴 필수 |
| 시간 제어 | 허용 시간 외 QR 숨김 | 🔴 필수 |
| 카운트다운 | 다음 갱신까지 시간 표시 | 🟡 중요 |
| 화면 잠금 | 비밀번호로 화면 보호 | 🟡 중요 |

---

## 2. Features

### 2.1 체크포인트 선택 및 인증

**User Story**:
```
As a host,
I want to select a checkpoint and authenticate,
So that I can display its QR code securely.
```

**UI Layout (Unauthenticated)**:
```
┌─────────────────────────────────────────┐
│ 🖥️ 호스트 페이지 - QR 코드 디스플레이   │
├─────────────────────────────────────────┤
│                                         │
│ 📍 체크포인트 선택                      │
│ [본관 입구 ▼]                           │
│                                         │
│ 🔐 관리 비밀번호                        │
│ [••••••••]                              │
│                                         │
│ [      시작      ]                      │
│                                         │
└─────────────────────────────────────────┘
```

**Streamlit Code**:
```python
st.title("🖥️ 호스트 페이지")
st.subheader("QR 코드 디스플레이")

# Session state for authentication
if "host_authenticated" not in st.session_state:
    st.session_state.host_authenticated = False
    st.session_state.selected_checkpoint_id = None

if not st.session_state.host_authenticated:
    st.write("### 📍 체크포인트 선택")

    # Load active checkpoints only
    checkpoints = storage.get_active_checkpoints()

    if not checkpoints:
        st.error("등록된 체크포인트가 없습니다. Admin 페이지에서 체크포인트를 먼저 생성하세요.")
        st.stop()

    selected_id = st.selectbox(
        "디스플레이할 체크포인트",
        options=[c["id"] for c in checkpoints],
        format_func=lambda x: f"{get_checkpoint_name(x)} ({get_checkpoint_location(x)})"
    )

    st.write("### 🔐 관리 비밀번호")
    password = st.text_input("비밀번호", type="password", key="host_password")

    if st.button("시작", type="primary"):
        if not password:
            st.error("비밀번호를 입력하세요")
        else:
            checkpoint = storage.get_by_id("checkpoints", selected_id)

            from core.auth import auth_manager
            if auth_manager.verify_password(password, checkpoint["admin_password_hash"]):
                st.session_state.host_authenticated = True
                st.session_state.selected_checkpoint_id = selected_id
                st.success("✅ 인증 성공!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ 비밀번호가 올바르지 않습니다")
```

**Acceptance Criteria**:
- [ ] Active 체크포인트만 표시
- [ ] 비밀번호 검증
- [ ] 인증 성공 시 QR 표시 화면으로 전환
- [ ] 인증 실패 시 에러 메시지

---

### 2.2 Static QR 코드 표시

**User Story**:
```
As a host,
I want to display a static QR code,
So that visitors can scan it for check-in/out.
```

**UI Layout**:
```
┌─────────────────────────────────────────┐
│ 📍 본관 입구            [🔒 잠금]       │
│ 서울시 강남구 테헤란로 123             │
├─────────────────────────────────────────┤
│                                         │
│ ✅ 현재 허용 시간 내입니다              │
│ ⏰ 2026-02-05 14:30:45 (Asia/Seoul)     │
│                                         │
│         ┌───────────────┐              │
│         │               │              │
│         │   QR  CODE    │              │
│         │   [STATIC]    │              │
│         │               │              │
│         └───────────────┘              │
│                                         │
│ ℹ️ QR 코드 타입: 고정형 (프린트 가능)  │
│                                         │
│ [🖨️ 프린트용 다운로드]                  │
│                                         │
└─────────────────────────────────────────┘
```

**Streamlit Code**:
```python
if st.session_state.host_authenticated:
    checkpoint = storage.get_by_id("checkpoints", st.session_state.selected_checkpoint_id)

    # Header with lock button
    col1, col2 = st.columns([4, 1])
    with col1:
        st.header(f"📍 {checkpoint['name']}")
        if checkpoint.get('location'):
            st.caption(checkpoint['location'])
    with col2:
        if st.button("🔒 잠금"):
            st.session_state.host_authenticated = False
            st.success("화면이 잠겼습니다")
            time.sleep(1)
            st.rerun()

    st.divider()

    # Get current time with Time API
    from core.time_service import time_service
    current_time, is_synced = time_service.get_current_time(
        checkpoint.get("timezone", "UTC")
    )

    # Show time sync status
    time_service.show_time_sync_status(is_synced, current_time)

    # Check if within allowed hours
    from core.time_validator import time_validator
    is_allowed, message = time_validator.is_within_allowed_hours(
        current_time,
        checkpoint["allowed_hours"]
    )

    if is_allowed:
        st.success(f"✅ {message}")

        if checkpoint["qr_mode"] == "static":
            # Generate static QR
            from core.qr_manager import qr_manager
            qr_content = qr_manager.generate_static_qr_content(checkpoint["id"])
            qr_image = qr_manager.generate_qr_image(qr_content, size=15)

            # Display QR code (large)
            st.image(qr_image, use_column_width=True)

            st.info("ℹ️ QR 코드 타입: 고정형 (프린트 가능)")

            # Download button
            if st.button("🖨️ 프린트용 다운로드"):
                qr_bytes = qr_manager.qr_image_to_bytes(qr_image)
                st.download_button(
                    label="QR 코드 이미지 다운로드",
                    data=qr_bytes,
                    file_name=f"qr_{checkpoint['name']}.png",
                    mime="image/png"
                )
    else:
        st.error(f"🚫 {message}")
        st.info("QR 코드가 비활성화되었습니다. 허용 시간에 다시 시도하세요.")
```

**Acceptance Criteria**:
- [ ] 체크포인트 정보 표시 (이름, 위치)
- [ ] 시간 동기화 상태 표시
- [ ] 허용 시간 체크
- [ ] Static QR 생성 및 표시 (큰 사이즈)
- [ ] 프린트용 다운로드 버튼
- [ ] 잠금 버튼으로 화면 보호

---

### 2.3 Dynamic QR 코드 표시 및 자동 갱신

**User Story**:
```
As a host,
I want to display a dynamic QR code that auto-refreshes,
So that security is enhanced through time-based QR rotation.
```

**UI Layout**:
```
┌─────────────────────────────────────────┐
│ 📍 본관 입구            [🔒 잠금]       │
│ 서울시 강남구 테헤란로 123             │
├─────────────────────────────────────────┤
│                                         │
│ ✅ 현재 허용 시간 내입니다              │
│ ⏰ 2026-02-05 14:30:45 (Asia/Seoul)     │
│                                         │
│         ┌───────────────┐              │
│         │               │              │
│         │   QR  CODE    │              │
│         │  [DYNAMIC]    │              │
│         │   Seq: 42     │              │
│         │               │              │
│         └───────────────┘              │
│                                         │
│ ℹ️ QR 코드 타입: 갱신형 (30분 주기)    │
│ ⏱️ 다음 갱신까지: 14:25                │
│ [████████████████░░░░] 75%             │
│                                         │
└─────────────────────────────────────────┘
```

**Streamlit Code**:
```python
if checkpoint["qr_mode"] == "dynamic":
    from core.qr_manager import qr_manager

    # Calculate next refresh time
    current_time, is_synced = time_service.get_current_time(
        checkpoint.get("timezone", "UTC")
    )

    # Generate current QR with sequence number
    qr_content, new_sequence = qr_manager.generate_dynamic_qr_content(
        checkpoint_id=checkpoint["id"],
        current_sequence=checkpoint.get("current_qr_sequence", 0),
        timestamp=current_time
    )

    # Update checkpoint sequence (if changed)
    if new_sequence != checkpoint.get("current_qr_sequence", 0):
        storage.update("checkpoints", checkpoint["id"], {
            "current_qr_sequence": new_sequence
        })
        # Reload checkpoint
        checkpoint = storage.get_by_id("checkpoints", checkpoint["id"])

    # Parse QR to get expiration
    qr_data = qr_manager.parse_qr_content(qr_content)
    expires_at = datetime.fromisoformat(qr_data["expires_at"])

    # Calculate time until expiration
    time_until_refresh = (expires_at - current_time).total_seconds()

    # Display QR code
    qr_image = qr_manager.generate_qr_image(qr_content, size=15)
    st.image(qr_image, use_column_width=True)

    # QR info
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"ℹ️ QR 타입: 갱신형 (30분 주기)")
    with col2:
        st.info(f"🔢 Sequence: {new_sequence}")

    # Countdown
    st.warning(f"⏱️ 다음 갱신까지: {time_validator.format_countdown(time_until_refresh)}")

    # Progress bar
    progress = 1 - (time_until_refresh / 1800)  # 1800s = 30min
    st.progress(max(0, min(1, progress)))

    # Auto-refresh logic
    if time_until_refresh <= 0:
        st.info("🔄 QR 코드 갱신 중...")
        time.sleep(1)
        st.rerun()
    else:
        # Refresh every 1 second to update countdown
        time.sleep(1)
        st.rerun()
```

**Acceptance Criteria**:
- [ ] 30분 주기 자동 갱신
- [ ] Sequence number 표시
- [ ] 다음 갱신까지 카운트다운
- [ ] Progress bar로 시각적 피드백
- [ ] 만료 시 자동 새로고침
- [ ] 프린트 버튼 비활성화 (동적이므로)

---

### 2.4 허용 시간 외 QR 숨김

**UI Layout (허용 시간 외)**:
```
┌─────────────────────────────────────────┐
│ 📍 본관 입구            [🔒 잠금]       │
│ 서울시 강남구 테헤란로 123             │
├─────────────────────────────────────────┤
│                                         │
│ 🚫 허용 시간이 아닙니다                 │
│ ⏰ 현재: 20:30 (Asia/Seoul)             │
│ 📅 허용 시간: 09:00 - 18:00             │
│                                         │
│         ┌───────────────┐              │
│         │               │              │
│         │   QR 코드     │              │
│         │   비활성화    │              │
│         │               │              │
│         └───────────────┘              │
│                                         │
│ ℹ️ 허용 시간에 다시 시도하세요          │
│                                         │
└─────────────────────────────────────────┘
```

**Streamlit Code**:
```python
else:  # Not within allowed hours
    st.error(f"🚫 {message}")

    # Show current time and allowed hours
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"⏰ 현재: {current_time.strftime('%H:%M')} ({checkpoint.get('timezone', 'UTC')})")
    with col2:
        st.write(f"📅 허용 시간: {checkpoint['allowed_hours']['start_time']} - {checkpoint['allowed_hours']['end_time']}")

    # Show placeholder (no QR)
    st.markdown("""
    <div style="text-align: center; padding: 100px; background-color: #f0f0f0; border-radius: 10px;">
        <h2>🚫 QR 코드 비활성화</h2>
        <p>허용 시간이 아닙니다</p>
    </div>
    """, unsafe_allow_html=True)

    st.info("ℹ️ 허용 시간에 다시 시도하세요")

    # Still refresh every 60 seconds to check if now within hours
    time.sleep(60)
    st.rerun()
```

**Acceptance Criteria**:
- [ ] 허용 시간 외 QR 숨김
- [ ] 명확한 메시지 표시
- [ ] 현재 시간과 허용 시간 표시
- [ ] 60초마다 자동 체크 (허용 시간 진입 감지)

---

### 2.5 화면 잠금

**User Story**:
```
As a host,
I want to lock the screen with a password,
So that unauthorized users cannot change the checkpoint.
```

**Streamlit Code**:
```python
# Lock button in header
if st.button("🔒 잠금", key="lock_btn"):
    st.session_state.host_authenticated = False
    st.session_state.show_lock_message = True
    st.rerun()

# Show lock confirmation
if st.session_state.get("show_lock_message"):
    st.success("✅ 화면이 잠겼습니다. 다시 시작하려면 비밀번호를 입력하세요.")
    time.sleep(2)
    st.session_state.show_lock_message = False
```

**Acceptance Criteria**:
- [ ] 잠금 버튼 클릭 시 인증 세션 종료
- [ ] 잠금 확인 메시지
- [ ] 재시작 시 비밀번호 재입력 필요

---

## 3. UI Specifications

### 3.1 Full Screen Mode

**목표**: QR 코드를 최대한 크게 표시

**Streamlit Config** (`.streamlit/config.toml`):
```toml
[ui]
hideTopBar = false  # Keep for lock button access
hideSidebarNav = true  # Hide sidebar in production
```

**CSS Customization**:
```python
st.markdown("""
<style>
    /* Full width container */
    .main .block-container {
        max-width: 100%;
        padding-top: 2rem;
    }

    /* Large QR image */
    .stImage > img {
        border: 5px solid #4CAF50;
        border-radius: 10px;
    }

    /* Large text for status */
    .stAlert {
        font-size: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)
```

### 3.2 Color Coding

| 상태 | 색상 | 용도 |
|------|------|------|
| 허용 시간 내 | Green (#4CAF50) | 성공 메시지, QR 테두리 |
| 허용 시간 외 | Red (#F44336) | 에러 메시지 |
| 정보 | Blue (#2196F3) | QR 타입, 카운트다운 |
| 경고 | Orange (#FF9800) | 갱신 임박 |

---

## 4. User Stories & Acceptance Criteria

### Story 1: Static QR 표시
**As a** host
**I want to** display a static QR code
**So that** visitors can scan it anytime within allowed hours

**Acceptance Criteria**:
- [ ] 체크포인트 선택 및 인증
- [ ] 허용 시간 체크
- [ ] Static QR 생성 및 표시 (큰 사이즈)
- [ ] 프린트용 다운로드
- [ ] 화면 잠금 기능

### Story 2: Dynamic QR 자동 갱신
**As a** host
**I want to** display a dynamic QR that auto-refreshes
**So that** security is enhanced

**Acceptance Criteria**:
- [ ] 30분 주기 자동 갱신
- [ ] Sequence number 증가
- [ ] 카운트다운 표시
- [ ] Progress bar
- [ ] 만료 시 자동 갱신

### Story 3: 허용 시간 제어
**As a** host
**I want to** hide QR outside allowed hours
**So that** access is controlled by time

**Acceptance Criteria**:
- [ ] 허용 시간 외 QR 숨김
- [ ] 명확한 메시지
- [ ] 60초마다 자동 체크

---

## 5. Testing

### 5.1 Manual Testing Checklist

#### 인증
- [ ] 올바른 비밀번호로 인증 성공
- [ ] 잘못된 비밀번호로 인증 실패
- [ ] 잠금 후 재인증 필요

#### Static QR
- [ ] Static QR 생성 및 표시
- [ ] 큰 사이즈로 표시
- [ ] 프린트용 다운로드 작동
- [ ] 허용 시간 외 QR 숨김

#### Dynamic QR
- [ ] Dynamic QR 생성 및 표시
- [ ] Sequence number 표시
- [ ] 카운트다운 작동
- [ ] 30분 후 자동 갱신 확인
- [ ] Progress bar 업데이트
- [ ] 프린트 버튼 없음

#### 시간 제어
- [ ] 허용 시간 내 QR 표시
- [ ] 허용 시간 외 QR 숨김
- [ ] 60초마다 자동 체크

#### Time Sync
- [ ] Time API 성공 시 동기화 메시지
- [ ] Time API 실패 시 경고 메시지
- [ ] Fallback to local time

---

## Document Metadata

- **문서 타입**: PRD - Host Page
- **프로젝트**: QR In/Out
- **버전**: 1.1
- **작성자**: Jake
- **작성일**: 2026-02-05
- **언어**: 한국어
- **상태**: Active
- **관련 문서**:
  - [PRD-Overview.md](PRD-Overview.md) - 시스템 개요
  - [PRD-Admin.md](PRD-Admin.md) - 관리자 페이지
  - [PRD-Guest.md](PRD-Guest.md) - 게스트 페이지

---

**End of PRD - Host Page**
