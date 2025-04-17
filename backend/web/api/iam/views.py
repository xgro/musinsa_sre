from typing import List

from fastapi import APIRouter, Depends  # type: ignore

from backend.services.iam.dependency import get_iam_service
from backend.services.iam.service import IAMService
from backend.web.api.iam.schema import (
    OldAccessKey,
    OldAccessKeyRequest,
    OldAccessKeyResponse,
)

router = APIRouter()


@router.get("/v1/iam/old-access-keys")
async def list_old_access_keys(
    request: OldAccessKeyRequest = Depends(),
    iam_service: IAMService = Depends(get_iam_service),
) -> OldAccessKeyResponse:
    """N시간 이상된 AWS Access Key 목록 조회.

    :param hours: 조회할 시간
    :return: 조회된 Access Key 목록
    """
    old_access_keys: List[OldAccessKey] = await iam_service.get_old_access_keys(
        hours=request.hours,
    )
    return OldAccessKeyResponse(old_access_keys=old_access_keys)
