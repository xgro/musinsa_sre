from typing import Dict

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check() -> Dict[str, str]:
    """
    Checks the health of a project.

    It returns 200 if the project is healthy.
    """
    return {"status": "ok"}
