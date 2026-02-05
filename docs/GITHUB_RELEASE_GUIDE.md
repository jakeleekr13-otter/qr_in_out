# GitHub Release Guide
## QR In/Out System 공개 가이드

**Version**: 1.0
**Date**: 2026-02-05

---

## 목차

1. [사전 준비](#사전-준비)
2. [Repository 생성](#repository-생성)
3. [코드 준비](#코드-준비)
4. [첫 커밋](#첫-커밋)
5. [Release 생성](#release-생성)
6. [문서 최종 점검](#문서-최종-점검)
7. [홍보 및 공유](#홍보-및-공유)

---

## 사전 준비

### 1. GitHub 계정 확인

GitHub 계정이 없다면 [github.com](https://github.com)에서 생성하세요.

### 2. Git 설치 확인

```bash
git --version
```

설치되지 않았다면:
- **macOS**: `brew install git`
- **Ubuntu**: `sudo apt-get install git`
- **Windows**: [Git for Windows](https://git-scm.com/download/win)

### 3. Git 사용자 정보 설정

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 4. SSH 키 설정 (권장)

```bash
# SSH 키 생성
ssh-keygen -t ed25519 -C "your.email@example.com"

# SSH 키를 SSH 에이전트에 추가
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# 공개 키 복사
cat ~/.ssh/id_ed25519.pub
# 출력된 내용을 GitHub Settings > SSH and GPG keys에 추가
```

---

## Repository 생성

### 1. GitHub에서 New Repository 생성

1. GitHub에 로그인
2. 우측 상단 `+` 클릭 → `New repository`
3. Repository 정보 입력:
   - **Repository name**: `qr-in-out`
   - **Description**: `QR code-based checkpoint access management system built with Python and Streamlit`
   - **Public** / Private 선택 (공개는 Public)
   - ❌ **Initialize with README 체크 해제** (이미 README 있음)
   - ❌ **Add .gitignore 체크 해제** (이미 .gitignore 생성 예정)
   - **License**: MIT License 선택 (권장)

4. `Create repository` 클릭

### 2. License 파일 추가

GitHub에서 생성하지 않았다면, 프로젝트 루트에 `LICENSE` 파일 생성:

```text
MIT License

Copyright (c) 2026 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 코드 준비

### 1. .gitignore 생성

프로젝트 루트에 `.gitignore` 파일 생성:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
venv/
ENV/
env/
.venv

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Streamlit
.streamlit/secrets.toml

# Environment Variables
.env
.env.local
.env.*.local
*.env

# Data (if you don't want to commit sample data)
data/*.json
!data/.gitkeep

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# Temporary files
*.tmp
tmp/
temp/

# pytest
.pytest_cache/
.coverage
htmlcov/

# mypy
.mypy_cache/
.dmypy.json
dmypy.json
```

### 2. data/.gitkeep 생성

데이터 폴더 구조는 유지하되 실제 데이터는 제외:

```bash
mkdir -p data
touch data/.gitkeep
```

### 3. 민감 정보 제거 확인

**⚠️ 중요**: 다음 사항 확인:

- [ ] `.env` 파일이 `.gitignore`에 포함되어 있는지
- [ ] `data/*.json` 파일이 커밋되지 않는지 (개인 데이터 포함 가능)
- [ ] API 키, 비밀번호 등이 코드에 하드코딩되어 있지 않은지
- [ ] `core/qr_manager.py`의 `SECRET_KEY`를 환경 변수로 변경했는지

### 4. 보안 취약점 수정 (선택사항이지만 강력 권장)

GitHub 공개 전에 [SECURITY.md](SECURITY.md)의 Critical 이슈 수정 권장:

1. **Password Hashing**: SHA-256 → bcrypt
2. **Secret Key**: 하드코딩 → 환경 변수
3. **Deleted Guest**: 인증 우회 수정

최소한 README.md에 "⚠️ This is a development version. See SECURITY.md before production use" 경고 추가

---

## 첫 커밋

### 1. Git 초기화

```bash
cd /Users/jakelee/personal_project/qr_in_out/qr_in_out

# 기존 .git이 있다면 제거 (선택사항)
# rm -rf .git

# Git 초기화
git init
```

### 2. 원격 저장소 연결

```bash
# HTTPS 사용 시
git remote add origin https://github.com/yourusername/qr-in-out.git

# SSH 사용 시 (권장)
git remote add origin git@github.com:yourusername/qr-in-out.git
```

### 3. 파일 스테이징

```bash
# 모든 파일 추가
git add .

# 추가된 파일 확인
git status
```

### 4. 첫 커밋

```bash
git commit -m "Initial commit: QR In/Out v1.0

- Add admin, host, and guest pages
- Implement static and dynamic QR code modes
- Add time-based access control
- Include comprehensive documentation
- Add security analysis and recommendations

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### 5. GitHub에 푸시

```bash
# 메인 브랜치 생성 및 푸시
git branch -M main
git push -u origin main
```

---

## Release 생성

### 1. GitHub Release 페이지 이동

1. GitHub repository 페이지로 이동
2. 우측 사이드바에서 `Releases` 클릭
3. `Create a new release` 클릭

### 2. Release 정보 입력

**Tag version**: `v1.0.0`

**Release title**: `v1.0.0 - Initial Release`

**Description** (예시):

```markdown
# QR In/Out v1.0.0 - Initial Release

## Overview
QR In/Out is a comprehensive QR code-based checkpoint access management system built with Python and Streamlit.

## Features
- ✅ Three role-based pages (Admin, Host, Guest)
- ✅ Static and Dynamic QR code modes
- ✅ Time-based access control with timezone support
- ✅ HMAC-SHA256 signatures for QR validation
- ✅ Soft delete mechanism for data preservation
- ✅ Local JSON storage (no external database required)
- ✅ Bilingual documentation (English & Korean)

## What's Included
- Complete implementation of all core features
- Comprehensive documentation (README, PRD, Security Analysis)
- Example usage scenarios
- Troubleshooting guide

## Installation

```bash
# Clone repository
git clone https://github.com/yourusername/qr-in-out.git
cd qr-in-out

# Install dependencies
pip install -r requirements.txt

# Install system dependency (macOS)
brew install zbar

# Run application
streamlit run app.py
```

## ⚠️ Security Notice

**This is a development release.** Before deploying to production:

1. Replace SHA-256 password hashing with bcrypt
2. Move SECRET_KEY to environment variable
3. Review and address security recommendations in [SECURITY.md](docs/SECURITY.md)

See [SECURITY.md](docs/SECURITY.md) for detailed security analysis.

## Documentation

- [README (English)](README.md)
- [README (한국어)](README.ko.md)
- [Security Analysis](docs/SECURITY.md)
- [Product Requirements Documents](docs/planning-artifacts/)

## Tech Stack

- Python 3.9+
- Streamlit
- QRCode & pyzbar
- World Time API
- pytz

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

Built with ❤️ using Python and Streamlit

Co-Authored-By: Claude Sonnet 4.5
```

**Attach binaries** (선택사항): 필요시 ZIP 파일 첨부

**Pre-release**: 베타 버전이라면 체크

**Set as the latest release**: 체크

### 3. Publish Release

`Publish release` 클릭

---

## 문서 최종 점검

### 1. README.md 확인사항

- [ ] 뱃지(Badges)가 정상 표시되는지
- [ ] 설치 가이드가 명확한지
- [ ] 스크린샷이 있다면 정상 로드되는지
- [ ] 라이선스 링크가 작동하는지
- [ ] GitHub repository URL이 올바른지

### 2. README.md에 스크린샷 추가 (권장)

```bash
# 프로젝트 루트에 images/ 폴더 생성
mkdir images

# 스크린샷 파일 추가
# - images/admin-dashboard.png
# - images/host-qr-display.png
# - images/guest-checkin.png
```

README.md 상단에 추가:

```markdown
## Screenshots

### Admin Dashboard
![Admin Dashboard](images/admin-dashboard.png)

### Host QR Display
![Host QR Display](images/host-qr-display.png)

### Guest Check-In
![Guest Check-In](images/guest-checkin.png)
```

커밋 및 푸시:

```bash
git add images/
git add README.md
git commit -m "Add screenshots to README"
git push
```

### 3. GitHub Repository Settings 확인

1. **About** 섹션 편집:
   - Description: `QR code-based checkpoint access management system`
   - Website: (배포한 데모 사이트 URL, 있다면)
   - Topics 추가:
     - `python`
     - `streamlit`
     - `qr-code`
     - `access-control`
     - `checkpoint-management`
     - `attendance-system`

2. **Features** 활성화:
   - ✅ Issues
   - ✅ Discussions (커뮤니티 활성화를 원한다면)
   - ❌ Projects (필요시)
   - ❌ Wiki (문서가 충분하다면 불필요)

---

## 홍보 및 공유

### 1. GitHub Topics 최적화

Repository에 관련 토픽 추가하여 발견 가능성 향상:

- `python`
- `streamlit`
- `qr-code`
- `access-management`
- `checkpoint-system`
- `attendance-tracking`
- `visitor-management`

### 2. Social Media 공유 (선택사항)

- **Twitter/X**: 프로젝트 소개 트윗
- **LinkedIn**: 프로페셔널 네트워크에 공유
- **Reddit**: r/Python, r/learnpython, r/opensource
- **Hacker News**: Show HN 게시

### 3. 관련 커뮤니티 참여

- **Streamlit Forum**: [discuss.streamlit.io](https://discuss.streamlit.io/)
- **Python Korea**: 파이썬 한국 사용자 모임
- **Stack Overflow**: `streamlit` 태그로 질문 답변

### 4. Package Index 등록 (선택사항)

PyPI에 패키지로 등록하려면:

1. `setup.py` 또는 `pyproject.toml` 작성
2. PyPI 계정 생성
3. `twine`으로 업로드:

```bash
pip install twine build

python -m build
twine upload dist/*
```

---

## 유지보수 계획

### 1. Issue 관리

- Bug reports 템플릿 생성
- Feature requests 템플릿 생성
- 라벨 시스템 구축 (bug, enhancement, documentation, etc.)

**Issue 템플릿 예시** (`.github/ISSUE_TEMPLATE/bug_report.md`):

```markdown
---
name: Bug Report
about: Report a bug to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

**Describe the bug**
A clear description of the bug.

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g., macOS 14.0]
- Python version: [e.g., 3.11.5]
- Streamlit version: [e.g., 1.30.0]

**Additional context**
Any other relevant information.
```

### 2. Pull Request 템플릿

`.github/pull_request_template.md`:

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Code refactoring

## Checklist
- [ ] Code follows PEP 8 style guidelines
- [ ] Self-review completed
- [ ] Comments added for hard-to-understand areas
- [ ] Documentation updated
- [ ] Tests added/updated (if applicable)
- [ ] No new warnings introduced
```

### 3. Version 관리

[Semantic Versioning](https://semver.org/) 사용:

- **MAJOR**: 호환성이 깨지는 변경 (예: 2.0.0)
- **MINOR**: 기능 추가 (예: 1.1.0)
- **PATCH**: 버그 수정 (예: 1.0.1)

### 4. 정기 업데이트

- 월 1회: 의존성 업데이트 확인
- 분기 1회: 보안 감사
- 반기 1회: 주요 기능 추가 검토

---

## 체크리스트

### 공개 전 최종 확인

- [ ] `.gitignore` 설정 완료
- [ ] 민감 정보 제거 확인
- [ ] README.md 작성 완료 (영문/한글)
- [ ] LICENSE 파일 추가
- [ ] SECURITY.md 작성
- [ ] 보안 취약점 수정 또는 문서화
- [ ] 스크린샷 추가 (선택사항)
- [ ] requirements.txt 최신화
- [ ] GitHub repository 생성
- [ ] 첫 커밋 및 푸시 완료
- [ ] Release 생성 완료
- [ ] Repository About 섹션 작성
- [ ] Topics 추가
- [ ] Issue/PR 템플릿 생성 (선택사항)

### 공개 후 작업

- [ ] Social media 공유
- [ ] 커뮤니티 포럼 게시
- [ ] Star watchers 모니터링
- [ ] Issue 응답 준비
- [ ] Contributing 가이드 작성 (필요시)
- [ ] Code of Conduct 추가 (필요시)

---

## 추가 리소스

### GitHub 관련

- [GitHub Guides](https://guides.github.com/)
- [GitHub Documentation](https://docs.github.com/)
- [Mastering Markdown](https://guides.github.com/features/mastering-markdown/)

### 오픈소스 관련

- [Open Source Guides](https://opensource.guide/)
- [Choose a License](https://choosealicense.com/)
- [Contributor Covenant](https://www.contributor-covenant.org/) (Code of Conduct)

### Python 패키징

- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI](https://pypi.org/)

---

## 문의

GitHub release 과정에서 문제가 발생하면:

1. GitHub Support: [support.github.com](https://support.github.com/)
2. Git 문서: [git-scm.com/doc](https://git-scm.com/doc)
3. Stack Overflow: `github` 태그로 질문

---

**행운을 빕니다!** 🎉

프로젝트 공개를 축하드립니다. 오픈소스 커뮤니티가 여러분의 작업을 높이 평가할 것입니다.
