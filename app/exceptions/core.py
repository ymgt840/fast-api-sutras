from typing import Any
from fastapi import HTTPException, status

class APIException(HTTPException):
    """ APIException を定義する """
    def __init__(
        self,
        error: Any,
        status_code: int = default_status_code,
        headers: dict[str, Any] | None = None,
    ) -> None:
        self.headers = headers
        try:
            error_obj = error()
        except Exception:
            error_obj = error

        try:
            message = error_obj.text_format(error_obj.param)
        except Exception:
            message = error_obj.text

        try:
            self.status_code = error_obj.status_code
        except Exception:
            self.status_code = status_code

        self.detail = {"error_code": str(error_obj), "error_msg": message}
        print(self.detail)
        super().__init__(self.status_code, self.detail)