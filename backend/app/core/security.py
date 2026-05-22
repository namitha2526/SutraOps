from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

# Passlib CryptContext using bcrypt for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain text password matches its stored bcrypt hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generates a secure bcrypt hash of a plain text password.
    """
    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, Any],
    org_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Creates a JWT access token containing subject (user_id), org_id, role and expiration.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "org_id": str(org_id),
        "role": str(role),
        "type": "access"
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any],
    org_id: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Creates a long-lived JWT refresh token used to request new access tokens.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "org_id": str(org_id),
        "type": "refresh"
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodes a JWT token using HS256 algorithm and verifies its signature and expiration.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
