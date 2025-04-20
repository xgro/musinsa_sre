# Docker 환경에서 민감 정보(Secrets) 안전하게 다루는 방법

## 요약 및 실무 보안 포인트

- **Dockerfile에는 절대 민감 정보(시크릿)를 직접 선언하지 않는다.**
- **이미지에는 민감 정보가 남지 않도록 설계한다.**
- **컨테이너 실행 시점에만 환경변수로 시크릿을 주입한다.**
- **.env 파일은 반드시 .dockerignore에 포함시켜 이미지에 복사되지 않도록 한다.**
- **민감 정보가 유출될 경우 즉시 키를 폐기하고 재발급한다.**

## ⚠️ 반드시 지켜야 할 주의사항

- **Dockerfile에 ENV/ARG로 민감 정보(예: AWS Access Key, Secret Key, DB 비밀번호 등)를 절대 선언하지 마세요!**
  - Dockerfile에 ENV/ARG로 선언된 값은 이미지 레이어에 영구적으로 남아, 이미지가 유출될 경우 누구나 확인할 수 있습니다.
  - 이미지를 공유하거나 레지스트리에 업로드할 때, 민감 정보가 외부에 노출될 수 있습니다.
- **이미지에는 민감 정보가 절대 포함되지 않아야 합니다.**
- **민감 정보는 반드시 컨테이너 실행 시점에만 주입해야 합니다.**

---

## 1. 안전한 민감 정보 주입 방법

### 1) 컨테이너 실행 시 환경변수로 주입

```bash
docker run -it --rm \
  -e AWS_ACCESS_KEY_ID=your_access_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret_key \
  myimage:latest
```

### 2) --env-file 옵션 사용

```bash
docker run --env-file .env myimage:latest
```

- `.env` 파일은 반드시 안전하게 관리하고, Git 등 버전관리 시스템에 절대 커밋하지 마세요.
- `.dockerignore`에 `.env`가 포함되어 있는지 항상 확인하세요.

### 3) 오케스트레이션/CI/CD Secret 관리 기능 사용

- **Kubernetes:** Secret 리소스를 활용하여 환경변수로 주입
- **AWS ECS:** Secrets Manager, Parameter Store 연동
- **GitHub Actions 등 CI/CD:** Secret 관리 기능을 통해 런타임에만 주입

### 4) (고급) Docker BuildKit의 --secret 옵션 활용

- 빌드 시점에만 임시로 secret을 주입할 수 있으나, 런타임 환경변수로는 전달되지 않음

---

## 2. 실무 권장 패턴

- **이미지에는 절대 민감 정보가 남지 않도록 설계**
- 운영 환경에서는 오케스트레이션/CI/CD의 Secret 관리 기능을 적극 활용
- 개발/테스트 환경에서도 .env 파일이나 -e 옵션으로만 주입
- .env 파일은 반드시 `.dockerignore`에 포함시켜 이미지에 복사되지 않도록 관리

---

## 3. 잘못된 예시 (절대 금지)

```dockerfile
# 아래와 같이 Dockerfile에 민감 정보를 직접 선언하지 마세요!
ENV AWS_ACCESS_KEY_ID=your_access_key
ENV AWS_SECRET_ACCESS_KEY=your_secret_key
```

---

## 4. 참고

- Dockerfile에는 민감 정보가 남지 않도록 설계
- BuildKit의 --secret은 빌드 시점에만 사용 가능, 런타임 환경변수로는 전달되지 않음
- 민감 정보가 유출될 경우, 즉시 키를 폐기하고 재발급해야 합니다.

---

## 5. 요약

- **Dockerfile에 민감 정보 선언 금지!**
- **이미지에는 민감 정보가 없어야 함!**
- **컨테이너 실행 시점에만 환경변수로 주입!**
- **Secret 관리 기능을 적극 활용!**

---

## 6. 실전 Docker 빌드/실행 검증 가이드

### 1) Docker 이미지 빌드

```bash
docker build -t myimage:latest .
```

### 2) 이미지 내 시크릿 미포함 검증

- 빌드된 이미지에 시크릿이 포함되지 않았는지 반드시 확인하세요.
- 예시: 이미지 내 환경변수/파일에 시크릿이 없는지 검사

```bash
docker run --rm myimage:latest env | grep AWS
# (아무것도 출력되지 않아야 안전)
```

- 또는 이미지 내 파일 시스템 검사

```bash
docker run --rm myimage:latest find / -type f | grep -i env
# .env 등 민감 파일이 없어야 함
```

### 3) 환경변수/시크릿 주입 후 실행 검증

```bash
docker run --rm -e AWS_ACCESS_KEY_ID=your_access_key -e AWS_SECRET_ACCESS_KEY=your_secret_key myimage:latest
```

또는

```bash
docker run --rm --env-file .env myimage:latest
```

### 4) Kubernetes 연동 시 검증

- Secret 리소스 생성 및 Pod에 환경변수로 주입
- 실제 Pod 내에서 시크릿이 잘 주입되는지, 이미지에는 포함되지 않는지 확인

```bash
kubectl exec -it <pod-name> -- env | grep AWS
# (실행 중인 컨테이너에서만 시크릿이 노출되어야 함)
```

### 5) CI/CD 파이프라인에서 검증

- 빌드/배포 파이프라인에서 시크릿이 로그/이미지에 노출되지 않는지 점검
- 필요시 BuildKit의 --secret, GitHub Actions의 secret masking 등 활용

---

**실제 운영 전, 이미지와 런타임 환경 모두에서 시크릿 노출 여부를 반드시 검증하세요!**
