import asyncio

from lnbits.core.models import Payment
from lnbits.core.services import websocket_updater
from lnbits.tasks import register_invoice_listener

from .crud import get_reccuring, update_reccuring
from .models import CreateReccuringData

#######################################
########## RUN YOUR TASKS HERE ########
#######################################

# The usual task is to listen to invoices related to this extension


async def wait_for_paid_invoices():
    invoice_queue = asyncio.Queue()
    register_invoice_listener(invoice_queue, "ext_reccuring")
    while True:
        payment = await invoice_queue.get()
        await on_invoice_paid(payment)


# Do somethhing when an invoice related top this extension is paid


async def on_invoice_paid(payment: Payment) -> None:
    if payment.extra.get("tag") != "Reccuring":
        return

    reccuring_id = payment.extra.get("reccuringId")
    assert reccuring_id, "reccuringId not set in invoice"
    reccuring = await get_reccuring(reccuring_id)
    assert reccuring, "Reccuring does not exist"

    # update something in the db
    if payment.extra.get("lnurlwithdraw"):
        total = reccuring.total - payment.amount
    else:
        total = reccuring.total + payment.amount

    reccuring.total = total
    await update_reccuring(CreateReccuringData(**reccuring.dict()))

    # here we could send some data to a websocket on
    # wss://<your-lnbits>/api/v1/ws/<reccuring_id> and then listen to it on

    some_payment_data = {
        "name": reccuring.name,
        "amount": payment.amount,
        "fee": payment.fee,
        "checking_id": payment.checking_id,
    }

    await websocket_updater(reccuring_id, str(some_payment_data))
