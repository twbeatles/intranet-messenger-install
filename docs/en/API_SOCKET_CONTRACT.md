[Korean version](../ko/API_SOCKET_CONTRACT.md)

# API / Socket Contract Summary

## Principles

- Existing REST/Socket contracts remain stable.
- Desktop migration adds device-session APIs only.

## Auth/Session APIs

1. `POST /api/device-sessions`
- Request: `{ username, password, device_name, remember }`
- Response: `{ access_ok, device_token, expires_at, user, csrf_token }`

2. `POST /api/device-sessions/refresh`
- Request: `{ device_token }`
- Response: `{ access_ok, device_token_rotated, expires_at, user, csrf_token }`

3. `DELETE /api/device-sessions/current`
- revoke current device token

4. `GET /api/device-sessions`
- list active sessions for current user

5. `DELETE /api/device-sessions/<id>`
- force logout a specific device

## Update Policy API

- `GET /api/client/update`
- Query parameters:
  - `client_version` (optional)
  - `channel=stable|canary` (optional, default `stable`)
- Response fields:
  - `channel`
  - `desktop_only_mode`
  - `minimum_version`
  - `latest_version`
  - `download_url`
  - `release_notes_url`
  - `update_available`
  - `force_update`

## Main Feature APIs

- Auth: `/api/register`, `/api/login`, `/api/logout`, `/api/me`
- Users: `/api/users`, `/api/users/online`, `/api/profile`
- Rooms:
  - `/api/rooms` (GET/POST)
  - `/api/rooms/<room_id>/messages`
  - `/api/rooms/<room_id>/members` (POST/DELETE)
  - `/api/rooms/<room_id>/leave`
  - `/api/rooms/<room_id>/name`
  - `/api/rooms/<room_id>/info`
- Messages:
  - `/api/messages/<message_id>` (PUT/DELETE)
  - `/api/messages/<message_id>/reactions` (GET/POST)
- Search: `/api/search`, `/api/search/advanced`
- Files:
  - `/api/upload`
  - `/uploads/<filename>`
  - `/api/rooms/<room_id>/files`
  - `/api/rooms/<room_id>/files/<file_id>`
- Polls:
  - `/api/rooms/<room_id>/polls`
  - `/api/polls/<poll_id>/vote`
  - `/api/polls/<poll_id>/close`
- Admin:
  - `/api/rooms/<room_id>/admins`
  - `/api/rooms/<room_id>/admin-check`

## File Upload Contract

1. client uploads file using `POST /api/upload`
2. server returns `upload_token`, `file_name`, `file_path`, `file_type`
3. client sends socket `send_message` with `upload_token`
4. server validates token and stores/broadcasts file message

## Socket.IO Events

Client -> Server:
- `subscribe_rooms`, `join_room`, `leave_room`
- `send_message`, `message_read`, `typing`
- `reaction_updated`, `poll_updated`, `poll_created`
- `pin_updated`, `admin_updated`
- `edit_message`, `delete_message`

Server -> Client:
- `new_message`, `read_updated`, `user_typing`
- `room_updated`, `room_name_updated`, `room_members_updated`
- `message_edited`, `message_deleted`
- `reaction_updated`, `poll_updated`, `poll_created`
- `pin_updated`, `admin_updated`, `user_status`, `error`

## Compatibility

- Encryption:
  - prefer `v2:salt:iv:cipher:hmac`
  - keep `v1` (`U2FsdGVkX...`) decrypt compatibility
- Server does not decrypt E2E message plaintext.
