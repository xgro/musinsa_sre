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
  -e MUSINSA_SRE_AWS_ACCESS_KEY_ID=your_access_key \
  -e MUSINSA_SRE_AWS_SECRET_ACCESS_KEY=your_secret_key \
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
ENV MUSINSA_SRE_AWS_ACCESS_KEY_ID=your_access_key
ENV MUSINSA_SRE_AWS_SECRET_ACCESS_KEY=your_secret_key
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
