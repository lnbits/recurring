from pydantic import BaseModel

class CreateRecurringPayment(BaseModel):
    price_id: str | None = ""
    payment_method_types: list[str]
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
    payment_method_types: list[str]
    success_url: str | None = ""
    metadata: str | None = ""
    customer_email: str | None = ""
    check_live: bool | None = True
    wallet_id: str | None = ""