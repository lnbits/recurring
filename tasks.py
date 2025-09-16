import asyncio

from lnbits.core.models import Payment
from lnbits.core.services import websocket_updater
from lnbits.tasks import register_invoice_listener

from .crud import get_recurring, update_recurring
from .models import CreateReccuringData

#######################################
########## RUN YOUR TASKS HERE ########
#######################################

# The usual task is to listen to invoices related to this extension


async def wait_for_paid_invoices():
    invoice_queue = asyncio.Queue()
    register_invoice_listener(invoice_queue, "ext_recurring")
    while True:
        payment = await invoice_queue.get()
        await on_invoice_paid(payment)


# Do somethhing when an invoice related top this extension is paid


async def on_invoice_paid(payment: Payment) -> None:
    if payment.extra.get("tag") != "Reccuring":
        return

    recurring_id = payment.extra.get("recurringId")
    assert recurring_id, "recurringId not set in invoice"
    recurring = await get_recurring(recurring_id)
    assert recurring, "Reccuring does not exist"

    # update something in the db
    if payment.extra.get("lnurlwithdraw"):
        total = recurring.total - payment.amount
    else:
        total = recurring.total + payment.amount

    recurring.total = total
    await update_recurring(CreateReccuringData(**recurring.dict()))

    # here we could send some data to a websocket on
    # wss://<your-lnbits>/api/v1/ws/<recurring_id> and then listen to it on

    some_payment_data = {
        "name": recurring.name,
        "amount": payment.amount,
        "fee": payment.fee,
        "checking_id": payment.checking_id,
    }

    await websocket_updater(recurring_id, str(some_payment_data))
