import os

import pytest


@pytest.fixture
def data_dir():
    dirname = os.path.dirname(__file__)
    return os.path.join(dirname, 'data')
