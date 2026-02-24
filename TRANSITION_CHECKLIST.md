# Desktop Cutover Checklist (2026-02-23)

## 1) 계약/호환
- [x] 기존 REST 계약 유지
- [x] 기존 Socket.IO 이벤트 계약 유지
- [x] E2E `v2` + `v1` 복호화 호환 유지
- [x] `device_sessions` API 추가
- [x] `/api/client/update` 정책 API 추가

## 2) 서버 인증 확장
- [x] `device_sessions` 테이블 추가
- [x] 토큰 해시 저장(평문 미저장)
- [x] refresh 시 회전(rotating token) 적용
- [x] 로그아웃 시 현재 토큰 폐기
- [x] 장기 미사용 세션 정리 배치 작업
- [x] 보안 감사 로그 대시보드

## 3) 데스크톱 클라이언트 코어
- [x] `PySide6` 메인 윈도우/로그인 창
- [x] `httpx` 기반 API 클라이언트
- [x] `python-socketio` 기반 실시간 연결
- [x] Windows Credential Manager 세션 저장
- [x] Windows 시작프로그램 등록/해제
- [x] 트레이 상주/알림
- [x] 소켓 이벤트 동기화 고도화(투표/관리자/공지)

## 4) 기능 이행(1차)
- [x] 인증/세션 복원
- [x] 방 목록/입장/메시지 조회
- [x] 텍스트 송신 + E2E 암호화 경로
- [x] 파일 업로드/다운로드/삭제 기본 흐름
- [x] 투표 조회/생성/투표/종료
- [x] 관리자 조회/권한 부여·해제
- [x] 리액션/멘션/답장 UI 고도화
- [x] 대량 메시지 가상화 렌더링

## 5) 배포/운영
- [x] WiX MSI 템플릿 추가
- [x] MSI 빌드 스크립트(`scripts/build_msi.ps1`) 추가
- [x] cutover 설정 스크립트(`scripts/set_cutover_mode.ps1`) 추가
- [x] CI 자동 빌드 파이프라인
- [x] 코드서명 및 배포 채널 분리

## 6) 전환 게이트
- [x] 핵심 체크리스트 100% 통과
- [x] 보안 회귀 테스트 통과
- [x] 자동실행/자동로그인/재연결 E2E 통과
- [x] 롤백 리허설 완료

## 다음 단계 우선순위
1. 데스크톱 파일럿 배포(하이브리드 모드)
2. 운영 데이터 성능/장애 리허설 완료
3. 전사 전환 후 데스크톱 전용 모드 고정

## 2026-02-24 점검/반영 메모
- 반영 파일:
  - `app/auth_tokens.py`, `app/models/base.py`, `app/sockets.py`
  - `client/services/socket_client.py`, `client/app_controller.py`, `client/ui/main_window.py`
  - `i18n/ko/client.json`, `i18n/en/client.json`
  - `app/routes.py`, `config.py`
  - `client/services/update_checker.py`, `client/services/api_client.py`
  - `scripts/sign_release.ps1`, `scripts/set_release_channel.ps1`, `scripts/rehearse_rollback.ps1`
  - `tests/test_desktop_e2e_smoke.py`, `tests/test_client_update_api.py`
  - `.github/workflows/ci.yml`
  - `tests/test_device_session_cleanup.py`
- 검증:
  - `python -m compileall app client gui` 통과
  - `pytest tests -q` 통과 (`99 passed`)
  - `scripts/rehearse_rollback.ps1` 통과

## 2026-02-24 정합성 보강(추가)

- [x] 비인증 소켓 연결 차단 (`connect` 인증 필수)
- [x] `reply_to` 교차 방 참조 차단 + 동일 방 JOIN 제한
- [x] `message_read` 메시지-방 정합성 검증
- [x] REST 성공 경로의 canonical socket emit 브릿지 보강
  - 방/멤버/이름/공지/투표/관리자 변경 이벤트
- [x] 데스크톱 기능 동등성 보강
  - 방 생성/초대/이름변경/나가기/프로필 편집 UI 연결
- [x] 타이핑 송신 debounce 경로 연결
- [x] 메시지 송신 ACK/pending/failed/retry UX 반영
- [x] 설정 UI 업데이트 채널(`stable`/`canary`) 추가
- [x] SessionStore keyring/fallback 일관성 수정
- [x] 내부 예외 문자열 사용자 응답 노출 제거
- [x] 운영 환경 HTTPS 기본값을 환경변수 기반으로 보강
- [x] 회귀 테스트 추가
  - `tests/test_socket_security_regressions.py`
  - `tests/test_session_store_fallback.py`
