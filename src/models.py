from pydantic import BaseModel


class FileConvertRequest(BaseModel):
    document: str
    document_type: str


class FileConvertResponse(BaseModel):
    document: str | None = None
    error: str | None = None
