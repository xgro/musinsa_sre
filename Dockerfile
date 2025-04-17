# 베이스 이미지
FROM python:3.10-slim-bookworm AS base

# 빌더 이미지
FROM base AS builder
# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# 작업 디렉토리 설정
WORKDIR /app

# Copying requirements of a project
COPY pyproject.toml uv.lock ./

# Configuring uv & installing requirements
RUN uv sync --frozen --no-install-project --no-dev

COPY . /app

RUN uv sync --frozen --no-dev

# 실행용 이미지
FROM base AS runtime

# 작업 디렉토리 설정
WORKDIR /app

# 이전 단계에서 복사한 Python 패키지 설치
COPY --from=builder /app /app

# venv의 bin을 PATH에 추가
ENV PATH="/app/.venv/bin:$PATH"

# 포트 노출 및 실행 명령어 설정
EXPOSE 8000
CMD ["python", "-m", "backend"]
