from fastapi import Request
from fastapi import status
from fastapi.responses import ORJSONResponse


class BlackListMiddleware:
    def __init__(self, black_list: set):
        self.black_list = black_list

    async def __call__(self, request: Request, call_next):
        client_ip = request.headers.get('X-Forwarded-For')
        host = request.headers.get('host', '').split(':')[0]
        # "Если по какой-то причине  не будет заголовка host, тут свалится IndexError"
        # почему - get('host', '') -> ''?
        if host in self.black_list or client_ip in self.black_list:
            return ORJSONResponse(status_code=status.HTTP_403_FORBIDDEN,
                                  content=f"client {client_ip} "
                                          f"{host} is in blacklist")
        return await call_next(request)
