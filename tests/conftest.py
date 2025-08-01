import os

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def data_dir():
    dirname = os.path.dirname(__file__)
    return os.path.join(dirname, 'data')


@pytest.fixture()
def client():
    return TestClient(app)
