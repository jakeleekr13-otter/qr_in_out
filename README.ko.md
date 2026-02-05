# QR In/Out - QR 코드 기반 체크포인트 출입 관리 시스템

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**한국어** | [English](README.md)

---

## 개요

**QR In/Out**은 Python과 Streamlit으로 구축된 포괄적인 QR 코드 기반 체크포인트 출입 관리 시스템입니다. 지정된 체크포인트에 정적 또는 동적 QR 코드를 배치하고, 권한이 있는 방문객이 모바일 기기로 코드를 스캔하여 체크인 및 체크아웃할 수 있습니다.

### 주요 기능

- **역할 기반 3개 페이지**
  - **Admin (관리자)**: 체크포인트 및 방문객 관리, 활동 기록 조회, 시스템 설정
  - **Host (호스트)**: 체크포인트에서 QR 코드 표시 (정적 또는 동적)
  - **Guest (방문객)**: QR 코드 스캔하여 체크인/체크아웃, 개인 방문 기록 조회

- **이중 QR 코드 모드**
  - **정적 QR**: 만료되지 않음, 인쇄용 안내판에 적합
  - **동적 QR**: 30분마다 자동 갱신, HMAC-SHA256 서명으로 보안 강화

- **시간 기반 접근 제어**
  - 체크포인트별 허용 시간
  - 방문객별 허용 시간 (선택사항)
  - World Time API를 사용한 타임존 인식 검증
  - 야간 근무 지원 (예: 22:00 - 06:00)

- **보안 기능**
  - 비밀번호로 보호되는 관리자 및 체크포인트 접근
  - 동적 QR 코드의 HMAC-SHA256 서명
  - 재사용 공격 방지를 위한 순차 번호 검증
  - 로컬 시간 조작 방지를 위한 World Time API 시간 동기화
  - 데이터 이력 보존을 위한 소프트 삭제 메커니즘

- **로컬 데이터 저장**
  - JSON 기반 저장 (외부 데이터베이스 불필요)
  - 스레드 안전 동시 접근
  - 오프라인 작동 가능
  - 활동 기록 영구 저장

---

## 기술 스택

- **프레임워크**: Streamlit (Python 웹 프레임워크)
- **QR 생성**: qrcode, Pillow
- **QR 스캔**: pyzbar (zbar 시스템 라이브러리 필요)
- **시간 동기화**: World Time API, TimeAPI.io
- **인증**: bcrypt 비밀번호 해싱 (솔트 포함)
- **데이터 저장**: 스레드 안전 잠금 기능이 있는 JSON 파일
- **타임존 처리**: pytz
- **환경 관리**: python-dotenv

---

## 설치 방법

### 1. 저장소 클론

```bash
git clone https://github.com/yourusername/qr-in-out.git
cd qr-in-out
```

### 2. Python 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 시스템 의존성 설치 (QR 스캔 지원)

`pyzbar` 라이브러리는 `zbar` 공유 라이브러리가 필요합니다.

**macOS (Homebrew):**
```bash
brew install zbar
```

**Ubuntu / Debian:**
```bash
sudo apt-get install libzbar0
```

**Windows:**
일반적으로 `pip install pyzbar`가 필요한 DLL을 포함합니다. 문제가 발생하면 [Visual C++ 재배포 가능 패키지](https://support.microsoft.com/ko-kr/help/2977003/the-latest-supported-visual-c-downloads)를 설치하세요.

### 4. 애플리케이션 실행

```bash
streamlit run app.py
```

애플리케이션이 `http://localhost:8501`에서 열립니다.

---

## 빠른 시작 가이드

### 1단계: 관리자 설정

1. **👤 Admin** 페이지로 이동
2. 최초 로그인 시 기본 자격 증명 사용 (비밀번호 변경 요청됨):
   - 사용자명: `admin`
   - 비밀번호: `admin`
3. **중요**: 즉시 기본 비밀번호를 변경하세요

### 2단계: 체크포인트 생성

1. Admin 페이지에서 **Create Checkpoint** 섹션으로 이동
2. 체크포인트 세부 정보 입력:
   - 이름 (예: "정문")
   - 위치 (예: "A동 1층")
   - 허용 시간 (예: 09:00 - 18:00)
   - QR 방식: **Static** (인쇄용) 또는 **Dynamic** (자동 갱신)
   - 관리자 비밀번호 (Host 페이지 접근용)
3. 이 체크포인트에 접근 가능한 방문객 선택
4. **Create Checkpoint** 클릭

### 3단계: 방문객 등록

1. **Guest Management** 섹션으로 이동
2. **Register New Guest** 클릭
3. 방문객 정보 입력:
   - 이름 (필수)
   - 이메일 (필수)
   - 전화번호 (선택)
   - 타임존 (예: Asia/Seoul)
   - 허용 체크포인트
   - 커스텀 허용 시간 (선택)
4. **Register Guest** 클릭

### 4단계: QR 코드 표시 (Host)

1. **🖥️ Host** 페이지로 이동
2. 드롭다운에서 체크포인트 선택
3. 체크포인트의 관리자 비밀번호 입력
4. QR 코드가 표시됩니다:
   - **정적 QR**: 다운로드하여 인쇄 후 영구 부착
   - **동적 QR**: 브라우저를 열어둠; 30분마다 자동 갱신

### 5단계: 방문객 체크인/체크아웃

1. **👋 Guest** 페이지로 이동
2. **이름**과 **이메일**을 입력하여 인증
3. 작업 선택: **Check In** 또는 **Check Out**
4. QR 코드 스캔:
   - **카메라** (모바일 기기)
   - **QR 이미지 업로드** (스크린샷 또는 파일)
5. 시스템이 검증하고 활동 기록
6. **My Visit History** 섹션에서 개인 방문 기록 조회

---

## 사용 예시

### 시나리오 1: 사무실 건물 출입

**설정:**
- 체크포인트 생성: "정문"
- 허용 시간: 08:00 - 20:00
- QR 방식: Dynamic (보안)
- 직원을 방문객으로 등록

**일일 사용:**
- 호스트가 입구 모니터에 동적 QR 코드 표시
- 직원들이 출근 시 QR 코드 스캔하여 체크인 (08:30)
- 퇴근 시 다시 스캔하여 체크아웃 (18:15)
- 관리자가 실시간 활동 기록 모니터링

---

### 시나리오 2: 이벤트 등록

**설정:**
- 체크포인트 생성: "컨퍼런스 등록 데스크"
- 허용 시간: 09:00 - 18:00
- QR 방식: Static (인쇄용)
- 이벤트 참석자를 방문객으로 등록

**행사 당일:**
- 정적 QR 코드를 인쇄하여 등록 데스크에 배치
- 참석자들이 도착 시 QR 코드 스캔
- 스태프가 Admin 대시보드로 체크인 상태 모니터링
- 활동 기록을 CSV로 내보내 출석 기록 작성

---

### 시나리오 3: 다중 시설 관리

**설정:**
- 각 건물(A, B, C, D)에 대한 체크포인트 생성
- 건물별로 다른 허용 시간
- 특정 방문객을 특정 건물에 할당
- 계약업체 직원에 대한 방문객 수준 시간 제한

**운영:**
- 각 건물이 자체 QR 코드 표시 (정적 또는 동적)
- 방문객은 권한이 있는 건물만 접근 가능
- 계약업체 직원 접근이 할당된 시간으로 자동 제한
- 활동 기록이 모든 건물 간 이동 추적

---

## 시스템 아키텍처

```
qr_in_out/
├── app.py                  # Streamlit 메인 진입점
├── pages/
│   ├── 1_👤_Admin.py      # 관리자 관리 인터페이스
│   ├── 2_🖥️_Host.py       # QR 코드 표시 페이지
│   └── 3_👋_Guest.py      # 방문객 체크인/체크아웃 페이지
├── core/
│   ├── models.py           # 데이터 모델 (Checkpoint, Guest, ActivityLog)
│   ├── storage.py          # 스레드 안전 작업이 있는 JSON 저장소
│   ├── auth.py             # 인증 및 비밀번호 해싱
│   ├── qr_manager.py       # QR 생성, 검증, 서명
│   ├── time_service.py     # World Time API를 통한 시간 동기화
│   └── time_validator.py   # 시간 기반 접근 제어 검증
├── utils/
│   └── helpers.py          # 유틸리티 함수 (이메일 검증, 조회)
├── data/                   # JSON 저장 파일 (자동 생성)
│   ├── checkpoints.json
│   ├── guests.json
│   ├── activity_logs.json
│   └── admin_settings.json
├── docs/                   # 문서 및 기획 산출물
│   └── planning-artifacts/
│       ├── PRD-Overview.md
│       ├── PRD-Admin.md
│       ├── PRD-Host.md
│       └── PRD-Guest.md
├── requirements.txt        # Python 의존성
└── README.md              # 이 파일
```

---

## 보안 고려사항

### 현재 보안 조치

- 관리자 및 체크포인트 접근을 위한 비밀번호 해싱
- 동적 QR 코드의 HMAC-SHA256 서명
- 재사용 공격 방지를 위한 순차 번호 검증
- 로컬 시간 조작 방지를 위한 시간 동기화
- 소프트 삭제 메커니즘 (데이터 보존)
- 스레드 안전 동시 저장소 접근

### ⚠️ 보안 경고

**프로덕션 배포 전:**

✅ **v1.0에서 수정됨**: 비밀번호 해싱을 bcrypt로 업그레이드
✅ **v1.0에서 수정됨**: SECRET_KEY를 환경 변수로 이동
✅ **v1.0에서 수정됨**: 삭제된 방문객 인증 우회 패치

**여전히 필요한 작업:**

1. **환경 설정**: `.env` 파일에 `QR_SECRET_KEY` 설정:
   ```bash
   # .env.example을 .env로 복사하고 비밀 키 설정
   cp .env.example .env
   # .env를 편집하여 QR_SECRET_KEY를 안전한 랜덤 값으로 설정
   ```

2. **기본 자격 증명**: 첫 로그인 시 기본 관리자 비밀번호 변경 (자동으로 안내됨)

3. **HTTPS**: 프로덕션에서는 HTTPS로 배포 (Streamlit은 리버스 프록시를 통해 지원)

4. **데이터 암호화**: 매우 민감한 배포 환경에서는 저장된 데이터 암호화 고려

5. **파일 권한**: `data/` 디렉토리에 제한된 권한 설정 (0700)

자세한 보안 분석 및 추가 권장사항은 [SECURITY.md](docs/SECURITY.md)를 참조하세요.

---

## 설정

### 시스템 설정 (Admin 페이지)

- **Admin Timezone**: 관리자 작업의 기본 타임존
- **Default Guest Timezone**: 새 방문객의 기본 타임존
- **QR Refresh Interval**: 동적 QR 갱신 주기 (기본: 1800초 / 30분)
- **Require Time Sync**: World Time API를 통한 시간 동기화 강제

### 환경 변수

`.env` 파일 생성 (git에 커밋하지 않음):

```env
QR_SECRET_KEY=여기에-안전한-랜덤-키-최소-32자
STREAMLIT_SERVER_PORT=8501
```

---

## 데이터 모델

### Checkpoint (체크포인트)
```python
{
  "id": "uuid",
  "name": "정문",
  "location": "A동 1층",
  "allowed_hours": {"start_time": "09:00", "end_time": "18:00"},
  "qr_mode": "static" | "dynamic",
  "admin_password_hash": "hashed_password",
  "allowed_guests": ["guest_id_1", "guest_id_2"],
  "current_qr_sequence": 0,
  "deleted_at": null,
  "created_at": "2026-02-05T10:00:00Z",
  "updated_at": "2026-02-05T10:00:00Z"
}
```

### Guest (방문객)
```python
{
  "id": "uuid",
  "name": "홍길동",
  "email": "hong@example.com",
  "phone": "+82-10-1234-5678",
  "timezone": "Asia/Seoul",
  "allowed_checkpoints": ["checkpoint_id_1"],
  "allowed_hours": {"start_time": "08:00", "end_time": "20:00"},
  "deleted_at": null,
  "created_at": "2026-02-05T10:00:00Z",
  "updated_at": "2026-02-05T10:00:00Z"
}
```

### Activity Log (활동 기록)
```python
{
  "id": "uuid",
  "timestamp": "2026-02-05T14:30:00Z",
  "checkpoint_id": "checkpoint_uuid",
  "guest_id": "guest_uuid",
  "action": "check_in" | "check_out",
  "qr_code_used": "{...qr_content...}",
  "status": "success" | "failure",
  "failure_reason": null | "에러 메시지",
  "metadata": {"scanned_at": "2026-02-05T14:30:00Z"}
}
```

---

## 문제 해결

### 일반적인 문제

**1. "pyzbar library is not available" 오류**

**원인**: `zbar` 시스템 라이브러리 미설치

**해결 방법**: 시스템 의존성 설치:
```bash
# macOS
brew install zbar

# Ubuntu/Debian
sudo apt-get install libzbar0
```

---

**2. 시간 동기화 실패**

**증상**: "Not Synchronized (Using Server Time)" 경고

**원인**:
- 인터넷 연결 없음
- World Time API 사용 불가
- 방화벽이 API 요청 차단

**해결 방법**:
- 인터넷 연결 확인
- 방화벽이 `worldtimeapi.org` 및 `timeapi.io`에 대한 HTTP/HTTPS를 허용하는지 확인
- 시스템은 경고와 함께 로컬 시간으로 대체됩니다

---

**3. "Invalid Signature"로 QR 코드 스캔 실패**

**원인**: SECRET_KEY 불일치 또는 QR 코드 변조

**해결 방법**:
- 모든 구성 요소에서 SECRET_KEY가 일치하는지 확인
- Host 페이지에서 QR 코드 재생성
- QR 코드 내용을 수동으로 편집하지 마세요

---

**4. 방문객 인증 불가**

**원인**:
- 이메일/이름 불일치 (대소문자 구분 확인)
- 방문객 삭제됨 (소프트 삭제)
- 이메일 또는 이름의 오타

**해결 방법**:
- 이름과 이메일의 정확한 철자 확인
- Admin 페이지에서 방문객이 활성 상태(삭제되지 않음)인지 확인
- 이메일은 대소문자를 구분하지 않지만 정확히 일치해야 합니다

---

**5. 허용 시간 중 접근 거부**

**원인**:
- 체크포인트 허용 시간 제한
- 방문객별 허용 시간 제한
- 타임존 불일치

**해결 방법**:
- 체크포인트 및 방문객 허용 시간 모두 확인
- 방문객의 타임존 설정이 실제 위치와 일치하는지 확인
- 현재 시간이 두 시간 창 내에 있는지 확인

---

## 기여

기여를 환영합니다! 다음 가이드라인을 따라주세요:

1. 저장소를 **Fork**하세요
2. 기능에 대한 **브랜치 생성** (`git checkout -b feature/amazing-feature`)
3. 변경 사항을 **커밋** (`git commit -m 'Add amazing feature'`)
4. 브랜치에 **푸시** (`git push origin feature/amazing-feature`)
5. **Pull Request 열기**

### 개발 설정

```bash
# Fork 클론
git clone https://github.com/yourusername/qr-in-out.git
cd qr-in-out

# 가상 환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 테스트 실행 (사용 가능한 경우)
pytest

# 애플리케이션 실행
streamlit run app.py
```

### 코드 스타일

- PEP 8 가이드라인 따르기
- 해당하는 경우 타입 힌트 사용
- 모든 공개 함수에 docstring 추가
- 새 기능에 대한 단위 테스트 작성

---

## 로드맵

### 계획된 기능

- [ ] **향상된 보안**: bcrypt/argon2 비밀번호 해싱으로 마이그레이션
- [ ] **다국어 지원**: 국제화 (i18n)
- [ ] **데이터베이스 백엔드**: 대규모 배포를 위한 PostgreSQL/MySQL 옵션
- [ ] **이메일 알림**: 체크인/체크아웃 시 방문객에게 알림
- [ ] **모바일 앱**: 네이티브 iOS/Android 동반 앱
- [ ] **API 엔드포인트**: 타사 통합을 위한 REST API
- [ ] **분석 대시보드**: 고급 리포팅 및 시각화
- [ ] **역할 기반 액세스 제어**: 관리자 사용자를 위한 세밀한 권한
- [ ] **감사 로그**: 포괄적인 관리자 작업 로깅
- [ ] **백업/복원**: 자동 데이터 백업 기능

---

## 라이선스

이 프로젝트는 MIT 라이선스에 따라 라이선스가 부여됩니다 - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

---

## 감사의 말

- [Streamlit](https://streamlit.io/)으로 구축
- QR 코드 생성: [qrcode](https://pypi.org/project/qrcode/)
- QR 코드 스캔: [pyzbar](https://pypi.org/project/pyzbar/)
- 시간 동기화: [World Time API](http://worldtimeapi.org/) 및 [TimeAPI.io](https://timeapi.io/)
- 타임존 처리: [pytz](https://pypi.org/project/pytz/)

---

## 지원

- **문서**: [docs/](docs/)
- **이슈**: [GitHub Issues](https://github.com/yourusername/qr-in-out/issues)
- **토론**: [GitHub Discussions](https://github.com/yourusername/qr-in-out/discussions)

---

## 면책 조항

이 소프트웨어는 보증 없이 "있는 그대로" 제공됩니다. 프로덕션 환경에 배포하기 전에 보안 고려 사항을 검토하세요. 기본 구성은 개발 및 테스트 목적으로 사용됩니다.

---

**Python과 Streamlit으로 ❤️를 담아 제작**
