import csv
import io
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import aioboto3  # type: ignore
from botocore.exceptions import ClientError
from loguru import logger

from backend.web.api.iam.schema import OldAccessKey


class IAMService:
    def __init__(self) -> None:
        """IAMService 초기화.

        :return: None
        """
        self.session = aioboto3.Session()

    async def get_old_access_keys_from_list_users(
        self,
        hours: int,
    ) -> List[OldAccessKey]:
        """N시간 이상된 Access Key 목록을 페이지네이션하여 반환

        :param hours: 조회할 시간
        :return: 조회된 Access Key 목록
        """
        try:
            async with self.session.client("iam") as client:  # type: ignore
                paginator = client.get_paginator("list_users")

                users = []
                async for page_obj in paginator.paginate():
                    users.extend(page_obj["Users"])

                # 임계값 설정
                threshold = datetime.now(timezone.utc) - timedelta(hours=hours)

                # 유저 목록 조회
                old_keys = []
                for user in users:
                    access_keys = await client.list_access_keys(
                        UserName=user["UserName"],
                    )
                    for key in access_keys["AccessKeyMetadata"]:
                        if key["CreateDate"] < threshold:
                            old_keys.append(
                                OldAccessKey(
                                    user_name=user["UserName"],
                                    access_key_id=key["AccessKeyId"],
                                    created_date=key["CreateDate"],
                                ),
                            )

                return old_keys
        except ClientError:
            logger.exception("Couldn't get access keys from list users.")
            raise

    async def get_old_access_keys_from_credential_report(
        self,
        hours: int,
    ) -> List[OldAccessKey]:
        """Credential Report에서 N시간 이상된 AWS Access Key 목록을 반환

        :param hours: 조회할 시간
        :return: 조회된 Access Key 목록
        """
        try:
            # 자격 증명 보고서 생성
            await self._generate_credential_report()

            # 자격 증명 보고서 조회
            credential_report = await self._get_credential_report()

            # 자격 증명 보고서 파싱
            return self._parse_credential_report(credential_report, hours)
        except Exception:
            logger.exception("Couldn't get access keys from credential report.")
            raise

    def _parse_credential_report(
        self,
        credential_report: bytes,
        hours: int,
    ) -> List[OldAccessKey]:
        """Credential Report를 파싱하여 N시간 이상된 Access Key 목록을 반환

        :param credential_report: Credential Report
        :param hours: 조회할 시간
        :return: 조회된 Access Key 목록
        """
        # credential_report를 문자열로 변환
        csv_str = credential_report.decode("utf-8")
        reader = csv.DictReader(io.StringIO(csv_str))

        # 현재 시간에서 hours만큼 빼서 임계값 설정
        threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
        old_keys = []
        for row in reader:
            user_name = row["user"]
            # 루트 계정은 무시
            if user_name == "<root_account>":
                continue

            # access_key_1과 access_key_2를 조회
            for idx in [1, 2]:
                # access_key가 비활성화되어 있으면 루프 패스
                if row[f"access_key_{idx}_active"] != "true":
                    logger.debug(
                        f"Access key {idx} is not active for user {user_name}.",
                    )
                    continue

                # access_key가 마지막으로 생성된 시간을 조회
                created_str = row[f"access_key_{idx}_last_rotated"]
                created_date = self._parse_datetime(created_str)

                # 임계값보다 오래 전에 생성된 경우 old_keys 배열에 추가
                if created_date and created_date < threshold:
                    old_keys.append(
                        OldAccessKey(
                            user_name=user_name,
                            access_key_id=f"access_key_{idx}",
                            created_date=created_date,
                        ),
                    )
        return old_keys

    @staticmethod
    def _parse_datetime(dt_str: str) -> Optional[datetime]:
        """datetime 문자열을 datetime 객체로 변환

        :param dt_str: datetime 문자열
        :return: datetime 객체
        """
        if not dt_str or dt_str == "N/A":
            return None
        return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc,
        )

    async def _generate_credential_report(self) -> None:
        """Credential Report를 생성

        :return: None
        """
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

    async def _get_credential_report(self) -> bytes:
        """Credential Report를 조회

        :return: The credentials report.
        """
        try:
            async with self.session.client("iam") as client:  # type: ignore
                response = await client.get_credential_report()
        except ClientError:
            logger.exception("Couldn't get credentials report.")
            raise
        return response["Content"]
