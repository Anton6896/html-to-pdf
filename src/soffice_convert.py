import asyncio
import base64
import logging
import os
import shutil
import tempfile
import uuid
from typing import Annotated

from fastapi import APIRouter
from fastapi import Header
from fastapi import Request

from src.config import settings
from src.metrics import FILE_SIZE_HISTOGRAM
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
    request_id = x_cellosign_request_id or str(uuid.uuid4())
    logger.info('start job [%s]', request_id, extra={'request_id': request_id})
    output_dir = None

    try:
        output_dir = tempfile.mkdtemp(prefix=f'{x_cellosign_request_id}-')
        incoming_file_name = os.path.join(output_dir, f'incoming.{body.document_type}')
        convert_to = 'pdf' if body.document_type == 'docx' else 'html'
        doc_in_bytes = base64.b64decode(body.document)
        FILE_SIZE_HISTOGRAM.labels('bytes').observe(len(doc_in_bytes))

        with open(incoming_file_name, 'wb') as f:
            f.write(doc_in_bytes)

        logger.info(
            '[%s] saved document to tmp folder %s',
            request_id,
            incoming_file_name,
            extra={'request_id': request_id},
        )

        command = [
            'soffice',
            '--headless',
            '--convert-to',
            convert_to,
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

        if body.document_type == 'docx':
            converted_file = incoming_file_name.replace('.docx', '.pdf')

        elif body.document_type == 'xlsx':
            converted_file = incoming_file_name.replace('.xlsx', '.html')

        else:
            return FileConvertResponse(document=None, error=f'{body.document_type}, can not be handled')

        with open(converted_file, 'rb') as f:
            converted_data = f.read()

        return FileConvertResponse(document=base64.b64encode(converted_data).decode())

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
