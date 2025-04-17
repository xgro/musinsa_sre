# flake8: noqa
import base64
from pathlib import Path
from typing import Any, Dict

import toml  # type: ignore
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import PlainTextResponse, UJSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from backend.logging import configure_logging
from backend.settings import settings
from backend.web.api.router import api_router
from backend.web.lifetime import register_shutdown_event, register_startup_event

APP_ROOT = Path(__file__).parent.parent


def get_version_from_pyproject() -> str:
    """
    Read the version from pyproject.toml.

    :return: The version string from pyproject.toml.
    """
    with open("pyproject.toml", "r", encoding="utf-8") as pyproject_file:
        pyproject_contents = toml.load(pyproject_file)
        return pyproject_contents["project"]["version"]


class BasicAuthMiddleware(BaseHTTPMiddleware):
    """Basic Authentication 미들웨어."""

    def __init__(
        self,
        app: FastAPI,
        username: str,
        password: str,
        include_path_prefix: str,
    ):
        super().__init__(app)
        self.valid_credentials = base64.b64encode(
            f"{username}:{password}".encode(),
        ).decode()
        self.include_path_prefix = include_path_prefix

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """
        Dispatch request.

        :param request: Request instance.
        :param call_next: Next middleware.
        :return: Response.
        """
        if request.url.path.startswith(self.include_path_prefix):
            authorization = request.headers.get("Authorization")
            if not authorization:
                return PlainTextResponse(
                    "Unauthorized",
                    status_code=401,
                    headers={"WWW-Authenticate": "Basic"},
                )

            scheme, _, credentials = authorization.partition(" ")
            if not (  # noqa: WPS337
                scheme.lower() == "basic" and credentials == self.valid_credentials
            ):

                return PlainTextResponse(
                    "Unauthorized",
                    status_code=401,
                    headers={"WWW-Authenticate": "Basic"},
                )

        return await call_next(request)


def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """
    OpenAPI 스키마를 커스터마이즈하여 'servers' 섹션을 추가합니다.

    :param app: FastAPI 애플리케이션 인스턴스.
    :return: OpenAPI schema.
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description="musinsa_sre API",
        routes=app.routes,
    )

    openapi_schema["servers"] = [
        {"url": settings.openapi_server, "description": "서버"},
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


def get_app() -> FastAPI:  # noqa: WPS213
    """
    Get FastAPI application.

    This is the main constructor of an application.

    :return: application.
    """
    configure_logging()
    app = FastAPI(
        title="musinsa_sre",
        version=get_version_from_pyproject(),
        docs_url=None,
        redoc_url=None,
        openapi_url="/api/openapi.json",
        default_response_class=UJSONResponse,
    )

    # Adds startup and shutdown events.
    register_startup_event(app)
    register_shutdown_event(app)

    # Main router for the API.
    app.include_router(router=api_router, prefix="/api")
    # Adds static directory.
    # This directory is used to access swagger files.
    app.mount(
        "/static",
        StaticFiles(directory=APP_ROOT / "static"),
        name="static",
    )

    # 커스텀 OpenAPI 설정
    app.openapi = lambda: custom_openapi(app)  # type: ignore

    origins = [origin.strip() for origin in settings.cors_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,  # localhost와 포트를 정확히 명시
        allow_credentials=True,
        allow_methods=["*"],  # 모든 HTTP 메소드 허용 (GET, POST 등)
        allow_headers=["*"],  # 모든 HTTP 헤더 허용
    )

    # if settings.environment != "local":
    app.add_middleware(
        BasicAuthMiddleware,  # type: ignore
        username=settings.swagger_id,
        password=settings.swagger_password,
        include_path_prefix="/api/docs",
    )

    return app
