"""Input validation and sanitization for security."""
import re
import html
from fastapi import HTTPException


def validate_password(password: str) -> str:
    """Validate password meets security requirements.

    Rules:
      - Minimum 8 characters
      - At least one uppercase letter
      - At least one lowercase letter
      - At least one digit
      - At least one special character
    """
    errors = []
    if len(password) < 8:
        errors.append("at least 8 characters")
    if not re.search(r"[A-Z]", password):
        errors.append("one uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("one lowercase letter")
    if not re.search(r"\d", password):
        errors.append("one digit")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("one special character")

    if errors:
        raise HTTPException(
            status_code=400,
            detail=f"Password must contain: {', '.join(errors)}",
        )
    return password


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """Sanitize user input to prevent XSS and injection."""
    if not text:
        return text
    # Truncate
    text = text[:max_length]
    # Escape HTML entities
    text = html.escape(text)
    # Remove null bytes
    text = text.replace("\x00", "")
    return text


def validate_service_name(name: str) -> str:
    """Validate service name format (alphanumeric, dashes, underscores)."""
    if not name:
        return name
    if not re.match(r"^[a-zA-Z0-9_-]{1,100}$", name):
        raise HTTPException(
            status_code=400,
            detail="Service name must be alphanumeric (dashes/underscores allowed, max 100 chars)",
        )
    return name


def validate_email(email: str) -> str:
    """Basic email format validation."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    return email
