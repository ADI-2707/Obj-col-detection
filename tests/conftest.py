import pytest

from orbix.config import Config


@pytest.fixture
def default_config():
    return Config()
