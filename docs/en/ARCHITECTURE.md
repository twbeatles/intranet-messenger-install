[Korean version](../ko/ARCHITECTURE.md)

# Architecture Overview

## Goal

Keep existing features/business logic while removing browser dependency and moving to an installable desktop-first messenger architecture.

## System Components

1. Central Server
- Stack: `Flask + Flask-SocketIO + SQLite`
- Responsibility:
  - authentication/session/authorization
  - message/file/poll/admin APIs
  - realtime relay via Socket.IO
  - device session token issue/rotate/revoke

2. Desktop Client
- Stack: `PySide6 + httpx + python-socketio`
- Responsibility:
  - sign-in/session restore
  - room/message UI
  - files/polls/admin UI flows
  - tray, notifications, startup behavior

3. Storage
- DB: `messenger.db` (SQLite)
- Uploads: `uploads/`
- Server-side sessions: `flask_session/`

## Server Layers

- Entry: `server.py`
- App factory: `app/__init__.py`
- REST routes: `app/routes.py`
- Socket events: `app/sockets.py`
- Device-token auth: `app/auth_tokens.py`
- Models: `app/models/*`

## Client Layers

- Entry: `client/main.py`
- Orchestration: `client/app_controller.py`
- UI widgets: `client/ui/*`
- Services: `client/services/*`

## Auth/Session Design

1. Login (`POST /api/device-sessions`)
- validates username/password
- issues `device_token`
- stores only `token_hash` on server

2. Auto-login after app restart
- load token from local secure storage
- rotate token via `POST /api/device-sessions/refresh`
- rebuild Flask session on success

3. Logout
- call `DELETE /api/device-sessions/current`
- remove local token

## Security Notes

- Message E2E: v2 format with v1 compatibility
- Server stores/relays encrypted content without plaintext decrypt
- File message send requires `upload_token`
- Socket.IO CORS default is same-origin

## Cutover Modes

- Hybrid mode: `DESKTOP_ONLY_MODE=False`
- Desktop-only mode: `DESKTOP_ONLY_MODE=True`
- Mode automation: `scripts/set_cutover_mode.ps1`
