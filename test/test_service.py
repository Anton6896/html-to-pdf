import os

import magic
import requests

"""

"""

SOFFICE_CONVERT_URL = 'http://localhost:8000/api/convert/'


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
