# Desktop Client (PySide6)

설치형 클라이언트 엔트리: `client/main.py`

## 실행

```powershell
python -m client.main --server-url http://127.0.0.1:5000
```

권장 개발/검증 기준은 Python `3.11`이며, 정적 분석/에디터 기본값은 루트의 `pyrightconfig.json`, `.editorconfig`, `.vscode/settings.json`을 따릅니다.

## 주요 구성

- 앱 제어(facade): `client/app_controller.py`
- 조정 계층:
  - `client/controllers/session_coordinator.py`
  - `client/controllers/rooms_coordinator.py`
  - `client/controllers/message_dispatcher.py`
  - `client/controllers/socket_router.py`
  - `client/controllers/dialogs_controller.py`
  - `client/controllers/update_policy.py`
- UI:
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
- 서비스:
  - `client/services/api_client.py` (`httpx`)
  - `client/services/socket_client.py` (`python-socketio`)
  - `client/services/crypto_compat.py` (E2E v1/v2 호환)
  - `client/services/session_store.py` (Credential Manager via `keyring`)
  - `client/services/startup_manager.py` (Windows 시작프로그램)
  - `client/services/tray_manager.py` (트레이/알림)
  - `client/services/update_checker.py` (`/api/client/update` 연동)

현재 구조 원칙:
- `client/app_controller.py`는 공개 진입점/호환 facade 역할을 유지
- coordinator가 서비스/소켓/UI 사이 협력을 조정하고, 직접적인 책임 분리를 담당
- `client/ui/main_window.py`는 signal surface와 윈도우 shell 역할을 유지하고, 렌더링 세부 구현은 helper 모듈로 분리

## 현재 구현 범위

- 인증:
  - 디바이스 세션 로그인
  - remember-me 세션 복원(토큰 refresh)
  - 로그아웃 시 서버 세션/로컬 토큰 정리
- 대화:
  - 방 목록 조회, 방 입장, 메시지 조회
  - 텍스트 메시지 송신(필요 시 E2E 암호화)
  - 새 메시지 수신/읽음/수정/삭제/리액션 증분 반영
- 부가 기능:
  - 파일 업로드 후 `upload_token` 기반 전송
  - 파일 목록/다운로드/삭제
  - 투표 목록/생성/투표/종료
  - 관리자 목록 조회/권한 부여·해제
  - 설정(서버 URL, 시작프로그램, 트레이)
  - 시스템 트레이 상주/알림
  - outbox 영속화 및 재시작 후 pending send 복구

## 동작 흐름

1. 앱 시작
2. 트레이 아이콘 로딩
3. 저장된 디바이스 토큰 refresh 시도
4. 성공 시 자동 로그인 후 소켓 연결
5. 실패 시 로그인 창 표시

## 알려진 다음 작업

- 소켓 이벤트 확장 동기화:
  - `poll_created`, `poll_updated`, `admin_updated`, `pin_updated`
- 채팅 렌더링 고도화:
  - 답장/멘션/코드블록 UX 강화
- 대량 메시지 최적화:
  - (반영) 증분 업데이트 인덱스(`message_id -> row`) 도입
  - (반영) 방 목록 렌더/구독 dedupe + 검색 원격 결과 캐시 적용
  - (잔여) 점진 렌더링 + lazy decrypt 정책 세분화

## 개발 검증

```powershell
pyright
pytest tests\test_client_rooms_performance.py tests\test_client_search_debounce.py tests\test_crypto_compat_client.py -q
```

소스와 문서는 UTF-8로 유지합니다.
