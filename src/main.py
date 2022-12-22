import uvicorn
from fastapi import FastAPI
from fastapi import Request
from fastapi import status
from fastapi.responses import ORJSONResponse

from src.api.v1 import shortlinks
from src.core import config
from src.core.config import app_settings

app = FastAPI(
    title=app_settings.app_title,
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    client_ip = request.headers.get('X-Forwarded-For')
    host = request.headers.get('host', '').split(':')[0]
    if host in app_settings.blacklist or client_ip in app_settings.blacklist:
        return ORJSONResponse(status_code=status.HTTP_403_FORBIDDEN,
                              content=f"client {client_ip} "
                                      f"{host} is in blacklist")

    return await call_next(request)


app.include_router(shortlinks.router, prefix="/api/v1/tinyurl",
                   tags=["short url"])
app.include_router(shortlinks.info_router, prefix="/info", tags=["info"])
if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host=config.PROJECT_HOST,
        port=config.PROJECT_PORT,
    )
