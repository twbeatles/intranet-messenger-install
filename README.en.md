# Intranet Messenger (Desktop-First)

Korean README: `README.md`

This project is an intranet messenger built with a `Flask + Socket.IO` server and a native `PySide6` desktop client.  
Default UI language is Korean (`ko-KR`) with English (`en-US`) support.

## Quick Start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pyright
python server.py --cli
python -m client.main --server-url http://127.0.0.1:5000
```

Python `3.11` is the recommended verification baseline. Static analysis and editor defaults are pinned in `pyrightconfig.json`, `.editorconfig`, and `.vscode/settings.json`, and source/docs should remain UTF-8.

## Key Features

- Desktop client: tray mode, startup option, session restore, dynamic avatars, and enhanced user theme
- Security: message encryption (v2) + v1 decrypt compatibility (server-trust key relay model)
- Authentication: `device_sessions` issue/rotate/revoke flow
- Operations: `GET /api/system/health` and policy-switch driven observability
- Server i18n compatibility: keep `error`, add `error_code`/`error_localized`
- Web client: i18n-focused maintenance scope (not a full design rewrite)

## Documentation

- Documentation hub: `docs/README.md`
- Korean docs index: `docs/ko/README.md`
- English docs index: `docs/en/README.md`
- Consistency audit (KO/EN): `docs/ko/CONSISTENCY_AUDIT_20260224.md`, `docs/en/CONSISTENCY_AUDIT_20260224.md`
- Implementation risk/roadmap: `OFFLINE_MESSENGER_IMPLEMENTATION_RISK_ROADMAP_20260226.md`
- Feature risk review / implementation batch plan: `IMPLEMENTATION_FEATURE_RISK_REVIEW_20260305.md`
- Root build/deploy guide: `BUILD_DEPLOY_GUIDE.md`
- Session guides: `claude.md`, `gemini.md`

## Project Structure

```text
app/                 Flask app factory + public compatibility shims
app/bootstrap/       runtime/bootstrap wiring
app/http/            split REST route registration/helpers
app/realtime/        split Socket.IO events/state/emission helpers
client/              PySide6 desktop client entry/facade/services
client/controllers/  desktop coordinators/router/policies
client/ui/           Qt windows + extracted render helpers
gui/                 PyQt6 server management GUI + split tray/process helpers
static/css/          CSS manifest entry + split fragments
static/js/modules/   module entry bridge for the maintained web client
i18n/                ko/en catalogs (server/client/web/server_gui)
packaging/wix/       MSI .wxs templates
scripts/             build/cutover automation
docs/                ko/en documentation
```

Compatibility entry points remain stable. `app/routes.py`, `app/sockets.py`, `client/app_controller.py`, and `static/css/style.css` stay as thin public layers so external contracts do not move.

## Tests

```powershell
pyright
pytest tests -q
python -m compileall app client gui
```
