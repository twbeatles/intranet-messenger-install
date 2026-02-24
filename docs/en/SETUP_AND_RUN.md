[Korean version](../ko/SETUP_AND_RUN.md)

# Setup and Run Guide

## Supported Environment

- Client: Windows 10/11
- Server: Windows-first (Linux also possible with Python runtime)
- Python: 3.10+

## 1) Development Environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2) Run Server

CLI mode:

```powershell
python server.py --cli
```

GUI mode (requires PyQt6):

```powershell
python server.py
```

Default port: `5000`

## 3) Run Client

```powershell
python -m client.main --server-url http://127.0.0.1:5000
```

## 4) Change Cutover Mode

Hybrid (web + desktop):

```powershell
.\scripts\set_cutover_mode.ps1 -Mode hybrid -MinVersion 1.0.0 -LatestVersion 1.0.0
```

Desktop-only:

```powershell
.\scripts\set_cutover_mode.ps1 -Mode desktop-only -MinVersion 1.0.0 -LatestVersion 1.0.0 -DownloadUrl "https://intranet.example/messenger/client"
```

## 5) Build EXE

```powershell
.\scripts\build_exe.ps1 -Target all -Clean
```

Output:
- `dist\MessengerServer.exe`
- `dist\MessengerClient.exe`
- `dist\exe\server\MessengerServer.exe`
- `dist\exe\client\MessengerClient.exe`

## 6) Build MSI

Prerequisites:
- WiX Toolset v4 (`wix` CLI)
- built EXEs in `dist\exe\server` and `dist\exe\client`

Client MSI:

```powershell
.\scripts\build_msi.ps1 -Target client -BuildDir "dist\exe\client"
```

Server MSI:

```powershell
.\scripts\build_msi.ps1 -Target server -BuildDir "dist\exe\server"
```

## 7) Tests

All tests:

```powershell
pytest tests -q
```

Critical regressions:

```powershell
pytest tests\test_device_sessions_api.py tests\test_client_update_api.py tests\test_crypto_compat_client.py tests\test_upload_contract_desktop.py -q
```

## 8) Operations Checklist

Verify these values in `config.py`:
- `DESKTOP_ONLY_MODE`
- `DESKTOP_CLIENT_MIN_VERSION`
- `DESKTOP_CLIENT_LATEST_VERSION`
- `DESKTOP_CLIENT_DOWNLOAD_URL`
- `USE_HTTPS`

Apply backup policy to `messenger.db`, `uploads/`, `.secret_key`, `.security_salt`.
