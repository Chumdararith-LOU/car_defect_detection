from fastapi import APIRouter

from schemas.host import HostProfile
from services.host_detector import detect_host_profile

router = APIRouter(tags=["host"])


@router.get("/host/profile", response_model=HostProfile)
def get_host_profile() -> HostProfile:
    return detect_host_profile()
