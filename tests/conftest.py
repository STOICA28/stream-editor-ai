"""Test conftest.py - M3 compatible."""
import tempfile
from pathlib import Path

import pytest

from stream_editor.editorial.providers.mock import MockEditorialProvider


@pytest.fixture
def tmp_storage():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


@pytest.fixture
def mock_editorial_provider():
    return MockEditorialProvider()

import sys
from unittest.mock import MagicMock
sys.modules['torch'] = MagicMock()
