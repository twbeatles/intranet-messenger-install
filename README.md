# 🔒 사내 메신저 (Intranet Desktop Messenger)

> **English README**: [`README.en.md`](README.en.md) | **문서 허브**: [`docs/README.md`](docs/README.md)

**사내 메신저**는 사내 업무 환경에서 안전하고 빠른 협업을 지원하기 위해 개발된 **Windows 데스크톱 우선(Desktop-First) 보안 메신저 솔루션**입니다.  
고성능 `Flask + Socket.IO` 백엔드 서버와 직관적이고 미려한 `PySide6` 데스크톱 클라이언트, 그리고 손쉬운 운영을 위한 `PySide6` 서버 관리 GUI를 제공합니다.

---

## 📑 목차

1. [핵심 특징](#-핵심-특징)
2. [빠른 시작 (Quick Start)](#-빠른-시작-quick-start)
3. [데스크톱 클라이언트 사용 가이드](#-데스크톱-클라이언트-사용-가이드)
   - [1. 로그인 및 회원가입](#1-로그인-및-회원가입)
   - [2. 대화방(채팅방) 관리 및 탐색](#2-대화방채팅방-관리-및-탐색)
   - [3. 실시간 대화 및 메시지 기능](#3-실시간-대화-및-메시지-기능)
   - [4. 파일 전송 및 파일 보관함](#4-파일-전송-및-파일-보관함)
   - [5. 투표(Polls) 생성 및 참여](#5-투표polls-생성-및-참여)
   - [6. 대화방 관리자(Admin) 권한 설정](#6-대화방-관리자admin-권한-설정)
   - [7. 클라이언트 환경 설정 및 트레이](#7-클라이언트-환경-설정-및-트레이)
4. [서버 관리자 가이드](#-서버-관리자-가이드)
   - [1. GUI 관리 콘솔 모드](#1-gui-관리-콘솔-모드)
   - [2. CLI 콘솔 모드](#2-cli-콘솔-모드)
   - [3. 주요 서버 환경 설정 (config.py)](#3-주요-서버-환경-설정-configpy)
5. [엔터프라이즈 및 보안 기능](#-엔터프라이즈-및-보안-기능)
6. [빌드 및 배포 (EXE / MSI)](#-빌드-및-배포-exe--msi)
7. [테스트 및 코드 품질 검증](#-테스트-및-코드-품질-검증)
8. [프로젝트 디렉터리 구조](#-프로젝트-디렉터리-구조)

---

## ✨ 핵심 특징

- 🛡️ **종단간 암호화(E2E Encryption v2)**: 서버를 통한 통신 구간 및 저장 데이터 암호화 지원 (v1 복호화 호환).
- 💻 **모던 데스크톱 클라이언트**: `PySide6(Qt6)` 기반의 반응형 UI, 시스템 트레이 백그라운드 상주, Windows 시작 시 자동 실행 지원.
- ⚡ **실시간 통신 & 복원력**: WebSocket(Socket.IO) 기반 실시간 메시징, 타이핑 인디케이터, 오프라인 Outbox 재전송 큐 및 자동 세션 복원.
- 🗂️ **협업 도구 내장**: 대화방 전용 파일 보관함(다운로드/권한 관리), 단일/복수/익명 투표(Polls), 대화방 관리자 위임 기능.
- 🖥️ **원클릭 GUI 서버 매니저**: 서버 시작/중지, 원클릭 자체 서명 SSL 인증서 생성, 실시간 접속자/메시지 통계 모니터링, 실시간 로그 뷰어 제공.
- 🏢 **엔터프라이즈 확장성**: LDAP / Active Directory 및 HTTP 사내 인증 연동 지원, ClamAV 바이러스 스캔 연동, RSA-SHA256 서명 기반 클라이언트 자동 업데이트 검증.
- 🌐 **다국어(i18n) 지원**: 한국어(`ko-KR`) 기본 지원 및 영어(`en-US`) 완벽 대응 (클라이언트/서버/GUI).

---

## 🚀 빠른 시작 (Quick Start)

### 1. 개발 환경 요구사항
- **OS**: Windows 10 / 11 (권장)
- **Python**: `3.11` (CI 및 정적 분석 기준)

### 2. 가상환경 생성 및 의존성 설치
```powershell
# 가상환경 생성 및 활성화
python -m venv .venv
.venv\Scripts\Activate.ps1

# 필수 패키지 설치
pip install -r requirements.txt
pip install pyright
```

### 3. 서버 실행

#### 방법 A. GUI 관리자 창으로 실행 (권장)
```powershell
python server.py
```
> 직관적인 GUI 창이 열리며, 포트 설정, SSL 인증서 발급, 시작/중지 및 실시간 통계를 확인할 수 있습니다.

#### 방법 B. CLI 콘솔 모드로 실행
```powershell
python server.py --cli
```
> 고성능 `gevent` 비동기 루프로 동작하며, 콘솔에 접속 정보와 로그가 출력됩니다. (기본 포트: `5000`)

### 4. 데스크톱 클라이언트 실행
새 PowerShell 터미널을 열고 가상환경을 활성화한 후 클라이언트를 실행합니다:
```powershell
.venv\Scripts\Activate.ps1
python -m client.main --server-url http://127.0.0.1:5000
```

#### 클라이언트 실행 옵션:
| 옵션 | 설명 | 기본값 |
| :--- | :--- | :--- |
| `--server-url <URL>` | 접속할 메신저 서버 주소 지정 | `http://127.0.0.1:5000` |
| `--lang <ko\|en\|auto>` | 클라이언트 UI 표시 언어 지정 | `auto` (시스템 언어 감지) |

---

## 🖥️ 데스크톱 클라이언트 사용 가이드

### 1. 로그인 및 회원가입

```text
┌────────────────────────────────────────┐
│               로그인 화면               │
├────────────────────────────────────────┤
│ 서버 주소 : [ http://127.0.0.1:5000  ] │
│ 아이디    : [ user1                  ] │
│ 비밀번호  : [ ********             👁] │
│ 닉네임    : [ 홍길동                 ] │ (회원가입 시)
│ 기기 이름 : [ Windows Desktop        ] │
│ [v] 로그인 상태 유지 (Remember Me)     │
│                                        │
│     [ 회원가입 ]     [ 로그인 ]        │
└────────────────────────────────────────┘
```

1. **서버 주소 입력**: 사내 메신저 서버 URL(예: `http://192.168.1.100:5000` 또는 `https://messenger.company.local:5000`)을 입력합니다.
2. **회원가입**:
   - `아이디`(3자 이상), `비밀번호`(4자 이상), `닉네임`을 입력한 뒤 **[회원가입]** 버튼을 클릭합니다.
3. **로그인**:
   - 아이디와 비밀번호를 입력하고 **[로그인]**을 클릭합니다.
   - 비밀번호 우측의 눈 아이콘(👁)을 클릭하여 입력한 비밀번호를 확인할 수 있습니다.
   - **[로그인 상태 유지]**를 체크하면 디바이스 토큰이 안전하게 저장되어 다음 실행 시 자동으로 로그인됩니다.

---

### 2. 대화방(채팅방) 관리 및 탐색

- **대화방 목록 및 검색**:
  - 좌측 사이드바 상단의 검색창에 키워드를 입력하면 실시간(디바운스 적용)으로 대화방과 메시지를 필터링합니다.
- **새 대화방 만들기**:
  - 하단의 **[+ 새 대화방]** 버튼을 눌러 대화방 제목을 입력하고 생성합니다.
- **대화방 설정 및 관리** (상단 헤더 우측 메뉴):
  - **초대 (`+`)**: 사내 사용자를 검색하여 현재 대화방으로 초대합니다.
  - **이름 변경**: 대화방 제목을 수정합니다.
  - **나가기**: 대화방에서 퇴장합니다.

---

### 3. 실시간 대화 및 메시지 기능

- **메시지 전송**:
  - 하단 텍스트 창에 내용을 입력하고 `Enter`를 누르거나 **[전송]** 버튼을 클릭합니다. (`Shift + Enter`로 줄바꿈)
- **종단간 암호화(E2E)**:
  - 모든 대화 메시지는 클라이언트 단에서 암호화되어 서버로 전달되므로 안전합니다.
- **실시간 타이핑 알림**:
  - 상대방이 메시지를 입력 중일 때 `"OOO님이 입력 중입니다..."` 안내가 표시됩니다.
- **이모지 리액션**:
  - 메시지에 마우스를 올려 원하는 이모지 반응을 추가하거나 취소할 수 있습니다.
- **메시지 전송 실패 시 복구 (Outbox)**:
  - 일시적인 네트워크 단절로 전송에 실패한 경우 `[재시도]` 버튼이 표시되어 원클릭으로 재전송할 수 있습니다.
- **과거 대화 내역 조회 (무한 스크롤)**:
  - 대화창을 위로 스크롤하면 이전 대화 기록이 자동으로 페이징 로드됩니다.

---

### 4. 파일 전송 및 파일 보관함

1. **파일 전송**:
   - 입력창 우측의 **[첨부 📎]** 버튼을 클릭하거나, 파일을 대화창으로 직접 드래그 앤 드롭합니다.
   - 지원 포맷: 이미지(`png`, `jpg`, `gif`, `webp`), 문서(`pdf`, `doc`, `docx`, `xls`, `xlsx`, `txt`), 압축 파일(`zip`, `7z`, `rar`) 등. (최대 16MB)
2. **파일 보관함 다이얼로그 (`파일 📁`)**:
   - 상단 헤더의 **[파일]** 버튼을 클릭하면 해당 대화방에 공유된 모든 파일 목록이 표시됩니다.
   - 파일 선택 후 **[다운로드]**하거나, 권한이 있는 경우 **[삭제]**할 수 있습니다.

---

### 5. 투표(Polls) 생성 및 참여

1. **투표 열기**:
   - 대화방 상단 메뉴의 **[투표 📊]** 버튼을 클릭합니다.
2. **투표 만들기**:
   - 질문과 선택 항목(최대 여러 개)을 입력합니다.
   - 옵션 설정:
     - `복수 선택 허용`: 참여자가 여러 항목을 동시에 투표 가능
     - `익명 투표`: 투표자 이름을 숨김 처리
     - `마감 일시 지정`: 정해진 일시에 자동으로 투표 마감
3. **투표 참여 및 결과 확인**:
   - 실시간으로 득표율 그래프와 참여 인원수를 확인할 수 있습니다.
   - 투표 생성자는 **[투표 마감]**을 통해 수동으로 투표를 종료할 수 있습니다.

---

### 6. 대화방 관리자(Admin) 권한 설정

- 대화방 상단의 **[관리자 👑]** 버튼을 클릭하여 방 구성원 관리 창을 엽니다.
- 참여자 목록에서 사용자의 온라인/오프라인 상태와 현재 권한(`[ADMIN]` / `[USER]`)을 확인합니다.
- 특정 멤버를 선택하고 **[관리자 지정]** 또는 **[관리자 해제]** 버튼을 눌러 방 관리 권한을 위임/회수합니다.

---

### 7. 클라이언트 환경 설정 및 트레이

좌측 상단 사용자 프로필 옆의 **설정(⚙️)** 버튼을 클릭하여 환경을 설정합니다:

- **서버 설정**:
  - 기본 접속 서버 URL 변경
  - 업데이트 채널 선택 (`stable` / `canary`) 및 **[업데이트 확인]**
- **기본 환경설정**:
  - **표시 언어**: `자동(시스템 기본)`, `한국어`, `English`
  - **Windows 시작 시 자동 실행**: 부팅 시 메신저 자동 기동
  - **닫기 시 트레이로 최소화**: `X` 버튼 클릭 시 프로그램을 종료하지 않고 트레이로 상주
- **시스템 트레이 기능**:
  - 백그라운드 상주 중 새 메시지 도착 시 Windows 알림 토스트 표시
  - 트레이 아이콘 우클릭 메뉴: `열기`, `로그아웃`, `종료`

---

## 🛠️ 서버 관리자 가이드

### 1. GUI 관리 콘솔 모드

실행 명령:
```powershell
python server.py
# 또는 배포된 실행 파일
.\MessengerServer.exe
```

#### 주요 탭 및 기능:
1. **제어(Control) 탭**:
   - **서버 설정**: 포트 번호 지정(기본 `5000`), HTTPS 사용 여부 체크박스
   - **서버 제어**: `▶ 서버 시작` / `■ 서버 중지` 버튼
   - **SSL 인증서 관리**: `🔑 인증서 생성` 버튼 클릭 시 개발/테스트용 자체 서명 SSL 인증서(`cert.pem`, `key.pem`) 즉시 생성
   - **옵션**: `프로그램 시작 시 서버 자동 시작`, `Windows 시작 시 자동 실행`, `트레이로 최소화`, `언어 변경`
   - **접속 정보 안내**: 로컬 IP(`localhost:5000`) 및 사내망 접속 IP(`192.168.x.x:5000`) 실시간 표시
2. **실시간 통계(Stats) 탭**:
   - `현재 접속자 수` (Active Connections)
   - `총 접속 횟수` (Total Connections)
   - `총 메시지 수` (Total Messages)
   - `서버 가동 시간` (Server Uptime)
3. **로그(Logs) 탭**:
   - 서버 내부 접속, 에러, API 호출 내역을 실시간으로 확인 및 `[로그 지우기]` 가능

---

### 2. CLI 콘솔 모드

GUI 없이 콘솔 또는 백그라운드 데몬으로 서버를 실행할 때 사용합니다:
```powershell
python server.py --cli
```

---

### 3. 주요 서버 환경 설정 (`config.py`)

`config.py` 파일 또는 환경변수를 통해 운영 정책을 손쉽게 변경할 수 있습니다:

```python
# [서버 네트워크 설정]
USE_HTTPS = False               # HTTPS 활성화 여부 (환경변수 USE_HTTPS=1 로 덮어쓰기 가능)
DEFAULT_PORT = 5000            # 메신저 기본 서비스 포트
SESSION_TIMEOUT_HOURS = 72     # 세션 유효 기간 (시간)
DEVICE_SESSION_TTL_DAYS = 30   # 디바이스 토큰 유지 기간 (일)

# [파일 업로드 제한]
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 업로드 최대 크기 (16MB)
UPLOAD_FOLDER = 'uploads'              # 업로드 파일 저장 경로

# [컷오버 모드 (웹/데스크톱 전용 모드 전환)]
DESKTOP_ONLY_MODE = False      # True 설정 시 웹 접근 차단 및 데스크톱 다운로드 페이지 안내
DESKTOP_CLIENT_MIN_VERSION = "1.0.0"
DESKTOP_CLIENT_LATEST_VERSION = "1.0.0"
DESKTOP_CLIENT_DOWNLOAD_URL = "http://intranet/downloads/MessengerClient.msi"

# [업데이트 채널 및 서명 검증]
REQUIRE_SIGNED_UPDATES_IN_PROD = True
DESKTOP_CLIENT_SIGNING_PUBLIC_KEY_PEM = "..."  # RSA 공개키
```

---

## 🔒 엔터프라이즈 및 보안 기능

### 1. 엔터프라이즈 계정 연동 (LDAP / Active Directory & HTTP Auth)
`config.py` 설정을 통해 사내 인사 DB나 Active Directory와 계정을 연동할 수 있습니다.
- **LDAP Provider**: `ENTERPRISE_AUTH_ENABLED = True`, `ENTERPRISE_AUTH_PROVIDER = "ldap"`
- **HTTP JSON Provider**: 사내 REST API 인증 시스템 연동

### 2. 파일 업로드 보안 검사 (Anti-Virus)
- **ClamAV (`clamd`) 연동**: 사내 ClamAV 데몬과 통신하여 업로드되는 모든 첨부파일의 악성코드 감염 여부를 실시간 검사합니다.
- **HTTP Scan Provider**: 사내 파일 보안 검사 솔루션 연동 가능.

### 3. 클라이언트 업데이트 서명 검증 (`rsa-sha256`)
- 배포된 클라이언트 실행 파일의 위변조를 방지하기 위해 RSA 공개키/개인키 기반의 서명 검증을 강제합니다.

### 4. 컷오버(Cutover) 전환 스크립트
```powershell
# 웹 인터페이스를 차단하고 데스크톱 전용 모드로 즉시 전환
.\scripts\set_cutover_mode.ps1 -Mode desktop-only -MinVersion "1.0.0" -LatestVersion "1.0.0" -DownloadUrl "http://intranet/MessengerClient.msi"

# 다시 웹/데스크톱 동시 사용(하이브리드) 모드로 복구
.\scripts\set_cutover_mode.ps1 -Mode hybrid -MinVersion "1.0.0" -LatestVersion "1.0.0"
```

---

## 📦 빌드 및 배포 (EXE / MSI)

상세 가이드: [`BUILD_DEPLOY_GUIDE.md`](BUILD_DEPLOY_GUIDE.md)

### 1. PyInstaller EXE 빌드
```powershell
# 전체 (서버 + 클라이언트) 빌드
.\scripts\build_exe.ps1 -Target all -Clean

# 개별 빌드
.\scripts\build_exe.ps1 -Target client -Clean
.\scripts\build_exe.ps1 -Target server -Clean
```
- 결과물: `dist/MessengerServer.exe`, `dist/MessengerClient.exe`

### 2. WiX Toolset v4 기반 MSI 인스톨러 빌드
```powershell
.\scripts\build_msi.ps1 -Target client -BuildDir "dist\exe\client"
.\scripts\build_msi.ps1 -Target server -BuildDir "dist\exe\server"
```
- 결과물: `dist/msi/MessengerClient.msi`, `dist/msi/MessengerServer.msi`

### 3. 코드 서명 (Code Signing)
```powershell
.\scripts\sign_release.ps1 -Target all -PfxPath "C:\cert\release.pfx" -PfxPassword "<비밀번호>"
```

---

## 🧪 테스트 및 코드 품질 검증

본 프로젝트는 철저한 정적 분석과 단위/통합 테스트를 거쳐 관리됩니다.

```powershell
# 1. Pyright 정적 타입 검사
pyright

# 2. Pytest 전체 테스트 실행
pytest tests -q

# 3. 전체 모듈 바이트코드 컴파일 검증
python -m compileall app client gui tests
```

---

## 📂 프로젝트 디렉터리 구조

```text
├─ app/                      # Flask 백엔드 및 Socket.IO 서버 로직
│  ├─ auth/                  # 엔터프라이즈 인증 프로바이더 (LDAP, HTTP)
│  ├─ bootstrap/             # 런타임 초기화, 로깅, 세션 가드, 보안 헤더
│  ├─ http/                  # 분할 REST API 라우트 (auth, messages, rooms, uploads 등)
│  ├─ realtime/              # Socket.IO 이벤트 및 실시간 브로드캐스트 핸들러
│  ├─ models/                # SQLite 데이터 모델 및 쿼리 함수
│  └─ security/              # 파일 업로드 악성코드 스캐너
├─ client/                   # PySide6 기반 데스크톱 클라이언트
│  ├─ controllers/           # 세션/방/메시지 코디네이터 및 소켓 라우터
│  ├─ services/              # API 통신, E2E 암호화, 소켓, 트레이, 업데이트 체커
│  └─ ui/                    # 메인 윈도우, 로그인 창, 설정/파일/투표/관리자 다이얼로그
├─ gui/                      # PySide6 기반 서버 관리자 GUI 콘솔
│  ├─ server_window.py       # 서버 관리 메인 윈도우 UI 및 탭 제어
│  └─ server_process.py      # Flask-SocketIO 멀티프로세스 분리 실행 스레드
├─ i18n/                     # 다국어(한국어/영어) 번역 카탈로그 JSON
├─ packaging/wix/            # WiX Toolset v4 MSI 인스톨러 템플릿
├─ scripts/                  # 빌드, 패키징, 서명, 컷오버 자동화 PowerShell 스크립트
├─ docs/                     # 전체 상세 기술 문서 및 운영 매뉴얼
├─ config.py                 # 전역 서버 및 보안 설정 파일
├─ server.py                 # 서버 실행 엔트리포인트 (GUI / CLI)
└─ BUILD_DEPLOY_GUIDE.md     # 빌드 및 배포 공식 가이드
```

---

## 📖 관련 문서

- 📘 **문서 전체 인덱스**: [`docs/README.md`](docs/README.md)
- 🛠️ **서버/클라이언트 상세 사용법**: [`docs/ko/USAGE_SERVER_CLIENT.md`](docs/ko/USAGE_SERVER_CLIENT.md)
- 🏗️ **시스템 아키텍처 정의서**: [`docs/ko/ARCHITECTURE.md`](docs/ko/ARCHITECTURE.md)
- 🚀 **빌드 및 배포 가이드**: [`BUILD_DEPLOY_GUIDE.md`](BUILD_DEPLOY_GUIDE.md)
- 📋 **운영 런북 & 장애 대응**: [`docs/ko/OPERATIONS_RUNBOOK.md`](docs/ko/OPERATIONS_RUNBOOK.md)
- 🔄 **전환 및 롤백 정책**: [`docs/ko/CUTOVER_ROLLBACK.md`](docs/ko/CUTOVER_ROLLBACK.md)

