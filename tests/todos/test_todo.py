from typing import Any
import pytest
from app.schemas.core import PagingMeta
from app.schemas.todo import TodoCreate, TodoUpdate
from httpx import AsyncClient
from starlette import status
from tests.base import assert_create, assert_get_by_id, assert_get_paged_list, assert_update