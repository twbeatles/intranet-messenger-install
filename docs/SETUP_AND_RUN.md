# 설치 및 실행 가이드

## 지원 환경

- 클라이언트: Windows 10/11
- 서버: Windows 우선 (Linux도 Python 실행 가능)
- Python: 3.10+

## 1) 개발 환경 준비

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2) 서버 실행

CLI 모드:

```powershell
python server.py --cli
```

GUI 서버 창 모드(PyQt6 필요):

```powershell
python server.py
```

기본 포트: `5000`

## 3) 클라이언트 실행

```powershell
python -m client.main --server-url http://127.0.0.1:5000
```

## 4) 컷오버 모드 변경

하이브리드(웹 허용):

```powershell
.\scripts\set_cutover_mode.ps1 -Mode hybrid -MinVersion 1.0.0 -LatestVersion 1.0.0
```

데스크톱 전용:

```powershell
.\scripts\set_cutover_mode.ps1 -Mode desktop-only -MinVersion 1.0.0 -LatestVersion 1.0.0 -DownloadUrl "https://intranet.example/messenger/client"
```

## 5) EXE 빌드

```powershell
.\scripts\build_exe.ps1 -Target all -Clean
```

결과:
- `dist\MessengerServer.exe`
- `dist\MessengerClient.exe`
- `dist\exe\server\MessengerServer.exe`
- `dist\exe\client\MessengerClient.exe`

## 6) MSI 빌드

사전 요구사항:
- WiX Toolset v4 (`wix` CLI)
- 클라이언트/서버 EXE 빌드 결과물 폴더 (`dist\exe\server`, `dist\exe\client`)

클라이언트 MSI:

```powershell
.\scripts\build_msi.ps1 -Target client -BuildDir "dist\exe\client"
```

서버 MSI:

```powershell
.\scripts\build_msi.ps1 -Target server -BuildDir "dist\exe\server"
```

## 7) 테스트

전체:

```powershell
pytest tests -q
```

핵심 회귀:

```powershell
pytest tests\test_device_sessions_api.py tests\test_client_update_api.py tests\test_crypto_compat_client.py tests\test_upload_contract_desktop.py -q
```

## 8) 운영 시 확인 포인트

- `config.py`의 다음 값 확인:
  - `DESKTOP_ONLY_MODE`
  - `DESKTOP_CLIENT_MIN_VERSION`
  - `DESKTOP_CLIENT_LATEST_VERSION`
  - `DESKTOP_CLIENT_DOWNLOAD_URL`
  - `USE_HTTPS`
- `messenger.db`, `uploads/`, 인증 키 파일(`.secret_key`, `.security_salt`) 백업 정책 적용
