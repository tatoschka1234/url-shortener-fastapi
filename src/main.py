import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.api.v1 import shortlinks, info_links
from src.core.config import app_settings
from src.middleware.black_list import BlackListMiddleware


def init_middlewares(fast_api_app: FastAPI) -> None:
    my_middleware = BlackListMiddleware(app_settings.blacklist)
    fast_api_app.add_middleware(BaseHTTPMiddleware, dispatch=my_middleware)


app = FastAPI(
    title=app_settings.app_title,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
)
init_middlewares(app)
app.include_router(shortlinks.router, prefix="/api/v1/tinyurl",
                   tags=["short url"])
app.include_router(info_links.info_router, prefix="/info", tags=["info"])

if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host=app_settings.PROJECT_HOST,
        port=app_settings.PROJECT_PORT,
    )
