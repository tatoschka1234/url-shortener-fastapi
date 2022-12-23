import random
import string

from fastapi import status
from httpx import AsyncClient
from http import HTTPStatus
from sqlalchemy.ext.asyncio import AsyncSession
from src.main import app


async def test_create_short_url(client: AsyncClient,
                                async_session: AsyncSession) -> None:
    url = ''.join(random.choices(string.ascii_lowercase, k=5))
    response = await client.post(
        app.url_path_for("create_short_url"),
        json={'original_url': f'http://{url}.com'}
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert 'short_url' in response.json()


async def test_create_several_urls(client: AsyncClient,
                                async_session: AsyncSession) -> None:
    url1 = f'{client.base_url}{app.url_path_for("info_handler")}'
    url2 = f'{client.base_url}{app.url_path_for("check_db_status")}'
    response = await client.post(
        app.url_path_for("create_short_urls"),
        json=[
            {'original_url': url1},
            {'original_url': url2},
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


async def test_create_duplicate(client: AsyncClient,
                                async_session: AsyncSession) -> None:
    url = f'{client.base_url}{app.url_path_for("info_handler")}'
    response = await client.post(
        app.url_path_for("create_short_url"),
        json={'original_url': url}
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert "duplicate key" in response.text


async def test_get_all(client: AsyncClient,
                       async_session: AsyncSession) -> None:
    response = await client.get(app.url_path_for("read_entities"),)
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    assert len(results) > 2


async def test_get_by_url(client: AsyncClient,
                          async_session: AsyncSession) -> None:
    response = await client.get(app.url_path_for("get_url", url_id=2))
    expected_url = f'{client.base_url}{app.url_path_for("info_handler")}'
    assert response.status_code == HTTPStatus.TEMPORARY_REDIRECT
    assert expected_url in response.headers.get('Location')


async def test_mark_deleted(client: AsyncClient,
                            async_session: AsyncSession) -> None:
    await client.delete(app.url_path_for("delete_url"), params={"url_id": 2})
    response = await client.get(app.url_path_for("get_url", url_id=2),
                                follow_redirects=True)
    assert response.status_code == HTTPStatus.GONE
    result = response.json()
    assert "marked as deleted" in result.get("detail")


async def test_get_status(client: AsyncClient,
                          async_session: AsyncSession) -> None:
    await client.get(app.url_path_for("get_url", url_id=3),
                     follow_redirects=True)
    await client.get(app.url_path_for("get_url", url_id=3),
                     follow_redirects=True)
    response = await client.get(app.url_path_for("get_url_usage_status",
                                                 short_url_id=3),
                                params={"full-info": True})
    assert response.status_code == HTTPStatus.OK
    results = response.json()
    assert isinstance(results, list)
    for result in results:
        assert result.get("used_at")
        assert result.get("client_host")
        assert result.get("client_port")
