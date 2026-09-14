import pytest
from pathlib import Path
from stream_editor.media.probe import validate_video_path

def test_validate_video_path_not_exists():
    with pytest.raises(FileNotFoundError):
        validate_video_path(Path("non_existent.mp4"))
