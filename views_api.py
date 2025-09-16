# Description: This file contains the extensions API endpoints.

from http import HTTPStatus

from fastapi import APIRouter, Depends, Request
from lnbits.core.crud import get_user
from lnbits.core.models import WalletTypeInfo
from lnbits.core.services import create_invoice
from lnbits.decorators import require_admin_key, require_invoice_key
from starlette.exceptions import HTTPException
import settings
from .crud import (
    create_reccuring,
    get_reccuring,
    get_reccurings,
)
from .helpers import check_live, is_entitled_status
from .models import RecurringPayment, CreateRecurringPayment

reccuring_api_router = APIRouter()

@reccuring_api_router.get(
    "/api/v1/reccuring/{reccuring_id}",
    dependencies=[Depends(require_admin_key)],
)
async def api_reccuring(reccuring_id: str) -> RecurringPayment:
    reccuring = await get_reccuring(reccuring_id)
    if not reccuring:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Reccuring payment does not exist."
        )
    status = await check_live(reccuring_id, settings.stripe_api_key)
    reccuring.check_live = is_entitled_status(status)
    return reccuring

@reccuring_api_router.get("/api/v1/reccuring")
async def api_reccurings(
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> list[RecurringPayment]:
    wallet_ids = [wallet.wallet.id]
    user = await get_user(wallet.wallet.user)
    if user.id != wallet.wallet.user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Not your wallet."
        )
    wallet_ids = user.wallet_ids if user else []
    reccurings = await get_reccurings(wallet_ids)
    return reccurings

@reccuring_api_router.post("/api/v1/reccuring", status_code=HTTPStatus.CREATED)
async def api_reccuring_create(
    data: CreateRecurringPayment,
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> RecurringPayment:
    data.wallet_id = wallet.wallet.id
    extra = {
        "recurring": {
            "price_id": data.price_id,
            "payment_method_types": data.payment_method_types,
            "user_email": data.customer_email,
            "success_url": data.success_url,
            "metadata": {"user_id": data.customer_id, "plan": data.plan},
            "customer_email": data.customer_email,
        }
    }
    resp = await provider_wallet.create_invoice(
        currency=data.currency,
        memo=data.memo,
        extra=extra,
    )
    if not resp or resp.error:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=resp.error)
    recurring_data = CreateRecurringPayment(
        id=resp.id,
        price_id=data.price_id,
        payment_method_types=",".join(data.payment_method_types),
        success_url=data.success_url,
        metadata=str({"user_id": data.customer_id, "plan": data.plan}),
        customer_email=data.customer_email,
        check_live=True,
        wallet_id=wallet.wallet.id,
    )
    reccuring = await create_reccuring(recurring_data)
    return reccuring