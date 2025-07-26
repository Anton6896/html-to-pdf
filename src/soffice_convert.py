import asyncio
import base64
import logging
import shutil
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


import os


@router.post('/convert_data/', response_model=FileConvertResponse)
async def send(
    request: Request,
    body: FileConvertRequest,
    x_cellosign_request_id: Annotated[str | None, Header()] = None,
):
    request_id = x_cellosign_request_id or str(uuid.uuid4())
    logger.info('start job [%s]', request_id, extra={'request_id': request_id})
    output_dir = None

    try:
        output_dir = tempfile.mkdtemp(prefix=f'{x_cellosign_request_id}-')
        incoming_file_name = os.path.join(output_dir, f'incoming.{body.document_type}')

        with open(incoming_file_name, 'wb') as f:
            f.write(base64.b64decode(body.document))

        logger.info(
            '[%s] saved document to tmp folder %s',
            request_id,
            incoming_file_name,
            extra={'request_id': request_id},
        )

        if body.document_type == 'docx':
            command = [
                'soffice',
                '--headless',
                '--convert-to',
                'pdf',
                incoming_file_name,
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
            logger.info('stdout: %s', str(stdout.decode()))

            if process.returncode != 0:
                raise Exception(f'Conversion failed: {stderr.decode()}')

            converted_file = incoming_file_name.replace('.docx', '.pdf')

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
        if output_dir and os.path.isdir(output_dir):
            try:
                shutil.rmtree(output_dir)
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
