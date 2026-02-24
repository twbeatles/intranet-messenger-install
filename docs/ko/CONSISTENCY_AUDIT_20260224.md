[English version](../en/CONSISTENCY_AUDIT_20260224.md)

# 문서-코드 정합성 점검 (2026-02-24)

## 1. 점검 범위

- 문서:
  - `README.md`, `README.en.md`
  - `TRANSITION_CHECKLIST.md`
  - `REAL_MESSENGER_IMPLEMENTATION_REVIEW_20260224.md`
  - `docs/ARCHITECTURE.md`, `docs/API_SOCKET_CONTRACT.md`
  - `docs/ko/*`, `docs/en/*` 인덱스/계약/아키텍처 문서
- 코드:
  - 서버: `app/routes.py`, `app/sockets.py`, `app/models/messages.py`, `config.py`
  - 클라이언트: `client/app_controller.py`, `client/ui/main_window.py`, `client/ui/settings_dialog.py`, `client/services/socket_client.py`, `client/services/session_store.py`

## 2. 불일치 항목 및 반영 결과

1. 소켓 보안/정합성
- 불일치: 문서에는 강화 필요로 남아 있었으나 코드 반영 상태가 최신화되지 않음.
- 반영:
  - 비인증 소켓 연결 거부 (`connect`에서 `return False`)
  - `reply_to` 교차 방 참조 차단
  - `message_read` 시 메시지-방 정합성 검증
  - 메시지 조회 JOIN에서 같은 방 답장만 노출

2. REST -> Socket 실시간 동기화
- 불일치: 일부 문서에서 REST 성공 후 실시간 반영 경로가 불명확.
- 반영:
  - 방 생성/초대/나가기/강퇴/이름변경
  - 공지 생성/삭제
  - 투표 생성/투표/종료
  - 관리자 권한 변경
  - 위 동작 성공 시 canonical socket 이벤트 emit

3. 데스크톱 기능 동등성
- 불일치: 문서 체크리스트 대비 UI 동작이 최신 상태로 문서화되지 않음.
- 반영:
  - 방 생성/멤버 초대/방 이름 변경/방 나가기/프로필 수정 UI 연결
  - 타이핑 송신 debounce(500ms) 연결
  - 송신 ACK 기반 pending/failed/retry 상태 표시
  - 업데이트 채널(stable/canary) 설정 UI 추가

4. 세션 저장소 및 운영 보안 기본값
- 반영:
  - keyring 값이 비어도 fallback 파일 로드 재시도
  - clear 시 keyring + fallback 동시 정리
  - `USE_HTTPS`를 운영 환경(`MESSENGER_ENV`, `USE_HTTPS`) 기반 기본값으로 전환

## 3. 계약 문서 보강 항목

- API 에러 응답 메타 필드:
  - `error`, `error_code`, `error_localized`, `locale`
- Socket 에러 메타 필드:
  - `message`, `message_code`, `message_localized`, `locale`
- `send_message` ACK 계약:
  - 성공: `{ ok: true, message_id }`
  - 실패: `{ ok: false, error }`
- `client_msg_id` 전달/반사 계약:
  - 클라이언트가 `send_message`에 `client_msg_id` 포함 가능
  - 서버 `new_message` 페이로드에 동일 값 반사

## 4. 테스트/검증

- 전체 테스트:
  - `pytest tests -q` 통과 (`99 passed`)
- 신규 회귀 테스트:
  - `tests/test_socket_security_regressions.py`
  - `tests/test_session_store_fallback.py`

## 5. 후속 운영 권고

1. 릴리즈 시 체크
- 문서 내 테스트 수치/기능 상태 문구를 배포 시점 결과로 갱신
- 계약 문서 변경 시 ko/en 동시 갱신

2. 자동 검증 제안
- CI에서 문서 링크 무결성 검사 + 주요 계약 스냅샷 검사 추가
