---
document_type: "Product Requirements Document - Admin Page"
project: "QR In/Out"
version: "1.1"
author: "Jake"
date: "2026-02-05"
status: "Active"
language: "Korean"
purpose: "관리자 페이지 상세 기능 명세"
parent_doc: "PRD-Overview.md"
related_docs:
  - "PRD-Host.md"
  - "PRD-Guest.md"
---

# PRD: Admin Page (관리자 페이지)

> **참고**: 이 문서는 관리자 페이지의 상세 명세입니다. 시스템 개요와 공통 모듈은 [PRD-Overview.md](PRD-Overview.md)를 참조하세요.

## Table of Contents
1. [Page Overview](#page-overview)
2. [Features](#features)
3. [UI Specifications](#ui-specifications)
4. [User Stories](#user-stories)
5. [Testing](#testing)

---

## 1. Page Overview

### 1.1 Purpose
관리자가 체크포인트와 방문객을 관리하고, 시스템 활동을 모니터링하며, 전역 설정을 조정하는 페이지입니다.

### 1.2 Access
- **URL**: `/Admin` (Streamlit multi-page)
- **인증**: 없음 (로컬 실행)
- **아이콘**: 👤

### 1.3 Main Functions

| 기능 | 설명 | 우선순위 |
|------|------|----------|
| 체크포인트 관리 | 생성, 수정, 삭제 (Soft Delete) | 🔴 필수 |
| 방문객 관리 | 생성, 수정, 삭제 (Soft Delete) | 🔴 필수 |
| 활동 로그 조회 | 체크포인트별/방문객별 조회 | 🔴 필수 |
| 통계 대시보드 | 주요 지표 및 차트 | 🟡 중요 |
| 시스템 설정 | 타임존, QR 갱신 주기 등 | 🟡 중요 |
| CSV 내보내기 | 로그 데이터 다운로드 | 🟢 선택 |

---

## 2. Features

### 2.1 체크포인트 관리

#### 2.1.1 체크포인트 생성

**User Story**:
```
As an admin,
I want to create a new checkpoint,
So that I can control access to a specific location.
```

**UI Layout**:
```
┌─────────────────────────────────────────┐
│ 체크포인트 관리                         │
├─────────────────────────────────────────┤
│ 📝 새 체크포인트 생성                   │
│                                         │
│ [Form]                                  │
│  체크포인트 이름 * : [_______________]  │
│  위치           : [_______________]      │
│                                         │
│  허용 시간대:                           │
│  시작 시간: [09:00 ▼]  종료: [18:00 ▼] │
│                                         │
│  QR 코드 방식:                          │
│  ( ) 고정형  (●) 갱신형                 │
│                                         │
│  관리 비밀번호 * : [••••••••]           │
│  비밀번호 확인   : [••••••••]           │
│                                         │
│  허용 방문객 (다중 선택):               │
│  □ 홍길동 (hong@example.com)            │
│  □ 김철수 (kim@example.com)             │
│  ☑ 이영희 (lee@example.com)             │
│                                         │
│  [      생성      ]                     │
└─────────────────────────────────────────┘
```

**Form Fields**:

| 필드 | 타입 | 필수 | 검증 규칙 | 기본값 |
|------|------|------|-----------|--------|
| 이름 | text | ✅ | 길이 1-100, 고유 | - |
| 위치 | text | ❌ | 길이 0-200 | "" |
| 시작 시간 | time | ✅ | HH:MM | 09:00 |
| 종료 시간 | time | ✅ | HH:MM, >= 시작 | 18:00 |
| QR 방식 | radio | ✅ | static/dynamic | dynamic |
| 비밀번호 | password | ✅ | 최소 4자 | - |
| 비밀번호 확인 | password | ✅ | 일치 확인 | - |
| 허용 방문객 | multiselect | ❌ | 0개 이상 | [] |

**Streamlit Code**:
```python
st.title("👤 관리자 페이지")
st.header("체크포인트 관리")
st.subheader("📝 새 체크포인트 생성")

with st.form("create_checkpoint"):
    name = st.text_input("체크포인트 이름 *", placeholder="예: 본관 입구")
    location = st.text_input("위치", placeholder="예: 서울시 강남구...")

    col1, col2 = st.columns(2)
    with col1:
        start_time = st.time_input("허용 시작 시간", value=time(9, 0))
    with col2:
        end_time = st.time_input("허용 종료 시간", value=time(18, 0))

    qr_mode = st.radio(
        "QR 코드 방식",
        options=["static", "dynamic"],
        format_func=lambda x: "고정형 (프린트 가능)" if x == "static" else "갱신형 (30분 주기)",
        index=1  # Default: dynamic
    )

    col1, col2 = st.columns(2)
    with col1:
        admin_password = st.text_input("관리 비밀번호 *", type="password")
    with col2:
        password_confirm = st.text_input("비밀번호 확인 *", type="password")

    # Load active guests only
    guests = storage.get_active_guests()
    allowed_guests = st.multiselect(
        "허용 방문객 (다중 선택)",
        options=[g["id"] for g in guests],
        format_func=lambda x: f"{get_guest_name(x)} ({get_guest_email(x)})",
        help="0개를 선택하면 모든 방문객이 차단됩니다"
    )

    submitted = st.form_submit_button("생성", type="primary")

    if submitted:
        # Validation
        errors = []

        if not name:
            errors.append("체크포인트 이름은 필수입니다")
        elif checkpoint_name_exists(name):
            errors.append("이미 존재하는 체크포인트 이름입니다")

        if start_time >= end_time:
            errors.append("종료 시간은 시작 시간보다 늦어야 합니다")

        if not admin_password or len(admin_password) < 4:
            errors.append("비밀번호는 최소 4자 이상이어야 합니다")

        if admin_password != password_confirm:
            errors.append("비밀번호가 일치하지 않습니다")

        if errors:
            for error in errors:
                st.error(f"❌ {error}")
        else:
            # Create checkpoint
            checkpoint = Checkpoint.create_new(
                name=name,
                location=location,
                allowed_hours=AllowedHours(
                    start_time=start_time.strftime("%H:%M"),
                    end_time=end_time.strftime("%H:%M")
                ),
                qr_mode=qr_mode,
                admin_password=admin_password,
                allowed_guests=allowed_guests
            )

            storage.add("checkpoints", checkpoint.to_dict())
            st.success(f"✅ 체크포인트 '{name}'이(가) 생성되었습니다!")

            # Warning if no guests
            if len(allowed_guests) == 0:
                st.warning("⚠️ 허용된 방문객이 없어 모든 방문객이 차단됩니다.")

            time.sleep(2)
            st.rerun()
```

**Acceptance Criteria**:
- [ ] 모든 필수 필드 입력 시에만 생성 버튼 활성화
- [ ] 체크포인트 이름 중복 방지
- [ ] 비밀번호 일치 확인
- [ ] 시작 시간 < 종료 시간 검증
- [ ] 생성 후 checkpoints.json에 저장
- [ ] 성공 메시지 표시 및 페이지 새로고침
- [ ] 허용 방문객 0개 시 경고 메시지

#### 2.1.2 체크포인트 수정

**UI Layout**:
```
┌─────────────────────────────────────────┐
│ 📝 기존 체크포인트 수정                 │
│                                         │
│ 선택: [본관 입구 ▼]                     │
│                                         │
│ [Form - Pre-filled with existing data] │
│  ... (생성 폼과 동일)                   │
│                                         │
│  [      수정      ]                     │
└─────────────────────────────────────────┘
```

**Streamlit Code**:
```python
st.subheader("📝 기존 체크포인트 수정")

checkpoints = storage.get_active_checkpoints()

if not checkpoints:
    st.info("등록된 체크포인트가 없습니다. 먼저 체크포인트를 생성하세요.")
else:
    selected_id = st.selectbox(
        "수정할 체크포인트 선택",
        options=[c["id"] for c in checkpoints],
        format_func=lambda x: get_checkpoint_name(x),
        key="edit_checkpoint_select"
    )

    if selected_id:
        checkpoint = storage.get_by_id("checkpoints", selected_id)

        with st.form("edit_checkpoint"):
            name = st.text_input("체크포인트 이름 *", value=checkpoint["name"])
            location = st.text_input("위치", value=checkpoint["location"])

            # ... (나머지 필드는 생성 폼과 동일, pre-filled)

            submitted = st.form_submit_button("수정", type="primary")

            if submitted:
                # Validation (동일)
                # Update
                updates = {
                    "name": name,
                    "location": location,
                    # ... (other fields)
                }
                storage.update("checkpoints", selected_id, updates)
                st.success(f"✅ 체크포인트가 수정되었습니다!")
                time.sleep(2)
                st.rerun()
```

**Acceptance Criteria**:
- [ ] 선택한 체크포인트 데이터 pre-fill
- [ ] 수정 시 updated_at 타임스탬프 갱신
- [ ] 이름 변경 시 중복 검증 (자기 자신 제외)
- [ ] Dynamic QR의 경우 current_qr_sequence 유지

#### 2.1.3 체크포인트 삭제 (Soft Delete)

**UI Layout**:
```
┌─────────────────────────────────────────┐
│ ⚠️ 위험 구역: 체크포인트 삭제          │
│                                         │
│ ⚠️ 경고: 체크포인트를 삭제하면 이름에  │
│ '_removed'가 추가되고 더 이상 사용할   │
│ 수 없습니다. 과거 활동 기록은 보존됩니다│
│                                         │
│ [    체크포인트 삭제    ]               │
│                                         │
│ (첫 클릭: 확인 요청)                    │
│ (두 번째 클릭: 실제 삭제)               │
└─────────────────────────────────────────┘
```

**Streamlit Code**:
```python
with st.expander("⚠️ 위험 구역: 체크포인트 삭제"):
    st.warning("""
    **주의**: 체크포인트를 삭제하면:
    - 이름에 '_removed'가 추가됩니다
    - 더 이상 호스트 페이지에서 선택할 수 없습니다
    - 과거 활동 기록은 보존됩니다 (삭제되지 않음)
    """)

    if st.button("체크포인트 삭제", type="secondary", key="delete_checkpoint_btn"):
        if st.session_state.get("confirm_delete_checkpoint"):
            # Second click: actually delete
            storage.soft_delete_checkpoint(selected_id)
            st.success(f"✅ 체크포인트가 삭제되었습니다 (이름에 '_removed' 추가)")
            st.session_state.confirm_delete_checkpoint = False
            time.sleep(2)
            st.rerun()
        else:
            # First click: ask for confirmation
            st.session_state.confirm_delete_checkpoint = True
            st.error("⚠️ 다시 한 번 클릭하여 삭제를 확인하세요.")
```

**Acceptance Criteria**:
- [ ] 이중 확인 메커니즘 (실수 방지)
- [ ] Soft delete: 이름에 "_removed" suffix 추가
- [ ] deleted_at 타임스탬프 설정
- [ ] 삭제 후 active 체크포인트 목록에서 제외
- [ ] Activity logs는 유지 (참조 보존)

---

### 2.2 방문객 관리

#### 2.2.1 방문객 등록

**User Story**:
```
As an admin,
I want to register a new guest with email,
So that they can scan QR codes at authorized checkpoints.
```

**UI Layout**:
```
┌─────────────────────────────────────────┐
│ 방문객 관리                             │
├─────────────────────────────────────────┤
│ 👤 새 방문객 등록                       │
│                                         │
│ [Form]                                  │
│  📋 필수 정보                           │
│  이름   * : [홍길동____]                │
│  이메일 * : [hong@example.com_____]     │
│                                         │
│  📋 선택 정보                           │
│  전화번호 : [010-1234-5678_______]      │
│                                         │
│  🌍 타임존 및 권한 설정                 │
│  타임존 : [Asia/Seoul ▼]                │
│                                         │
│  □ 방문객별 허용 시간 설정              │
│    (체크 시 시간 입력 필드 표시)        │
│                                         │
│  허가 체크포인트 (다중 선택):           │
│  ☑ 본관 입구                            │
│  □ 2층 회의실                           │
│  ☑ 주차장                               │
│                                         │
│  [      등록      ]                     │
└─────────────────────────────────────────┘
```

**Form Fields**:

| 필드 | 타입 | 필수 | 검증 규칙 | 기본값 |
|------|------|------|-----------|--------|
| 이름 | text | ✅ | 길이 1-100 | - |
| 이메일 | text | ✅ | 유효한 이메일, 고유 | - |
| 전화번호 | text | ❌ | - | "" |
| 타임존 | selectbox | ✅ | IANA timezone | Asia/Seoul |
| 허용 시간 사용 | checkbox | ❌ | - | False |
| 허용 시작 시간 | time | ❌ | HH:MM | 08:00 |
| 허용 종료 시간 | time | ❌ | HH:MM | 20:00 |
| 허가 체크포인트 | multiselect | ❌ | 0개 이상 | [] |

**Streamlit Code**:
```python
st.title("👤 관리자 페이지")
st.header("방문객 관리")
st.subheader("👤 새 방문객 등록")

with st.form("create_guest"):
    st.write("**📋 필수 정보**")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("이름 *", placeholder="홍길동")
    with col2:
        email = st.text_input("이메일 *", placeholder="hong@example.com")

    st.write("**📋 선택 정보**")
    phone = st.text_input("전화번호", placeholder="010-1234-5678")

    st.write("**🌍 타임존 및 권한 설정**")

    # Load admin settings for default timezone
    settings = AdminSettings.load_or_create_default()

    timezone = st.selectbox(
        "타임존",
        options=pytz.all_timezones,
        index=pytz.all_timezones.index(settings.default_guest_timezone),
        help="방문객의 현재 위치 타임존"
    )

    # Optional: Per-guest allowed hours
    use_custom_hours = st.checkbox("방문객별 허용 시간 설정 (선택사항)")
    guest_allowed_hours = None

    if use_custom_hours:
        col1, col2 = st.columns(2)
        with col1:
            guest_start = st.time_input("허용 시작 시간", value=time(8, 0))
        with col2:
            guest_end = st.time_input("허용 종료 시간", value=time(20, 0))

        guest_allowed_hours = AllowedHours(
            start_time=guest_start.strftime("%H:%M"),
            end_time=guest_end.strftime("%H:%M")
        )

    # Allowed checkpoints
    checkpoints = storage.get_active_checkpoints()
    allowed_checkpoints = st.multiselect(
        "허가 체크포인트 (다중 선택)",
        options=[c["id"] for c in checkpoints],
        format_func=lambda x: get_checkpoint_name(x),
        help="0개를 선택하면 어떤 체크포인트에도 접근할 수 없습니다"
    )

    submitted = st.form_submit_button("등록", type="primary")

    if submitted:
        # Validation
        errors = []

        if not name:
            errors.append("이름은 필수입니다")

        if not email:
            errors.append("이메일은 필수입니다")
        elif not is_valid_email(email):
            errors.append("유효한 이메일 주소를 입력하세요")
        elif guest_email_exists(email):
            errors.append("이미 등록된 이메일입니다")

        if use_custom_hours and guest_start >= guest_end:
            errors.append("종료 시간은 시작 시간보다 늦어야 합니다")

        if errors:
            for error in errors:
                st.error(f"❌ {error}")
        else:
            # Create guest
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

            # Warnings
            if len(allowed_checkpoints) == 0:
                st.warning("⚠️ 허가된 체크포인트가 없어 이 방문객은 어떤 체크포인트에도 접근할 수 없습니다.")

            time.sleep(2)
            st.rerun()

def is_valid_email(email: str) -> bool:
    """Simple email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
```

**Acceptance Criteria**:
- [ ] 이름과 이메일 필수 입력
- [ ] 이메일 형식 검증 (정규식)
- [ ] 이메일 중복 방지
- [ ] 타임존 선택 가능 (기본값: AdminSettings의 default_guest_timezone)
- [ ] 허용 시간 선택사항 (체크박스로 활성화)
- [ ] 허가 체크포인트 0개 이상 선택
- [ ] 0개 선택 시 경고 메시지

#### 2.2.2 방문객 수정 및 삭제

(체크포인트와 유사한 구조)

**Acceptance Criteria (수정)**:
- [ ] 선택한 방문객 데이터 pre-fill
- [ ] 이메일 변경 시 중복 검증 (자기 자신 제외)
- [ ] updated_at 타임스탬프 갱신

**Acceptance Criteria (삭제)**:
- [ ] Soft delete: 이름에 "_removed" suffix
- [ ] deleted_at 타임스탬프 설정
- [ ] Activity logs는 유지

---

### 2.3 활동 로그 조회

#### 2.3.1 체크포인트별 조회

**User Story**:
```
As an admin,
I want to view all activity logs for a specific checkpoint,
So that I can monitor who visited and when.
```

**UI Layout**:
```
┌─────────────────────────────────────────┐
│ 📊 활동 로그                            │
├─────────────────────────────────────────┤
│ 조회 방식: (●) 체크포인트별  ( ) 방문객별  ( ) 전체
│                                         │
│ 체크포인트: [본관 입구 ▼]               │
│ 기간: [2026-01-29] ~ [2026-02-05]       │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ 시간              | 방문객 | 활동   │ │
│ ├─────────────────────────────────────┤ │
│ │ 2026-02-05 10:30 | 홍길동 | ✅ IN  │ │
│ │ 2026-02-05 11:15 | 이영희 | ✅ IN  │ │
│ │ 2026-02-05 12:00 | 홍길동 | 🚪 OUT │ │
│ │ 2026-02-05 14:30 | 김철수 | ❌ 실패 │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [📥 CSV 다운로드]                       │
└─────────────────────────────────────────┘
```

**Streamlit Code**:
```python
st.title("📊 활동 로그")

view_mode = st.radio(
    "조회 방식",
    options=["체크포인트별", "방문객별", "전체"],
    horizontal=True
)

if view_mode == "체크포인트별":
    checkpoint_id = st.selectbox(
        "체크포인트 선택",
        options=[c["id"] for c in storage.get_active_checkpoints()],
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

    if logs:
        # Convert to DataFrame
        df = pd.DataFrame(logs)

        # Enrich with names
        df["checkpoint_name"] = df["checkpoint_id"].apply(get_checkpoint_name)
        df["guest_name"] = df["guest_id"].apply(get_guest_name)

        # Format columns
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp", ascending=False)

        # Display dataframe
        st.dataframe(
            df[["timestamp", "guest_name", "action", "status"]],
            column_config={
                "timestamp": st.column_config.DatetimeColumn(
                    "시간",
                    format="YYYY-MM-DD HH:mm:ss"
                ),
                "guest_name": "방문객",
                "action": st.column_config.SelectboxColumn(
                    "활동",
                    options=["check_in", "check_out"]
                ),
                "status": st.column_config.SelectboxColumn(
                    "상태",
                    options=["success", "failure"]
                )
            },
            use_container_width=True,
            hide_index=True
        )

        # Export to CSV
        if st.button("📥 CSV 다운로드"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"checkpoint_{checkpoint_id}_logs_{date.today()}.csv",
                mime="text/csv"
            )
    else:
        st.info("선택한 기간에 활동 기록이 없습니다.")

elif view_mode == "방문객별":
    # Similar implementation...
    pass

else:  # 전체
    # Show all logs with both filters...
    pass
```

**Acceptance Criteria**:
- [ ] 체크포인트별, 방문객별, 전체 조회 지원
- [ ] 날짜 범위 필터링
- [ ] 테이블 형태로 표시 (시간순 정렬)
- [ ] 삭제된 체크포인트/방문객도 표시 ("_removed" suffix)
- [ ] CSV 다운로드 기능
- [ ] 페이지네이션 (1000개 이상 시)

---

### 2.4 통계 대시보드

**UI Layout**:
```
┌─────────────────────────────────────────┐
│ 📊 통계 대시보드                        │
├─────────────────────────────────────────┤
│ 기간: [2026-01-29] ~ [2026-02-05]       │
│                                         │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │
│ │ 총   │ │ 총   │ │ 성공 │ │ 활성 │   │
│ │체크인│ │체크  │ │ 률   │ │방문객│   │
│ │      │ │아웃  │ │      │ │      │   │
│ │ 125  │ │ 98   │ │ 97.3%│ │  23  │   │
│ └──────┘ └──────┘ └──────┘ └──────┘   │
│                                         │
│ 📈 시간대별 활동                        │
│ [Line Chart]                            │
│                                         │
│ 📊 체크포인트별 활동                    │
│ [Bar Chart]                             │
└─────────────────────────────────────────┘
```

**Acceptance Criteria**:
- [ ] 주요 지표 표시 (메트릭 카드)
- [ ] 시간대별 활동 차트 (라인 차트)
- [ ] 체크포인트별 활동 차트 (바 차트)
- [ ] 날짜 범위 필터링
- [ ] 실시간 업데이트 (페이지 새로고침 시)

---

### 2.5 시스템 설정

**UI Layout**:
```
┌─────────────────────────────────────────┐
│ ⚙️ 시스템 설정                          │
├─────────────────────────────────────────┤
│ 👤 관리자 설정                          │
│ 관리자 타임존: [Asia/Seoul ▼]           │
│ 기본 방문객 타임존: [Asia/Seoul ▼]      │
│                                         │
│ 🔲 QR 코드 설정                         │
│ QR 갱신 주기 (분): [30____]             │
│ □ 시간 동기화 필수 (API 실패 시 차단)   │
│                                         │
│ [    설정 저장    ]                     │
└─────────────────────────────────────────┘
```

**Acceptance Criteria**:
- [ ] 관리자 타임존 변경
- [ ] 기본 방문객 타임존 변경
- [ ] QR 갱신 주기 변경 (5-120분)
- [ ] 시간 동기화 필수 여부 설정
- [ ] 설정 저장 후 admin_settings.json 업데이트

---

## 3. UI Specifications

### 3.1 Color Scheme

| 요소 | 색상 | 용도 |
|------|------|------|
| Primary | #4CAF50 (Green) | 생성, 성공 버튼 |
| Secondary | #2196F3 (Blue) | 수정 버튼 |
| Danger | #F44336 (Red) | 삭제 버튼 |
| Warning | #FF9800 (Orange) | 경고 메시지 |
| Success | #4CAF50 (Green) | 성공 메시지 |

### 3.2 Layout Structure

```
Admin Page Layout:
┌─────────────────────────────────────────┐
│ [Sidebar]                               │
│  - 메뉴                                 │
│  - 페이지 네비게이션                    │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ [Main Content]                          │
│  ┌─────────────────────────────────┐   │
│  │ 헤더 (아이콘 + 제목)            │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │ Tabs / Sections                 │   │
│  │  - 체크포인트 관리              │   │
│  │  - 방문객 관리                  │   │
│  │  - 활동 로그                    │   │
│  │  - 통계                         │   │
│  │  - 설정                         │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

---

## 4. User Stories & Acceptance Criteria

### Story 1: 체크포인트 생성
**As an** admin
**I want to** create a checkpoint with allowed hours and QR mode
**So that** I can control when and how visitors access the location

**Acceptance Criteria**:
- [ ] 이름, 위치, 허용 시간, QR 방식, 비밀번호 입력
- [ ] 허용 방문객 다중 선택 (0개 이상)
- [ ] 이름 중복 방지
- [ ] 비밀번호 4자 이상, 확인 일치
- [ ] 생성 후 데이터 저장 및 성공 메시지

### Story 2: 방문객 등록
**As an** admin
**I want to** register a guest with name and email
**So that** they can authenticate and scan QR codes

**Acceptance Criteria**:
- [ ] 이름, 이메일 필수 입력
- [ ] 전화번호 선택 입력
- [ ] 이메일 형식 및 중복 검증
- [ ] 타임존 선택 (기본값: AdminSettings)
- [ ] 허용 시간 선택사항 (체크박스)
- [ ] 허가 체크포인트 다중 선택
- [ ] 0개 선택 시 경고

### Story 3: 활동 로그 조회
**As an** admin
**I want to** view activity logs by checkpoint or guest
**So that** I can monitor access and identify issues

**Acceptance Criteria**:
- [ ] 조회 방식 선택 (체크포인트/방문객/전체)
- [ ] 날짜 범위 필터
- [ ] 테이블 표시 (시간, 방문객, 활동, 상태)
- [ ] 삭제된 항목 표시
- [ ] CSV 다운로드

### Story 4: Soft Delete
**As an** admin
**I want to** soft-delete checkpoints/guests
**So that** I preserve historical data while removing active use

**Acceptance Criteria**:
- [ ] 이중 확인 메커니즘
- [ ] 이름에 "_removed" suffix 추가
- [ ] deleted_at 타임스탬프 설정
- [ ] Activity logs 유지
- [ ] Active 목록에서 제외

---

## 5. Testing

### 5.1 Unit Tests
- `test_checkpoint_creation()` - 체크포인트 생성 로직
- `test_guest_creation()` - 방문객 등록 로직
- `test_soft_delete()` - Soft delete 메커니즘
- `test_email_validation()` - 이메일 검증

### 5.2 Integration Tests
- `test_checkpoint_to_qr_flow()` - 체크포인트 생성 → QR 생성
- `test_guest_to_scan_flow()` - 방문객 등록 → 인증 → 스캔
- `test_log_filtering()` - 로그 필터링 정확도

### 5.3 Manual Testing Checklist

#### 체크포인트 관리
- [ ] 생성: 모든 필드 입력, 성공 메시지
- [ ] 수정: 기존 데이터 pre-fill, 수정 반영
- [ ] 삭제: 이중 확인, _removed suffix
- [ ] 중복 이름 방지
- [ ] 허용 방문객 0개 경고

#### 방문객 관리
- [ ] 등록: 이름+이메일 필수, 성공 메시지
- [ ] 이메일 형식 검증
- [ ] 이메일 중복 방지
- [ ] 타임존 선택
- [ ] 허용 시간 선택사항
- [ ] 허가 체크포인트 다중 선택

#### 활동 로그
- [ ] 체크포인트별 조회
- [ ] 방문객별 조회
- [ ] 전체 조회
- [ ] 날짜 범위 필터링
- [ ] CSV 다운로드
- [ ] 삭제된 항목 표시

#### 시스템 설정
- [ ] 타임존 변경
- [ ] QR 갱신 주기 변경
- [ ] 설정 저장 및 반영

---

## Document Metadata

- **문서 타입**: PRD - Admin Page
- **프로젝트**: QR In/Out
- **버전**: 1.1
- **작성자**: Jake
- **작성일**: 2026-02-05
- **언어**: 한국어
- **상태**: Active
- **관련 문서**:
  - [PRD-Overview.md](PRD-Overview.md) - 시스템 개요
  - [PRD-Host.md](PRD-Host.md) - 호스트 페이지
  - [PRD-Guest.md](PRD-Guest.md) - 게스트 페이지

---

**End of PRD - Admin Page**
