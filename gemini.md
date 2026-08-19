# GEMINI.md

프로젝트: `intranet-messenger-main-install`  
최종 업데이트: 2026-04-16

## 1) 이 문서의 역할

Gemini 기반 새 작업 세션이 시작될 때, 현재 프로젝트의 운영 기준선과 구현 규칙을 즉시 파악하도록 돕는 세션 부트스트랩 문서.

## 2) 빠른 컨텍스트 로딩 순서

1. `README.md`
2. `README.en.md`
3. `docs/CUTOVER_ROLLBACK.md`
4. `docs/OPERATIONS_RUNBOOK.md`
5. `IMPLEMENTATION_FUNCTIONAL_AUDIT_20260416.md`
6. `docs/README.md` (`docs/ko`, `docs/en` 인덱스)
7. 작업 대상 코드 파일
   - 서버: `app/__init__.py`, `app/routes.py`, `app/sockets.py`, `app/bootstrap/*`, `app/http/*`, `app/realtime/*`
   - 클라이언트: `client/app_controller.py`, `client/controllers/*`, `client/ui/*`, `client/services/*`
   - 배포: `messenger.spec`, `messenger_client.spec`, `scripts/build_msi.ps1`

### 리스크 수용 메모 (R1)

- 현재 저장소에서는 `IMPLEMENTATION_RISK_AUDIT_20260224.md`, `IMPLEMENTATION_RISK_AUDIT_20260225.md`가 삭제 상태일 수 있음.
- 본 세션 기준 정책: **복구하지 않고 삭제 상태를 유지**하며, 대체 기준 문서로 `IMPLEMENTATION_FUNCTIONAL_AUDIT_20260416.md`를 사용.

## 3) 프로젝트 스냅샷 (2026-04-16 기준)

- 제품: 사내 메신저 Desktop-First 전환
- 서버: `Flask + Socket.IO + SQLite`
- 클라이언트: `PySide6 + httpx + python-socketio`
- i18n:
  - 기본: `ko-KR`
  - 지원: `en-US`
  - 카탈로그: `i18n/ko/*`, `i18n/en/*`
  - API 에러 호환: `error` 유지 + `error_code`, `error_localized`, `locale` 추가
- 테스트 기준:
  - `pyright` -> `0 errors`
  - `python -m compileall app client gui` -> 성공
  - `pytest --collect-only -q` -> `177 tests collected`
  - `pytest tests -q` -> `177 passed`
- 테스트 기준(2026-04-16):
  - `pyright` -> `0 errors, 0 warnings`
  - `python -m compileall app client gui tests` -> 성공
  - `pytest tests -q` -> `187 passed`
- 정적 분석/에디터 기준:
  - `pyrightconfig.json` (`typeCheckingMode: standard`, Python `3.11`)
  - `.editorconfig`, `.vscode/settings.json` (UTF-8 / workspace Pylance baseline)
- 배포 기준:
  - 서버 EXE: `messenger.spec`
  - 클라이언트 EXE: `messenger_client.spec`
  - MSI: `scripts/build_msi.ps1`, `packaging/wix/*`
- 구조 분할 기준:
  - `app/routes.py`, `app/sockets.py`, `client/app_controller.py`, `static/css/style.css`는 공개 호환 진입점 유지
  - 실제 서버 구현은 `app/bootstrap/*`, `app/http/*`, `app/realtime/*`로 분리
  - 클라이언트 협력 로직은 `client/controllers/*`로 분리
  - `client/ui/main_window.py`는 shell 유지, 렌더 헬퍼는 `client/ui/*` helper 모듈로 분리
  - `gui/server_window.py`는 shell 유지, 프로세스/트레이/설정/토스트는 `gui/*` helper로 분리
  - 웹 엔트리는 `templates/index.html` -> `static/js/modules/main.js` 단일 module 로더 + `static/css/style.css` manifest

## 4) 반드시 지켜야 할 규칙

### 4.1 보안/인증

- `device_sessions` 토큰은 해시만 저장
- refresh 시 rotating token 유지
- 로그아웃 시 현재 토큰 폐기 + 로컬 토큰 삭제
- `upload_token` 없는 파일형 소켓 메시지는 거부

### 4.2 암호화

- `v2` 포맷 완전 호환 유지
- `v1 (U2FsdGVkX...)` 복호화 호환 유지
- 서버는 일반 경로에서 E2E 평문 복호화를 수행하지 않음
- 단, 현재 모델은 서버 신뢰형 키 중계 모델이며 strict server-blind E2E는 아님

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
   - `pyright`
   - `python -m compileall app client gui tests`
   - `pytest tests -q`
   - `pytest --maxfail=1`
5. 결과를 다음 포맷으로 보고:
   - 변경 파일
   - 기능 영향
   - 테스트 결과
   - 남은 리스크/후속 작업

## 6) 현재 우선 점검 대상 (Open Items)

`IMPLEMENTATION_FUNCTIONAL_AUDIT_20260416.md` 기준:

1. `ENTERPRISE_AUTH_PROVIDER` 운영 환경 실설정(HTTP/LDAP 엔드포인트, 타임아웃, 헤더) 검증
2. `UPLOAD_SCAN_PROVIDER` 운영 환경 실설정(HTTP/ClamAV, fail-open 정책, 백엔드 SLA) 검증
3. 업데이트 서명 공개키 운영값과 배포 체크리스트 정합성 검증
4. SQLite -> 서버형 RDBMS/외부 MQ 전환 리허설 구체화
5. DR 리허설 정례화 및 장애주입 시나리오 확대

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
Read `gemini.md`, `README.md`, and `IMPLEMENTATION_FUNCTIONAL_AUDIT_20260416.md`.
Before editing, provide:
1) baseline summary,
2) non-negotiable contracts in this scope,
3) exact files to modify.
Then implement and verify with:
`pyright`, `python -m compileall app client gui tests`, `pytest tests -q`, `pytest --maxfail=1`.
Finally report changed files and residual risks.
```

<!-- SPECKIT-AGENT-GUIDE:START -->

## Spec Kit / Spec-Driven Development (AI 에이전트 필독)

> 이 블록은 GitHub Spec Kit 활성화 및 기능 명세 작업 결과를 AI 에이전트가 바로 쓰도록 정리한 안내입니다.
> 수정 시 마커 주석을 유지하세요. 스크립트/후속 세션이 이 구간을 갱신합니다.

### 이 저장소 상태

- **프로젝트**: `intranet-messenger-main-install`
- **Spec Kit 초기화**: `.specify/ 있음`
- **에이전트 스킬**: Grok=True, Claude=True, Codex/Agy(.agents)=True
- **활성 기능**: 아직 `specs/` 기능 명세 없음 — `.specify/` 만 준비된 상태

### 에이전트가 먼저 읽을 파일

1. `.specify/` 및 `.grok/skills` / `.claude/skills` / `.agents/skills` 의 `speckit-*`
2. 기능 작업 시작 시 `/speckit-specify` 로 `specs/00N-...` 생성

### 권장 워크플로 (스킬 / 슬래시 커맨드)

| 단계 | 커맨드 (Grok/Claude 등) | 산출 |
|------|-------------------------|------|
| 원칙 | `/speckit-constitution` | `.specify/memory/constitution.md` |
| 명세 | `/speckit-specify` | `specs/<id>/spec.md` |
| 계획 | `/speckit-plan` | `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md` |
| 작업 | `/speckit-tasks` | `tasks.md` |
| 구현 | `/speckit-implement` | 코드 (tasks 순서) |
| 갭점검 | `/speckit-converge` | `tasks.md` 에 Phase Convergence **append-only** |

- Codex skills 모드: `$speckit-specify` 형태일 수 있음
- 스킬 파일: `.grok/skills/speckit-*/SKILL.md`, `.claude/skills/speckit-*/SKILL.md`

### 작업 규칙 (에이전트)

1. **새 기능/큰 변경 전** 활성 `spec.md`·`tasks.md` 를 읽고, 없으면 specify→plan→tasks 순으로 만든다.
2. **구현은 tasks.md 체크리스트**를 따른다. 완료 시 `- [ ]` → `- [x]`.
3. **`/speckit-converge` 는 tasks.md 를 rewrite 하지 않는다** — 잔여 갭만 하단 Phase 로 append.
4. brownfield 프로젝트는 상당 기능이 이미 있을 수 있다. 중복 구현 전에 코드·`[x]` 태스크를 확인한다.
5. 웹/데스크톱 패리티 등 **out-of-scope Assumptions** 는 새 feature 로 분리하는 것을 선호한다.
6. 기본 integration 은 **grok** 이며, 동일 레포에 claude / codex / agy 스킬도 multi-install 되어 있을 수 있다.

### 관련 링크

- Spec Kit: https://github.com/github/spec-kit
- 로컬 CLI: `specify` (uv tool, 버전은 `specify version`)

<!-- SPECKIT-AGENT-GUIDE:END -->
