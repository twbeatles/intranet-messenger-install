# 기능 구현 리스크 점검 보고서 (2026-02-24)

## 1) 점검 기준

- 참조 문서:
  - `claude.md`
  - `README.md`
  - `docs/ARCHITECTURE.md`
  - `docs/API_SOCKET_CONTRACT.md`
- 점검 코드:
  - 서버: `app/routes.py`, `app/sockets.py`, `app/auth_tokens.py`, `app/models/*`
  - 클라이언트: `client/app_controller.py`, `client/ui/main_window.py`, `client/services/*`

## 2) 현재 검증 상태

- 테스트 실행: `pytest tests -q`
- 결과: `99 passed` (2026-02-24 실행)

## 3) 주요 발견사항 (심각도 순)

### R1. [Critical] 비멤버의 `leave` 호출이 성공 처리되고 잘못된 소켓 이벤트가 전파됨

- 근거 코드:
  - `app/routes.py:697-722` (`/api/rooms/<room_id>/leave`)
  - `app/models/rooms.py:286-287` (`DELETE` 결과와 무관하게 커밋)
- 확인 결과:
  - 비멤버가 `POST /api/rooms/<id>/leave` 호출 시 `200 {"success": true}`
  - 실제로 방 멤버에게 `room_members_updated(action=member_left)`/`room_updated` 이벤트 전파됨
- 영향:
  - 멤버십 변경 이벤트 위조 가능
  - 클라이언트의 방 목록/읽음 상태 재동기화 오염
- 권고:
  - 라우트에서 `is_room_member` 선검증(비멤버 403)
  - `leave_room_db`가 실제 삭제 여부(`rowcount`)를 반환하도록 변경
  - 삭제 성공 시에만 소켓 emit

### R2. [Critical] 방을 나간 생성자가 관리자 권한을 계속 보유(유령 관리자)

- 근거 코드:
  - `app/models/rooms.py:385-388` (`created_by`만으로 관리자 판단)
  - `app/models/rooms.py:259-287` (생성자 퇴장 시 `rooms.created_by` 정리 없음)
  - `app/routes.py:724-733`, `app/routes.py:1489-1494` (멤버십 없이 관리자 권한 체크만 수행)
- 확인 결과:
  - 생성자가 퇴장 후에도 `DELETE /api/rooms/<id>/members/<target_user_id>` 수행 가능(재현됨)
- 영향:
  - 비멤버가 방 권한/구성을 변경하는 권한 상승
- 권고:
  - 관리자 권한 API에서 `is_room_member`를 필수로 선검증
  - 생성자 퇴장 시 `created_by` 재할당 또는 NULL 처리 규칙 도입
  - `is_room_admin`에서 멤버십 조건을 함께 확인

### R3. [High] 일반 사용자가 `system` 타입 메시지를 위장 전송 가능

- 근거 코드:
  - `app/sockets.py:282-286` (`'system'`을 클라이언트 입력으로 허용)
  - `app/sockets.py:358-360` (검증 없이 `create_message(..., message_type='system')`)
- 확인 결과:
  - 일반 사용자 `send_message(type='system')` 송신 시 서버 저장/브로드캐스트됨
- 영향:
  - 시스템 공지/운영 메시지 신뢰성 훼손
- 권고:
  - 클라이언트 입력에서 `system` 타입 금지
  - 시스템 메시지는 서버 내부 액션(이름변경/공지변경 등)에서만 생성

### R4. [High] `client_msg_id`가 중복 방지에 사용되지 않아 재시도 시 중복 메시지 저장

- 근거 코드:
  - `app/sockets.py:297-300`, `app/sockets.py:362-363` (`client_msg_id`는 trim/반사만 수행)
  - `app/sockets.py:358-360` (중복 체크 없이 매번 insert)
- 확인 결과:
  - 동일 `client_msg_id`를 두 번 보내면 서로 다른 `message_id`로 2건 저장(재현됨)
- 영향:
  - 네트워크 재시도/ACK 유실 시 중복 메시지 발생
- 권고:
  - `(room_id, sender_id, client_msg_id)` 기준 idempotency 보장
  - 중복 요청에는 기존 `message_id`를 ACK로 반환

### R5. [High] 앱 첫 실행 시 시작프로그램이 강제로 활성화됨

- 근거 코드:
  - `client/app_controller.py:180-184`
- 영향:
  - 사용자 동의 없는 자동실행 설정 변경
  - `claude.md` 오픈 이슈와 동일
- 권고:
  - 기본값 OFF 유지
  - `startup/initialized`는 상태 플래그만 저장하고 자동 활성화 제거

### R6. [Medium] 자동 로그인 복원 실패 시 예외 종류와 무관하게 저장 토큰 삭제

- 근거 코드:
  - `client/app_controller.py:211-214`
- 영향:
  - 일시적 네트워크/서버 장애에도 remember-me 세션 소실
- 권고:
  - 401/토큰 무효 응답일 때만 삭제
  - 연결 오류/타임아웃은 유지 후 재시도 유도

### R7. [Medium] 파일 메시지 송신은 ACK/재시도 경로가 없어 실패 감지가 약함

- 근거 코드:
  - `client/app_controller.py:470-478` (ACK callback 없이 전송)
  - `client/app_controller.py:479-482` (서버 반영 전 업로드 성공 알림)
- 영향:
  - 업로드 성공 후 메시지 반영 실패 시 사용자 혼란
- 권고:
  - 텍스트 메시지와 동일하게 pending/failed/retry 큐에 통합
  - `client_msg_id` 기반 ACK 처리 적용

### R8. [Medium] 메시지/타이핑의 본인 판별이 닉네임 문자열 기반이라 충돌 가능

- 근거 코드:
  - `client/ui/main_window.py:272` (`_user_aliases`에 nickname/username 저장)
  - `client/ui/main_window.py:518` (`sender in _user_aliases`로 own 판별)
  - `client/ui/main_window.py:668-669` (동일 방식으로 타이핑 숨김)
- 영향:
  - 같은 닉네임 사용자 메시지가 내 메시지로 렌더링될 수 있음
- 권고:
  - `sender_id == current_user_id` 기준으로 일원화

### R9. [Medium] “활성 디바이스 세션” API에 만료 세션이 포함됨

- 근거 코드:
  - `app/auth_tokens.py:196-203` (`revoked_at IS NULL`만 필터, `expires_at` 필터 없음)
  - `app/routes.py:353-362` (`/api/device-sessions`가 그대로 반환)
- 영향:
  - UI/운영에서 실제 활성 세션 파악 혼선
- 권고:
  - 활성 목록은 `expires_at > now`로 필터
  - 필요 시 `expired_sessions`를 별도 필드로 분리

### R10. [Medium] `room_updated` 이벤트가 전역 전파되어 불필요한 재조회/정보 노출 가능

- 근거 코드:
  - `app/routes.py:99-121` (`_emit_socket_event`, `broadcast` 인자를 실질적으로 사용하지 않음)
  - `app/routes.py:563-572`, `685-693`, `713-721`, `757-766`, `795-804` (broadcast 이벤트 다수)
  - `client/app_controller.py:143` (`room_updated` 수신 시 방 목록 재조회 스케줄)
- 영향:
  - 비관련 사용자까지 재조회 트래픽 증가
  - 방 활동 메타(룸 ID/행위) 불필요 노출
- 권고:
  - 영향 사용자(해당 방 멤버/관련 당사자) 대상 emit으로 축소

### R11. [Medium] 파일 메시지 처리 실패 시 orphan 파일/메타 불일치 가능

- 근거 코드:
  - `app/sockets.py:339-347` (토큰 소비 후)
  - `app/sockets.py:369-374`, `382-385` (실패 시 orphan 경고만 남김)
- 영향:
  - 디스크 누수
  - 메시지 존재하지만 파일 목록/다운로드와 불일치 가능
- 권고:
  - `create_message`와 `add_room_file`를 트랜잭션 단위로 묶고 실패 보상 삭제 수행

### R12. [Low/Perf] 읽음/변경 이벤트마다 전체 메시지 재조회

- 근거 코드:
  - `client/app_controller.py:647-653`, `662-664`, `666-670`, `676-680`
- 영향:
  - 다중 사용자/활발한 방에서 API 호출량 급증
- 권고:
  - 이벤트 payload 기반 부분 업데이트(증분 반영) 전환

## 4) 우선 조치 권고 (단기)

1. 권한/무결성 이슈 우선 수정: `R1`, `R2`, `R3`, `R4`
2. 데스크톱 UX 회귀/신뢰성 개선: `R5`, `R6`, `R7`
3. 성능/운영 품질 개선: `R9`, `R10`, `R11`, `R12`

## 5) 테스트 추가 권고

- `test_leave_room_requires_membership`:
  - 비멤버 `leave`가 403이며 소켓 이벤트가 발생하지 않아야 함
- `test_left_creator_cannot_admin_or_kick`:
  - 퇴장한 생성자는 관리자 API 호출 불가
- `test_socket_send_message_rejects_system_type_from_client`:
  - 클라이언트 `type=system` 거부
- `test_send_message_idempotency_by_client_msg_id`:
  - 동일 `client_msg_id` 재전송 시 중복 insert 방지
- `test_file_send_ack_flow_desktop_client`:
  - 파일 송신 실패 시 pending/failed 상태 반영
