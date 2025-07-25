import logging
import uuid
from typing import Annotated

from fastapi import APIRouter
from fastapi import Header
from fastapi import Request

from src.config import settings
from src.models import FileConvertRequest
from src.models import FileConvertResponse

router = APIRouter(prefix=settings.API_PREFIX)

logger = logging.getLogger('app')


@router.post('/convert_data/', response_model=FileConvertResponse)
async def send(
    request: Request, body: FileConvertRequest, x_cellosign_request_id: Annotated[str | None, Header()] = None
):
    request_id = x_cellosign_request_id or str(uuid.uuid4())
    logger.info('[%s] got check_file request', request_id, extra={'request_id': request_id})
    try:
        return FileConvertResponse(document='some document data')
    
        """
        1. get file from request 
        2. save localy as tmp file 
        3. send file to convertion with 
        sh -c "soffice --headless --convert-to pdf 1-page.docx --outdir /data && cat /data/myfile.pdf
        4. read the converted file
        5. send return it to client
        """

    except Exception as e:  # noqa
        logger.exception('%s unexpected', request_id, extra={'request_id': request_id})
        return FileConvertResponse(document=None, error=str(e))


"""

curl -L -m 120 "http://localhost:8022/api/v1/convert_data/" -H "Content-Type: application/json" -d "{
    \"document\": \"13213123\",
    \"document_type\": \"docx\"
}" | jq .
"""