# Kubernetes 배포/운영 전용 README

본 문서는 Minikube 및 일반 Kubernetes 환경에서 본 프로젝트를 배포/운영하기 위한 가이드입니다.

---

## 1. 목적

- 본 프로젝트의 백엔드 서비스를 Kubernetes 환경에서 안전하게 배포/운영하기 위한 실무 지침 제공
- Minikube 및 일반 k8s 환경 모두 지원

---

## 2. 디렉토리 구조

```plaintext
k8s/
├── deployment.yaml      # Deployment 리소스
├── service.yaml         # Service 리소스 (NodePort)
├── secret.yaml          # Secret 리소스 (예시, 실제 값은 base64 인코딩 필요)
└── configmap.yaml       # ConfigMap 리소스 (환경변수 등)
```

---

## 3. 배포 방법

1. **Secret 값 준비 (base64 인코딩 필수)**
   Secret 값은 민감정보를 담는 용도이지만, 단순 base64로 인코딩 되어 저장되므로, 외부에 노출되지 않도록 주의해야 합니다.

   제공된 secret.yaml.sample 파일을 변경하여 secret.yaml 파일을 생성합니다.

   ```bash
   mv secret.yaml.sample secret.yaml
   ```

   - 예시: `echo -n 'your_access_key' | base64`
   - secret.yaml에 인코딩된 값을 입력

2. **리소스 생성**

   ```bash
   kubectl apply -f
   ```

3. **서비스 확인 및 접근**
   - 서비스 NodePort 확인: `kubectl get svc musinsa-sre-backend`
   - 서비스 접속: `kubectl port-forward svc/musinsa-sre-backend 8000:8000`
   - 접속: `http://localhost:8000`

---

## 4. 주의사항 및 고려사항

- **secret.yaml은 예시만 제공하며, 실제 민감 정보는 안전하게 별도 관리해야 합니다.**
- secret.yaml, configmap.yaml 등 민감 정보가 포함된 파일은 Git 등 버전관리 시스템에 커밋하지 마세요.
- Secret 값은 반드시 base64로 인코딩해야 하며, 인코딩 오류 시 서비스가 정상 동작하지 않을 수 있습니다.
- Service는 NodePort로 노출되어 있으므로, 외부 접근이 필요한 경우에만 사용하세요.
- Minikube 환경에서는 NodePort로 접근, 클라우드 환경에서는 LoadBalancer 타입으로 변경 가능합니다.
- 환경별 구성이 필요한 경우 k8s/ 디렉토리를 확장하거나 kustomize/Helm 등 템플릿 도구 도입을 고려할 수 있습니다.
- 민감 정보가 유출될 경우 즉시 키를 폐기하고 재발급해야 합니다.
- 오케스트레이션/CI/CD 환경에서는 Secret 관리 기능을 적극 활용하는 것이 바람직합니다.

---

## 5. 참고 명령어

```bash
# 리소스 삭제
kubectl delete -f k8s/

# 서비스/파드 상태 확인
kubectl get all

# 파드 로그 확인
kubectl logs <pod-name>
```

---

## 6. Minikube에서 로컬 Docker 이미지 사용 가이드

이미지를 외부 저장소에 업로드하지 않고, Minikube의 Docker 환경에서 직접 빌드하여 사용할 수 있습니다. 아래 절차를 따라주세요.

### 1. Minikube의 Docker 환경으로 전환

1. **Minikube의 Docker 환경으로 전환**

   ```bash
   eval $(minikube docker-env)
   ```

   위 명령을 실행하면, 현재 터미널 세션에서 Docker 명령이 Minikube의 Docker 데몬을 사용하도록 설정됩니다.

2. **Docker 이미지 빌드**

   ```bash
   docker build -t myimage:latest .
   ```

   위 명령으로 현재 디렉토리의 Dockerfile을 기반으로 이미지를 빌드합니다. 이 이미지는 Minikube 내부에서 바로 사용할 수 있습니다.

3. **Kubernetes 매니페스트에서 이미지 참조**

   deployment.yaml 등에서 `image: myimage:latest`로 지정하면, 별도의 이미지 푸시 없이 Minikube에서 바로 배포가 가능합니다.

4. **환경 복구(원래 Docker 환경으로 복귀)**

   ```bash
   eval $(minikube docker-env -u)
   ```

   위 명령으로 Docker 환경을 원래대로 되돌릴 수 있습니다.

### 2. Minikube 환경으로 Docker 이미지 가져오기

```bash
minikube image load <이미지 이름>
```

위 명령으로 Minikube 환경에서 Docker 이미지를 로드할 수 있습니다.

단, VM 내부에서 이미지를 로드하는 것이므로, 외부 저장소에 이미지를 업로드하는 것이 아니라면 이미지 빌드 후 바로 로드하는 것이 좋습니다.

이미지는 Minikube VM 내부에 있기 때문에 따로 `imagePullPolicy`를 `Never`로 설정하는 것도 고려해야 합니다.

---

## 7. 실전 배포 및 시크릿/환경변수 검증 절차 (Minikube)

아래 절차는 실제 deployment.yaml의 이미지 태그(`musinsa-sre-backend:latest`)를 기준으로, Minikube 환경에서 빌드, 배포, 시크릿/환경변수 주입 및 검증까지 실무적으로 따라할 수 있는 가이드입니다.

### 1) Minikube Docker 환경으로 전환

```bash
eval $(minikube docker-env)
```

### 2) Docker 이미지 빌드 (deployment.yaml의 이미지 태그와 일치시켜야 함)

```bash
docker build -t musinsa-sre-backend:latest .
```

### 3) (필요시) 이미지 강제 로드

```bash
minikube image load musinsa-sre-backend:latest
```

### 4) 시크릿 설정 및 리소스 배포

```bash
# 제공된 샘플 파일을 복사하여 민감 정보 입력
cp secret.yaml.sample secret.yaml

# 민감 정보는 다음과 같이 base64 인코딩한 값을 입력
# 예시)
echo -n 'your_secret_key' | base64

# 리소스 배포
kubectl apply -f k8s/
```

### 5) Pod 상태 및 서비스 확인

```bash
kubectl get pods
kubectl get svc musinsa-sre-backend
```

### 6) Pod 내 환경변수/시크릿 주입 검증

```bash
kubectl exec -it <pod-name> -- env | grep AWS
# (여기서만 시크릿이 노출되어야 하며, 이미지에는 포함되지 않아야 함)
```

### 7) Pod 내 파일 시스템에 시크릿/민감 정보 미포함 검증

```bash
kubectl exec -it <pod-name> -- find / -type f | grep -i env
# .env 등 민감 파일이 없어야 함
```

### 8) 서비스 정상 동작 확인

```bash
# 서비스 포트 포워딩
kubectl port-forward svc/musinsa-sre-backend 8000:8000

# 서비스 정상 동작 확인
curl http://localhost:8000/api/health
```

---

**Tip:**

- 이미지 태그(`musinsa-sre-backend:latest`)는 deployment.yaml과 반드시 일치해야 하며, Minikube 환경에서는 `imagePullPolicy: Never`로 설정되어 있어야 합니다.
- 위 절차를 통해 실제 배포 환경에서 시크릿/환경변수 주입 및 이미지 내 민감 정보 미포함 여부를 안전하게 검증할 수 있습니다.
