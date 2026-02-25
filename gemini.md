# GEMINI.md

프로젝트: `intranet-messenger-main-install`  
최종 업데이트: 2026-02-25

## 1) 이 문서의 역할

Gemini 기반 새 작업 세션이 시작될 때, 현재 프로젝트의 운영 기준선과 구현 규칙을 즉시 파악하도록 돕는 세션 부트스트랩 문서.

## 2) 빠른 컨텍스트 로딩 순서

1. `README.md`
2. `README.en.md`
3. `TRANSITION_CHECKLIST.md` (deprecated, 대체: `docs/CUTOVER_ROLLBACK.md`, `docs/OPERATIONS_RUNBOOK.md`)
4. `FUNCTIONAL_REVIEW_20260223.md` (deprecated, 대체: `IMPLEMENTATION_RISK_AUDIT_20260225.md`)
5. `docs/README.md` (`docs/ko`, `docs/en` 인덱스)
6. 작업 대상 코드 파일

## 3) 프로젝트 스냅샷 (2026-02-25 기준)

- 제품: 사내 메신저 Desktop-First 전환
- 서버: `Flask + Socket.IO + SQLite`
- 클라이언트: `PySide6 + httpx + python-socketio`
- i18n:
  - 기본: `ko-KR`
  - 지원: `en-US`
  - 카탈로그: `i18n/ko/*`, `i18n/en/*`
  - API 에러 호환: `error` 유지 + `error_code`, `error_localized`, `locale` 추가
- 테스트 기준:
  - `pytest tests -q` -> `116 passed`
  - `pytest --maxfail=1` -> `116 passed`
- 배포 기준:
  - 서버 EXE: `messenger.spec`
  - 클라이언트 EXE: `messenger_client.spec`
  - MSI: `scripts/build_msi.ps1`, `packaging/wix/*`

## 4) 반드시 지켜야 할 규칙

### 4.1 보안/인증

- `device_sessions` 토큰은 해시만 저장
- refresh 시 rotating token 유지
- 로그아웃 시 현재 토큰 폐기 + 로컬 토큰 삭제
- `upload_token` 없는 파일형 소켓 메시지는 거부

### 4.2 암호화

- `v2` 포맷 완전 호환 유지
- `v1 (U2FsdGVkX...)` 복호화 호환 유지
- 서버는 E2E 평문 복호화하지 않음

### 4.3 API/소켓 계약

- 기존 REST/Socket 계약을 임의 변경하지 않음
- `POST /api/rooms`는 `members` 우선, `member_ids` 하위 호환
- `GET /api/search`의 `limit/offset` 방어 로직 유지

### 4.4 데스크톱 UX

- `client/ui` 변경 시 시그널/슬롯 인터페이스 유지
- 공통 테마는 `client/ui/theme.py`를 통해 일관 적용
- 로그인/메인/설정/투표/파일/관리자 창의 동작 계약 유지

## 5) 작업 시 권장 절차 (Gemini Session Protocol)

1. 변경 목표를 1~2문장으로 재정의
2. 영향 파일 목록 확정
3. 최소 범위 수정(기능 계약 우선)
4. 아래 검증을 순서대로 실행:
   - `python -m compileall client`
   - `pytest tests -q`
   - `pytest --maxfail=1`
5. 결과를 다음 포맷으로 보고:
   - 변경 파일
   - 기능 영향
   - 테스트 결과
   - 남은 리스크/후속 작업

## 6) 현재 우선 점검 대상 (Open Items)

`IMPLEMENTATION_RISK_AUDIT_20260225.md` 기준:

1. 업로드 토큰 정리 주기/보관 정책 운영값 확정
2. orphan 파일 정리 작업의 운영 모니터링 지표 추가
3. 확장 파일 시그니처 검증의 오탐/누락 관찰 및 정책 보정
4. `room_updated` 증분 업데이트 고도화(추가 API 호출 축소)
5. 릴리즈 시 문서 테스트 수치/날짜 동기화 유지

## 7) 자주 쓰는 명령

- 서버 실행:
  - `python server.py --cli`
- 클라이언트 실행:
  - `python -m client.main --server-url http://127.0.0.1:5000`
- 테스트:
  - `pytest tests -q`
  - `pytest --maxfail=1`
- EXE 빌드:
  - `pyinstaller messenger.spec --noconfirm --clean`
  - `pyinstaller messenger_client.spec --noconfirm --clean`

## 8) Gemini 시작 프롬프트 템플릿

```text
Read `gemini.md`, `README.md`, and `IMPLEMENTATION_RISK_AUDIT_20260225.md`.
Before editing, provide:
1) baseline summary,
2) non-negotiable contracts in this scope,
3) exact files to modify.
Then implement and verify with:
`python -m compileall client`, `pytest tests -q`, `pytest --maxfail=1`.
Finally report changed files and residual risks.
```
