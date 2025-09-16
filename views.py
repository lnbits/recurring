from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from lnbits.core.models import User
from lnbits.decorators import check_user_exists
from lnbits.helpers import template_renderer

recurring_generic_router = APIRouter()

def recurring_renderer():
    return template_renderer(["recurring/templates"])

@recurring_generic_router.get("/", response_class=HTMLResponse)
async def index(req: Request, user: User = Depends(check_user_exists)):
    return recurring_renderer().TemplateResponse(
        "recurring/index.html", {"request": req, "user": user.json()}
    )
