import os

import pytest

pytest_plugins = ('pytest_asyncio',)
SOFFICE_CONVERT_URL = 'http://localhost:8022/api/convert/'


@pytest.mark.asyncio()
async def test_create_pdf(data_dir, client):
    with open(os.path.join(data_dir, '1-page.docx'), 'rb') as f:
        files = {'file': ('1-page.docx', f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}

        response = client.post(
            SOFFICE_CONVERT_URL, files=files, headers={'X-CELLOSIGN-REQUEST-ID': 'test-request-id-001'}
        )

        assert response.status_code == 200
        assert 'pdf' in str(response.content)


@pytest.mark.asyncio()
async def test_create_html(data_dir, client):
    # dc exec soffice-worker pytest /tests/test_service.py::test_create_html
    with open(os.path.join(data_dir, 'testing.xlsx'), 'rb') as f:
        files = {'file': ('testing.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}

        response = client.post(
            SOFFICE_CONVERT_URL + 'xhtml/', files=files, headers={'X-CELLOSIGN-REQUEST-ID': 'test-request-id-002'}
        )

        assert response.status_code == 200
        assert 'DOCTYPE html' in str(response.content)
