# 전환/롤백 계획

## 전환 전략

1. 서버 선배포
- `device_sessions` 스키마/API 포함 버전 배포
- 웹/데스크톱 동시 접속 허용(`DESKTOP_ONLY_MODE=False`)

2. 파일럿 배포
- 제한된 조직에 `MessengerClient.msi` 배포
- 자동실행/자동로그인/재연결 시나리오 검증

3. 전사 전환
- 최소 버전 강제(`DESKTOP_CLIENT_MIN_VERSION`)
- 다운로드 URL 공지

4. 데스크톱 전용 전환
- `DESKTOP_ONLY_MODE=True`
- 웹 루트는 안내 페이지로 전환

## Go/No-Go 게이트

- 핵심 기능 체크리스트 100% 통과
- 보안 회귀 테스트 통과
- 파일럿 장애율 허용 기준 이내
- 롤백 리허설 완료

## 다음 단계 전환 시 고려 요소

1. 사용자 경험
- 사내망 DNS/인증서 배포 방식
- 최초 실행 시 서버 주소 입력 UX
- 업데이트 강제 시점(업무시간 vs 비업무시간)

2. 운영 안정성
- SQLite 단일 파일 백업/잠금 전략
- 서버 단일 장애점(SPOF) 대응 방안
- 로그 수집/장애 티켓 연계

3. 보안/컴플라이언스
- 디바이스 세션 만료/폐기 정책
- 로컬 토큰 저장소 정책(Windows 계정 분리)
- 파일 보관 기간 및 삭제 정책

4. 배포/릴리즈
- MSI 코드서명 필수
- 채널 분리(stable/canary)
- 자동 업데이트 2차 도입(현재는 체크 API 중심)

## 롤백 시나리오

1. 서버 롤백
- 이전 서버 바이너리/패키지 복구
- `DESKTOP_ONLY_MODE=False` 즉시 전환

2. 클라이언트 롤백
- 이전 `MessengerClient.msi` 재배포
- 최소 버전 정책 하향 조정

3. 데이터 호환
- `device_sessions`는 추가 스키마이므로 기존 메시지/방/사용자 데이터는 영향 없음

## 운영 커맨드 예시

```powershell
# 데스크톱 전용 모드
.\scripts\set_cutover_mode.ps1 -Mode desktop-only -MinVersion 1.0.0 -LatestVersion 1.0.0

# 하이브리드 모드(롤백 시)
.\scripts\set_cutover_mode.ps1 -Mode hybrid -MinVersion 1.0.0 -LatestVersion 1.0.0
```
