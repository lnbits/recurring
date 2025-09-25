from fastapi import APIRouter

from .crud import db
from .views import recurring_generic_router
from .views_api import recurring_api_router

recurring_ext: APIRouter = APIRouter(prefix="/recurring", tags=["Recurring"])
recurring_ext.include_router(recurring_generic_router)
recurring_ext.include_router(recurring_api_router)

recurring_static_files = [
    {
        "path": "/recurring/static",
        "name": "recurring_static",
    }
]


__all__ = [
    "db",
    "recurring_ext",
    "recurring_static_files",
]
