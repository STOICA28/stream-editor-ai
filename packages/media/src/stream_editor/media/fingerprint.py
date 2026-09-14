import hashlib
import os

def generate_fingerprint(path: str) -> str:
    stat_result = os.stat(path)
    file_size = stat_result.st_size
    mtime = stat_result.st_mtime
    
    sha256 = hashlib.sha256()
    with open(path, 'rb') as f:
        chunk = f.read(1024 * 1024)
        sha256.update(chunk)
    
    first_mb_hash = sha256.hexdigest()
    
    return f"{file_size}_{mtime}_{first_mb_hash}"
