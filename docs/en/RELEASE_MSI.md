[Korean version](../ko/RELEASE_MSI.md)

# MSI Release Guide

## Purpose

Standard procedure for building, validating, and shipping `MessengerClient.msi` and `MessengerServer.msi`.

## Prerequisites

- OS: Windows 10/11
- Python 3.10+
- dependencies installed: `pip install -r requirements.txt`
- WiX Toolset v4 (`wix` CLI)
- code-signing certificate (required for production)

## Artifact Paths

- MSI output: `dist/msi/`
- EXE build script: `scripts/build_exe.ps1`
- EXE spec:
  - server: `messenger.spec`
  - client: `messenger_client.spec`
- WiX definitions:
  - `packaging/wix/MessengerClient.wxs`
  - `packaging/wix/MessengerServer.wxs`
- MSI build script: `scripts/build_msi.ps1`

## Release Steps

1. Pin versions
- update `config.py`:
  - `DESKTOP_CLIENT_MIN_VERSION`
  - `DESKTOP_CLIENT_LATEST_VERSION`
- if needed, sync WiX `Version` fields:
  - `packaging/wix/MessengerClient.wxs`
  - `packaging/wix/MessengerServer.wxs`

2. Build EXEs

```powershell
.\scripts\build_exe.ps1 -Target all -Clean
```

- `scripts/build_msi.ps1` consumes built EXEs.
- server input EXE name: `MessengerServer.exe`
- client input EXE name: `MessengerClient.exe`

3. Build MSI

```powershell
# Server MSI
.\scripts\build_msi.ps1 -Target server -BuildDir "dist\exe\server"

# Client MSI
.\scripts\build_msi.ps1 -Target client -BuildDir "dist\exe\client"
```

4. Verify artifacts
- `dist\msi\MessengerServer.msi`
- `dist\msi\MessengerClient.msi`

5. Installation smoke test
- clean environment install/uninstall check
- server:
  - startup works
  - `GET /api/client/update` response OK
- client:
  - sign in works
  - tray + auto-login restore works

6. Code-signing (recommended)
- sign EXE/MSI to reduce SmartScreen warnings
- record SHA256 hashes after signing

7. Publish
- publish download URL and release notes
- update runtime update policy in `config.py` (or deployment config)

## Operational Validation Commands

```powershell
pytest tests\test_device_sessions_api.py tests\test_client_update_api.py tests\test_crypto_compat_client.py tests\test_upload_contract_desktop.py -q
```

```powershell
python -m compileall server.py app client
```

## Failure Checklist

- `wix` command missing: check WiX install/path
- EXE name mismatch: verify `MessengerClient.exe`, `MessengerServer.exe`
- WiX `Source` path issue: verify `BuildDir`
- version conflict on install: verify version increment + `MajorUpgrade`

## Release Checklist

| Item | Criteria | Done |
|---|---|---|
| Version sync | `config.py` + WiX versions updated | [ ] |
| EXE ready | server/client EXE names and locations are correct | [ ] |
| MSI built | `dist/msi/*.msi` generated | [ ] |
| Feature sanity | login/message/file/poll/admin smoke tests pass | [ ] |
| Auto-login | token refresh after app restart works | [ ] |
| Code-sign | EXE/MSI signed and hashes recorded | [ ] |
| Update policy | `/api/client/update` values applied | [ ] |
