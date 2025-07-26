from typing import Literal

from pydantic import BaseModel


class FileConvertRequest(BaseModel):
    document: str
    document_type: Literal["docx", "xlsx"]


class FileConvertResponse(BaseModel):
    document: str | None = None
    error: str | None = None
