# Musinsa SRE 과제

## 1. 프로젝트 개요

AWS IAM Access Key의 보안 위험을 사전에 식별하고 관리할 수 있도록 설계된 백엔드 시스템입니다.
실시간 AWS API 및 Credential Report 기반으로, 오래된 Access Key를 효율적으로 탐지합니다.

---

## 2. 디렉토리 구조

```
.
├── backend/         # FastAPI 백엔드 서비스
├── k8s/             # Kubernetes 매니페스트 및 배포 가이드
├── docs/            # 설계/운영/실습 관련 문서
├── .env.sample      # 환경 변수 샘플
├── Dockerfile       # 컨테이너 빌드 파일
├── pyproject.toml   # Python 패키지 관리(uv)
└── README.md        # 메인 문서
```

---

## 3. 주요 기술 스택 및 개발 환경

- Python 3.10+, FastAPI, aioboto3
- Kubernetes, Minikube, Docker
- 패키지 관리: uv
- 환경 변수 관리: pydantic, dotenv
- 문서화: Markdown, docs 폴더

---

## 4. 빠른 시작(Quick Start)

1. **저장소 클론 및 의존성 설치**

   ```bash
   git clone https://github.com/xgro/musinsa_sre.git
   cd musinsa_sre
   uv venv
   source .venv/bin/activate
   uv pip install -e .
   ```

2. **환경 변수 설정**

   ```bash
   cp .env.sample .env
   # .env 파일에 AWS 자격증명 입력
   ```

3. **로컬 서버 실행**

   ```bash
   python -m backend
   ```

4. **Kubernetes(Minikube) 배포**
   - [k8s/README.md](k8s/README.md) 및 [docs/03_endpoint_usage_guide.md](docs/03_endpoint_usage_guide.md) 참고

---

## 5. Kubernetes 배포/운영 가이드

- Minikube 환경에서 로컬 Docker 이미지 사용법, port-forward, 시크릿 인코딩 등 실습에 최적화된 가이드 제공
- [k8s/README.md](k8s/README.md)에서 배포 절차, 주의사항, 실습 팁 확인

---

## 6. API 문서 및 주요 엔드포인트

- `GET /api/health` : 서버 상태 확인
- `GET /v1/iam/old-access-keys/list-users` : 실시간 AWS API 기반, N시간 이상된 Access Key 조회
- `POST /v1/iam/old-access-keys/credential-report` : Credential Report 기반 대량 조회
- **Swagger(OpenAPI) 문서:**
  - 브라우저에서 `예시) http://localhost:8000/api/docs` 접속 시, 모든 엔드포인트의 스펙과 테스트가 가능합니다.
  - Swagger 접속 시, ID/PW 입력이 필요합니다. (기본값: musinsa_sre / musinsa123!@#)
  - ID와 PW는 환경변수(`SWAGGER_ID`, `SWAGGER_PASSWORD`)로 설정할 수 있습니다.

자세한 사용법 및 예시는 [docs/03_endpoint_usage_guide.md](docs/03_endpoint_usage_guide.md) 참고

---

<br>

## 7. 설계 의도 및 주요 고려사항

- **환경변수/시크릿 설계**:
  표준 AWS 환경변수 대신, 서비스 구분을 위해 커스텀 변수명을 사용하고 코드에서 명시적으로 처리
  (자세한 배경: [docs/02_docker_secret_handling.md](docs/02_docker_secret_handling.md))
- **보안/운영 주의사항**:
  시크릿 인코딩, 민감 정보 커밋 금지, 실습 환경에서의 port-forward 활용 등
  (자세한 내용: [k8s/README.md](k8s/README.md))
- **AWS API Rate Limit**:
  공식 수치는 공개되어 있지 않으나, 실무적으로 5~10 TPS 수준에서 주의가 필요합니다.
  (자세한 내용: [docs/04_aws_api_rate_limit_handling.md](docs/04_aws_api_rate_limit_handling.md))

---

## 7-1. 보안: 커밋 시 민감정보(크레덴셜) 노출 방지

본 프로젝트는 개발자가 실수로 시크릿, API 키, 비밀번호 등 민감정보를 커밋하는 것을 방지하기 위해 [detect-secrets](https://github.com/Yelp/detect-secrets) 기반의 pre-commit hook을 적용하고 있습니다.

- 커밋 단계에서 자동으로 코드 내 민감정보 패턴을 검사하며, 시크릿이 감지되면 커밋이 차단됩니다.
- `.pre-commit-config.yaml`에 detect-secrets가 등록되어 있습니다.
- pre-commit이 설치되어 있지 않다면 `pip install pre-commit` 후, `pre-commit install`로 활성화하세요.

이미 커밋된 민감정보는 git history에서 완전히 제거해야 하며, pre-commit hook은 새로운 커밋에 대해서만 동작합니다.

---

## 8. 문서/참고자료

- [docs/00_mvp_design.md](docs/00_mvp_design.md) : 전체 시스템 설계 및 구조
- [docs/01_backend_improvement_points.md](docs/01_backend_improvement_points.md) : 백엔드 개선/확장 아이디어
- [docs/02_docker_secret_handling.md](docs/02_docker_secret_handling.md) : 시크릿/환경변수 관리
- [docs/03_endpoint_usage_guide.md](docs/03_endpoint_usage_guide.md) : API 사용 가이드
- [docs/04_aws_api_rate_limit_handling.md](docs/04_aws_api_rate_limit_handling.md) : AWS API Rate Limit 대응
- [docs/05_iam_credential_report_endpoint_design.md](docs/05_iam_credential_report_endpoint_design.md) : Credential Report 설계

---

## 9. 기타

- 라이선스: MIT
- 문의: [프로젝트 오너 GitHub](https://github.com/xgro)

---
