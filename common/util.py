import hashlib
import zlib

import hashlib

def sha256_file_checksum(file_path: str, offset: int = 0, length: int = -1) -> bytes:
    with open(file_path, "r+b") as file:
        sha256_hash = hashlib.sha256()
        file.seek(offset)
        
        if length == -1:
            # Read the entire file from the offset
            while chunk := file.read(4096):
                sha256_hash.update(chunk)
        else:
            # Read only up to offset + length
            remaining_bytes = length
            while remaining_bytes > 0:
                chunk_size = min(4096, remaining_bytes)
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                sha256_hash.update(chunk)
                remaining_bytes -= len(chunk)
        
        return sha256_hash.digest()

def crc32_file_checksum(file_path: str, offset: int = 0, length: int = 0) -> int:
    with open(file_path, "r+b") as file:
        crc32_hash = zlib.crc32(b"")
        file.seek(offset)
        if length == -1:
            # Read the entire file from the offset
            while chunk := file.read(4096):
                crc32_hash = zlib.crc32(chunk, crc32_hash)
        else:
            # Read only up to offset + length
            remaining_bytes = length
            while remaining_bytes > 0:
                chunk_size = min(4096*8, remaining_bytes)
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                crc32_hash = zlib.crc32(chunk, crc32_hash)
                remaining_bytes -= len(chunk)
        
        return crc32_hash