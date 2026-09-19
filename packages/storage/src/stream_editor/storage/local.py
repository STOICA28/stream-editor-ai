import os
import shutil
from pathlib import Path
from .provider import StorageProvider

class LocalStorageProvider(StorageProvider):
    def __init__(self, base_path: Path | None = None):
        if base_path is None:
            self.base_path = Path(os.environ.get("DATA_DIR", "./data"))
        else:
            self.base_path = Path(base_path)

    def _check_disk_space(self, required_bytes: int) -> None:
        total, used, free = shutil.disk_usage(self.base_path)
        # Require at least 5GB free or the required bytes + 2GB buffer
        if free < required_bytes + 2 * 1024 * 1024 * 1024:
            raise IOError(f"Insufficient disk space. Needed {required_bytes}, free {free}.")

    async def store(self, project_id: str, category: str, filename: str, data: bytes) -> str:
        self._check_disk_space(len(data))
        path = await self.get_path(project_id, category, filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        partial_path = path.with_suffix(path.suffix + ".partial")
        partial_path.write_bytes(data)
        partial_path.rename(path)
        
        return f"{project_id}/{category}/{filename}"

    async def retrieve(self, path: str) -> bytes:
        full_path = self.base_path / "projects" / path
        return full_path.read_bytes()

    async def get_path(self, project_id: str, category: str, filename: str) -> Path:
        path = self.base_path / "projects" / project_id / category / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    async def exists(self, path: str) -> bool:
        full_path = self.base_path / "projects" / path
        return full_path.exists()

    async def delete(self, path: str) -> None:
        full_path = self.base_path / "projects" / path
        if full_path.exists():
            full_path.unlink()

    async def list_category(self, project_id: str, category: str) -> list[str]:
        dir_path = self.base_path / "projects" / project_id / category
        if not dir_path.exists() or not dir_path.is_dir():
            return []
        return [f.name for f in dir_path.iterdir() if f.is_file()]

    async def copy_in(self, source_file_path: str, project_id: str, category: str, filename: str) -> str:
        source_size = Path(source_file_path).stat().st_size
        self._check_disk_space(source_size)
        
        path = await self.get_path(project_id, category, filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        partial_path = path.with_suffix(path.suffix + ".partial")
        shutil.copy2(source_file_path, partial_path)
        partial_path.rename(path)
        
        return f"{project_id}/{category}/{filename}"

