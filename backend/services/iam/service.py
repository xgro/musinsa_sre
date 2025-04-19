import asyncio
import csv
import io
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import aioboto3  # type: ignore
from botocore.client import BaseClient

from backend.web.api.iam.schema import OldAccessKey

# ---------------------------------------------------------------------------
# IAMService
# ---------------------------------------------------------------------------


class IAMService:
    """재사용 가능한, 비동기 친화적인 IAM 액세스 키 관리를 위한 도우미.

    - 싱글톤 aioboto3 클라이언트 (비동기 락)
    - 세마포어로 동시성 제한 (AWS IAM API rate limit 보호)
    - 오래된 액세스 키 조회를 위한 두 가지 public 메서드 제공
    """

    _TIME_FMT = "%Y-%m-%dT%H:%M:%SZ"

    # ---------------------------- life‑cycle ----------------------------
    def __init__(self) -> None:
        """aioboto3 세션 및 싱글톤 클라이언트, 락/세마포어 초기화."""

        self._session = aioboto3.Session()
        self._client: Optional[BaseClient] = None
        self._lock = asyncio.Lock()  # double‑check locking
        self._sem = asyncio.Semaphore(5)  # IAM ≈ 10 TPS → 5 동시 호출 정도로 제한

    async def close(self) -> None:
        """싱글톤 클라이언트 종료 (자원 해제).

        서비스 종료 시 반드시 호출 필요
        """
        if self._client is not None:
            await self._client.__aexit__(None, None, None)
            self._client = None

    # --------------------------- low‑level I/O ---------------------------
    async def _client_async(self) -> BaseClient:
        """
        싱글톤 IAM 클라이언트 반환 (비동기 락으로 중복 생성 방지)
        """
        # 이미 생성된 경우 반환
        if self._client is None:
            async with self._lock:
                if self._client is None:  # double check
                    self._client = await self._session.client("iam").__aenter__()

        # 클라이언트가 여전히 None인 경우 예외 발생
        assert self._client is not None

        # 클라이언트 반환
        return self._client

    async def _generate_credential_report(
        self,
        client: BaseClient,
        *,
        max_attempts: int = 10,
        delay: int = 2,
    ) -> None:
        """IAM Credential Report 생성 (비동기 폴링).

        - IN_PROGRESS 상태일 경우 delay 간격으로 재시도
        - 실패/타임아웃 시 예외 발생

        :param client: IAM 클라이언트
        :param max_attempts: 최대 재시도 횟수
        :param delay: 재시도 간격 (초)
        :return: None
        """
        # 자격 증명 보고서 생성
        resp = await client.generate_credential_report()
        state = resp["State"]
        attempt = 0

        # 생성 완료 또는 최대 재시도 횟수 도달 시 종료
        while state == "IN_PROGRESS" and attempt < max_attempts:
            await asyncio.sleep(delay)
            resp = await client.generate_credential_report()
            state = resp["State"]
            attempt += 1

        # 생성 실패 시 예외 발생
        if state != "COMPLETE":
            raise RuntimeError(f"Credential report generation failed: {state}")

    async def _fetch_keys_for_user(
        self,
        client: BaseClient,
        user: str,
    ) -> List[Dict[str, Any]]:
        """ListAccessKeys API를 rate-limit 하여 호출 (세마포어 사용).

        :param client: IAM 클라이언트
        :param user: 유저 이름
        :return: 액세스 키 목록
        """
        # 세마포어 사용
        async with self._sem:
            return (await client.list_access_keys(UserName=user))["AccessKeyMetadata"]

    # -------------------------- helper utilities -------------------------
    @classmethod
    def _parse_dt(cls, s: str) -> Optional[datetime]:
        """
        AWS ISO8601 문자열을 datetime 객체로 변환
        """
        # N/A 또는 빈 문자열인 경우 None 반환
        if not s or s == "N/A":
            return None

        # 시간 문자열 파싱
        return datetime.strptime(s, cls._TIME_FMT).replace(tzinfo=timezone.utc)

    # ---------------------------- public API ----------------------------
    async def get_old_access_keys_from_list_users(
        self, *, hours: int
    ) -> List[OldAccessKey]:
        """모든 유저의 액세스 키를 brute-force로 조회하여, 생성된 지 N시간 이상된 키를 반환.
        (ListUsers + ListAccessKeys 조합, 비용↑)

        :param hours: 임계값 (시간)
        :return: 오래된 액세스 키 목록
        """
        # 클라이언트 초기화
        client = await self._client_async()

        # 임계값 계산
        threshold = datetime.now(timezone.utc) - timedelta(hours=hours)

        # 모든 유저 목록 수집
        users: List[str] = []

        # 모든 유저 목록 조회 (루트 계정 포함), 페이지네이터 사용
        paginator = client.get_paginator("list_users")
        pages = paginator.paginate()
        async for page in pages:  # type: ignore
            users.extend(u["UserName"] for u in page["Users"])

        async def process(user: str) -> List[OldAccessKey]:
            """각 유저의 액세스 키 중 임계값 이전 생성된 것만 필터링.

            :param user: 유저 이름
            :return: 오래된 액세스 키 목록
            """
            # 유저의 액세스 키 목록 조회
            keys = await self._fetch_keys_for_user(client, user)

            # 임계값 이전 생성된 것만 필터링
            return [
                OldAccessKey(
                    user_name=user,
                    access_key_id=k["AccessKeyId"],
                    created_date=k["CreateDate"],
                )
                for k in keys
                if k["CreateDate"] < threshold
            ]

        # 모든 유저의 오래된 액세스 키 목록 수집
        batches = await asyncio.gather(*(process(u) for u in users))
        return [item for sub in batches for item in sub]

    async def get_old_access_keys_from_credential_report(
        self, *, hours: int
    ) -> List[OldAccessKey]:
        """Credential Report를 우선 활용해 후보를 추린 뒤, 실제 키 ID 조회는 ListAccessKeys로 제한적으로 호출 (비용↓).

        :param hours: 임계값 (시간)
        :return: 오래된 액세스 키 목록
        """
        # 클라이언트 초기화
        client = await self._client_async()

        # 자격 증명 보고서 생성
        await self._generate_credential_report(client)

        # 자격 증명 보고서 조회
        report_bytes = (await client.get_credential_report())["Content"]

        # 임계값 계산
        threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
        reader = csv.DictReader(io.StringIO(report_bytes.decode()))

        # (user, rotated_at) 검사 대상 유저 목록
        users: List[Tuple[str, datetime]] = []
        for row in reader:
            user = row["user"]
            # 루트 계정은 무시
            if user == "<root_account>":
                continue

            # 활성화된 키 중 last_rotated된 시간이 임계값 이전인 것만 추려냄
            for idx in (1, 2):
                # 활성화된 키만 처리
                if row[f"access_key_{idx}_active"] != "true":
                    continue

                # last_rotated된 시간이 있고, 임계값 이전인 경우 검사 대상에 추가
                rotated = self._parse_dt(row[f"access_key_{idx}_last_rotated"])
                if rotated and rotated < threshold:
                    users.append((user, rotated))

        async def id_for(user: str, rotated_at: datetime) -> Optional[OldAccessKey]:
            """검사 대상 유저의 액세스 키 중 생성일이 정확히 일치하는 키만 반환.

            :param user: 유저 이름
            :param rotated_at: 회전 일시
            :return: 오래된 액세스 키 목록
            """
            # 유저의 액세스 키 목록 조회
            keys = await self._fetch_keys_for_user(client, user)

            # 생성일이 정확히 일치하는 키만 반환
            for k in keys:
                # IAM 시간은 초 단위로 정확하므로, 엄격한 동등성 검사 가능
                if k["CreateDate"] == rotated_at:
                    return OldAccessKey(
                        user_name=user,
                        access_key_id=k["AccessKeyId"],
                        created_date=k["CreateDate"],
                    )
            return None

        results = await asyncio.gather(*(id_for(u, t) for u, t in users))
        return [r for r in results if r is not None]
