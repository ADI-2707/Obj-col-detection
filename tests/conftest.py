import pytest

from mill_motion.config import Config


@pytest.fixture
def default_config():
    return Config()
