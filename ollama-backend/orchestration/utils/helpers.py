"""
Helper Utilities

Common utility functions used across the orchestration layer.
"""

import os
import re
import unicodedata
from typing import Optional


def truncate_text(
    text: str,
    max_length: int,
    suffix: str = "..."
) -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to append if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length - len(suffix)]
    # Try to end at word boundary
    last_space = truncated.rfind(' ')
    if last_space > max_length // 2:
        truncated = truncated[:last_space]
    
    return truncated + suffix


def estimate_tokens(text: str) -> int:
    """
    Estimate the number of tokens in text.
    
    Uses a rough approximation of 1 token ≈ 4 characters.
    More accurate for English text.
    
    Args:
        text: Input text
        
    Returns:
        Estimated token count
    """
    # Simple estimation: ~4 characters per token
    # This is a rough approximation that works reasonably well
    return len(text) // 4


def estimate_tokens_words(text: str) -> int:
    """
    Estimate tokens based on word count.
    
    Uses approximation of 1.3 tokens per word.
    
    Args:
        text: Input text
        
    Returns:
        Estimated token count
    """
    words = len(text.split())
    return int(words * 1.3)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing/replacing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Normalize unicode characters
    filename = unicodedata.normalize('NFKD', filename)
    filename = filename.encode('ASCII', 'ignore').decode('ASCII')
    
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Replace spaces with underscores
    filename = re.sub(r'\s+', '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Limit length
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200-len(ext)] + ext
    
    return filename or 'unnamed'


def ensure_directory(path: str) -> str:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        The path (for chaining)
    """
    os.makedirs(path, exist_ok=True)
    return path


def normalize_text(text: str) -> str:
    """
    Normalize text for processing.
    
    - Normalize unicode
    - Remove excessive whitespace
    - Normalize line endings
    
    Args:
        text: Input text
        
    Returns:
        Normalized text
    """
    # Normalize unicode
    text = unicodedata.normalize('NFKC', text)
    
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Normalize whitespace (but preserve single newlines)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def chunk_list(lst: list, chunk_size: int) -> list:
    """
    Split a list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_get(d: dict, *keys, default=None):
    """
    Safely get nested dictionary value.
    
    Args:
        d: Dictionary
        *keys: Keys to traverse
        default: Default value if not found
        
    Returns:
        Value or default
    """
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key, default)
        else:
            return default
    return d


def format_bytes(size: int) -> str:
    """
    Format byte size to human-readable string.
    
    Args:
        size: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def format_duration(seconds: float) -> str:
    """
    Format duration to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., "1h 30m 45s")
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    return f"{minutes}m {seconds}s"


def extract_urls(text: str) -> list:
    """
    Extract URLs from text.
    
    Args:
        text: Input text
        
    Returns:
        List of URLs found
    """
    url_pattern = re.compile(
        r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
        r'(?:/[-\w%@.~+#=]*)*'
        r'(?:\?[-\w%@.~+#=&]*)?'
    )
    return url_pattern.findall(text)


def mask_sensitive(text: str, patterns: Optional[list] = None) -> str:
    """
    Mask sensitive information in text.
    
    Args:
        text: Input text
        patterns: Optional list of regex patterns to mask
        
    Returns:
        Text with sensitive info masked
    """
    if patterns is None:
        patterns = [
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
            (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]'),
            (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]'),
        ]
    
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    
    return text
