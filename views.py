from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from lnbits.core.models import User
from lnbits.decorators import check_user_exists
from lnbits.helpers import template_renderer

reccuring_generic_router = APIRouter()

def reccuring_renderer():
    return template_renderer(["reccuring/templates"])

@reccuring_generic_router.get("/", response_class=HTMLResponse)
async def index(req: Request, user: User = Depends(check_user_exists)):
    return reccuring_renderer().TemplateResponse(
        "reccuring/index.html", {"request": req, "user": user.json()}
    )
