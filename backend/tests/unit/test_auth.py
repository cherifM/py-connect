import pytest
from fastapi import HTTPException, status
from unittest.mock import Mock, patch
from app import auth, schemas, models
from app.database import SessionLocal

def test_verify_password():
    """Test password verification"""
    plain_password = "testpassword"
    hashed_password = auth.get_password_hash(plain_password)
    assert auth.verify_password(plain_password, hashed_password) is True
    assert auth.verify_password("wrongpassword", hashed_password) is False

def test_get_password_hash():
    """Test password hashing"""
    password = "testpassword"
    hashed = auth.get_password_hash(password)
    assert isinstance(hashed, str)
    assert hashed != password
    assert len(hashed) > 0

@patch('app.auth.pwd_context.verify')
def test_authenticate_user(mock_verify, db_session):
    """Test user authentication"""
    # Setup test user
    test_user = models.User(
        username="testuser",
        email="test@example.com",
        hashed_password=auth.get_password_hash("testpassword"),
        is_active=True
    )
    db_session.add(test_user)
    db_session.commit()
    
    # Test successful authentication
    mock_verify.return_value = True
    user = auth.authenticate_user(db_session, "testuser", "testpassword")
    assert user is not None
    assert user.username == "testuser"
    
    # Test wrong password
    mock_verify.return_value = False
    user = auth.authenticate_user(db_session, "testuser", "wrongpassword")
    assert user is False
    
    # Test non-existent user
    user = auth.authenticate_user(db_session, "nonexistent", "testpassword")
    assert user is False

@patch('app.auth.ldap_auth.ldap_authenticate')
def test_authenticate_ldap_user(mock_ldap_auth, db_session):
    """Test LDAP user authentication"""
    # Mock successful LDAP authentication
    mock_ldap_auth.return_value = {
        "username": "ldapuser",
        "email": "ldapuser@example.com",
        "full_name": "LDAP User",
        "is_admin": False
    }
    
    # Test successful LDAP authentication
    user = auth.authenticate_user(db_session, "ldapuser", "ldappassword", use_ldap=True)
    assert user is not None
    assert user.username == "ldapuser"
    assert user.email == "ldapuser@example.com"
    assert user.is_admin is False
    
    # Test failed LDAP authentication
    mock_ldap_auth.return_value = None
    user = auth.authenticate_user(db_session, "ldapuser", "wrongpassword", use_ldap=True)
    assert user is False

def test_create_access_token():
    """Test JWT token creation"""
    data = {"sub": "testuser"}
    token = auth.create_access_token(data)
    assert isinstance(token, str)
    assert len(token) > 0

@patch('app.auth.jwt.decode')
def test_get_current_user(mock_jwt_decode, db_session):
    """Test getting current user from token"""
    # Setup test user
    test_user = models.User(
        username="testuser",
        email="test@example.com",
        hashed_password=auth.get_password_hash("testpassword"),
        is_active=True
    )
    db_session.add(test_user)
    db_session.commit()
    
    # Mock JWT decode
    mock_jwt_decode.return_value = {"sub": "testuser"}
    
    # Test with valid token
    user = auth.get_current_user(db_session, "valid_token")
    assert user is not None
    assert user.username == "testuser"
    
    # Test with invalid token
    mock_jwt_decode.side_effect = Exception("Invalid token")
    with pytest.raises(HTTPException) as exc_info:
        auth.get_current_user(db_session, "invalid_token")
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Could not validate credentials" in str(exc_info.value.detail)
