from fastapi import APIRouter

from .crud import db
from .views import reccuring_generic_router
from .views_api import reccuring_api_router

reccuring_ext: APIRouter = APIRouter(prefix="/reccuring", tags=["Reccuring"])
reccuring_ext.include_router(reccuring_generic_router)
reccuring_ext.include_router(reccuring_api_router)

reccuring_static_files = [
    {
        "path": "/reccuring/static",
        "name": "reccuring_static",
    }
]


__all__ = [
    "db",
    "reccuring_ext",
    "reccuring_static_files",
]
