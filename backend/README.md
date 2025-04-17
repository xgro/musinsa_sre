# Backend

AWS IAM Access Key 모니터링 시스템

## 개요

Backend는 AWS IAM 사용자의 Access Key를 모니터링하고 관리하는 도구입니다.
이 시스템은 Access Key의 생성 시간을 추적하고, 오래된 키를 식별하여 보안 위험을 최소화합니다.

## 주요 기능

- IAM 사용자의 Access Key 모니터링
- Access Key 생성 시간 추적
- 만료 예정 키 알림
- 보안 정책 준수 확인

## 기술 스택

- Python 3.12+
- FastAPI
- AWS SDK (Boto3)

## 설치 방법

```bash
# 프로젝트 클론
git clone https://github.com/xgro/musinsa_sre.git

# 의존성 설치
uv venv
source .venv/bin/activate
uv pip install -e .
```

## 실행

```bash
python -m backend
```

## 라이선스

MIT License
