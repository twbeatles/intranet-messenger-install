# 기능 구현 리스크 점검 보고서 (2026-03-05)

## 점검 범위
- 참조 문서: `README.md`, `claude.md`
- 핵심 코드: `app/routes.py`, `app/sockets.py`, `app/models/*`, `client/app_controller.py`, `config.py`
- 최종 검증 실행(배치 반영 후): `python -m compileall app client gui`, `pytest tests -q`, `pytest --maxfail=1` (`174 passed`)

## 단일 배치 적용 결과 (2026-03-05)
- 상태: 완료
- 적용 요약:
  - 검색 날짜 경계 정규화(`date_from=00:00:00`, `date_to=23:59:59`) 및 회귀 테스트 추가
  - 소켓 inbound 제어 이벤트(`room_name_updated`, `room_members_updated`, `profile_updated`) 클라이언트 발신 차단
  - 프로필 변경은 REST 성공 후 서버 canonical 이벤트(`user_profile_updated`) emit으로 통일
  - 업데이트 정책에 `signature_required` 추가 및 prod 환경 서명 필수 차단(`REQUIRE_SIGNED_UPDATES_IN_PROD`)
  - 프로필 이미지 업로드에 업로드 스캔 체인(저장 전/후) 통합
  - 엔터프라이즈 인증 Provider 추상화 및 `mock` provider 구현
  - 플랫폼 관리자 판별을 DB 플래그(`users.is_platform_admin`) 기반으로 전환
  - 운영 하드닝 경고를 startup log + `/api/system/health.hardening` payload로 노출
  - 문서 참조 누락 파일 복구 및 관련 문서 동기화

## 원본 주요 발견사항 (심각도 순, 이력)

### [High] 고급 검색 `date_to`가 사실상 "해당일 전체"를 포함하지 못함
- 근거:
  - `app/routes.py:1838-1853`에서 `date_to`를 `YYYY-MM-DD` 문자열로만 파싱
  - `app/models/messages.py:570-572`에서 `m.created_at <= date_to` 조건 사용
- 영향:
  - 사용자가 `date_to=2026-03-05`로 조회하면 `2026-03-05 00:00:00` 이후 메시지가 누락될 수 있음
  - 검색 정확도 저하 및 운영/감사 조회 오탐 가능
- 권장 조치:
  - `date_from`은 `00:00:00`, `date_to`는 `23:59:59`로 정규화하거나
  - `date(created_at)` 기반 비교로 일 단위 의미를 명확히 보장
  - 회귀 테스트 추가: "종료일 당일 오후 메시지 포함" 케이스

### [High] 일부 소켓 이벤트가 "클라이언트 발신"으로도 브로드캐스트 가능 (서버 권한 소스와 분리)
- 근거:
  - `app/sockets.py:639-649` `room_members_updated`는 멤버십/권한 확인 없이 room으로 이벤트 송출
  - `app/sockets.py:654-667` `profile_updated`는 클라이언트 payload(`nickname`, `profile_image`)를 검증 없이 전체 브로드캐스트
  - `app/sockets.py:614-635` `room_name_updated`는 DB 업데이트 없이 시스템 메시지+이벤트 송출 가능
- 영향:
  - 실제 DB 상태와 실시간 UI 상태 불일치 가능
  - 악의적/오동작 클라이언트가 이벤트 노이즈를 유발할 수 있음
- 권장 조치:
  - 해당 이벤트를 "클라이언트 입력 이벤트"가 아닌 "서버 내부 emit 전용"으로 전환
  - 불가피하게 유지 시, 멤버십/권한/데이터 유효성 검증 + 서버 DB 재조회값만 브로드캐스트
  - 회귀 테스트 추가: 비멤버/임의 payload 이벤트 송신 차단

### [High] 클라이언트 업데이트 메타데이터 검증이 정책으로 강제되지 않음
- 근거:
  - `client/app_controller.py:136-148`에서 메타데이터 존재 여부만 점검
  - `client/app_controller.py:1612-1632`에서 `artifact_verified` 실패 시 차단 로직 없음
  - `app/routes.py:694-699` 및 `config.py:74-76`에서 서명 필드가 비어도 응답 가능
- 영향:
  - 업데이트 무결성 정책이 "권고" 수준에 머물고, 실제 강제 차단이 되지 않음
  - 공급망 리스크(위·변조 메타데이터/아티팩트) 대응력이 낮음
- 권장 조치:
  - 정책 플래그(예: `REQUIRE_SIGNED_UPDATES`) 도입 후 로그인/업데이트 경로에서 강제
  - `artifact_verified=False` 시 최소 경고, 운영 모드에서는 로그인 차단 또는 업데이트 강제
  - 서명 검증(공개키 기반)까지 포함한 E2E 검증 경로 추가

### [Medium] 프로필 이미지 업로드 경로는 업로드 스캔 훅을 타지 않음
- 근거:
  - 일반 파일 업로드는 `app/routes.py:1180-1200`에서 `scan_upload_stream`/`scan_saved_file` 수행
  - 프로필 업로드 `app/routes.py:1345-1405`는 헤더/크기 검증만 수행하고 스캔 훅 미호출
- 영향:
  - 향후 실스캐너 연동 시에도 프로필 경로가 정책 사각지대가 될 가능성
- 권장 조치:
  - `/api/profile/image`에도 동일 스캔 체인을 적용
  - 회귀 테스트 추가: 프로필 업로드에서 unknown provider 차단 확인

### [Medium] 엔터프라이즈 로그인은 활성화해도 스캐폴딩(501)만 반환
- 근거:
  - `app/routes.py:465-473`
- 영향:
  - `ENTERPRISE_AUTH_ENABLED=True` 환경에서 실제 인증 경로 부재
  - 운영 전환 시 기능 갭 발생
- 권장 조치:
  - provider 인터페이스(AD/LDAP/SSO) 확정 후 최소 1개 구현 연결
  - 실패 코드/감사 로그/잠금 정책까지 포함한 통합 테스트 필요

### [Medium] 플랫폼 관리자 판별이 `user_id == 1`에 하드코딩
- 근거:
  - `app/routes.py:263-266`
- 영향:
  - 데이터 이관/복구/초기화 시 관리자 판별 오동작 가능
- 권장 조치:
  - 전역 관리자 role/claim 기반 판별로 전환 (`users.is_platform_admin` 등)

### [Medium] 기본 설정값이 보안 강제보다 호환성 우선 (운영 오배포 리스크)
- 근거:
  - `config.py:79` `ENFORCE_HTTPS = False`
  - `config.py:82` `REQUIRE_MESSAGE_ENCRYPTION = False`
  - `config.py:85` `SESSION_TOKEN_FAIL_OPEN = True`
  - `config.py:86` `UPLOAD_SCAN_ENABLED = False`
- 영향:
  - 운영 환경에서 별도 하드닝 누락 시 평문/완화 정책으로 기동될 수 있음
- 권장 조치:
  - prod 전용 설정 프로파일 도입 및 기동 시 하드닝 미설정 경고/실패 처리

### [Low] 핵심 참조 문서 링크 불일치 (운영/온보딩 효율 저하)
- 근거:
  - `README.md:33`, `claude.md:15`, `claude.md:25`, `claude.md:100`, `claude.md:141`에서 `OFFLINE_MESSENGER_IMPLEMENTATION_RISK_ROADMAP_20260226.md` 참조
  - 실제 루트에 해당 파일 부재 확인
- 영향:
  - 세션 시작 가이드 및 운영 문서 참조 흐름 단절
- 권장 조치:
  - 파일 복구 또는 대체 경로로 문서 업데이트

## 우선순위 제안
1. `date_to` 검색 정확도 수정 + 회귀 테스트
2. 소켓 "클라이언트 발신 브로드캐스트" 이벤트 정리(권한검증/내부전용화)
3. 업데이트 서명/해시 검증 강제 정책 구현
4. 프로필 업로드 스캔 경로 통합
5. 엔터프라이즈 인증 연동과 관리자 판별 모델 정비

## 최종 회귀 결과
- `python -m compileall app client gui` 통과
- `pytest tests -q` 통과 (`174 passed`)
- `pytest --maxfail=1` 통과 (`174 passed`)
