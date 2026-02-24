# 백업/정리 기록 (2026-02-23)

## 백업 경로

- `backup/cleanup_20260223_225202`
- 검증 후 재생성 캐시 이동: `backup/cleanup_20260223_225202/post_verify_cleanup`

## 이동 기준

- 실행에 불필요한 캐시/세션/로그
- 이름이 ` (1)` 인 중복 파일
- 테스트 결과 텍스트 산출물
- 테스트 업로드 잔여 텍스트 파일
- 레거시 AI 세션 가이드 문서

## 이동 결과

- 전체 이동 기록: `backup/cleanup_20260223_225202/MOVED_FILES.txt`
- 루트 기준 정리 목록: `backup/cleanup_20260223_225202/MOVED_FILES_ROOT_ONLY.txt`
- 검증 후 캐시 이동 목록: `backup/cleanup_20260223_225202/post_verify_cleanup/MOVED_POST_VERIFY.txt`
- 영구 삭제 후보 목록: `backup/cleanup_20260223_225202/DELETE_CANDIDATES.txt`
- 보존 후보 목록: `backup/cleanup_20260223_225202/KEEP_CANDIDATES.txt`
- 루트 기준 항목 수: `41`

## 주요 이동 항목(루트 기준)

- `.pytest_cache/`
- `__pycache__/` 전체
- `flask_session/`
- `server.log`
- `app/routes (1).py`, `app/sockets (1).py`
- `app/models/messages (1).py`, `app/models/polls (1).py`, `app/models/users (1).py`
- `templates/index (1).html`
- `static/css/style (1).css`
- `static/js/messages (1).js`
- `static/js/modules/main (1).js`
- `tests/*.txt` 산출물
- `uploads/*token-file*.txt`, `uploads/*room-mismatch*.txt`, `uploads/testfile.txt`
- `claude.md`, `gemini.md`

## 영구 삭제/보존 분류

| 분류 | 기준 | 예시 | 권장 조치 |
|---|---|---|---|
| 영구 삭제 대상 | 재생성 가능한 런타임/테스트 산출물 | `__pycache__/`, `.pytest_cache/`, `flask_session/`, `server.log`, `tests/*.txt`, `uploads/*token-file*.txt` | 즉시 삭제 가능 |
| 보존 대상(단기) | 중복 소스/자산 또는 과거 맥락 문서 | `app/routes (1).py`, `templates/index (1).html`, `static/js/messages (1).js`, `claude.md`, `gemini.md` | 1~2 릴리즈 보관 후 검토 삭제 |
| 보존 대상(상시) | 정리 이력 및 복구 기준 정보 | `MOVED_FILES*.txt`, `MOVED_POST_VERIFY.txt`, 본 문서 | 유지 |

## 분류 결과 요약

- 삭제 후보: `23`건
- 보존 후보: `18`건

## 복구 방법

필요 시 백업 폴더에서 원래 상대 경로로 되돌리면 됩니다.

예시:

```powershell
Move-Item "backup\\cleanup_20260223_225202\\templates\\index (1).html" "templates\\index (1).html"
```
