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
from loguru import logger
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

    # Build nested "recurring" options for the Stripe provider
    recurring_opts: dict[str, Any] = {
        "price_id": data.price_id,                 # live recurring price id
        "success_url": data.success_url,           # required by Checkout
        "cancel_url": data.success_url,            # use same as success if you don't have one
        "metadata": {
            "user_id": str(data.customer_id),
            "plan": (data.plan or "default"),
            "wallet_id": wallet.wallet.id,
        },
        # tip: you can add "trial_days": 7 here if you want a trial
    }
    if data.customer_email:
        recurring_opts["customer_email"] = data.customer_email

    extra = {"recurring": recurring_opts}

    resp = await provider_wallet.create_invoice(
        amount=0,                    # ignored for subscriptions
        payment_hash="recurring",
        currency=data.currency,      # ignored; Stripe uses the price's currency
        memo=data.memo,
        extra=extra,
    )
    logger.debug(resp)
    if not resp or not resp.ok:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=resp.error_message or "Could not create invoice.",
        )

    # Store whatever you like locally (keeping your original fields)
    recurring_data = RecurringPayment(
        id=resp.checking_id,
        price_id=data.price_id,
        payment_method_types=data.payment_method_types,
        success_url=data.success_url,
        metadata=str({"user_id": data.customer_id, "plan": data.plan}),
        customer_email=data.customer_email,
        check_live=True,
        wallet_id=wallet.wallet.id,
    )
    return await create_recurring(recurring_data)
