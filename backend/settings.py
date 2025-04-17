import enum
import os
from pathlib import Path
from tempfile import gettempdir

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

TEMP_DIR = Path(gettempdir())


class LogLevel(str, enum.Enum):  # noqa: WPS600
    """Possible log levels."""

    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


class Settings(BaseSettings):
    """
    Application settings.

    These parameters can be configured
    with environment variables.
    """

    host: str = "0.0.0.0"  # noqa
    port: int = 8000
    # quantity of workers for uvicorn
    # workers_count: int = multiprocessing.cpu_count() * 2 + 1
    workers_count: int = 1
    # Enable uvicorn reloading
    reload: bool = False

    # Current environment
    environment: str = "local"

    log_level: LogLevel = LogLevel.INFO

    # openapi server
    openapi_server: str = "http://localhost:8000"
    swagger_id: str = "musinsa_sre"
    swagger_password: str = "musinsa123!@#"

    # cors origins
    cors_origins: str = ""

    # AWS credentials
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    class Config:
        env_file = ".env"
        env_prefix = "MUSINSA_SRE_"
        env_file_encoding = "utf-8"


try:
    # 환경변수 설정
    current_env = os.getenv("FASTAPI_ENV")

    # 환경변수 파일 경로 설정
    env_path = ".env" if not current_env else f".env.{current_env}"

    # 환경변수 파일 경로 존재 여부 확인
    if Path(env_path).exists():
        # 환경변수 파일 로드
        load_dotenv(dotenv_path=env_path)

    # 설정 클래스 인스턴스 생성
    settings = Settings()
except Exception as e:
    raise e
