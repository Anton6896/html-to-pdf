import asyncio
import base64
import logging
import os
import shutil
import tempfile
import uuid
from typing import Annotated

# import magic
from fastapi import APIRouter
from fastapi import File
from fastapi import Header
from fastapi import HTTPException
from fastapi import Request
from fastapi import UploadFile
from fastapi.responses import Response

from src.config import settings
from src.metrics import FILE_SIZE_HISTOGRAM
from src.models import FileConvertRequest
from src.models import FileConvertResponse

router = APIRouter(prefix=settings.LEGACY_API_PREFIX)

logger = logging.getLogger('app')


@router.post('/xhtml')
@router.post('/xhtml/')
async def xhtml_file(
    file: UploadFile = File(...),
    x_cellosign_request_id: str | None = Header(None),
):
    request_id = x_cellosign_request_id or str(uuid.uuid4())
    extra = {'request_id': request_id}
    logger.info('%s: starting conversion for xlsx -> xhtml', request_id, extra=extra)
    output_dir = None

    try:
        output_dir = tempfile.mkdtemp(prefix=f'{x_cellosign_request_id}-')
        incoming_file_name = os.path.join(output_dir, 'incoming.xlsx')

        with open(incoming_file_name, 'wb') as f:
            f.write(file.file.read())

        command = [
            'soffice',
            '--headless',
            '--convert-to',
            'html',
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

        converted_file = incoming_file_name.replace('.xlsx', '.html')

        with open(converted_file, 'rb') as f:
            converted_data = f.read()

        return Response(converted_data)

    except Exception as e:
        logger.exception('%s unexpected exception', request_id, extra=extra)
        raise HTTPException(status_code=422, detail=str(e)) from e

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
