# Description: This file contains the CRUD operations for talking to the database.


from lnbits.db import Database
from lnbits.helpers import urlsafe_short_hash

from .models import CreateReccuringData, Reccuring

db = Database("ext_reccuring")


async def create_reccuring(data: CreateReccuringData) -> Reccuring:
    data.id = urlsafe_short_hash()
    await db.insert("reccuring.maintable", data)
    return Reccuring(**data.dict())

async def get_reccuring(reccuring_id: str) -> Reccuring | None:
    return await db.fetchone(
        "SELECT * FROM reccuring.maintable WHERE id = :id",
        {"id": reccuring_id},
        Reccuring,
    )

async def get_reccurings(wallet_ids: str | list[str]) -> list[Reccuring]:
    if isinstance(wallet_ids, str):
        wallet_ids = [wallet_ids]
    q = ",".join([f"'{w}'" for w in wallet_ids])
    return await db.fetchall(
        f"SELECT * FROM reccuring.maintable WHERE wallet IN ({q}) ORDER BY id",
        model=Reccuring,
    )

async def delete_reccuring(reccuring_id: str) -> None:
    await db.execute(
        "DELETE FROM reccuring.maintable WHERE id = :id", {"id": reccuring_id}
    )
