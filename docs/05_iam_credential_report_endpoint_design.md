# IAM Credential Report 기반 엔드포인트 설계

## 요약 및 실무 설계 포인트

- **Credential Report 기반 엔드포인트는 대량/정기 리포트에 최적화되어 있으며, Rate Limit 문제를 근본적으로 회피합니다.**
- **실시간성이 필요한 경우 실시간 엔드포인트를, 대량 데이터 환경에서는 Credential Report 엔드포인트를 선택적으로 활용할 수 있도록 설계했습니다.**
- **구현 구조, 예외 처리, 환경변수 기반 보안 등 실무적 요구사항을 반영했습니다.**

## 1. 도입 배경

AWS IAM의 Access Key 모니터링에서 대량 사용자 환경의 Rate Limit 문제와 성능 저하를 해결하기 위해, Credential Report 기반 접근 방식을 도입합니다. Credential Report는 단일 API 호출로 모든 IAM 사용자에 대한 인증 정보를 취합할 수 있어, 대량 데이터 환경에서 효율적입니다.

---

## 2. Credential Report의 특징

- **단일 API 호출**로 모든 IAM 사용자 정보 취합 (Rate Limit 걱정 없음)
- Access Key 생성일, 마지막 사용일, 활성/비활성 상태 등 다양한 정보 포함
- 최신성이 100% 보장되지는 않음 (최대 4시간 캐시)
- 실시간성이 아주 중요한 경우에는 부적합할 수 있음

---

## Credential Report 기반 방식의 AccessKeyId 조회 구조

Credential Report는 각 유저의 access_key_1, access_key_2의 활성/비활성, 마지막 회전 시각 등은 제공하지만, **AccessKeyId(실제 키 값)는 직접적으로 제공하지 않습니다.**

따라서, 오래된 키 후보(유저명, 생성일시)를 Credential Report에서 먼저 추출한 뒤, 각 유저에 대해 `ListAccessKeys` API를 호출하여 생성일이 일치하는 키의 ID를 찾아 최종적으로 반환합니다.

이로 인해 Credential Report 기반 방식은 "후보 추출 → 실제 키 ID 조회"의 2단계 구조로 동작합니다.

---

## 3. 엔드포인트 설계 (실제 구현 기준)

### 3.1 실시간 AWS API 기반 엔드포인트

- **GET /v1/iam/old-access-keys/list-users**
  - 실시간 AWS API 호출 기반
  - 실시간성은 높으나, 대량 데이터 처리 시 Rate Limit 이슈

### 3.2 Credential Report 기반 엔드포인트

- **POST /v1/iam/old-access-keys/credential-report**
  - Credential Report(CSV) 기반 Access Key 정보 조회
  - 대량 데이터 환경에서 효율적, Rate Limit 걱정 없음
  - 최신성이 100% 필요하지 않은 모니터링/리포트 용도에 적합
  - Request Body: `{ "hours": int }`
  - Response 예시:

```json
{
  "old_access_keys": [
    {
      "user_name": "string",
      "access_key_id": "string",
      "created_date": "datetime"
    }
  ]
}
```

---

## 4. 서비스 구조 및 구현 포인트

- Credential Report 엔드포인트와 실시간 엔드포인트를 분리 제공
- `IAMService` 클래스에서 aioboto3 세션을 **싱글톤(1회 생성, 재사용)**으로 통합 관리
- **비동기 락(asyncio.Lock)**으로 멀티코어 환경에서 중복 생성 방지
- **세마포어(asyncio.Semaphore)**로 IAM API 동시 호출 개수 제한(기본 5)
- 서비스 종료 시 반드시 `await iam_service.close()`로 자원 해제 필요
- access_key_1, access_key_2 파싱을 반복문으로 처리
- 유저별 액세스 키 조회는 **asyncio.gather**로 병렬 처리
- ClientError 등 예외 상황에 대한 로깅 및 핸들링 강화
- 환경 변수(pydantic+dotenv) 기반 AWS 인증 정보 관리

---

## 5. 폴더/코드 구조 (실제 구현 기준)

```
backend/web/api/iam/
    ├── views.py                # 엔드포인트 통합 구현 (실시간 + Credential Report)
    └── schema.py              # 요청/응답 스키마 정의
backend/services/iam/
    └── service.py             # IAMService 클래스 (비동기, 세션 통합)
```

---

## 6. 운영 가이드

- Credential Report 기반 엔드포인트는 대량/정기 리포트에 적합
- 사용자에게 데이터 소스, 최신성, 성능 특성을 명확히 안내
- 실시간성이 필요한 경우 실시간 엔드포인트 사용 권장
- **IAMService는 싱글톤 클라이언트, 비동기 락, 세마포어, 병렬 처리, 자원 해제(close) 구조를 갖춤**

---

## 7. 참고

- [AWS 공식 Credential Report 문서](https://docs.aws.amazon.com/IAM/latest/UserGuide/credential-reports.html)
- [AWS 공식 블로그 - 대량 데이터 처리 팁 2](https://aws.amazon.com/ko/blogs/security/how-to-monitor-and-query-iam-resources-at-scale-part-2/)
