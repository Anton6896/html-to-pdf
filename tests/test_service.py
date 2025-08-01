import os
import base64
import pytest

pytest_plugins = ('pytest_asyncio',)
LEGACY_SOFFICE_CONVERT_URL = 'http://localhost:8000/api/convert/'
NEW_SOFFICE_CONVERT_URL = 'http://localhost:8000/api/v1/convert_data/'


@pytest.mark.asyncio()
async def test_create_pdf(data_dir, client):
    with open(os.path.join(data_dir, '1-page.docx'), 'rb') as f:
        files = {'file': ('1-page.docx', f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}

        response = client.post(
            LEGACY_SOFFICE_CONVERT_URL, files=files, headers={'X-CELLOSIGN-REQUEST-ID': 'test-request-id-001'}
        )

        assert response.status_code == 200
        assert 'pdf' in str(response.content)


@pytest.mark.asyncio()
async def test_create_html(data_dir, client):
    # dc exec soffice-worker pytest /tests/test_service.py::test_create_html
    with open(os.path.join(data_dir, 'testing.xlsx'), 'rb') as f:
        files = {'file': ('testing.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}

        response = client.post(
            LEGACY_SOFFICE_CONVERT_URL + 'xhtml/', files=files, headers={'X-CELLOSIGN-REQUEST-ID': 'test-request-id-002'}
        )

        assert response.status_code == 200
        assert 'DOCTYPE html' in str(response.content)


@pytest.mark.asyncio()
async def test_create_new_pdf(data_dir, client):
    # dc exec soffice-worker pytest /tests/test_service.py::test_create_new_pdf
    with open(os.path.join(data_dir, '1-page.docx'), 'rb') as f:
        payload = {'document': base64.b64encode(f.read()).decode(), 'document_type': 'docx'}

    response = client.post(
            NEW_SOFFICE_CONVERT_URL, 
            headers={
                'X-CELLOSIGN-REQUEST-ID': 'test-request-id-003',
                'Content-Type': 'application/json'
            },
            json=payload
    )

    data = response.json()

    assert data.get('document')
    assert not data.get('error')
