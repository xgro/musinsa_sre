from fastapi import FastAPI

from backend.services.iam.service import IAMService


def init_iam_service(app: FastAPI) -> None:  # pragma: no cover
    """
    initialize iam service.

    :param app: fastAPI application.
    """
    app.state.iam_service = IAMService()
