from datetime import datetime

from pydantic import BaseModel


class HTTPError(BaseModel):
    detail: str

    class Config:
        schema_extra = {
            "example": {"detail": "HTTPException raised."},
        }


class ORMBase(BaseModel):
    class Config:
        orm_mode = True


class DBHealthModel(ORMBase):
    db_status: str


class ShortUrlBase(BaseModel):
    original_url: str


class ShortUrlCreate(ShortUrlBase):
    pass


class ShortUrl(ORMBase):
    id: int
    original_url: str
    short_url: str
    created_at: datetime


class UrlUsageBase(BaseModel):
    url_id: int


class UrlUsageCreate(UrlUsageBase):
    client_host: str
    client_port: int


class UrlUsage(ORMBase):
    id: int
    url_id: int
    used_at: datetime


class UrlUsageFull(UrlUsageBase):
    url_id: int
    used_at: datetime
    client_host: str
    client_port: int
