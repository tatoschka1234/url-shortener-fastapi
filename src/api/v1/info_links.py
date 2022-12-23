import sys
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from src.db.db import get_session
from src.schemas import shorturl as shorturl_schema
from src.services.urls import url_crud

info_router = APIRouter()


@info_router.get('/version')
async def info_handler():
    return {
        'api': 'v1',
        'python': sys.version_info
    }


@info_router.get('/ping', response_model=shorturl_schema.DBHealthModel)
async def check_db_status(db: AsyncSession = Depends(get_session)) -> Any:
    return await url_crud.get_db_status(db=db)
