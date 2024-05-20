from fastapi import APIRouter

from . import dmo, provider

router = APIRouter()

router.include_router(dmo.router, prefix="/monitor/dmo", tags=["dmo"])
router.include_router(provider.router, prefix="/monitor/provider", tags=["provider"])

