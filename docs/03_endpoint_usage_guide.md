# 엔드포인트 사용 가이드

## 0. 요약 및 실무 활용 팁

- **실시간성이 중요하면 `/list-users` 엔드포인트, 대량 데이터/정기 리포트는 `/credential-report` 엔드포인트를 사용하세요.**
- **실시간 API는 Rate Limit(TPS, 초당 요청 수)에 주의해야 하며, 대량 환경에서는 Credential Report 기반 방식을 권장합니다.**
- **두 엔드포인트 모두 `hours` 파라미터로 만료 기준 시간(시간 단위)을 지정합니다.**
- **Swagger(OpenAPI) 문서:**
  - 브라우저에서 `예시) http://localhost:8000/api/docs` 접속 시, 모든 엔드포인트의 스펙과 테스트가 가능합니다.
  - Swagger 접속 시, ID/PW 입력이 필요합니다. (기본값: musinsa_sre / musinsa123!@#)
  - ID와 PW는 환경변수(`SWAGGER_ID`, `SWAGGER_PASSWORD`)로 설정할 수 있습니다.

---

본 문서는 AWS IAM Access Key 모니터링 시스템의 주요 엔드포인트 사용법과 활용 시나리오, 주의사항을 안내합니다.

---

## 1. 실시간 AWS API 기반 엔드포인트

### GET /v1/iam/old-access-keys/list-users

- **설명**: 실시간 AWS API를 통해 N시간 이상된 Access Key 목록을 조회합니다.
- **특징**: 최신 데이터, 대량 데이터 환경에서는 Rate Limit(속도 제한, 동시성 제어, 재시도 등)에 주의
- **요청 예시**:

```bash
curl -X GET "http://localhost:8000/v1/iam/old-access-keys/list-users?hours=48"
```

- **응답 예시**:

```json
{
  "old_access_keys": [
    {
      "user_name": "alice",
      "access_key_id": "AKIA...",
      "created_date": "2024-05-01T12:34:56Z"
    }
  ]
}
```

- **활용 시나리오**: 실시간성이 중요한 보안 점검, 소규모/중간 규모 환경
- **주의사항**: 대량 데이터 환경에서는 Rate Limit(TPS) 초과 가능성, 속도 제한/동시성 제어/재시도 등 필요

---

## 2. Credential Report 기반 엔드포인트

### POST /v1/iam/old-access-keys/credential-report

- **설명**: AWS Credential Report를 활용하여 N시간 이상된 Access Key 목록을 조회합니다.
- **특징**: 대량 데이터 환경에 적합, Rate Limit 걱정 없음, 최신성 100%는 아님(최대 4시간 캐시)
- **요청 예시**:

```bash
curl -X POST "http://localhost:8000/v1/iam/old-access-keys/credential-report" \
  -H "Content-Type: application/json" \
  -d '{"hours": 48}'
```

- **응답 예시**:

```json
{
  "old_access_keys": [
    {
      "user_name": "bob",
      "access_key_id": "AKIA...",
      "created_date": "2024-04-28T09:12:34Z"
    }
  ]
}
```

- **활용 시나리오**: 대량/정기 리포트, 대규모 계정 점검, Rate Limit 걱정 없는 환경
- **주의사항**: 최신성이 100% 필요하다면 실시간 API 사용 권장

---

## 3. 선택 기준 및 권장 사항

- **실시간성**이 중요하면 `/list-users` 엔드포인트 사용
- **대량 데이터/정기 리포트**는 `/credential-report` 엔드포인트 사용
- 두 엔드포인트 모두 `hours` 파라미터로 만료 기준 시간(시간 단위) 지정

---

## 4. 참고

- AWS 인증 정보는 환경 변수 또는 .env 파일로 안전하게 관리해야 합니다.
- 응답 데이터는 Pydantic 스키마에 따라 일관된 구조로 반환됩니다.
