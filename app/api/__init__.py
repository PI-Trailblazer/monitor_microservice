from fastapi import APIRouter

from . import offer

router = APIRouter()

router.include_router(offer.router, prefix="/offer", tags=["offer"])
# router.include_router(payment.router, prefix="/payment", tags=["payment"])
