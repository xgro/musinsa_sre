from datetime import datetime
from typing import List

from pydantic import BaseModel, Field  # type: ignore


class OldAccessKey(BaseModel):
    user_name: str = Field(
        ...,
        description="사용자 이름",
    )
    access_key_id: str = Field(
        ...,
        description="엑세스 키 ID",
    )
    created_date: datetime = Field(
        ...,
        description="생성 일시",
    )


class OldAccessKeyRequest(BaseModel):
    hours: int = Field(..., description="N시간 이상된 키 조회")


class OldAccessKeyResponse(BaseModel):
    old_access_keys: List[OldAccessKey]
