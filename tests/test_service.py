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
        assert response.headers['content-type'] == 'application/pdf'


"""

def test_xlsx_file(data_dir):
    # pytest -vv /tests/test_service.py::test_xlsx_file
    print('*' * 100)
    xml_path = os.path.join(data_dir, 'text_table_data_1.xlsx')
    expected_path = os.path.join(data_dir, 'expected', 'output.html')

    with open(xml_path, 'rb') as f:
        data = f.read()

    with open(expected_path, 'rb') as f:
        expected_html = f.read()

    url = f'{SOFFICE_CONVERT_URL}xhtml'

    headers = {
        'X-CELLOSIGN-REQUEST-ID': 'request-id-123123',
    }

    res = requests.request('POST', url, files={'file': data}, headers=headers)
    assert res.status_code == 200

    assert expected_html == res.content


def test_docx_file_to_pdf(data_dir):
    # pytest -vv /tests/test_service.py::test_docx_file_to_pdf
    print('*' * 100)
    docx_path = os.path.join(data_dir, 'zap.docx')

    with open(docx_path, 'rb') as f:
        data = f.read()

    headers = {
        'X-CELLOSIGN-REQUEST-ID': 'request-id-123123',
    }

    res = requests.request('POST', SOFFICE_CONVERT_URL, files={'file': data}, headers=headers)
    assert res.status_code == 200

    type_of_data = magic.from_buffer(res.content, mime=True)
    assert type_of_data == 'application/pdf'


"""
