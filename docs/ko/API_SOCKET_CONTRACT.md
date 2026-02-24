[English version](../en/API_SOCKET_CONTRACT.md)

# API / Socket 계약 요약

## 원칙

- 기존 REST/소켓 계약은 유지합니다.
- 데스크톱 전환을 위해 디바이스 세션 API만 확장되었습니다.

## 인증/세션 API

1. `POST /api/device-sessions`
- 요청: `{ username, password, device_name, remember }`
- 응답: `{ access_ok, device_token, expires_at, user, csrf_token }`

2. `POST /api/device-sessions/refresh`
- 요청: `{ device_token }`
- 응답: `{ access_ok, device_token_rotated, expires_at, user, csrf_token }`

3. `DELETE /api/device-sessions/current`
- 현재 디바이스 토큰 폐기

4. `GET /api/device-sessions`
- 내 활성 디바이스 목록 조회

5. `DELETE /api/device-sessions/<id>`
- 특정 디바이스 세션 강제 로그아웃

## 업데이트 정책 API

- `GET /api/client/update`
- 쿼리 파라미터:
  - `client_version` (선택)
  - `channel=stable|canary` (선택, 기본 `stable`)
- 응답 필드:
  - `channel`
  - `desktop_only_mode`
  - `minimum_version`
  - `latest_version`
  - `download_url`
  - `release_notes_url`
  - `update_available`
  - `force_update`

## 주요 기능 API

- 인증: `/api/register`, `/api/login`, `/api/logout`, `/api/me`
- 사용자: `/api/users`, `/api/users/online`, `/api/profile`
- 방:
  - `/api/rooms` (GET/POST)
  - `/api/rooms/<room_id>/messages`
  - `/api/rooms/<room_id>/members` (POST/DELETE)
  - `/api/rooms/<room_id>/leave`
  - `/api/rooms/<room_id>/name`
  - `/api/rooms/<room_id>/info`
- 메시지:
  - `/api/messages/<message_id>` (PUT/DELETE)
  - `/api/messages/<message_id>/reactions` (GET/POST)
- 검색:
  - `/api/search`
  - `/api/search/advanced`
- 파일:
  - `/api/upload`
  - `/uploads/<filename>`
  - `/api/rooms/<room_id>/files`
  - `/api/rooms/<room_id>/files/<file_id>`
- 투표:
  - `/api/rooms/<room_id>/polls`
  - `/api/polls/<poll_id>/vote`
  - `/api/polls/<poll_id>/close`
- 관리자:
  - `/api/rooms/<room_id>/admins`
  - `/api/rooms/<room_id>/admin-check`

## 파일 업로드 계약

1. 클라이언트가 `POST /api/upload`로 파일 업로드
2. 서버 응답: `upload_token`, `file_name`, `file_path`, `file_type` 포함
3. 클라이언트 소켓 `send_message` 시 `upload_token` 전달
4. 서버가 토큰 검증 후 파일 메시지 저장/중계

## Socket.IO 이벤트

클라이언트 -> 서버:
- `subscribe_rooms`
- `join_room`
- `leave_room`
- `send_message`
- `message_read`
- `typing`
- `reaction_updated`
- `poll_updated`
- `poll_created`
- `pin_updated`
- `admin_updated`
- `edit_message`
- `delete_message`

서버 -> 클라이언트:
- `new_message`
- `read_updated`
- `user_typing`
- `room_updated`
- `room_name_updated`
- `room_members_updated`
- `message_edited`
- `message_deleted`
- `reaction_updated`
- `poll_updated`
- `poll_created`
- `pin_updated`
- `admin_updated`
- `user_status`
- `error`

## 버전 호환

- 암호화:
  - `v2:salt:iv:cipher:hmac` 포맷 우선
  - `v1` (`U2FsdGVkX...`) 복호화 호환 유지
- 메시지 평문은 서버에서 복호화하지 않습니다.

