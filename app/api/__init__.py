from fastapi import APIRouter

from . import monitor

router = APIRouter()

router.include_router(monitor.router, prefix="/monitor", tags=["monitor"])
