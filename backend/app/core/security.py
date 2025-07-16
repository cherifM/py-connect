import secrets
from datetime import datetime, timedelta
from typing import Optional, Any, Union

from jose import jwt
from passlib.context import CryptContext
from pydantic import ValidationError

from app.config.settings import settings
from app.schemas.token import TokenPayload

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: Subject to be stored in the token (usually user ID)
        expires_delta: Expiration time delta
        
    Returns:
        str: Encoded JWT token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY.get_secret_value(),
        algorithm="HS256"
    )
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Hash a password.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)

def generate_password_reset_token() -> str:
    """
    Generate a password reset token.
    
    Returns:
        str: Random URL-safe token
    """
    return secrets.token_urlsafe(32)

def verify_token(token: str) -> Optional[TokenPayload]:
    """
    Verify a JWT token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Optional[TokenPayload]: Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY.get_secret_value(),
            algorithms=["HS256"]
        )
        return TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        return None
