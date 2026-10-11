"""
Authentication and Authorization Module
Implements random 256-bit loopback bearer token management with strict file permissions.
"""

from __future__ import annotations
import secrets
import os
from pathlib import Path
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings

security = HTTPBearer(auto_error=False)


def ensure_token_file() -> str:
    """Ensure token file exists with secure permissions, returning token."""
    token_path = settings.TOKEN_FILE_PATH
    token_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not token_path.exists():
        token = secrets.token_hex(32)  # 256-bit random token
        token_path.write_text(token.strip(), encoding="utf-8")
        try:
            # POSIX 0600: read/write user only
            os.chmod(token_path, 0o600)
        except (AttributeError, OSError):
            pass
        return token
    
    return token_path.read_text(encoding="utf-8").strip()


def verify_bearer_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> bool:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    expected_token = ensure_token_file()
    if not secrets.compare_digest(credentials.credentials, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True

