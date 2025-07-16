import hashlib
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import BinaryIO, Optional, Tuple

from fastapi import UploadFile, HTTPException, status

from app.config.settings import settings
from app.core.security import get_password_hash


def save_upload_file(upload_file: UploadFile, destination: Path) -> Path:
    """
    Save an uploaded file to the specified destination.
    
    Args:
        upload_file: The uploaded file
        destination: The destination path
        
    Returns:
        Path: Path to the saved file
        
    Raises:
        HTTPException: If file size exceeds limit or other IO error occurs
    """
    try:
        # Ensure directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        # Check file size
        file_size = 0
        with destination.open("wb") as buffer:
            while True:
                chunk = upload_file.file.read(8192)  # 8KB chunks
                if not chunk:
                    break
                file_size += len(chunk)
                if file_size > settings.MAX_UPLOAD_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File size exceeds {settings.MAX_UPLOAD_SIZE} bytes"
                    )
                buffer.write(chunk)
        
        return destination
    except Exception as e:
        if destination.exists():
            destination.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving file: {str(e)}"
        )

def extract_zip(zip_path: Path, extract_to: Path) -> Path:
    """
    Extract a zip file to the specified directory.
    
    Args:
        zip_path: Path to the zip file
        extract_to: Directory to extract to
        
    Returns:
        Path: Path to the extracted directory
        
    Raises:
        ValueError: If the file is not a valid zip file
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Create a safe extraction directory
            extract_to.mkdir(parents=True, exist_ok=True)
            zip_ref.extractall(extract_to)
            return extract_to
    except zipfile.BadZipFile as e:
        raise ValueError(f"Invalid zip file: {e}")

def create_temp_dir(prefix: str = "pyconnect_") -> Path:
    """
    Create a temporary directory with the given prefix.
    
    Args:
        prefix: Directory name prefix
        
    Returns:
        Path: Path to the created directory
    """
    temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
    return temp_dir

def validate_zip_contains_file(zip_path: Path, required_file: str) -> bool:
    """
    Check if a zip file contains a specific file.
    
    Args:
        zip_path: Path to the zip file
        required_file: Name of the file to check for
        
    Returns:
        bool: True if the file exists in the zip, False otherwise
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            return any(name == required_file for name in zip_ref.namelist())
    except zipfile.BadZipFile:
        return False

def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate the hash of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        str: Hexadecimal digest of the file hash
    """
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def cleanup_directory(directory: Path) -> None:
    """
    Recursively remove a directory and its contents.
    
    Args:
        directory: Directory to remove
    """
    if directory.exists() and directory.is_dir():
        shutil.rmtree(directory)

def get_file_mime_type(file_path: Path) -> str:
    """
    Get the MIME type of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: MIME type of the file
    """
    import mimetypes
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"
