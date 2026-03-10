# OFFLINE_MESSENGER_IMPLEMENTATION_RISK_ROADMAP_20260226

기준일: 2026-02-26  
범위: Desktop-First 사내 메신저 서버/클라이언트

## 목적
운영 전환에 필요한 미해결 리스크를 우선순위 기반으로 관리한다.

## 우선순위 백로그

1. 엔터프라이즈 인증 실연동
- 목표: `ENTERPRISE_AUTH_PROVIDER`를 mock 외 실 provider(AD/LDAP/SSO)로 확장
- 완료 기준: 운영 인증 경로/장애 시 fallback 정책/감사 로그 테스트 통과

2. 업로드 스캐너 운영 연동
- 목표: `UPLOAD_SCAN_PROVIDER`를 noop에서 실스캐너로 전환
- 완료 기준: 일반 업로드 + 프로필 업로드 모두 정책 적용 및 차단 테스트 통과

3. 업데이트 무결성 강제
- 목표: 운영 환경에서 서명/해시 검증 실패 시 업데이트 차단
- 완료 기준: `signature_required` 정책/클라이언트 차단/릴리즈 파이프라인 검증 완료

4. 스토리지/확장성 전환 리허설
- 목표: SQLite 단일노드 한계를 넘어 서버형 RDBMS/MQ 확장 리허설 수행
- 완료 기준: 부하/복구 시나리오 문서화 및 리허설 로그 확보

5. DR(재해복구) 정례화
- 목표: 장애주입, 백업복원, 롤백 리허설을 정례 운영
- 완료 기준: 월간 점검표와 복구 시간(RTO/RPO) 기록 축적

## 추적 규칙
- 계약 변경(API/소켓/보안)은 테스트와 문서를 함께 갱신한다.
- 정적 분석 기준(`pyrightconfig.json`)과 UTF-8 워크스페이스 기준(`.editorconfig`, `.vscode/settings.json`)도 문서와 함께 유지한다.
- prod 하드닝 이슈는 `docs/OPERATIONS_RUNBOOK.md`와 동기화한다.
