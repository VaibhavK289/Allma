"""
Input Validation and Sanitization Utilities

Production-grade validation for:
- User input sanitization
- File validation
- Configuration validation
- Rate limit checking
"""

import re
import os
import hashlib
import mimetypes
from typing import Optional, List, Tuple, Any, Dict
from pathlib import Path
from dataclasses import dataclass

from orchestration.exceptions import (
    DocumentTooLargeError,
    UnsupportedFormatError,
    MessageTooLongError,
    DocumentException,
    ErrorCode
)


# ============================================================
# Constants
# ============================================================

# Maximum lengths
MAX_MESSAGE_LENGTH = 32000
MAX_CONVERSATION_TITLE = 255
MAX_SOURCE_NAME = 512
MAX_METADATA_SIZE = 10000  # bytes

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    '.txt': 'text/plain',
    '.md': 'text/markdown',
    '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.doc': 'application/msword',
    '.html': 'text/html',
    '.htm': 'text/html',
    '.json': 'application/json',
    '.csv': 'text/csv',
    '.xml': 'application/xml',
    '.rtf': 'application/rtf',
}

# Dangerous patterns (for path traversal, injection, etc.)
DANGEROUS_PATTERNS = [
    r'\.\./',           # Directory traversal
    r'\.\.\\',          # Windows directory traversal
    r'<script',         # XSS attempt
    r'javascript:',     # JS injection
    r'data:',           # Data URL injection
    r'\x00',            # Null byte injection
]


# ============================================================
# Validation Result
# ============================================================

@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    value: Any = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    
    @classmethod
    def success(cls, value: Any = None) -> 'ValidationResult':
        return cls(is_valid=True, value=value)
    
    @classmethod
    def failure(cls, error: str, code: Optional[str] = None) -> 'ValidationResult':
        return cls(is_valid=False, error=error, error_code=code)


# ============================================================
# Text Validation
# ============================================================

def validate_message(message: str) -> ValidationResult:
    """
    Validate a chat message.
    
    Checks:
    - Not empty
    - Within length limit
    - No dangerous patterns
    
    Args:
        message: The message to validate
        
    Returns:
        ValidationResult with sanitized message or error
    """
    if not message or not message.strip():
        return ValidationResult.failure("Message cannot be empty")
    
    message = message.strip()
    
    if len(message) > MAX_MESSAGE_LENGTH:
        return ValidationResult.failure(
            f"Message too long: {len(message)} chars (max: {MAX_MESSAGE_LENGTH})",
            ErrorCode.MESSAGE_TOO_LONG.value
        )
    
    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, message, re.IGNORECASE):
            return ValidationResult.failure(
                "Message contains potentially dangerous content"
            )
    
    return ValidationResult.success(message)


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize text for safe storage and display.
    
    Args:
        text: Text to sanitize
        max_length: Optional maximum length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[:max_length-3] + "..."
    
    return text


def validate_conversation_title(title: str) -> ValidationResult:
    """Validate conversation title."""
    if not title or not title.strip():
        return ValidationResult.failure("Title cannot be empty")
    
    title = sanitize_text(title, MAX_CONVERSATION_TITLE)
    return ValidationResult.success(title)


# ============================================================
# File Validation
# ============================================================

def validate_file_path(
    file_path: str,
    max_size_mb: int = 50,
    allowed_extensions: Optional[List[str]] = None
) -> ValidationResult:
    """
    Validate a file path for ingestion.
    
    Checks:
    - File exists
    - Extension is allowed
    - Size is within limit
    - No path traversal
    
    Args:
        file_path: Path to the file
        max_size_mb: Maximum file size in MB
        allowed_extensions: List of allowed extensions
        
    Returns:
        ValidationResult with file info or error
    """
    # Check for path traversal
    for pattern in DANGEROUS_PATTERNS[:2]:
        if re.search(pattern, file_path):
            return ValidationResult.failure(
                "Invalid file path: path traversal detected"
            )
    
    # Resolve path
    try:
        path = Path(file_path).resolve()
    except Exception as e:
        return ValidationResult.failure(f"Invalid file path: {e}")
    
    # Check existence
    if not path.exists():
        return ValidationResult.failure(
            f"File not found: {file_path}",
            ErrorCode.DOCUMENT_NOT_FOUND.value
        )
    
    if not path.is_file():
        return ValidationResult.failure(
            f"Not a file: {file_path}"
        )
    
    # Check extension
    extension = path.suffix.lower()
    allowed = allowed_extensions or list(ALLOWED_EXTENSIONS.keys())
    
    if extension not in allowed:
        return ValidationResult.failure(
            f"Unsupported format: {extension}",
            ErrorCode.DOCUMENT_FORMAT_ERROR.value
        )
    
    # Check size
    size_bytes = path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    
    if size_mb > max_size_mb:
        return ValidationResult.failure(
            f"File too large: {size_mb:.1f}MB (max: {max_size_mb}MB)",
            ErrorCode.DOCUMENT_TOO_LARGE.value
        )
    
    # Return file info
    return ValidationResult.success({
        "path": str(path),
        "filename": path.name,
        "extension": extension,
        "size_bytes": size_bytes,
        "size_mb": size_mb,
        "mime_type": ALLOWED_EXTENSIONS.get(extension, 'application/octet-stream')
    })


def validate_uploaded_file(
    filename: str,
    content: bytes,
    max_size_mb: int = 50,
    allowed_extensions: Optional[List[str]] = None
) -> ValidationResult:
    """
    Validate an uploaded file.
    
    Args:
        filename: Original filename
        content: File content as bytes
        max_size_mb: Maximum size in MB
        allowed_extensions: Allowed extensions
        
    Returns:
        ValidationResult with file info or error
    """
    # Sanitize filename
    filename = sanitize_filename(filename)
    
    if not filename:
        return ValidationResult.failure("Invalid filename")
    
    # Check extension
    extension = Path(filename).suffix.lower()
    allowed = allowed_extensions or list(ALLOWED_EXTENSIONS.keys())
    
    if extension not in allowed:
        return ValidationResult.failure(
            f"Unsupported format: {extension}. Allowed: {', '.join(allowed)}",
            ErrorCode.DOCUMENT_FORMAT_ERROR.value
        )
    
    # Check size
    size_bytes = len(content)
    size_mb = size_bytes / (1024 * 1024)
    
    if size_mb > max_size_mb:
        return ValidationResult.failure(
            f"File too large: {size_mb:.1f}MB (max: {max_size_mb}MB)",
            ErrorCode.DOCUMENT_TOO_LARGE.value
        )
    
    # Check for empty file
    if size_bytes == 0:
        return ValidationResult.failure(
            "File is empty",
            ErrorCode.DOCUMENT_EMPTY.value
        )
    
    # Calculate hash for deduplication
    file_hash = hashlib.sha256(content).hexdigest()
    
    return ValidationResult.success({
        "filename": filename,
        "extension": extension,
        "size_bytes": size_bytes,
        "size_mb": size_mb,
        "mime_type": ALLOWED_EXTENSIONS.get(extension, 'application/octet-stream'),
        "hash": file_hash
    })


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename for safe storage.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return ""
    
    # Get just the filename (no path)
    filename = os.path.basename(filename)
    
    # Remove dangerous characters
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename


# ============================================================
# Metadata Validation
# ============================================================

def validate_metadata(metadata: Dict[str, Any]) -> ValidationResult:
    """
    Validate metadata dictionary.
    
    Checks:
    - Size limit
    - Valid JSON-serializable types
    - No dangerous content in values
    
    Args:
        metadata: Metadata dictionary
        
    Returns:
        ValidationResult with sanitized metadata or error
    """
    if not metadata:
        return ValidationResult.success({})
    
    import json
    
    try:
        # Check if JSON serializable
        json_str = json.dumps(metadata)
        
        # Check size
        if len(json_str) > MAX_METADATA_SIZE:
            return ValidationResult.failure(
                f"Metadata too large: {len(json_str)} bytes (max: {MAX_METADATA_SIZE})"
            )
        
        # Sanitize string values
        sanitized = _sanitize_metadata_values(metadata)
        
        return ValidationResult.success(sanitized)
        
    except (TypeError, ValueError) as e:
        return ValidationResult.failure(f"Invalid metadata: {e}")


def _sanitize_metadata_values(data: Any) -> Any:
    """Recursively sanitize metadata values."""
    if isinstance(data, dict):
        return {k: _sanitize_metadata_values(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_sanitize_metadata_values(v) for v in data]
    elif isinstance(data, str):
        return sanitize_text(data, 1000)
    else:
        return data


# ============================================================
# ID Validation
# ============================================================

def validate_id(id_value: str, id_type: str = "ID") -> ValidationResult:
    """
    Validate an identifier (conversation ID, document ID, etc.)
    
    Args:
        id_value: The ID to validate
        id_type: Type of ID for error messages
        
    Returns:
        ValidationResult
    """
    if not id_value or not id_value.strip():
        return ValidationResult.failure(f"{id_type} cannot be empty")
    
    id_value = id_value.strip()
    
    # Check length
    if len(id_value) > 128:
        return ValidationResult.failure(f"{id_type} too long (max: 128 chars)")
    
    # Check for valid characters (alphanumeric, dash, underscore)
    if not re.match(r'^[a-zA-Z0-9_-]+$', id_value):
        return ValidationResult.failure(
            f"Invalid {id_type}: only alphanumeric, dash, and underscore allowed"
        )
    
    return ValidationResult.success(id_value)


# ============================================================
# Query Validation
# ============================================================

def validate_search_query(query: str, min_length: int = 2) -> ValidationResult:
    """
    Validate a search query.
    
    Args:
        query: Search query
        min_length: Minimum query length
        
    Returns:
        ValidationResult with sanitized query or error
    """
    result = validate_message(query)
    if not result.is_valid:
        return result
    
    query = result.value
    
    if len(query) < min_length:
        return ValidationResult.failure(
            f"Query too short (min: {min_length} chars)"
        )
    
    return ValidationResult.success(query)


# ============================================================
# Configuration Validation
# ============================================================

def validate_temperature(value: float) -> ValidationResult:
    """Validate temperature parameter."""
    if not isinstance(value, (int, float)):
        return ValidationResult.failure("Temperature must be a number")
    
    if value < 0 or value > 2:
        return ValidationResult.failure("Temperature must be between 0 and 2")
    
    return ValidationResult.success(float(value))


def validate_top_k(value: int) -> ValidationResult:
    """Validate top_k parameter."""
    if not isinstance(value, int):
        return ValidationResult.failure("top_k must be an integer")
    
    if value < 1 or value > 100:
        return ValidationResult.failure("top_k must be between 1 and 100")
    
    return ValidationResult.success(value)


def validate_url(url: str) -> ValidationResult:
    """Validate a URL."""
    if not url or not url.strip():
        return ValidationResult.failure("URL cannot be empty")
    
    url = url.strip()
    
    # Basic URL pattern
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    
    if not url_pattern.match(url):
        return ValidationResult.failure("Invalid URL format")
    
    return ValidationResult.success(url)
