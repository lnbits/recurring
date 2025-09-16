# Description: This file contains the extensions API endpoints.

from http import HTTPStatus

from fastapi import APIRouter, Depends, Request
from lnbits.core.crud import get_user
from lnbits.core.models import WalletTypeInfo
from lnbits.core.services import create_invoice
from lnbits.decorators import require_admin_key, require_invoice_key
from starlette.exceptions import HTTPException
from lnbits.settings import settings
from .crud import (
    create_recurring,
    get_recurring,
    get_recurrings,
)
from lnbits.fiat import get_fiat_provider
from .helpers import check_live, is_entitled_status
from .models import RecurringPayment, CreateRecurringPayment

recurring_api_router = APIRouter()

@recurring_api_router.get(
    "/api/v1/recurring/{recurring_id}",
    dependencies=[Depends(require_admin_key)],
)
async def api_recurring(recurring_id: str) -> RecurringPayment:
    recurring = await get_recurring(recurring_id)
    if not recurring:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="recurring payment does not exist."
        )
    status = await check_live(recurring_id, settings.stripe_api_secret_key)
    recurring.check_live = is_entitled_status(status)
    return recurring

@recurring_api_router.get("/api/v1/recurring")
async def api_recurrings(
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> list[RecurringPayment]:
    wallet_ids = [wallet.wallet.id]
    user = await get_user(wallet.wallet.user)
    if user.id != wallet.wallet.user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Not your wallet."
        )
    wallet_ids = user.wallet_ids if user else []
    recurrings = await get_recurrings(wallet_ids)
    return recurrings

@recurring_api_router.post("/api/v1/recurring", status_code=HTTPStatus.CREATED)
async def api_recurring_create(
    data: CreateRecurringPayment,
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> RecurringPayment:
    provider_wallet = await get_fiat_provider("stripe")
    resp = await provider_wallet.create_invoice(
        amount=0,
        payment_hash="recurring",
        currency=data.currency,
        memo=data.memo,
        extra=data.dict(exclude={"memo"}),
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
    recurring = await create_recurring(recurring_data)
    return recurring