# src/api/middleware/file_validation.py

from fastapi import HTTPException, status, UploadFile
from pathlib import Path
import os

MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_FILE_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

class FileValidator:
    @staticmethod
    def validate_file_type(filename: str) -> bool:
        if not filename:
            return False
        file_ext = Path(filename).suffix.lower()
        return file_ext in ALLOWED_FILE_EXTENSIONS

    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        return file_size <= MAX_UPLOAD_SIZE_BYTES

    @staticmethod
    def get_file_extension(filename: str) -> str:
        return Path(filename).suffix.lower()

def validate_uploaded_file(file: UploadFile) -> None:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )

    if not FileValidator.validate_file_type(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed: {', '.join(ALLOWED_FILE_EXTENSIONS)}"
        )
