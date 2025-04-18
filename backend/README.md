# Backend

AWS IAM Access Key 모니터링 시스템

## 개요

Backend는 AWS IAM 사용자의 Access Key를 모니터링하고 관리하는 도구입니다.
이 시스템은 Access Key의 생성 시간을 추적하고, 오래된 키를 식별하여 보안 위험을 최소화합니다.

## 주요 기능

- IAM 사용자의 Access Key 모니터링
- Access Key 생성 시간 추적
- 만료 예정 키 알림
- Credential Report 기반 대량 Access Key 조회 (Rate Limit 걱정 없음)
- 실시간/비동기 AWS API 연동
- 보안 정책 준수 확인

## 기술 스택

- Python 3.10+
- FastAPI (비동기)
- AWS SDK (aioboto3)
- 패키지 관리: uv
- 환경 변수 관리: pydantic + dotenv

## 주요 엔드포인트

- `GET /v1/iam/old-access-keys/list-users` : 실시간 AWS API 기반, N시간 이상된 Access Key 조회
- `POST /v1/iam/old-access-keys/credential-report` : Credential Report 기반, 대량 데이터 환경에 적합

## 설치 방법

```bash
# 프로젝트 클론
git clone https://github.com/xgro/musinsa_sre.git

# 의존성 설치 (uv 사용)
uv venv
source .venv/bin/activate
uv pip install -e .
```

## 실행

```bash
python -m backend
```

## 환경 변수 설정

- `.env.sample` 파일을 참고하여 `.env` 파일을 생성

```bash
cp .env.sample .env
```

### AWS 크레덴셜 환경변수 설계 의도

- AWS SDK는 기본적으로 `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` 환경변수를 자동 인식합니다.
- 본 프로젝트에서는 서비스 구분 및 환경별 충돌 방지를 위해
  `MUSINSA_SRE_AWS_ACCESS_KEY_ID`, `MUSINSA_SRE_AWS_SECRET_ACCESS_KEY`와 같이 커스텀 환경변수명을 사용하였습니다.
- 코드에서는 이 커스텀 환경변수를 읽어 AWS SDK에 명시적으로 전달하도록 설계하였습니다.
- 이를 통해, 여러 서비스가 동일한 인프라 환경에서 동작할 때 변수 충돌을 방지하고,
  운영/보안 정책에 유연하게 대응할 수 있습니다.

## 라이선스

MIT License
