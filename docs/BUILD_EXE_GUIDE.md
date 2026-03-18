# EXE 빌드 가이드 (서버/클라이언트)

## 목적

spec 분리 빌드 기반으로 아래 2개 실행파일을 생성합니다.

- `MessengerServer.exe`
- `MessengerClient.exe`

## 사전 준비

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pyinstaller pyright
```

## 1) 자동 빌드 (권장)

```powershell
.\scripts\build_exe.ps1 -Target all -Clean
```

주요 결과:

- 원본 EXE:
  - `dist\MessengerServer.exe`
  - `dist\MessengerClient.exe`
- MSI 입력용 정리 폴더:
  - `dist\exe\server\MessengerServer.exe`
  - `dist\exe\client\MessengerClient.exe`

## 2) 수동 빌드

```powershell
pyinstaller messenger.spec --noconfirm --clean
pyinstaller messenger_client.spec --noconfirm --clean
```

spec 기준:
- `messenger.spec`: `server.py` + `app/**` + `gui/**` + `static/`, `templates/`, `i18n/`, `certs/`
- `messenger_client.spec`: `client/main.py` + `client/**` + `i18n/`

현재 분할 구조 기준 포함 범위:
- 서버 spec는 `collect_submodules("app")`, `collect_submodules("gui")`를 사용하므로 `app/bootstrap/*`, `app/http/*`, `app/realtime/*`, `gui/server_process.py` 등 분리된 하위 모듈을 자동 포함합니다.
- 서버 spec의 `static/` 데이터 포함 범위에는 `static/css/style.css` manifest, 분할 CSS 파일, `static/js/modules/main.js` 브리지 엔트리가 모두 포함됩니다.
- 클라이언트 spec는 `collect_submodules("client")`를 사용하므로 `client/controllers/*`와 `client/ui/*` helper 모듈도 자동 포함됩니다.

## 3) 타겟별 준비

서버 패키지 폴더만 갱신:

```powershell
.\scripts\build_exe.ps1 -Target server
```

클라이언트 패키지 폴더만 갱신:

```powershell
.\scripts\build_exe.ps1 -Target client
```

## 4) 실패 시 점검

- `pyinstaller` 없음:
  - `pip install pyinstaller`
- 빌드 후 EXE 미생성:
  - `messenger.spec` 경로 확인
  - `build/`, `dist/` 정리 후 `-Clean` 재시도
- 누락 모듈 오류:
  - 가상환경에서 `pip install -r requirements.txt` 재실행
  - `messenger.spec`는 `collect_submodules("app")`, `collect_submodules("gui")`를 사용함
  - `messenger_client.spec`는 `collect_submodules("client")`를 사용하므로 신규 하위 모듈(`client/controllers/*`, `client/services/*`, `client/ui/*`)은 기본적으로 자동 포함됨

## 5) 다음 단계 (MSI)

```powershell
.\scripts\build_msi.ps1 -Target server -BuildDir "dist\exe\server"
.\scripts\build_msi.ps1 -Target client -BuildDir "dist\exe\client"
```

## 6) 채널/서명 운영 (권장)

빌드 전 최소 검증:

```powershell
pyright
pytest tests -q
```

업데이트 채널(stable/canary) 구성:

```powershell
.\scripts\set_release_channel.ps1 -DefaultChannel stable -StableLatestVersion "1.0.0" -CanaryLatestVersion "1.1.0"
```

코드서명 자동화:

```powershell
.\scripts\sign_release.ps1 -Target all -CertThumbprint "<thumbprint>"
```
