# Intranet Messenger (Desktop-First)

Korean README: `README.md`

This project is an intranet messenger built with a `Flask + Socket.IO` server and a native `PySide6` desktop client.  
Default UI language is Korean (`ko-KR`) with English (`en-US`) support.

## Quick Start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python server.py --cli
python -m client.main --server-url http://127.0.0.1:5000
```

## Key Features

- Desktop client: tray mode, startup option, session restore
- Security: E2E encryption (v2) + v1 decrypt compatibility
- Authentication: `device_sessions` issue/rotate/revoke flow
- Server i18n compatibility: keep `error`, add `error_code`/`error_localized`
- Web client: i18n-focused maintenance scope (not a full design rewrite)

## Documentation

- Documentation hub: `docs/README.md`
- Korean docs index: `docs/ko/README.md`
- English docs index: `docs/en/README.md`
- Root build/deploy guide: `BUILD_DEPLOY_GUIDE.md`
- Session guides: `claude.md`, `gemini.md`

## Project Structure

```text
app/                 Flask routes, sockets, models
client/              PySide6 desktop client
gui/                 PyQt6 server management GUI
i18n/                ko/en catalogs (server/client/web/server_gui)
packaging/wix/       MSI .wxs templates
scripts/             build/cutover automation
docs/                ko/en documentation
```

## Tests

```powershell
pytest tests -q
python -m compileall app client gui
```
