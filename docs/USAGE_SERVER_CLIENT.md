# 서버/클라이언트 사용 가이드

## 서버 EXE 사용법

파일: `MessengerServer.exe`

### 기본 실행 (GUI)

```powershell
.\MessengerServer.exe
```

- 서버 관리 창이 열립니다.
- 시스템 트레이 기반 관리가 가능합니다.

### CLI 실행

```powershell
.\MessengerServer.exe --cli
```

- 콘솔 서버 모드로 실행됩니다.
- 기본 포트: `5000`

### 접속 주소

- 같은 PC: `http://127.0.0.1:5000`
- 사내망: `http://<서버IP>:5000`

## 클라이언트 EXE 사용법

파일: `MessengerClient.exe`

### 기본 실행

```powershell
.\MessengerClient.exe
```

기본 서버 주소는 `http://127.0.0.1:5000` 입니다.

### 서버 주소 지정 실행

```powershell
.\MessengerClient.exe --server-url http://10.0.0.10:5000
```

### 동작 흐름

1. 트레이 상주 시작
2. 저장된 디바이스 토큰으로 자동 로그인 복원 시도
3. 실패 시 로그인 창 표시
4. 로그인 성공 후 방/메시지/파일/투표/관리자 기능 사용

## 운영 시 권장

- 서버:
  - 고정 IP 또는 DNS 이름 사용
  - 정기 백업: `messenger.db`, `uploads/`, `.secret_key`, `.security_salt`
- 클라이언트:
  - 시작프로그램 ON 권장
  - 첫 실행 시 서버 URL 정책 공지

## 자주 발생하는 문제

- 로그인 복원이 안됨:
  - 서버 시간 동기화 확인
  - 디바이스 세션 만료/폐기 상태 확인
- 파일 전송 실패:
  - 서버 파일 크기 제한(`MAX_CONTENT_LENGTH`) 확인
  - 업로드 토큰 만료 여부 확인
- 연결 실패:
  - 방화벽/프록시 WebSocket 정책 확인
