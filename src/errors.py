import logging

from fastapi import HTTPException

logger = logging.getLogger(__name__)


class CustomHTTPException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)
