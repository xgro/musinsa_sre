from datetime import datetime, timedelta, timezone
from typing import List

import aioboto3  # type: ignore

from backend.settings import settings
from backend.web.api.iam.schema import OldAccessKey


class IAMService:
    def __init__(self) -> None:
        """IAMService 초기화.

        :return: None
        """
        self.aws_access_key_id = settings.aws_access_key_id
        self.aws_secret_access_key = settings.aws_secret_access_key

    async def get_old_access_keys(
        self,
        hours: int,
    ) -> List[OldAccessKey]:
        """N시간 이상된 Access Key 목록을 페이지네이션하여 반환

        :param hours: 조회할 시간
        :return: 조회된 Access Key 목록
        """
        session = aioboto3.Session(
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )

        async with session.client("iam") as client:  # type: ignore
            paginator = client.get_paginator("list_users")

            users = []
            async for page_obj in paginator.paginate():
                users.extend(page_obj["Users"])

            old_keys = []
            threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
            for user in users:
                access_keys = await client.list_access_keys(UserName=user["UserName"])
                for key in access_keys["AccessKeyMetadata"]:
                    if key["CreateDate"] < threshold:
                        old_keys.append(
                            {
                                "user_name": user["UserName"],
                                "access_key_id": key["AccessKeyId"],
                                "created_date": key["CreateDate"],
                            },
                        )

            return [OldAccessKey(**item) for item in old_keys]
