# CLAUDE.md

프로젝트: `intranet-messenger-main-install`  
최종 업데이트: 2026-04-16

## 1) 목적

새 작업 세션에서 Claude가 이 파일 하나로 현재 기준선, 절대 깨지면 안 되는 계약, 실행/검증 루틴을 빠르게 파악하도록 하기 위한 운영 문서.

## 2) 세션 시작 시 필수 확인

1. `README.md`
2. `README.en.md`
3. `docs/CUTOVER_ROLLBACK.md`
4. `docs/OPERATIONS_RUNBOOK.md`
5. `IMPLEMENTATION_FUNCTIONAL_AUDIT_20260416.md`
6. `docs/README.md` (`docs/ko`, `docs/en` 인덱스)
7. 관련 구현 파일(작업 범위별):
   - 서버: `app/__init__.py`, `app/routes.py`, `app/sockets.py`, `app/bootstrap/*`, `app/http/*`, `app/realtime/*`, `app/models/*`
   - 클라이언트: `client/app_controller.py`, `client/controllers/*`, `client/ui/*`, `client/services/*`
   - 배포: `messenger.spec`, `messenger_client.spec`, `scripts/build_msi.ps1`

### 리스크 수용 메모 (R1)

- 현재 저장소에서는 `IMPLEMENTATION_RISK_AUDIT_20260224.md`, `IMPLEMENTATION_RISK_AUDIT_20260225.md`가 삭제 상태일 수 있음.
- 본 세션 기준 정책: **복구하지 않고 삭제 상태를 유지**하며, 대체 기준 문서로 `IMPLEMENTATION_FUNCTIONAL_AUDIT_20260416.md`와 `docs/CUTOVER_ROLLBACK.md`를 사용.

## 3) 현재 기준선 (Baseline)

- 제품 방향: Desktop-First (Windows 설치형 클라이언트 중심)
- 아키텍처: `Flask + Socket.IO + SQLite` 서버 + `PySide6` 클라이언트
- 최신 검증(2026-03-05):
  - `pytest tests -q` -> `173 passed`
  - `pytest --maxfail=1` -> `173 passed`
- 최신 검증(2026-03-10):
  - `pyright` -> `0 errors`
  - `pytest tests -q` -> `174 passed`
- 최신 검증(2026-03-18):
  - `pyright` -> `0 errors`
  - `python -m compileall app client gui` -> 성공
  - `pytest --collect-only -q` -> `177 tests collected`
  - `pytest tests -q` -> `177 passed`
- 최신 검증(2026-04-16):
  - `pyright` -> `0 errors, 0 warnings`
  - `python -m compileall app client gui tests` -> 성공
  - `pytest tests -q` -> `187 passed`
- 정적 분석/에디터 기준:
  - `pyrightconfig.json` (`typeCheckingMode: standard`, Python `3.11`)
  - `.editorconfig`, `.vscode/settings.json` (UTF-8 / workspace Pylance baseline)
- i18n 적용 기준:
  - 기본 로케일: `ko-KR`
  - 지원 로케일: `en-US`
  - 공통 카탈로그: `i18n/ko/*`, `i18n/en/*`
  - 서버 에러 호환: `error` 유지 + `error_code`, `error_localized`, `locale` 추가
- 메신저 UI/UX 리팩토링 적용:
  - `client/ui/theme.py`
  - `client/ui/login_window.py`
  - `client/ui/main_window.py`
  - `client/ui/main_window_sections.py`
  - `client/ui/message_list.py`
  - `client/ui/room_list.py`
  - `client/ui/message_formatters.py`
  - `client/ui/settings_dialog.py`
  - `client/ui/polls_dialog.py`
  - `client/ui/files_dialog.py`
  - `client/ui/admin_dialog.py`
- 구조 분할 기준선:
  - 서버 공개 엔트리(`app/routes.py`, `app/sockets.py`)는 shim 유지
  - 실제 서버 구현은 `app/bootstrap/*`, `app/http/*`, `app/realtime/*`로 분할
  - `client/app_controller.py`는 facade 유지, 세부 협력은 `client/controllers/*`로 이동
  - `gui/server_window.py`는 shell 유지, 프로세스/트레이/설정/토스트는 `gui/*` helper로 이동
  - `static/css/style.css`는 manifest 유지, 실제 규칙은 분할 CSS 파일에서 import
  - `templates/index.html`은 `static/js/modules/main.js` 단일 module 엔트리만 로드

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
- 서버는 일반 경로에서 메시지 평문 복호화를 수행하지 않음
- 단, 현재 모델은 **서버 신뢰형 키 중계 모델**이며 strict server-blind E2E는 아님

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

우선순위가 높은 미해결 항목은 `IMPLEMENTATION_FUNCTIONAL_AUDIT_20260416.md` 기준으로 관리:

1. `ENTERPRISE_AUTH_PROVIDER` 운영 환경 실설정(HTTP/LDAP 엔드포인트, 타임아웃, 헤더) 검증
2. `UPLOAD_SCAN_PROVIDER` 운영 환경 실설정(HTTP/ClamAV, fail-open 정책, 백엔드 SLA) 검증
3. 업데이트 서명 공개키 운영값과 배포 체크리스트 정합성 검증
4. SQLite -> 서버형 RDBMS/외부 MQ 전환 리허설 구체화
5. DR 리허설 정례화 및 장애주입 시나리오 확대

## 6) 작업 원칙

1. 서버/클라이언트 계약 변경 시 문서 + 테스트를 반드시 같이 갱신
2. 보안 관련 로직(토큰/권한/업로드)은 회귀 테스트 동반
3. 데스크톱 UX 변경은 시그널/슬롯 인터페이스를 깨지 않도록 구현
4. 불필요 파일 삭제 전 `backup/` 이동 기준 유지
5. 루트가 Git 저장소가 아닐 수 있으므로 변경 내역은 문서로 명시
6. 문서 변경 시 `docs/ko/*`와 `docs/en/*`를 함께 갱신

## 7) 변경 후 검증 루틴

1. `pyright`
2. `python -m compileall app client gui tests`
3. `pytest tests -q`
4. `pytest --maxfail=1`
5. 수동 확인:
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
Read `claude.md`, `README.md`, and `IMPLEMENTATION_FUNCTIONAL_AUDIT_20260416.md` first.
Then summarize:
1) current baseline (tests/contracts),
2) risks for this change area,
3) exact files to edit,
and execute the change with verification:
`pyright`, `python -m compileall app client gui tests`, `pytest tests -q`, `pytest --maxfail=1`.
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
