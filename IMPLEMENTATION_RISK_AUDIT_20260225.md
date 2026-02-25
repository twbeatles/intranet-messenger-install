# 기능 구현 리스크 및 추가 과제 점검 보고서 (2026-02-25)

## 0) 가정 및 기본값

- 작성 언어: 한국어
- 기존 문서 보존: `IMPLEMENTATION_RISK_AUDIT_20260224.md`는 유지
- 이번 산출물: 신규 문서 1개 생성 (`IMPLEMENTATION_RISK_AUDIT_20260225.md`)
- 날짜 표기: 절대 날짜 `2026-02-25` 고정
- 범위: 확정 이슈 + 확장 제안 모두 포함
- 이번 턴은 코드 변경 없이 문서 점검 결과만 기록

## 1) 점검 기준

- 기준 문서
  - `claude.md`
  - `README.md`
- 코드 점검 범위
  - 서버: `app/routes.py`, `app/__init__.py`, `app/upload_tokens.py`, `app/utils.py`
  - 클라이언트: `client/app_controller.py`
- 관련 테스트 참조
  - `tests/test_device_session_policy.py`
  - `tests/test_session_token_invalidation.py`
  - 기타 `tests/` 전체 회귀 결과

## 2) 검증 기준선

- 테스트 실행 명령: `pytest tests -q`
- 실행 결과: `106 passed (2026-02-25)`
- 참고: Python 3.14 환경의 외부 라이브러리 경고 1건(`langsmith/schemas.py`)이 있었으나 테스트 실패는 아님

## 3) 확정 이슈 (재현/근거 있음)

### R1. [High] `remember` 불리언 파싱 취약 (`POST /api/device-sessions`)

#### 증상

- `remember`에 문자열 `"false"`를 보내도 서버가 `True`로 처리하여 장기 세션 TTL이 발급됨.

#### 근거 라인

- `app/routes.py:273` (`remember = bool(data.get('remember', True))`)
- `app/routes.py:283` (`remember` 값에 따라 TTL 분기)

#### 재현 절차

1. 사용자 등록 후 `POST /api/device-sessions` 호출
2. JSON에 `"remember": "false"`(문자열) 전달
3. 응답/세션 목록의 `remember`, `ttl_days` 확인
4. 실제 관찰: `remember=True`, `ttl_days=30`으로 처리됨

#### 영향

- 클라이언트/중간 계층이 타입을 잘못 보낼 경우, 의도와 다르게 장기 로그인 상태가 유지될 수 있음.
- 보안 정책(단기 세션 강제)의 신뢰성이 낮아짐.

#### 수정 방향

- `remember`는 JSON boolean만 허용하고, 비boolean 입력은 `400`으로 거절.
- 공통 파서(예: strict bool parser) 또는 요청 스키마 검증으로 강제.

#### 필요 테스트

- `test_device_session_remember_strict_boolean`

---

### R2. [High] `is_admin` 불리언 파싱 취약 (`POST /api/rooms/<room_id>/admins`)

#### 증상

- `is_admin`에 문자열 `"false"`를 전달해도 관리자 해제가 되지 않고 성공 응답이 반환될 수 있음.

#### 근거 라인

- `app/routes.py:1539` (`is_admin = data.get('is_admin', True)`)
- `app/models/rooms.py:408` (`role = 'admin' if is_admin else 'member'`)

#### 재현 절차

1. 방 생성 후 대상 사용자를 관리자 승격
2. `POST /api/rooms/<room_id>/admins`에 `"is_admin": "false"` 전달
3. 응답은 `success: true`이나 관리자 목록을 재조회하면 대상이 계속 관리자

#### 영향

- 관리자 권한 제어 API의 의도와 실제 동작이 불일치.
- 운영자가 해제했다고 인지했지만 권한이 유지되는 오동작 가능.

#### 수정 방향

- `is_admin`은 JSON boolean만 허용, 타입 불일치 시 `400` 반환.
- 권한 변경 후 응답에 변경된 최종 role을 포함해 검증 가능성 강화.

#### 필요 테스트

- `test_admin_update_requires_boolean_is_admin`

---

### R3. [High] 세션 토큰 가드의 `/uploads/` 예외로 무효화 직후 요청 우회 가능성

#### 증상

- 세션 무효화 이후에도 `/uploads/...` 요청은 세션 토큰 일관성 가드를 건너뛰어 즉시 `401`이 아닌 응답 경로로 진입 가능.

#### 근거 라인

- `app/__init__.py:267`~`268` (`/uploads/` 경로를 세션 토큰 가드 예외 처리)
- `app/routes.py:1022` 이하 업로드 다운로드 라우트

#### 재현 절차

1. 동일 계정 2세션 로그인
2. 세션 A에서 비밀번호 변경(세션 B 무효화)
3. 세션 B에서 다른 API 호출 전에 `/uploads/notfound.png` 먼저 호출
4. 실제 관찰: `401` 대신 `404` 응답(무효 세션 즉시 차단 계약과 불일치)

#### 영향

- 무효 세션이 보호 리소스 경로에서 즉시 거절되지 않아 인증 계약 일관성이 깨짐.
- 파일 존재 여부/권한 경로에서 추가 정보 노출 가능성이 생김.

#### 수정 방향

- 세션 토큰 무효화 가드를 `/uploads/`에도 동일 적용.
- 파일 라우트는 가드 이후 멤버십/파일권한 검증만 수행하도록 정렬.

#### 필요 테스트

- `test_uploads_respects_session_token_invalidation`

---

### R4. [Medium] 운영 기준 문서 불일치(누락 문서 참조, 테스트 수치 불일치, 기존 리스크 문서 노후화)

#### 증상

- 세션 기준 문서에 존재하지 않는 파일 참조가 남아 있고, 테스트 통과 수치가 최신 상태와 다름.
- 이전 리스크 문서에는 이미 수정된 항목이 남아 있어 현재 우선순위 판단을 왜곡할 수 있음.

#### 근거 라인

- `claude.md:14~15`, `claude.md:94`, `claude.md:135` (누락 문서 참조)
- `claude.md:27~28` (74 passed), `IMPLEMENTATION_RISK_AUDIT_20260224.md:17` (99 passed)
- 현재 기준선: `pytest tests -q` 결과 `106 passed (2026-02-25)`

#### 재현 절차

1. 루트 파일 존재 여부 확인 시 `TRANSITION_CHECKLIST.md`, `FUNCTIONAL_REVIEW_20260223.md` 부재
2. 문서별 테스트 수치 비교 시 74/99/106 혼재
3. 기존 리스크 문서 항목 일부가 현재 코드와 불일치 확인

#### 영향

- 후속 작업자가 잘못된 기준으로 우선순위를 잡을 수 있음.
- 배포/운영 체크리스트 신뢰도 저하.

#### 수정 방향

- 누락 참조 문서는 생성/대체/폐기 표기 중 하나로 정리.
- 테스트 수치는 문서 갱신 시점의 절대 날짜와 함께 동기화.
- 리스크 문서는 날짜별 이력 유지하되, 최신판 링크를 루트/문서 인덱스에 고정.

#### 필요 테스트

- `test_docs_references_exist_or_are_marked_deprecated`

## 4) 확장 제안 (중장기/아키텍처)

### A1. 업로드 토큰 메모리 저장소 내구성/다중 워커 한계

- 근거: `app/upload_tokens.py`는 프로세스 메모리 딕셔너리 기반
- 한계:
  - 서버 재시작 시 토큰 소실
  - 멀티프로세스/다중 인스턴스에서 토큰 공유 불가
- 제안:
  - Redis 또는 DB 기반 토큰 저장소로 전환
  - 토큰 상태(issued/consumed/expired) 감사 로그 추가

### A2. 업로드 토큰 미소비 파일(orphan) 정리 정책/배치 도입

- 현상:
  - `/api/upload`에서 파일 저장 후 토큰 발급
  - 토큰 미소비/만료 시 파일이 남을 수 있음
- 제안:
  - 주기적 orphan 스캐너(파일 시스템 + room_files/upload_token 상태 비교)
  - 유예 기간 기반 정리 및 운영 로그/메트릭화

### A3. 확장자 허용 대비 시그니처 검증 범위 확대

- 근거:
  - `config.py:29` 허용 확장자는 넓음
  - `app/utils.py:179`~`181`에서 시그니처 미정의 확장자는 확장자만으로 허용
- 제안:
  - 확장자별 MIME/매직넘버 검증 커버리지 확대
  - 검증 불가 확장자 정책(차단/제한 업로드) 명확화

### A4. `room_updated` 이벤트 기반 전체 룸 재조회 빈도 최적화

- 근거:
  - `client/app_controller.py:143`에서 `room_updated` 수신 시 룸 재조회 스케줄
  - `client/app_controller.py:335` `_schedule_rooms_reload()` 경로가 다수 이벤트에서 호출
- 제안:
  - 이벤트 payload 기반 부분 업데이트 우선
  - 동일 시간창 내 다중 이벤트 coalescing/debounce 강화
  - 백오프 정책으로 API 버스트 방지

## 5) 우선순위 실행 로드맵

### P0 (즉시) 권한/인증/입력 파싱 보정: R1~R3

1. `remember` strict boolean 강제 + 400 에러 계약 정리
2. `is_admin` strict boolean 강제 + 권한 변경 결과 검증 응답
3. 세션 토큰 무효화 가드에 `/uploads` 포함

### P1 (단기) 테스트/문서 정합성 회복: R4

1. `claude.md` 참조 문서 경로 최신화
2. 테스트 수치/날짜 동기화(절대 날짜 표기)
3. 최신 리스크 문서 링크를 루트/문서 허브에 고정

### P2 (중기) 확장 제안 반영: A1~A4

1. 토큰 저장소 외부화(내구성)
2. orphan 파일 수명주기 관리
3. 파일 시그니처 검증 확장
4. 룸 재조회 트래픽 최적화

## 6) 추가 테스트 설계

### `test_device_session_remember_strict_boolean`

- 목적: `remember` 타입 안정성 보장
- 시나리오:
  - boolean `true/false` 정상 동작
  - 문자열/숫자 입력(`"false"`, `0`, `"0"`)은 `400`

### `test_admin_update_requires_boolean_is_admin`

- 목적: 관리자 권한 변경 API의 타입 안정성 보장
- 시나리오:
  - boolean 입력만 허용
  - `"false"` 입력 시 `400` 및 실제 role 불변 확인

### `test_uploads_respects_session_token_invalidation`

- 목적: 세션 무효화 계약 일관성 보장
- 시나리오:
  - 비밀번호 변경 후 무효 세션으로 `/uploads/...` 첫 요청 시 즉시 `401`
  - 파일 존재/부재 여부와 무관하게 인증 선차단 확인

### `test_docs_references_exist_or_are_marked_deprecated`

- 목적: 운영 문서 참조 무결성 확보
- 시나리오:
  - `claude.md`/운영 핵심 문서의 참조 대상 존재 검증
  - 미존재 문서는 `deprecated`/대체 경로 명시 여부 검증

## 7) 공개 API/인터페이스 변경사항 (이번 턴)

- 이번 턴은 코드 변경 없음(문서 생성만 수행)
- 다만 다음 구현 턴에서 아래 계약 강화를 권고:
  - `POST /api/device-sessions`의 `remember`는 JSON boolean만 허용
  - `POST /api/rooms/<room_id>/admins`의 `is_admin`은 JSON boolean만 허용
  - 세션 무효화 가드는 `/uploads`에도 동일 적용
