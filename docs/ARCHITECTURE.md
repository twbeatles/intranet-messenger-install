# 아키텍처 개요

## 목표

기존 기능/비즈니스 로직을 유지하면서 웹 브라우저 의존을 제거하고, 설치형 데스크톱 메신저 중심 구조로 전환합니다.

## 시스템 구성

1. 중앙 서버
- 기술: `Flask + Flask-SocketIO + SQLite`
- 책임:
  - 인증/세션/권한
  - 메시지/파일/투표/관리자 API
  - 소켓 실시간 중계
  - 디바이스 세션 토큰 발급/회전/폐기

2. 데스크톱 클라이언트
- 기술: `PySide6 + httpx + python-socketio`
- 책임:
  - 사용자 로그인/세션 복원
  - 방/메시지 UI
  - 파일/투표/관리자 기능 UI
  - 트레이 상주/알림/자동실행

3. 저장소/파일
- DB: `messenger.db` (SQLite)
- 파일 저장: `uploads/`
- 세션 파일: `flask_session/` (서버사이드 세션)

## 서버 계층

- 엔트리: `server.py`
- 앱 팩토리: `app/__init__.py`
- 라우트: `app/routes.py`
- 소켓 이벤트: `app/sockets.py`
- 인증 토큰: `app/auth_tokens.py`
- 모델: `app/models/*`

## 클라이언트 계층

- 엔트리: `client/main.py`
- 오케스트레이션: `client/app_controller.py`
- UI 위젯: `client/ui/*`
- 서비스: `client/services/*`

## 인증/세션 설계

1. 로그인(`POST /api/device-sessions`)
- 아이디/비밀번호 검증
- `device_token` 발급
- 서버는 `token_hash`만 저장

2. 앱 재시작 자동 로그인
- 로컬 저장소(Windows Credential Manager)에서 토큰 로드
- `POST /api/device-sessions/refresh`로 회전
- 성공 시 Flask 세션 재수립

3. 로그아웃
- `DELETE /api/device-sessions/current` 호출
- 로컬 토큰 삭제

## 보안 포인트

- 메시지 E2E: `v2` 포맷 + `v1` 호환
- 서버는 메시지 평문 복호화 없이 저장/중계
- 파일 메시지 전송은 `upload_token` 검증 필수
- Socket.IO CORS는 기본 동일 출처 정책

## 전환 정책

- 하이브리드 모드: `DESKTOP_ONLY_MODE=False`
- 데스크톱 전용 모드: `DESKTOP_ONLY_MODE=True`
- 모드 변경 자동화: `scripts/set_cutover_mode.ps1`
