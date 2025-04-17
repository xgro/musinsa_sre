from datetime import datetime, timedelta, timezone
from typing import List

import aioboto3  # type: ignore
from botocore.exceptions import ClientError
from loguru import logger

from backend.settings import settings
from backend.web.api.iam.schema import OldAccessKey


class IAMService:
    def __init__(self) -> None:
        """IAMService 초기화.

        :return: None
        """
        self.session = aioboto3.Session(
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )

    async def get_old_access_keys_from_list_users(
        self,
        hours: int,
    ) -> List[OldAccessKey]:
        """N시간 이상된 Access Key 목록을 페이지네이션하여 반환

        :param hours: 조회할 시간
        :return: 조회된 Access Key 목록
        """
        async with self.session.client("iam") as client:  # type: ignore
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

    async def get_old_access_keys_from_credential_report(
        self,
        hours: int,
    ) -> List[OldAccessKey]:
        """Credential Report에서 N시간 이상된 AWS Access Key 목록을 페이지네이션하여 반환

        :param hours: 조회할 시간
        :return: 조회된 Access Key 목록
        """
        # if not self.credential_report:
        await self._generate_credential_report()
        self.credential_report = await self._get_credential_report()

        # logger.info(f"Credential Report created: {self.credential_report}")

        return await self._parse_credential_report(self.credential_report, hours)

    async def _parse_credential_report(
        self,
        credential_report: str,
        hours: int,
    ) -> List[OldAccessKey]:
        """Credential Report를 파싱하여 N시간 이상된 Access Key 목록을 반환"""
        import csv
        import io
        from datetime import datetime, timedelta, timezone

        # credential_report가 bytes라면 디코딩
        if isinstance(credential_report, bytes):
            csv_str = credential_report.decode("utf-8")
        else:
            csv_str = credential_report

        csv_file = io.StringIO(csv_str)
        reader = csv.DictReader(csv_file)

        threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
        old_keys = []
        for row in reader:
            user_name = row["user"]
            if user_name == "<root_account>":
                continue
            # access_key_1
            if row["access_key_1_active"] == "true":
                key_id = "access_key_1"
                created_str = row["access_key_1_last_rotated"]
                if created_str and created_str != "N/A":
                    created_date = datetime.strptime(
                        created_str,
                        "%Y-%m-%dT%H:%M:%SZ",
                    ).replace(tzinfo=timezone.utc)
                    if created_date < threshold:
                        old_keys.append(
                            OldAccessKey(
                                user_name=user_name,
                                access_key_id=key_id,
                                created_date=created_date,
                            ),
                        )
            # access_key_2
            if row["access_key_2_active"] == "true":
                key_id = "access_key_2"
                created_str = row["access_key_2_last_rotated"]
                if created_str and created_str != "N/A":
                    created_date = datetime.strptime(
                        created_str,
                        "%Y-%m-%dT%H:%M:%SZ",
                    ).replace(tzinfo=timezone.utc)
                    if created_date < threshold:
                        old_keys.append(
                            OldAccessKey(
                                user_name=user_name,
                                access_key_id=key_id,
                                created_date=created_date,
                            ),
                        )
        return old_keys

    async def _generate_credential_report(self) -> None:
        """Credential Report를 생성"""
        try:
            async with self.session.client("iam") as client:  # type: ignore
                response = await client.generate_credential_report()
                logger.info(
                    "Generating credentials report for your account. "
                    f"Current state is {response['State']}.",
                )
        except ClientError:
            logger.exception("Couldn't generate a credentials report for your account.")
            raise
        else:
            return response

    async def _get_credential_report(self) -> str:
        """Credential Report를 조회

        :return: The credentials report.
        """
        try:
            async with self.session.client("iam") as client:  # type: ignore
                response = await client.get_credential_report()
        except ClientError:
            logger.exception("Couldn't get credentials report.")
            raise
        else:
            return response["Content"]
