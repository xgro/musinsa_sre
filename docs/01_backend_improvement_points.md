# 백엔드 개선 포인트 정리 (최신화)

## 요약 및 실무 개선 포인트

- **API 명세, 입력 검증, 예외 처리, 테스트, 로깅 등 실무적 완성도를 높이기 위한 개선 방향을 제시합니다.**
- **비동기 처리, 세션 관리, Rate Limit 대응 등 실무 환경에서의 신뢰성 확보에 중점**
- **코드/문서 일관성, 운영 자동화, 보안 등 실무적 요구사항을 반영**

---

## 1. API 명세 및 엔드포인트 일치

- 요구 명세에 맞는 엔드포인트로 구현
  - `/v1/iam/old-access-keys/list-users` (실시간 AWS API 기반)
  - `/v1/iam/old-access-keys/credential-report` (Credential Report 기반)
- 두 방식을 분리하여 제공, 상황에 따라 선택적으로 활용 가능

## 2. API 응답 반환 및 스키마 정의

- 만료된 Access Key 정보를 명확한 JSON 구조로 반환
- 응답 예시:
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
- Pydantic 모델을 활용한 요청/응답 스키마 정의

## 3. 파라미터 처리 개선

- N시간(만료 기준 시간)을 API Body 파라미터로 받을 수 있도록 구현
- 환경 변수(pydantic+dotenv) 기반 설정

## 4. 비동기 AWS SDK 및 세션 관리 일원화

- boto3(동기) → aioboto3(비동기)로 개선
- FastAPI의 비동기 처리와 일관성 확보
- IAMService 클래스에서 aioboto3 세션을 인스턴스 변수로 통합 관리

## 5. Credential Report 기반 기능 추가

- 대량 데이터 환경에서 효율적이고 Rate Limit 걱정 없는 Credential Report 기반 엔드포인트 구현
- access_key_1, access_key_2 파싱을 반복문으로 처리

## 6. 예외 처리 및 입력 검증 강화

- AWS API 호출 실패, 파라미터 오류 등 예외 상황에 대한 핸들링 구현
- 입력값 유효성 검사 추가
- ClientError 등 예외 상황에 대한 로깅 강화
