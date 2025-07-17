from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from .models import User
from .ldap_auth import LDAPAuth
import os

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize LDAP if configured
def get_ldap_auth():
    ldap_config = {
        "LDAP_SERVER_URI": os.getenv("LDAP_SERVER_URI"),
        "LDAP_BIND_DN": os.getenv("LDAP_BIND_DN"),
        "LDAP_BIND_PASSWORD": os.getenv("LDAP_BIND_PASSWORD"),
        "LDAP_USER_SEARCH_BASE": os.getenv("LDAP_USER_SEARCH_BASE"),
        "LDAP_USER_DN_TEMPLATE": os.getenv("LDAP_USER_DN_TEMPLATE")
    }
    
    # Only enable LDAP if all required config is present
    if all(ldap_config.values()):
        return LDAPAuth(ldap_config)
    return None

# Verify password
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Authenticate user
def authenticate_user(username: str, password: str):
    # Try LDAP authentication first if enabled
    ldap_auth = get_ldap_auth()
    if ldap_auth and os.getenv("AUTH_METHOD") == "ldap":
        ldap_user = ldap_auth.authenticate(username, password)
        if ldap_user:
            # Check if user exists in local DB, if not create
            user = User.get_by_username(username)
            if not user:
                user = User.create(
                    username=username,
                    email=ldap_user['email'],
                    first_name=ldap_user['first_name'],
                    last_name=ldap_user['last_name'],
                    is_active=True,
                    is_superuser=ldap_user.get('is_superuser', False)
                )
            return user
    
    # Fall back to local authentication
    user = User.get_by_username(username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

# Create access token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Get current user from token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = User.get_by_username(username=username)
    if user is None:
        raise credentials_exception
    return user

# Get current active user
async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Check if user is admin
async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user
