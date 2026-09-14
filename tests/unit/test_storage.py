
import pytest

from stream_editor.storage.local import LocalStorageProvider


@pytest.mark.asyncio
async def test_storage_provider(tmp_storage):
    provider = LocalStorageProvider(base_path=tmp_storage)
    path = await provider.store("proj_1", "source", "test.txt", b"hello")
    assert path == "proj_1/source/test.txt"
    data = await provider.retrieve(path)
    assert data == b"hello"
    exists = await provider.exists(path)
    assert exists is True
    await provider.delete(path)
    assert await provider.exists(path) is False
