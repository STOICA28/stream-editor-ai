import hashlib
import os

FINGERPRINT_VERSION = "2.0.0"
SAMPLE_SIZE = 1024 * 1024  # 1 MB

def generate_fingerprint(path: str) -> str:
    stat_result = os.stat(path)
    file_size = stat_result.st_size
    
    sha256 = hashlib.sha256()
    sha256.update(f"v={FINGERPRINT_VERSION};size={file_size}".encode())
    
    if file_size <= SAMPLE_SIZE * 3:
        with open(path, 'rb') as f:
            while chunk := f.read(SAMPLE_SIZE):
                sha256.update(chunk)
    else:
        with open(path, 'rb') as f:
            # Beginning
            f.seek(0)
            sha256.update(f.read(SAMPLE_SIZE))
            # Middle
            f.seek(file_size // 2)
            sha256.update(f.read(SAMPLE_SIZE))
            # End
            f.seek(file_size - SAMPLE_SIZE)
            sha256.update(f.read(SAMPLE_SIZE))
            
    return sha256.hexdigest()
