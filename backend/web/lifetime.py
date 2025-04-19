from typing import Awaitable, Callable

from fastapi import FastAPI

from backend.services.iam.lifetime import init_iam_service


def register_startup_event(
    app: FastAPI,
) -> Callable[[], Awaitable[None]]:  # pragma: no cover
    """
    Actions to run on application startup.

    This function uses fastAPI app to store data
    in the state, such as db_engine.

    :param app: the fastAPI application.
    :return: function that actually performs actions.
    """

    @app.on_event("startup")
    async def _startup() -> None:  # noqa: WPS430

        # 미들웨어 초기화
        app.middleware_stack = None
        app.middleware_stack = app.build_middleware_stack()

        # iam service 초기화
        init_iam_service(app)

    return _startup


def register_shutdown_event(
    app: FastAPI,
) -> Callable[[], Awaitable[None]]:  # pragma: no cover
    """
    Actions to run on application's shutdown.

    :param app: fastAPI application.
    :return: function that actually performs actions.
    """

    @app.on_event("shutdown")
    async def _shutdown() -> None:  # noqa: WPS430
        """
        IAMService 종료
        """
        if app.state.iam_service:
            await app.state.iam_service.close()

    return _shutdown
