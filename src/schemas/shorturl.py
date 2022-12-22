from datetime import datetime

from pydantic import BaseModel


class HTTPError(BaseModel):
    detail: str

    class Config:
        schema_extra = {
            "example": {"detail": "HTTPException raised."},
        }


class DBHealthModel(BaseModel):
    db_status: str

    class Config:
        orm_mode = True


class ShortUrlBase(BaseModel):
    original_url: str


class ShortUrlCreate(ShortUrlBase):
    pass


class ShortUrl(ShortUrlBase):
    id: int
    original_url: str
    short_url: str
    created_at: datetime

    class Config:
        orm_mode = True


class UrlUsageBase(BaseModel):
    url_id: int


class UrlUsageCreate(UrlUsageBase):
    client_host: str
    client_port: int


class UrlUsage(UrlUsageBase):
    id: int
    url_id: int
    used_at: datetime

    class Config:
        orm_mode = True


class UrlUsageFull(UrlUsageBase):
    url_id: int
    used_at: datetime
    client_host: str
    client_port: int
