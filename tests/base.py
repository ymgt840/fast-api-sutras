from typing import Any
from httpx import AsyncClient
from starlette import status
from tests.testing_utils import assert_dict_part

async def assert_create(
    uri: str,
    client: AsyncClient,
    data_in: dict[str, Any],
    expected_status: int,
    expected_data: dict[str, Any] | None,
):
    """新規作成実行後、成功した場合は、生成されたデータの整合性をテストする"""
    res = await client.post(uri, json=data_in)
    assert res.status_code == expected_status

    if expected_status == status.status.HTTP_200_OK:
        res_data = res.json()
        assert_dict_part(res_data, expected_data)

async def assert_update(
    uri: str,
    client: AsyncClient,
    id: str,
    data_in: dict[str, Any],
    expected_status: int,
    expected_data: dict[str, Any] | None,
):
    """更新実行後、成功した場合は、更新されたデータの整合性をテストする"""
    res = await client.patch(f"{uri}/{id}", json=data_in)
    assert res.status_code == expected_status

    if expected_status == status.HTTP_200_OK:
        res_data = res.json()
        assert_dict_part(res_data, expected_data)

async def assert_get_by_id(
    uri: str,
    client: AsyncClient,
    id: str,
    expected_status: int,
    expected_data: dict[str, Any] | None,
):
    res = await client.get(f"{uri}/{id}")
    assert res.status_code == expected_status

    if expected_status == status.HTTP_200_OK:
        res_data = res.json()
        assert_dict_part(res_data, expected_data)

async def assert_get_paged_list(
    uri: str,
    client: AsyncClient,
    params: dict[str, Any],
    expected_status: int,
    expected_first_data: dict[str, Any],
    expected_paging_data: dict[str, Any],
):
    res = await client.get(uri, params=params)
    assert res.status_code == expected_status

    if expected_status == status.HTTP_200_OK:
        res_data = res.json()
        assert res_data["data"] is not None
        assert_dict_part(res_data["data"][0], expected_first_data)
        assert_dict_part(res_data["meta"], expected_paging_data)
