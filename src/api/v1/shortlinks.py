import sys
from fastapi import APIRouter, Depends, HTTPException, status, Request, \
    Response, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List, Optional, Union

from src.db.db import get_session
from src.schemas import shorturl as shorturl_schema
from src.services.urls import url_crud, usage_crud

router = APIRouter()
info_router = APIRouter()


@router.get("/", response_model=List[shorturl_schema.ShortUrl])
async def read_entities(
        *,
        db: AsyncSession = Depends(get_session),
        limit: int = Query(
            default=100,
            ge=1,
            alias='max-size',
            description='Query max size.'
        ),
        skip: int = Query(
            default=0,
            ge=0,
            description='Query offset.'
        ),
) -> Any:
    """
    Retrieve all records.
    """
    return await url_crud.get_multi(db=db, skip=skip, limit=limit)


@router.get("/{url_id}", response_class=RedirectResponse,
            status_code=
            status.HTTP_307_TEMPORARY_REDIRECT | status.HTTP_410_GONE,
            description='Redirect to original URL by short url id',
            responses={
                404:
                    {
                        "model": shorturl_schema.HTTPError,
                        "description": "Url was not found",
                    },
                410:
                    {
                        "model": shorturl_schema.HTTPError,
                        "description": "Url is marked as deleted",
                    }
            }
            )
async def get_url(
        *,
        url_id: int,
        request: Request,
        db: AsyncSession = Depends(get_session),
) -> Any:
    """
    Redirect to original url by ID.
    """
    record = await url_crud.get(db=db, id=url_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"URL with {url_id = } doesn't exist"
        )
    if record.deleted:
        raise HTTPException(status_code=status.HTTP_410_GONE,
                            detail=f"URL with {url_id = } marked as deleted")
    obj_in = {"client_host": request.client.host,
              "client_port": request.client.port,
              "url_id": url_id}
    await usage_crud.create(db=db, obj_in=obj_in)
    return RedirectResponse(record.original_url)


@router.get("/{short_url_id}/status", description='Get URL usage status',
            response_model=Union[int, List[shorturl_schema.UrlUsageFull]],
            responses={
                404:
                    {
                        "model": shorturl_schema.HTTPError,
                        "description": "Url was not found",
                    }
            }
            )
async def get_url_usage_status(
        *,
        short_url_id: int,
        full_info: Optional[bool] = Query(default=False, alias='full-info'),
        max_result: int = Query(
            default=10,
            ge=1,
            alias='max-size',
            description='Query max size.'
        ),
        offset: int = Query(
            default=0,
            ge=0,
            description='Query offset.'
        ),
        db: AsyncSession = Depends(get_session),
) -> Any:
    """
    Get URL usage status.
    """
    count = await usage_crud.count(db=db, obj_id=short_url_id,
                                   max_result=max_result,
                                   offset=offset,
                                   full_info=full_info)
    if not count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not found"
        )
    return count


@router.post(
    "/",
    response_model=Union[shorturl_schema.ShortUrl, shorturl_schema.HTTPError],
    status_code=status.HTTP_201_CREATED,
    description='Create a short URL',
    responses={
        400: {
            "model": shorturl_schema.HTTPError,
            "description": "Url already exists in the system",
        }
    }
)
async def create_short_url(
    *,
    db: AsyncSession = Depends(get_session),
    url_in: shorturl_schema.ShortUrlCreate,
) -> Any:
    """
    Create new short url.
    """
    url = await url_crud.create(db=db, obj_in=url_in)
    if hasattr(url, "detail"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=url.detail)
    return url


@router.post(
    "/multi", response_model=List[shorturl_schema.ShortUrl],
    status_code=status.HTTP_201_CREATED,
    description='Create several short URLs',
    responses={
        400: {
            "model": shorturl_schema.HTTPError,
            "description": "Url already exists in the system",
        }
    }
)
async def create_short_urls(
    *,
    db: AsyncSession = Depends(get_session),
    urls_in: List[shorturl_schema.ShortUrlCreate],
) -> Any:
    """
    Create new short urls.
    """
    url = await url_crud.create_multi(db=db, objs_in=urls_in)
    if url:
        return url
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Url already exists in the system")


@router.patch("/", description='Mark url as Gone')
async def delete_url(
    *,
    db: AsyncSession = Depends(get_session),
    url_id: int,
) -> Any:
    """
    Mark url as Gone.
    """
    await url_crud.update_deleted_field(db=db, url_id=url_id)
    return Response(status_code=status.HTTP_200_OK)


@info_router.get('/version')
async def info_handler():
    return {
        'api': 'v1',
        'python': sys.version_info
    }


@info_router.get('/ping', response_model=shorturl_schema.DBHealthModel)
async def check_db_status(db: AsyncSession = Depends(get_session)) -> Any:
    return await url_crud.get_db_status(db=db)
