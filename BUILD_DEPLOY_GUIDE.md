# 빌드 및 배포 가이드 (Windows 기준)

관련 상세 문서:
- MSI 릴리즈 상세: `docs/RELEASE_MSI.md`
- 운영/장애 대응: `docs/OPERATIONS_RUNBOOK.md`
- 전환/롤백 정책: `docs/CUTOVER_ROLLBACK.md`

## 1) 목표 산출물

- 서버 EXE: `dist/MessengerServer.exe`
- 클라이언트 EXE: `dist/MessengerClient.exe`
- MSI 입력 폴더:
  - 서버: `dist/exe/server/`
  - 클라이언트: `dist/exe/client/`
- MSI 패키지:
  - `dist/msi/MessengerServer.msi`
  - `dist/msi/MessengerClient.msi`

## 2) 사전 준비

1. Windows 10/11
2. Python 3.10+ 및 가상환경
3. 의존성 설치

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pyinstaller
```

4. WiX Toolset v4 설치 (`wix` 명령 사용 가능해야 함)

```powershell
wix --version
```

## 3) EXE 빌드

전체 빌드:

```powershell
.\scripts\build_exe.ps1 -Target all -Clean
```

개별 빌드:

```powershell
.\scripts\build_exe.ps1 -Target server -Clean
.\scripts\build_exe.ps1 -Target client -Clean
```

`spec` 파일 기준:
- 서버: `messenger.spec`
- 클라이언트: `messenger_client.spec`

## 4) MSI 빌드

EXE 빌드 이후 실행:

```powershell
.\scripts\build_msi.ps1 -Target server -BuildDir "dist\exe\server"
.\scripts\build_msi.ps1 -Target client -BuildDir "dist\exe\client"
```

WiX 정의 파일:
- `packaging/wix/MessengerServer.wxs`
- `packaging/wix/MessengerClient.wxs`

## 5) 배포 절차 (권장 순서)

1. 서버 먼저 배포
- `MessengerServer.msi` 설치
- 서버 기동 확인
- `GET /api/client/update` 응답 확인

2. 클라이언트 배포
- `MessengerClient.msi` 전사 배포 (수동/배포도구)
- 자동실행/토큰 복원 정책 확인

3. 컷오버 모드 반영 (필요 시)

```powershell
# 웹 차단 + 데스크톱 전용 전환
.\scripts\set_cutover_mode.ps1 -Mode desktop-only -MinVersion "1.0.0" -LatestVersion "1.0.0" -DownloadUrl "<배포URL>" -ReleaseNotesUrl "<릴리즈노트URL>"

# 하이브리드 복귀
.\scripts\set_cutover_mode.ps1 -Mode hybrid -MinVersion "1.0.0" -LatestVersion "1.0.0"
```

4. 업데이트 채널 분리 설정 (stable/canary)

```powershell
.\scripts\set_release_channel.ps1 `
  -DefaultChannel stable `
  -StableMinVersion "1.0.0" `
  -StableLatestVersion "1.0.0" `
  -StableDownloadUrl "<stable URL>" `
  -CanaryMinVersion "1.1.0" `
  -CanaryLatestVersion "1.1.0" `
  -CanaryDownloadUrl "<canary URL>"
```

## 6) 배포 전 검증 체크

```powershell
pytest tests -q
python -m compileall app client gui
```

필수 수동 검증:
- 로그인/자동로그인 복원
- 메시지 송수신/읽음/리액션
- 파일 업로드/다운로드
- 투표/관리자 기능
- 트레이 상주/재연결

## 7) 코드 서명 (운영 권장)

인증서가 있으면 EXE/MSI에 서명:

```powershell
signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /a dist\MessengerServer.exe
signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /a dist\MessengerClient.exe
signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /a dist\msi\MessengerServer.msi
signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 /a dist\msi\MessengerClient.msi
```

자동 서명 스크립트:

```powershell
.\scripts\sign_release.ps1 -Target all -CertThumbprint "<thumbprint>"
# 또는
.\scripts\sign_release.ps1 -Target all -PfxPath "C:\cert\release.pfx" -PfxPassword "<password>"
```

## 8) 롤백

1. 서버 롤백: 이전 `MessengerServer.msi` 재설치
2. 클라이언트 롤백: 이전 `MessengerClient.msi` 재배포
3. 컷오버 롤백: `-Mode hybrid` 적용

롤백 리허설 자동화:

```powershell
.\scripts\rehearse_rollback.ps1 -MinVersion "1.0.0" -LatestVersion "1.0.0"
```

## 9) 자주 발생하는 실패 원인

- `pyinstaller` 없음: `pip install pyinstaller`
- `wix` 없음: WiX Toolset v4 설치/환경변수 확인
- MSI 빌드 입력 경로 오류: `dist\exe\server`, `dist\exe\client` 확인
- 파일명 불일치: `MessengerServer.exe`, `MessengerClient.exe` 확인
