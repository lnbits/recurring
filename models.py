from pydantic import BaseModel
from datetime import datetime, timezone

class CreateRecurringPayment(BaseModel):
    price_id: str | None = ""
    payment_method_types: list[str] = ["bacs_debit"]
    success_url: str | None = ""
    customer_email: str | None = ""
    currency: str | None = ""
    customer_id: bool | None = True
    memo: str | None = ""
    email: str | None = ""
    plan: str | None = ""


class RecurringPayment(BaseModel):
    id: str | None = ""
    price_id: str | None = ""
    payment_method_types: list[str] = ["bacs_debit"]
    success_url: str | None = ""
    metadata: str | None = ""
    customer_email: str | None = ""
    check_live: bool | None = True
    wallet_id: str | None = ""
    last_checked: datetime = datetime.now(timezone.utc)


class RecurringPaymentReturn(BaseModel):
    id: str | None = ""
    price_id: str | None = ""
    payment_method_types: list[str] = ["bacs_debit"]
    success_url: str | None = ""
    metadata: str | None = ""
    customer_email: str | None = ""
    check_live: bool | None = True
    wallet_id: str | None = ""
    payment_request: str | None = ""
