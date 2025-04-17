from starlette.requests import Request

from backend.services.iam.service import IAMService


async def get_iam_service(
    request: Request,
) -> IAMService:  # pragma: no cover
    """
    Get IAMService instance.

    :param request: Request instance.
    :return: IAMService instance.
    """
    return request.app.state.iam_service
