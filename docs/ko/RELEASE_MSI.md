[English version](../en/RELEASE_MSI.md)

# MSI 릴리즈 가이드

## 목적

`MessengerClient.msi`, `MessengerServer.msi`를 일관된 절차로 빌드/검증/배포하기 위한 운영 문서입니다.

## 사전 요구사항

- OS: Windows 10/11
- Python 3.10+
- 의존성 설치: `pip install -r requirements.txt`
- WiX Toolset v4 (`wix` CLI)
- 코드서명 인증서(운영 배포 시 필수)

## 현재 저장소 기준 산출물 경로

- MSI 출력: `dist/msi/`
- EXE 빌드 스크립트: `scripts/build_exe.ps1`
- EXE spec:
  - 서버: `messenger.spec`
  - 클라이언트: `messenger_client.spec`
- WiX 정의:
  - `packaging/wix/MessengerClient.wxs`
  - `packaging/wix/MessengerServer.wxs`
- MSI 빌드 스크립트: `scripts/build_msi.ps1`

## 릴리즈 단계

1. 버전 고정
- `config.py`의 다음 값을 릴리즈 버전에 맞게 업데이트:
  - `DESKTOP_CLIENT_MIN_VERSION`
  - `DESKTOP_CLIENT_LATEST_VERSION`
- 필요 시 WiX `Version` 필드도 동기화:
  - `packaging/wix/MessengerClient.wxs`
  - `packaging/wix/MessengerServer.wxs`

2. EXE 빌드 준비
- 먼저 EXE 생성:

```powershell
.\scripts\build_exe.ps1 -Target all -Clean
```

- `scripts/build_msi.ps1`는 만들어진 EXE를 입력으로 받습니다.
- 서버 EXE 입력 파일명: `MessengerServer.exe`
- 클라이언트 EXE 입력 파일명: `MessengerClient.exe`

3. MSI 빌드

```powershell
# Server MSI
.\scripts\build_msi.ps1 -Target server -BuildDir "dist\exe\server"

# Client MSI
.\scripts\build_msi.ps1 -Target client -BuildDir "dist\exe\client"
```

4. 산출물 확인
- `dist\msi\MessengerServer.msi`
- `dist\msi\MessengerClient.msi`

5. 기본 설치 검증
- 클린 환경에서 설치/삭제 정상 동작 확인
- 서버:
  - 기동 가능 여부
  - `GET /api/client/update` 응답 확인
- 클라이언트:
  - 로그인 가능 여부
  - 트레이 실행/자동 로그인 복원 확인

6. 코드서명 (운영 권장)
- EXE/MSI에 서명 적용 후 SmartScreen 경고 최소화
- 서명 후 해시값(SHA256) 기록

7. 릴리즈 노트/배포
- 배포 URL 및 릴리즈 노트를 공개
- `config.py` 또는 운영 설정으로 업데이트 정책 반영

## 운영 체크 명령

```powershell
pytest tests\test_device_sessions_api.py tests\test_client_update_api.py tests\test_crypto_compat_client.py tests\test_upload_contract_desktop.py -q
```

```powershell
python -m compileall server.py app client
```

## 실패 시 점검 포인트

- `wix` 명령 미존재: WiX 설치/환경변수 확인
- EXE 파일명 불일치: `MessengerClient.exe`, `MessengerServer.exe` 확인
- WiX `Source` 경로 오류: `BuildDir` 경로 재확인
- 버전 충돌 설치 실패: `MajorUpgrade`/버전 증가 여부 확인

## 릴리즈 체크리스트

| 항목 | 기준 | 완료 |
|---|---|---|
| 버전 동기화 | `config.py` + WiX 버전 반영 | [ ] |
| EXE 준비 | client/server EXE 파일명 일치 | [ ] |
| MSI 빌드 | `dist/msi/*.msi` 생성 | [ ] |
| 기능 검증 | 로그인/메시지/파일/투표/관리자 확인 | [ ] |
| 자동로그인 검증 | 앱 재시작 후 토큰 refresh | [ ] |
| 코드서명 | EXE/MSI 서명 및 해시 기록 | [ ] |
| 배포 정책 반영 | `/api/client/update` 값 반영 | [ ] |

