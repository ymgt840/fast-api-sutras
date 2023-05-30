from typing import Any
from urllib.request import Request
from fastapi.response import PlainTextResponse
from app.core.logger import get_logger
logger = get_logger(__name__)

async def http_exception_handler(req: Request, exc: Any) -> PlainTextResponse:
    """HTTPリクエストに起因したExceptionエラー発生時のフック処理を定義する"""
    logger.exception(str(exc))
    return PlainTextResponse("Server Error: " + str(exc), status_code=500)