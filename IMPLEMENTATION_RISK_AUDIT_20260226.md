# 기능 구현 리스크 및 추가 과제 점검 보고서 (2026-02-26)

## 0) 점검 범위와 기준

- 참조 문서
  - `claude.md`
  - `README.md`
  - `IMPLEMENTATION_RISK_AUDIT_20260225.md`
- 코드 점검 범위
  - 서버: `app/__init__.py`, `app/routes.py`, `app/sockets.py`, `app/upload_tokens.py`, `app/models/*`
  - 클라이언트: `client/app_controller.py`, `client/services/socket_client.py`, `client/ui/main_window.py`
- 목적
  - 기능 구현 관점에서 잠재 장애/권한 누수/운영 리스크를 재점검하고, 즉시 반영 가능한 보강 과제를 우선순위화

## 1) 실행 검증 결과 (이번 점검 세션)

### 1.1 테스트 실행 상태

- 실행 명령: `pytest tests -q`
- 결과: **수집 단계에서 실패(3 errors)**
- 공통 원인: `flask_compress` import 시 `brotli`/`brotlicffi` 미설치로 `ModuleNotFoundError`

### 1.2 재현 명령

- 실행 명령: `python -c "import flask_compress; print('ok')"`
- 결과: `ModuleNotFoundError: No module named 'brotli'`

## 2) 확정/유력 리스크

### R1. [Critical] 클린 환경에서 서버/테스트 기동 실패 가능 (의존성 누락)

- 근거
  - `requirements.txt:20`에 `Flask-Compress`만 명시되어 있고 `brotli`/`brotlicffi`가 없음
  - `app/extensions.py:5`에서 `from flask_compress import Compress`를 모듈 import 시점에 즉시 수행
- 영향
  - `README.md`의 빠른 시작(`pip install -r requirements.txt`)만으로는 서버 및 테스트가 즉시 기동되지 않을 수 있음
  - CI/신규 개발 환경에서 초기 세팅 실패 확률 높음
- 권고
  - `requirements.txt`에 `brotli` 또는 `brotlicffi` 명시 추가
  - 보조적으로 `app/extensions.py`에서 압축 확장 import 실패 시 graceful fallback 처리

---

### R2. [High] 강퇴/퇴장 직후 소켓 room 구독이 해제되지 않아 메시지 수신이 지속될 가능성

- 근거 (정적 분석)
  - 서버 연결 시 사용자의 모든 room에 `join_room` 수행: `app/sockets.py:143`~`149`
  - 메시지 송신 시 room 브로드캐스트: `app/sockets.py:414`
  - 강퇴/퇴장 API는 DB 멤버십만 변경하고 대상 SID를 room에서 강제 `leave`하지 않음: `app/routes.py:722`~`809`
  - 클라이언트는 본인 강퇴/퇴장 이벤트 수신 시 UI 상태만 정리하고 `leave_room` emit을 호출하지 않음: `client/app_controller.py:694`~`707`
  - 소켓 클라이언트 래퍼에 `leave_room` 메서드 자체가 없음: `client/services/socket_client.py`
- 영향
  - 멤버십이 제거된 사용자가 재연결 전까지 해당 room의 `new_message`를 계속 수신할 가능성
  - 권한 모델과 실시간 이벤트 전파 사이의 보안 경계 불일치
- 권고
  - 서버에서 강퇴/퇴장 시 대상 사용자의 활성 SID들을 `room_{id}`에서 강제 제거
  - 클라이언트에도 방어적으로 `leave_room` API를 추가해 self-removal 수신 시 즉시 탈퇴 emit
  - 회귀 테스트 추가: “강퇴/퇴장 직후 해당 사용자에게 `new_message` 미수신” 검증

---

### R3. [Medium] 프로필 이미지 업데이트 비원자성으로 데이터 손실/고아 파일 가능

- 근거
  - 기존 프로필 이미지를 먼저 삭제: `app/routes.py:1182`~`1191`
  - 새 파일 저장 후 DB 반영 시도: `app/routes.py:1194`~`1205`
  - DB 업데이트 실패 시 새 파일 정리/기존 파일 복구 로직 없음
  - 고아 파일 정리 로직은 `profiles` 폴더를 제외: `app/upload_tokens.py:373`~`376`
- 영향
  - DB 갱신 실패 시 사용자 입장에서 기존 프로필이 사라지고, 새 파일이 디스크에 잔류할 수 있음
- 권고
  - 새 파일 임시 저장 -> DB 반영 성공 후 기존 파일 삭제 순서로 트랜잭션 유사 흐름 적용
  - 실패 시 새 파일 즉시 정리
  - 프로필 폴더 전용 orphan 정리 배치(보수적 grace time) 추가

---

### R4. [Medium] 검색 UX에서 서버 레이트 리밋(30/min) 초과 가능성

- 근거
  - 입력 변경마다 즉시 검색 이벤트 발생: `client/ui/main_window.py:265`
  - 로컬 매칭 실패 시 키 입력 단위로 서버 검색 호출: `client/app_controller.py:860`~`892`
  - 서버 `/api/search` 레이트 리밋: `app/routes.py:934` (`30 per minute`)
- 영향
  - 빠른 타이핑/지우기 반복 시 429 응답 유발 가능
  - 사용자에게 결과 목록 빈 화면/깜빡임으로 체감될 수 있음
- 권고
  - 클라이언트 원격 검색 debounce(250~400ms) + in-flight 요청 취소/무시
  - Enter 제출 기반 검색 옵션 또는 최소 글자수 상향(예: 3자)

---

### R5. [Medium] `/api/search/advanced` 운영 방어선이 `/api/search` 대비 약함

- 근거
  - 라우트에 레이트 리밋 데코레이터 없음: `app/routes.py:1604`~`1618`
  - 검색 파라미터 길이/형식 제한(날짜, query 길이 등) 정책이 `/api/search`보다 느슨함
- 영향
  - 고급 검색 경로를 통한 과도한 DB 부하 유입 가능성
  - 일반 검색과의 정책 일관성 저하
- 권고
  - `/api/search/advanced`에도 limiter 적용
  - `query` 길이, `date_from/date_to` 형식, `room_id/sender_id` 타입 검증 추가

---

### R6. [Low, 정책 리스크] 세션 토큰 가드 예외 시 fail-open

- 근거
  - 세션 토큰 검증 중 예외 발생 시 요청을 통과시킴: `app/__init__.py:289`~`291`
- 영향
  - DB 장애/일시 에러 시 만료/무효 세션 차단이 느슨해질 수 있음
- 권고
  - 최소한 민감 API(`메시지 전송/파일 다운로드/계정변경`)는 fail-closed 또는 제한 모드로 분기
  - 예외 발생량 모니터링 지표 추가

## 3) 우선순위 실행 제안

### P0 (즉시)

1. R1 해결: `brotli` 계열 의존성 명시 및 CI 환경에서 재검증
2. R2 해결: 강퇴/퇴장 직후 서버 강제 room unsubscribe 구현 + 회귀 테스트 추가

### P1 (단기)

1. R3 해결: 프로필 이미지 교체 플로우 원자성 보강
2. R4 해결: 검색 입력 debounce/스로틀 적용
3. R5 해결: 고급 검색 라우트 방어선(레이트 리밋/입력 검증) 정렬

### P2 (중기)

1. R6 정책 결정: fail-open 유지 여부 확정 및 운영 경보 체계 보강

## 4) 다음 구현 턴 권장 테스트 추가

- `test_bootstrap_requires_compression_dependency_or_fallback`
- `test_kicked_user_does_not_receive_room_new_message_after_membership_removal`
- `test_profile_image_update_rollback_on_db_failure`
- `test_search_ui_debounce_prevents_rate_limit_burst` (클라이언트 통합/시뮬레이션)
- `test_advanced_search_has_rate_limit_and_input_validation`

## 5) 요약

- 이번 점검에서 가장 시급한 항목은 **환경 기동 실패(R1)** 와 **실시간 권한 경계 누수 가능성(R2)** 입니다.
- `claude.md`에 명시된 “계약을 깨지 않기” 관점에서 보면, 특히 R2는 API 멤버십 상태와 소켓 room 상태의 불일치 문제라 우선 보완이 필요합니다.
- 이번 문서는 코드 변경 없이 점검 결과만 기록했으며, 실제 수정 턴에서는 P0부터 회귀 테스트와 함께 반영하는 것을 권장합니다.
