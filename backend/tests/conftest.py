import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator, Optional, Dict, Any, List, Tuple, Union
from fastapi import Depends, HTTPException
from unittest.mock import patch, MagicMock, ANY
import ldap
import os
from datetime import datetime, timedelta
from jose import jwt

# Application imports
from app.database import Base, get_db
from app.main import app
from app import models, schemas, auth, ldap_auth
from fastapi.testclient import TestClient
from fastapi.security import OAuth2PasswordBearer

# Test configuration
TEST_SECRET_KEY = "test-secret-key"
TEST_ALGORITHM = "HS256"
TEST_ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Configure test database URL
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Test user data
TEST_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpassword",
    "full_name": "Test User",
    "is_active": True,
    "is_admin": False
}

# Test LDAP configuration
TEST_LDAP_CONFIG = {
    "server_uri": "ldap://test-ldap-server:389",
    "bind_dn": "cn=admin,dc=example,dc=com",
    "bind_password": "adminpassword",
    "user_search_base": "ou=users,dc=example,dc=com",
    "user_dn_template": "uid={username},ou=users,dc=example,dc=com",
    "username_attribute": "uid",
    "email_attribute": "mail",
    "full_name_attribute": "cn",
    "group_attribute": "memberOf",
    "admin_groups": ["admins", "administrators"],
    "use_ssl": False,
    "require_cert": False,
    "timeout": 5,
    "retries": 3,
    "page_size": 1000,
    "nested_groups": False
}

# Configure test database URL
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create engine and session factory for testing
engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables before any tests run
Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a new database session for a test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Begin a nested transaction (using SAVEPOINT).
    nested = connection.begin_nested()
    
    # If the application code calls session.commit, it will end the nested
    # transaction. We need to start a new one when that happens.
    @event.listens_for(session, 'after_transaction_end')
    def end_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()
    
    yield session
    
    # Cleanup
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client that uses the override_get_db fixture."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    # Override dependencies
    app.dependency_overrides[get_db] = override_get_db
    
    # Set test secret key
    app.state.SECRET_KEY = TEST_SECRET_KEY
    app.state.ALGORITHM = TEST_ALGORITHM
    app.state.ACCESS_TOKEN_EXPIRE_MINUTES = TEST_ACCESS_TOKEN_EXPIRE_MINUTES
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up overrides
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_user(db_session: Session) -> models.User:
    """Create a test user in the database."""
    hashed_password = auth.get_password_hash(TEST_USER["password"])
    db_user = models.User(
        username=TEST_USER["username"],
        email=TEST_USER["email"],
        hashed_password=hashed_password,
        full_name=TEST_USER["full_name"],
        is_active=TEST_USER["is_active"],
        is_admin=TEST_USER["is_admin"]
    )
    db_session.add(db_user)
    db_session.commit()
    db_session.refresh(db_user)
    return db_user

@pytest.fixture(scope="function")
def test_admin_user(db_session: Session) -> models.User:
    """Create a test admin user in the database."""
    hashed_password = auth.get_password_hash("adminpassword")
    db_user = models.User(
        username="admin",
        email="admin@example.com",
        hashed_password=hashed_password,
        full_name="Admin User",
        is_active=True,
        is_admin=True
    )
    db_session.add(db_user)
    db_session.commit()
    db_session.refresh(db_user)
    return db_user

@pytest.fixture(scope="function")
def auth_headers(test_user: models.User) -> Dict[str, str]:
    """Generate JWT token and return authorization headers."""
    access_token = create_test_token({"sub": test_user.username})
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture(scope="function")
def admin_auth_headers(test_admin_user: models.User) -> Dict[str, str]:
    """Generate JWT token for admin user and return authorization headers."""
    access_token = create_test_token({"sub": test_admin_user.username})
    return {"Authorization": f"Bearer {access_token}"}

def create_test_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a test JWT token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, TEST_SECRET_KEY, algorithm=TEST_ALGORITHM)

@pytest.fixture(scope="function")
def mock_ldap_authenticate():
    """Mock LDAP authentication."""
    mock_user = {
        "username": "ldapuser",
        "email": "ldapuser@example.com",
        "full_name": "LDAP User",
        "groups": ["users"],
        "is_admin": False
    }
    
    def _mock_ldap_authenticate(username: str, password: str):
        if username == "ldapuser" and password == "ldappassword":
            return mock_user

@pytest.fixture
def mock_ldap_admin_authenticate():
    """Mock LDAP authentication for admin user"""
    with patch('app.ldap_auth.LDAPAuth') as mock_ldap_auth:
        mock_instance = mock_ldap_auth.return_value
        mock_instance.authenticate.return_value = ldap_auth.LDAPUser(
            username="admin",
            email="admin@example.com",
            full_name="Admin User",
            groups=["admins"],
            is_admin=True
        )
        yield mock_instance

@pytest.fixture
def mock_ldap_config(monkeypatch):
    """Mock LDAP configuration"""
    # Set environment variables for LDAP config
    for key, value in TEST_LDAP_CONFIG.items():
        if isinstance(value, list):
            value = ",".join(value)
        monkeypatch.setenv(f"LDAP_{key.upper()}", str(value))
    
    # Return the test config
    return ldap_auth.LDAPConfig(**TEST_LDAP_CONFIG)

@pytest.fixture
def mock_ldap_auth(mock_ldap_config):
    """Mock LDAP authentication with config"""
    with patch('app.ldap_auth.LDAPAuth') as mock_ldap_auth:
        mock_instance = mock_ldap_auth.return_value
        mock_instance.config = mock_ldap_config
        yield mock_instance

@pytest.fixture
def mock_ldap_initialize(mock_ldap_connection):
    """Mock ldap.initialize to return our mock connection"""
    with patch('ldap.initialize') as mock_init:
        mock_init.return_value = mock_ldap_connection
        yield mock_init

@pytest.fixture
def ldap_test_user():
    """Create a test LDAP user"""
    return ldap_auth.LDAPUser(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        groups=["users"],
        is_admin=False
    )

@pytest.fixture
def ldap_test_admin():
    """Create a test LDAP admin user"""
    return ldap_auth.LDAPUser(
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        groups=["admins"],
        is_admin=True
    )

@pytest.fixture
def ldap_test_group():
    """Create a test LDAP group"""
    return {
        "cn": [b"testgroup"],
        "member": [
            b"uid=testuser,ou=users,dc=example,dc=com",
            b"uid=admin,ou=users,dc=example,dc=com"
        ]
    }

# Override the get_ldap_auth dependency in the FastAPI app
@pytest.fixture
def app_with_ldap(mock_ldap_auth):
    """Provide an app with mocked LDAP authentication"""
    def override_get_ldap_auth():
        return mock_ldap_auth
    
    app.dependency_overrides[ldap_auth.get_ldap_auth] = override_get_ldap_auth
    yield app
    app.dependency_overrides.clear()

# Client with LDAP support
@pytest.fixture
def ldap_client(app_with_ldap):
    """Test client with LDAP support"""
    with TestClient(app_with_ldap) as client:
        yield client
    monkeypatch.setattr("app.config.Settings.AUTH_METHOD", "ldap")
