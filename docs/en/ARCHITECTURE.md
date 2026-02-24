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

## Auth / Session Design

1. Login (`POST /api/device-sessions`)
- validates username/password
- issues `device_token`
- stores only `token_hash` on server

2. Auto-login after app restart
- loads token from local secure storage (Windows Credential Manager + fallback file)
- rotates token via `POST /api/device-sessions/refresh`
- rebuilds Flask session on success

3. Logout
- calls `DELETE /api/device-sessions/current`
- removes local token

4. Active session list (`GET /api/device-sessions`)
- default returns active (non-expired) sessions only
- `include_expired=1` includes expired sessions in the response

## Realtime Integrity Layer

- Socket.IO `connect` rejects unauthenticated sessions
- on successful connect, server joins a personal room (`user_{user_id}`) plus membership rooms (`room_{room_id}`)
- `send_message`:
  - client-allowed types are `text|file|image` (`system` is server-internal only)
  - validates same-room `reply_to`
  - enforces DB idempotency using `room_id + sender_id + client_msg_id` unique key
  - validates `upload_token` for file/image types
  - returns ACK (`ok`, `message_id`/`error`)
  - duplicate retries return existing `message_id` ACK without re-insert/re-broadcast
- `message_read`:
  - validates message-room consistency before update
- On REST success paths, server emits canonical socket events only to related rooms/users for multi-client consistency

## Desktop Reliability Layer

- outbound typing with debounce (default 500ms)
- text/file sends share one pending/failed/retry + ACK pipeline
- own-message and own-typing checks are based on `user_id` (not nickname)
- `read_updated`, `reaction_updated`, `message_edited`, `message_deleted` prefer incremental UI updates (fallback reload on miss)
- settings UI supports update channel selection (`stable`/`canary`)

## Security / Operations Notes

- Message E2E: v2 format with v1 compatibility
- Server stores/relays encrypted content without plaintext decrypt
- File message send requires `upload_token`
- when room creator leaves, `created_by` is reassigned (remaining admin first, then member, else `NULL`)
- Socket.IO CORS default is same-origin
- `USE_HTTPS` default is environment-driven (`MESSENGER_ENV`, `USE_HTTPS`) for production safety

## Cutover Modes

- Hybrid mode: `DESKTOP_ONLY_MODE=False`
- Desktop-only mode: `DESKTOP_ONLY_MODE=True`
- Mode automation: `scripts/set_cutover_mode.ps1`
