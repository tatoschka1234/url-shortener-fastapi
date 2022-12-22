import pytest
import random
import string

from fastapi import status
from httpx import AsyncClient
from http import HTTPStatus
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_short_url(client: AsyncClient,
                                async_session: AsyncSession) -> None:
    url = ''.join(random.choices(string.ascii_lowercase, k=5))
    response = await client.post(
        '/api/v1/tinyurl/',
        json={'original_url': f'http://{url}.com'}
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert 'short_url' in response.json()


@pytest.mark.asyncio
async def test_create_several_urls(client: AsyncClient,
                                async_session: AsyncSession) -> None:
    response = await client.post(
        '/api/v1/tinyurl/multi',
        json=[
            {'original_url': 'http://127.0.0.1:8000/info/version/'},
            {'original_url': 'http://127.0.0.1:8000/info/ping'},
        ]
    )
    assert response.status_code == HTTPStatus.CREATED
    results = response.json()
    assert len(results) == 2
    assert isinstance(results, list)
    for result in results:
        assert result.get('created_at')
        assert result.get('short_url')
        assert result.get('original_url')


@pytest.mark.asyncio
async def test_create_duplicate(client: AsyncClient,
                                async_session: AsyncSession) -> None:
    response = await client.post(
        '/api/v1/tinyurl/',
        json=
        {'original_url': 'http://127.0.0.1:8000/info/version/'},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "duplicate key" in response.text


@pytest.mark.asyncio
async def test_get_all(client: AsyncClient,
                       async_session: AsyncSession) -> None:
    response = await client.get("/api/v1/tinyurl/")
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    assert len(results) > 2


@pytest.mark.asyncio
async def test_get_by_url(client: AsyncClient,
                          async_session: AsyncSession) -> None:
    response = await client.get("/api/v1/tinyurl/2")
    assert response.status_code == HTTPStatus.TEMPORARY_REDIRECT
    assert response.headers.get('Location') == 'http://127.0.0.1:8000/info/version/'


@pytest.mark.asyncio
async def test_mark_deleted(client: AsyncClient,
                            async_session: AsyncSession) -> None:
    await client.patch("/api/v1/tinyurl/", params={"url_id": 2})
    response = await client.get("/api/v1/tinyurl/2/", follow_redirects=True)
    assert response.status_code == HTTPStatus.GONE
    result = response.json()
    assert "marked as deleted" in result.get("detail")


@pytest.mark.asyncio
async def test_get_status(client: AsyncClient,
                          async_session: AsyncSession) -> None:
    await client.get("/api/v1/tinyurl/3/", follow_redirects=True)
    await client.get("/api/v1/tinyurl/3/", follow_redirects=True)
    response = await client.get("/api/v1/tinyurl/3/status",
                                params={"full-info": True})
    assert response.status_code == HTTPStatus.OK
    results = response.json()
    assert isinstance(results, list)
    for result in results:
        assert result.get("used_at")
        assert result.get("client_host")
        assert result.get("client_port")
