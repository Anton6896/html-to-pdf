import asyncio
import logging
import os
import shutil
import tempfile
import uuid

# import magic
from fastapi import APIRouter
from fastapi import File
from fastapi import Header
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi.responses import Response

from src.config import settings
from src.metrics import FILE_SIZE_HISTOGRAM

router = APIRouter(prefix=settings.LEGACY_API_PREFIX)

logger = logging.getLogger('app')

CONFORMANCE_PDF = 'pdf'
CONFORMANCE_PDFA = 'pdf/a'


@router.post('/xhtml')
@router.post('/xhtml/')
async def xhtml_file(
    file: UploadFile,
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
            doc_in_bytes = f.read()

        FILE_SIZE_HISTOGRAM.labels('bytes').observe(len(doc_in_bytes))
        return Response(doc_in_bytes)

    except Exception as e:  # noqa
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


@router.post('/')
async def post(
    file: UploadFile,
    conformance: str | None = None,
    x_cellosign_request_id: str | None = Header(None),
):
    import magic

    request_id = x_cellosign_request_id or str(uuid.uuid4())
    extra = {'request_id': request_id}
    output_dir = None
    conformance = conformance or CONFORMANCE_PDF
    logger.info('%s: starting conversion, conformance = %s', request_id, conformance, extra=extra)

    try:
        output_dir = tempfile.mkdtemp(prefix=f'{x_cellosign_request_id}-')
        incoming_file_name = os.path.join(output_dir, 'incoming.html')

        with open(incoming_file_name, 'wb') as f:
            f.write(file.file.read())

        command = [
            'soffice',
            '--headless',
            '--convert-to',
            'pdf',
            incoming_file_name,
        ]

        if conformance == CONFORMANCE_PDFA:
            command.append('-eSelectedPdfVersion=1')
            command.append('-eUseTaggedPDF=1')

        command.append('--outdir')
        command.append(output_dir)

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

        converted_file = incoming_file_name.replace('.html', '.pdf')

        with open(converted_file, 'rb') as f:
            doc_in_bytes = f.read()
        
        type_of_data = magic.from_buffer(doc_in_bytes, mime=True)
        logger.info('%s: type_of_data: %s', request_id, type_of_data, extra=extra)

        if type_of_data != 'application/pdf':
            raise Exception(f'{request_id}: issue while generating pdf')

        FILE_SIZE_HISTOGRAM.labels('bytes').observe(len(doc_in_bytes))
        return Response(doc_in_bytes)

    except Exception as e:  # noqa
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
