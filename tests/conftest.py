import pytest

from vision.config import Config


@pytest.fixture
def default_config():
    return Config()
