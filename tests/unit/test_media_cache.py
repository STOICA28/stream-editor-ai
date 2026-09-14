import pytest
import shutil
import os
from pathlib import Path
from stream_editor.contracts.media import ProxyConfig, AudioConfig, MediaInfo
from stream_editor.media.validation import validate_proxy

@pytest.fixture
def temp_dir(tmp_path):
    # Setup temp dir
    d = tmp_path / "cache_test"
    d.mkdir()
    yield d
    shutil.rmtree(d, ignore_errors=True)

def test_proxy_config_signature():
    config1 = ProxyConfig(max_height=720, crf=28)
    config2 = ProxyConfig(max_height=720, crf=28)
    config3 = ProxyConfig(max_height=360, crf=28)
    
    fp = "fake_fingerprint_123"
    
    assert config1.get_signature(fp) == config2.get_signature(fp)
    assert config1.get_signature(fp) != config3.get_signature(fp)

def test_validation_rejects_corrupt_file(temp_dir):
    config = ProxyConfig(max_height=720)
    source_info = MediaInfo(
        width=1920, height=1080, duration=30.0, fps=30.0, has_audio=True,
        duration_seconds=30.0, video_codec="h264", audio_codec="aac",
        file_size_bytes=1000, format_name="mp4", bit_rate=1000
    )
    
    corrupt_file = temp_dir / "corrupt.mp4"
    corrupt_file.write_text("not a real video file")
    
    with pytest.raises(Exception):
        validate_proxy(str(corrupt_file), source_info, config)

