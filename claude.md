# CLAUDE.md

프로젝트: `intranet-messenger-main-install`  
최종 업데이트: 2026-02-25

## 1) 목적

새 작업 세션에서 Claude가 이 파일 하나로 현재 기준선, 절대 깨지면 안 되는 계약, 실행/검증 루틴을 빠르게 파악하도록 하기 위한 운영 문서.

## 2) 세션 시작 시 필수 확인

1. `README.md`
2. `README.en.md`
3. `TRANSITION_CHECKLIST.md` (deprecated, 대체: `docs/CUTOVER_ROLLBACK.md`, `docs/OPERATIONS_RUNBOOK.md`)
4. `FUNCTIONAL_REVIEW_20260223.md` (deprecated, 대체: `IMPLEMENTATION_RISK_AUDIT_20260225.md`)
5. `docs/README.md` (`docs/ko`, `docs/en` 인덱스)
6. 관련 구현 파일(작업 범위별):
   - 서버: `app/routes.py`, `app/sockets.py`, `app/models/*`
   - 클라이언트: `client/app_controller.py`, `client/ui/*`, `client/services/*`
   - 배포: `messenger.spec`, `messenger_client.spec`, `scripts/build_msi.ps1`

## 3) 현재 기준선 (Baseline)

- 제품 방향: Desktop-First (Windows 설치형 클라이언트 중심)
- 아키텍처: `Flask + Socket.IO + SQLite` 서버 + `PySide6` 클라이언트
- 최신 검증(2026-02-25):
  - `pytest tests -q` -> `116 passed`
  - `pytest --maxfail=1` -> `116 passed`
- i18n 적용 기준:
  - 기본 로케일: `ko-KR`
  - 지원 로케일: `en-US`
  - 공통 카탈로그: `i18n/ko/*`, `i18n/en/*`
  - 서버 에러 호환: `error` 유지 + `error_code`, `error_localized`, `locale` 추가
- 메신저 UI/UX 리팩토링 적용:
  - `client/ui/theme.py`
  - `client/ui/login_window.py`
  - `client/ui/main_window.py`
  - `client/ui/settings_dialog.py`
  - `client/ui/polls_dialog.py`
  - `client/ui/files_dialog.py`
  - `client/ui/admin_dialog.py`

## 4) 핵심 계약 (절대 깨지면 안 됨)

### 4.1 파일 전송 보안 계약

- 업로드: `POST /api/upload`
  - `room_id` 필수
  - 성공 응답에 `upload_token` 포함
- 소켓: `send_message`
  - `type in ('file', 'image')`이면 `upload_token` 필수
  - 클라이언트가 보낸 임의 `file_path`를 신뢰하지 않음

### 4.2 디바이스 세션 계약

- 자동 로그인 API:
  1. `POST /api/device-sessions`
  2. `POST /api/device-sessions/refresh`
  3. `DELETE /api/device-sessions/current`
  4. `GET /api/device-sessions`
  5. `DELETE /api/device-sessions/<id>`
- 정책:
  - 토큰 평문 미저장(해시 저장)
  - refresh 시 rotating token
  - 만료/폐기 토큰 인증 실패 처리

### 4.3 암호화 호환 계약

- 메시지 E2E:
  - `v2` 포맷 유지: `v2:salt_b64:iv_b64:cipher_b64:hmac_b64`
  - `v1`(CryptoJS/OpenSSL `"U2FsdGVkX..."`) 복호화 호환 유지
- 서버는 평문 복호화하지 않고 저장/중계 계약 유지

### 4.4 API 안정성 계약

- `POST /api/rooms`
  - 표준 키: `members`
  - 호환 키: `member_ids` (하위 호환)
- `GET /api/search`
  - `limit` clamp(`1..200`)
  - `offset >= 0`

### 4.5 운영 모드 계약

- `config.py`:
  - `DESKTOP_ONLY_MODE`
  - `DESKTOP_CLIENT_MIN_VERSION`
  - `DESKTOP_CLIENT_LATEST_VERSION`
  - `DESKTOP_CLIENT_DOWNLOAD_URL`
- 전환 스크립트: `scripts/set_cutover_mode.ps1`

## 5) 현재 오픈 이슈 (다음 구현 시 우선 점검)

우선순위가 높은 미해결 항목은 `IMPLEMENTATION_RISK_AUDIT_20260225.md` 기준으로 관리:

1. 업로드 토큰 정리 주기/보관 정책 운영값 확정
2. orphan 파일 정리 작업의 운영 모니터링 지표 추가
3. 확장 파일 시그니처 검증의 오탐/누락 관찰 및 정책 보정
4. `room_updated` 증분 업데이트 고도화(추가 API 호출 축소)
5. 릴리즈 시 문서 테스트 수치/날짜 동기화 유지

## 6) 작업 원칙

1. 서버/클라이언트 계약 변경 시 문서 + 테스트를 반드시 같이 갱신
2. 보안 관련 로직(토큰/권한/업로드)은 회귀 테스트 동반
3. 데스크톱 UX 변경은 시그널/슬롯 인터페이스를 깨지 않도록 구현
4. 불필요 파일 삭제 전 `backup/` 이동 기준 유지
5. 루트가 Git 저장소가 아닐 수 있으므로 변경 내역은 문서로 명시
6. 문서 변경 시 `docs/ko/*`와 `docs/en/*`를 함께 갱신

## 7) 변경 후 검증 루틴

1. `python -m compileall client`
2. `pytest tests -q`
3. `pytest --maxfail=1`
4. 수동 확인:
   - 자동 로그인 복원(앱 재시작)
   - 파일 업로드 후 `upload_token` 연계 전송
   - 룸 입장 후 소켓 메시지 수신/읽음 반영
   - 설정에서 자동실행/트레이 옵션 동작

## 8) 빌드/실행 명령 요약

- 서버 실행: `python server.py --cli`
- 클라이언트 실행: `python -m client.main --server-url http://127.0.0.1:5000`
- 서버 EXE: `pyinstaller messenger.spec --noconfirm --clean`
- 클라이언트 EXE: `pyinstaller messenger_client.spec --noconfirm --clean`
- MSI: `scripts/build_msi.ps1`

## 9) Claude 세션 시작 프롬프트 템플릿

아래를 새 세션 첫 메시지로 사용:

```text
Read `claude.md`, `README.md`, and `IMPLEMENTATION_RISK_AUDIT_20260225.md` first.
Then summarize:
1) current baseline (tests/contracts),
2) risks for this change area,
3) exact files to edit,
and execute the change with verification:
`python -m compileall client`, `pytest tests -q`, `pytest --maxfail=1`.
```
