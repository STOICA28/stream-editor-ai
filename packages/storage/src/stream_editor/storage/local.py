import os
from pathlib import Path
from typing import List
from .provider import StorageProvider

class LocalStorageProvider(StorageProvider):
    def __init__(self, base_path: Path | None = None):
        if base_path is None:
            self.base_path = Path(os.environ.get("DATA_DIR", "./data"))
        else:
            self.base_path = Path(base_path)

    async def store(self, project_id: str, category: str, filename: str, data: bytes) -> str:
        path = await self.get_path(project_id, category, filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
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

    async def list_category(self, project_id: str, category: str) -> List[str]:
        dir_path = self.base_path / "projects" / project_id / category
        if not dir_path.exists() or not dir_path.is_dir():
            return []
        return [f.name for f in dir_path.iterdir() if f.is_file()]

    async def copy_in(self, source_file_path: str, project_id: str, category: str, filename: str) -> str:
        path = await self.get_path(project_id, category, filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        import shutil
        shutil.copy2(source_file_path, path)
        return f"{project_id}/{category}/{filename}"
