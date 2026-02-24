# API / Socket 계약 요약

## 원칙

- 기존 REST/소켓 계약을 유지하면서 비파괴 확장을 적용합니다.
- 데스크톱 전환 항목은 `device_sessions` API와 클라이언트 동기화 계약으로 반영합니다.
- 에러 응답은 기존 필드(`error`, `message`)를 유지하고 i18n 메타 필드를 추가합니다.

## 공통 헤더/언어 계약

- 요청 헤더:
  - `X-App-Language`: `ko`, `ko-KR`, `en`, `en-US` 지원
  - `Accept-Language`: `X-App-Language` 미지정 시 보조 사용
- 서버 API 로케일 우선순위:
  1. 세션 설정값
  2. `X-App-Language`
  3. `Accept-Language`
  4. 기본값 `ko-KR`
- 소켓 로케일 우선순위:
  1. handshake query `lang`
  2. `X-App-Language`
  3. `Accept-Language`
  4. 기본값 `ko-KR`

## 에러 응답 스키마 (호환)

1. HTTP API 에러 (`4xx/5xx`)
- 기존 유지: `error` (한국어 canonical)
- 추가 필드:
  - `error_code`
  - `error_localized`
  - `locale`
- 예시:
```json
{
  "error": "로그인이 필요합니다.",
  "error_code": "AUTH_LOGIN_REQUIRED",
  "error_localized": "Login required.",
  "locale": "en-US"
}
```

2. Socket `error` 이벤트
- 기존 유지: `message` (한국어 canonical)
- 추가 필드:
  - `message_code`
  - `message_localized`
  - `locale`

## 인증/세션 API

1. `POST /api/device-sessions`
- 요청: `{ username, password, device_name, remember }`
- 응답: `{ access_ok, device_token, expires_at, user, csrf_token, device_session_id, remember }`

2. `POST /api/device-sessions/refresh`
- 요청: `{ device_token }` (또는 `X-Device-Token`)
- 응답: `{ access_ok, device_token_rotated, expires_at, user, csrf_token, device_session_id, remember }`

3. `DELETE /api/device-sessions/current`
- 현재 디바이스 세션 폐기

4. `GET /api/device-sessions`
- 현재 사용자 활성 디바이스 목록

5. `DELETE /api/device-sessions/<id>`
- 특정 디바이스 세션 강제 로그아웃

## 업데이트 정책 API

- `GET /api/client/update`
- 쿼리:
  - `client_version` (선택)
  - `channel=stable|canary` (선택, 기본 `stable`)
- 응답:
  - `channel`, `desktop_only_mode`
  - `minimum_version`, `latest_version`
  - `download_url`, `release_notes_url`
  - `update_available`, `force_update`

## 주요 REST API

- 인증: `/api/register`, `/api/login`, `/api/logout`, `/api/me`
- 사용자: `/api/users`, `/api/users/online`, `/api/profile`
- 방:
  - `/api/rooms` (GET/POST)
  - `/api/rooms/<room_id>/messages`
  - `/api/rooms/<room_id>/members` (POST)
  - `/api/rooms/<room_id>/members/<target_user_id>` (DELETE)
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

1. 클라이언트: `POST /api/upload`
2. 서버 응답: `upload_token`, `file_name`, `file_path`, `file_type`
3. 클라이언트 소켓 `send_message`에 `upload_token` 전달
4. 서버가 토큰 검증 후 파일 메시지 저장/중계

## Socket.IO 이벤트 계약

### 클라이언트 -> 서버

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

### 서버 -> 클라이언트

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

## `send_message` 상세 계약

### 요청 페이로드

```json
{
  "room_id": 12,
  "content": "message or cipher text",
  "type": "text|file|image|system",
  "encrypted": true,
  "reply_to": 123,
  "upload_token": "optional-for-file",
  "client_msg_id": "optional-client-generated-id"
}
```

### 서버 검증

- 인증 세션 없는 소켓 연결/송신 거부
- `reply_to`는 동일 `room_id` 메시지만 허용
- 파일/이미지는 `upload_token` 필수
- 잘못된 방 접근, 잘못된 payload 차단

### ACK 응답 (Socket callback)

- 성공: `{ "ok": true, "message_id": 456 }`
- 실패: `{ "ok": false, "error": "..." }`

### `new_message` 반사 필드

- `client_msg_id`가 요청에 있으면 브로드캐스트 payload에도 포함
- 클라이언트는 이를 이용해 pending 메시지와 매칭 가능

## REST -> Socket canonical 브릿지

다음 REST 성공 시 서버가 소켓 이벤트를 직접 emit합니다.

- `POST /api/rooms` -> `room_updated(action=room_created)`
- `POST /api/rooms/<room_id>/members` -> `room_members_updated`, `room_updated`
- `POST /api/rooms/<room_id>/leave` -> `room_members_updated`, `room_updated`
- `DELETE /api/rooms/<room_id>/members/<target_user_id>` -> `room_members_updated`, `room_updated`
- `PUT /api/rooms/<room_id>/name` -> `room_name_updated`, `room_updated`
- `POST /api/rooms/<room_id>/pins` / `DELETE /api/rooms/<room_id>/pins/<pin_id>` -> `pin_updated`
- `POST /api/rooms/<room_id>/polls` -> `poll_created`
- `POST /api/polls/<poll_id>/vote` / `POST /api/polls/<poll_id>/close` -> `poll_updated`
- `POST /api/rooms/<room_id>/admins` -> `admin_updated`, `room_members_updated`

## 보안 정합성 보강 항목

- 소켓 `connect`에서 인증 세션 필수
- `message_read`는 `message_id`가 해당 `room_id` 소속인지 검증
- 메시지 조회 SQL의 답장 JOIN은 동일 방(`rm.room_id = m.room_id`)으로 제한

## 버전 호환

- 암호화:
  - `v2:salt:iv:cipher:hmac` 포맷 우선
  - `v1` (`U2FsdGVkX...`) 복호화 호환 유지
- 서버는 메시지 평문을 복호화하지 않고 저장/중계만 수행합니다.
