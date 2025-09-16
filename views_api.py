# Description: This file contains the extensions API endpoints.

from datetime import datetime, timezone
from http import HTTPStatus

from fastapi import APIRouter, Depends
from lnbits.core.crud import get_user, get_wallet
from lnbits.core.models import WalletTypeInfo
from lnbits.decorators import require_admin_key
from lnbits.fiat import get_fiat_provider
from lnbits.settings import settings
from starlette.exceptions import HTTPException

from .crud import (
    create_recurring,
    delete_recurring,
    get_recurring,
    get_recurrings,
    update_recurring,
)
from .helpers import check_live, is_entitled_status
from .models import CreateRecurringPayment, RecurringPayment, RecurringPaymentReturn

recurring_api_router = APIRouter()


@recurring_api_router.get("/api/v1/{recurring_id}")
async def api_recurring(
    recurring_id: str, wallet: WalletTypeInfo = Depends(require_admin_key)
) -> RecurringPayment:
    recurring = await get_recurring(recurring_id)
    if not recurring:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="recurring payment does not exist."
        )
    wallet_info = await get_wallet(recurring.wallet_id)
    if wallet_info.user != wallet.wallet.user:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Not your wallet.")
    status = await check_live(recurring_id, settings.stripe_api_secret_key)
    recurring.check_live = is_entitled_status(status)
    return recurring


@recurring_api_router.get("/api/v1")
async def api_recurrings(
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> list[RecurringPayment]:
    wallet_ids = [wallet.wallet.id]
    user = await get_user(wallet.wallet.user)
    if user.id != wallet.wallet.user:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Not your wallet.")
    wallet_ids = user.wallet_ids if user else []
    recurrings = await get_recurrings(wallet_ids)

    updated_recurrings: list[RecurringPayment] = []
    for recurring in recurrings:
        now_ts = int(datetime.now(timezone.utc).timestamp())
        # if it its not live and 1 day has passed check,
        # or if it is live and 30 days have passed check.
        if (not recurring.check_live and (recurring.last_checked + 86400) > now_ts) or (
            recurring.check_live and (recurring.last_checked + 2592000) > now_ts
        ):
            status = await check_live(recurring.id, settings.stripe_api_secret_key)
            recurring.check_live = is_entitled_status(status)
            if recurring.check_live:
                # payment is active again, update it
                updated = await update_recurring(recurring)
                updated_recurrings.append(updated)
            else:
                # assume its abandoned and delete it
                await delete_recurring(recurring.id)
        else:
            updated_recurrings.append(recurring)

    return updated_recurrings


@recurring_api_router.post("/api/v1", status_code=HTTPStatus.CREATED)
async def api_recurring_create(
    data: CreateRecurringPayment,
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> RecurringPaymentReturn:
    provider_wallet = await get_fiat_provider("stripe")

    # Build nested "recurring" options for the Stripe provider
    recurring_opts: dict[str, Any] = {
        "price_id": data.price_id,
        "success_url": data.success_url,
        "cancel_url": data.success_url,
        "metadata": {
            "user_id": str(data.customer_id),
            "plan": (data.plan or "default"),
            "wallet_id": wallet.wallet.id,
        },
        "trial_days": 7,
    }
    if data.customer_email:
        recurring_opts["customer_email"] = data.customer_email

    extra = {"recurring": recurring_opts}

    resp = await provider_wallet.create_invoice(
        amount=0,  # ignored for subscriptions
        payment_hash="recurring",
        currency=data.currency,  # ignored; Stripe uses the price's currency
        memo=data.memo,
        extra=extra,
    )
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
    returned_data = RecurringPaymentReturn(
        **recurring_data.dict(),
        payment_request=resp.payment_request,
    )
    created = await create_recurring(recurring_data)
    if not created:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail="Could not create recurring payment.",
        )
    return returned_data
