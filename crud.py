# Description: This file contains the CRUD operations for talking to the database.


from lnbits.db import Database

from .models import CreateRecurringPayment, RecurringPayment

db = Database("ext_recurring")


async def create_recurring(data: CreateRecurringPayment) -> RecurringPayment:
    await db.insert("recurring.maintable", data)
    return RecurringPayment(**data.dict())


async def update_recurring(data: RecurringPayment) -> RecurringPayment:
    await db.update("recurring.maintable", data)
    return RecurringPayment(**data.dict())


async def get_recurring(recurring_id: str) -> RecurringPayment | None:
    return await db.fetchone(
        "SELECT * FROM recurring.maintable WHERE id = :id",
        {"id": recurring_id},
        RecurringPayment,
    )


async def get_recurrings(wallet_ids: str | list[str]) -> list[RecurringPayment]:
    if isinstance(wallet_ids, str):
        wallet_ids = [wallet_ids]
    q = ",".join([f"'{w}'" for w in wallet_ids])
    return await db.fetchall(
        f"SELECT * FROM recurring.maintable WHERE wallet_id IN ({q}) ORDER BY id",
        model=RecurringPayment,
    )


async def delete_recurring(recurring_id: str) -> None:
    await db.execute(
        "DELETE FROM recurring.maintable WHERE id = :id", {"id": recurring_id}
    )
