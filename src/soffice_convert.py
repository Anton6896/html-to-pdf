import asyncio
import base64
import logging
import tempfile
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
    request: Request,
    body: FileConvertRequest,
    x_cellosign_request_id: Annotated[str | None, Header()] = None,
):
    import os

    request_id = x_cellosign_request_id or str(uuid.uuid4())
    logger.info('[%s] got check_file request', request_id, extra={'request_id': request_id})
    file_ = None
    output_dir = None
    try:
        document_bytes = base64.b64decode(body.document)
        suffix = f'.{body.document_type}'
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp_file.write(document_bytes)
        tmp_file.flush()
        file_ = tmp_file.name

        logger.info('[%s] saved document to temporary file %s', request_id, file_, extra={'request_id': request_id})

        output_dir = tempfile.mkdtemp(prefix=x_cellosign_request_id)

        if body.document_type == 'docx':
            command = [
                'soffice',
                '--headless',
                '--convert-to',
                'pdf',
                file_,
                '--outdir',
                output_dir,
            ]

            logger.info('running command %s', ' '.join(command))

            process = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()
            logger.info(stdout)

            if process.returncode != 0:
                raise Exception(f'Conversion failed: {stderr.decode()}')

            converted_file = os.path.join(output_dir, os.path.basename(file_).replace('.docx', '.pdf'))

            with open(converted_file, 'rb') as f:
                converted_data = f.read()

            return FileConvertResponse(document=base64.b64encode(converted_data).decode())

        elif body.document_type == 'xlsx':
            pass

        else:
            return FileConvertResponse(document=None, error=f'{body.document_type}, can not be handled')

        """
        1. get file from request 
        2. save localy as tmp file 
            - check file type xlsx | docx 
            - save as tmp file

        3. send file to convertion with 
        soffice --headless --convert-to pdf 1-page.docx --outdir /data && cat /data/myfile.pdf
        soffice --headless --convert-to html your_file.xlsx --outdir /your/output/dir
        4. read the converted file
        5. send return it to client
        """

        return FileConvertResponse(document='some document data')

    except Exception as e:  # noqa
        logger.exception('%s unexpected', request_id, extra={'request_id': request_id})
        return FileConvertResponse(document=None, error=str(e))

    finally:
        import os

        if file_:
            try:
                os.remove(file_)
                logger.info('[%s] removed temporary file %s', request_id, file_, extra={'request_id': request_id})
            except Exception as cleanup_error:
                logger.warning(
                    '[%s] failed to remove temporary file %s: %s',
                    request_id,
                    file_,
                    cleanup_error,
                    extra={'request_id': request_id},
                )
        if output_dir and os.path.isdir(output_dir):
            try:
                for f in os.listdir(output_dir):
                    os.remove(os.path.join(output_dir, f))
                os.rmdir(output_dir)
                logger.info(
                    '[%s] removed temporary output directory %s',
                    request_id,
                    output_dir,
                    extra={'request_id': request_id},
                )
            except Exception as cleanup_error:
                logger.warning(
                    '[%s] failed to remove output directory %s: %s',
                    request_id,
                    output_dir,
                    cleanup_error,
                    extra={'request_id': request_id},
                )


"""

curl -L -m 120 "http://localhost:8022/api/v1/convert_data/" -H "Content-Type: application/json" -d "{
    \"document\": \"13213123\",
    \"document_type\": \"docx\"
}" | jq .
"""
