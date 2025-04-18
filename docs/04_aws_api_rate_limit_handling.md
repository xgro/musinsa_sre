# AWS IAM API Rate Limit Handling (최신화)

## 요약 및 실무 권장 포인트

- **실시간 API는 Rate Limit(공식 수치는 공개되어 있지 않으나, 실무적으로 5~10 TPS 수준에서 주의가 필요합니다)에 주의해야 하며, 대량 데이터 환경에서는 Credential Report 기반 엔드포인트 사용을 권장합니다.**
- **Credential Report 기반 방식은 Rate Limit 문제를 근본적으로 회피하며, 대량/정기 리포트에 적합합니다.**
- **실시간성이 반드시 필요한 경우에만 실시간 API + 속도 제한/재시도/동시성 제어를 적용합니다.**

## 개요

AWS IAM API는 계정 및 리전별로 **공식적인 요청 제한(TPS)이 명확히 공개되어 있지 않습니다.** 실무적으로는 **5~10 TPS(초당 요청 수)** 수준에서 Throttling(요청 제한) 오류가 발생할 수 있다는 경험적 사례가 많으므로, 대량의 IAM 사용자 또는 Access Key 정보를 실시간 API로 반복 조회할 때는 반드시 속도 제한 및 재시도 로직을 적용해야 합니다.

본 문서는 이러한 Rate Limit 초과를 방지하고, 안정적으로 IAM 정보를 수집하기 위한 설계 및 구현 방안을 실제 구현 구조에 맞게 제시합니다.

---

## 1. 문제점

- 실시간 AWS API(`list_users`, `list_access_keys`)를 반복적으로 호출할 때, 제한에 도달할 수 있음
- 초과 시 AWS에서 요청을 거부(ThrottlingException) → 서비스 장애, 지연 발생

---

## 2. 방지 대책 (실제 구현 기준)

### 2.1 Credential Report 기반 방식

- **POST /v1/iam/old-access-keys/credential-report** 엔드포인트는 AWS Credential Report를 활용하여 단일 호출로 대량의 Access Key 정보를 수집
- 이 방식은 Rate Limit 문제를 근본적으로 회피하며, 대량/정기 리포트에 적합
- 단, 최신성이 100%는 아니므로 실시간성이 필요한 경우에는 부적합

### 2.2 실시간 API 호출 시 일반적 Rate Limit 대응

- **GET /v1/iam/old-access-keys/list-users** 엔드포인트는 실시간 AWS API 호출 기반
- 대량 데이터 환경에서는 호출 속도를 제한하거나, Throttling 발생 시 Exponential Backoff(점진적 재시도) 적용
- 동시에 너무 많은 사용자에 대해 API를 호출하지 않도록 동시 실행 개수 제한(Semaphore 등) 적용

---

## 3. 설계/구현 시 고려사항

- 대량 데이터 환경에서는 Credential Report 기반 엔드포인트 사용을 우선 권장
- 실시간성이 반드시 필요한 경우에만 실시간 API + 속도 제한/재시도/동시성 제어 적용
- 서비스 구조상 두 방식을 분리 제공하여, 상황에 따라 선택적으로 활용 가능

---

## 4. 참고

- [AWS 공식 Credential Report 문서](https://docs.aws.amazon.com/IAM/latest/UserGuide/credential-reports.html)

---

## 5. 결론

- Credential Report 기반 방식은 Rate Limit 문제를 근본적으로 회피하며, 대량 데이터 환경에 적합
- 실시간 API는 속도 제한, 재시도(Exponential Backoff), 동시성 제어를 통해 안정적인 서비스 운영이 가능
- 실제 구현 구조에 맞춰 두 방식을 분리 제공함
