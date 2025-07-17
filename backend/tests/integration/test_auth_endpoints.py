import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
from app.main import app
from app import models, schemas, auth, ldap_auth
from app.config import settings

# Test data
TEST_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpassword"
}

def test_register_user(client: TestClient, db: Session):
    """Test user registration endpoint"""
    # Test successful registration
    response = client.post(
        "/api/auth/register",
        json={
            "username": TEST_USER["username"],
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["username"] == TEST_USER["username"]
    assert data["email"] == TEST_USER["email"]
    assert "password" not in data
    assert "hashed_password" not in data
    
    # Test duplicate username
    response = client.post(
        "/api/auth/register",
        json={
            "username": TEST_USER["username"],
            "email": "another@example.com",
            "password": "anotherpassword"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Username already registered" in response.text

def test_login(client: TestClient, db: Session):
    """Test user login endpoint"""
    # First register a user
    hashed_password = auth.get_password_hash(TEST_USER["password"])
    db_user = models.User(
        username=TEST_USER["username"],
        email=TEST_USER["email"],
        hashed_password=hashed_password,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    
    # Test successful login
    response = client.post(
        "/api/auth/token",
        data={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Test invalid credentials
    response = client.post(
        "/api/auth/token",
        data={
            "username": TEST_USER["username"],
            "password": "wrongpassword"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect username or password" in response.text

@pytest.fixture
def mock_ldap_config():
    """Fixture to provide a mock LDAP configuration"""
    return ldap_auth.LDAPConfig(
        server_uri="ldap://test-ldap:389",
        bind_dn="cn=admin,dc=example,dc=com",
        bind_password="adminpassword",
        user_search_base="ou=users,dc=example,dc=com",
        user_dn_template="uid={username},ou=users,dc=example,dc=com"
    )

@patch('app.auth.ldap_auth.LDAPAuth')
def test_ldap_login_success(mock_ldap_auth, client: TestClient, db: Session, mock_ldap_config):
    """Test successful LDAP login"""
    # Setup mock LDAP user
    mock_ldap_user = ldap_auth.LDAPUser(
        username=TEST_USER["username"],
        email=TEST_USER["email"],
        full_name="Test User",
        groups=["users", "developers"],
        is_admin=False
    )
    
    # Configure mock
    mock_ldap_instance = MagicMock()
    mock_ldap_instance.authenticate.return_value = mock_ldap_user
    mock_ldap_auth.return_value = mock_ldap_instance
    
    # Test successful LDAP login
    response = client.post(
        "/api/auth/ldap-login",
        data={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"],
            "grant_type": "password"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    # Verify response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["username"] == TEST_USER["username"]
    assert data["email"] == TEST_USER["email"]
    assert data["is_admin"] is False
    assert "groups" in data
    assert set(data["groups"]) == {"users", "developers"}
    
    # Verify LDAP auth was called with correct credentials
    mock_ldap_instance.authenticate.assert_called_once_with(
        TEST_USER["username"], 
        TEST_USER["password"]
    )

@patch('app.auth.ldap_auth.LDAPAuth')
def test_ldap_login_invalid_credentials(mock_ldap_auth, client: TestClient, db: Session, mock_ldap_config):
    """Test LDAP login with invalid credentials"""
    # Configure mock to return None (invalid credentials)
    mock_ldap_instance = MagicMock()
    mock_ldap_instance.authenticate.return_value = None
    mock_ldap_auth.return_value = mock_ldap_instance
    
    # Test with invalid credentials
    response = client.post(
        "/api/auth/ldap-login",
        data={
            "username": TEST_USER["username"],
            "password": "wrongpassword",
            "grant_type": "password"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    # Verify unauthorized response
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect username or password" in response.text

@patch('app.auth.ldap_auth.LDAPAuth')
def test_ldap_login_missing_credentials(mock_ldap_auth, client: TestClient, db: Session, mock_ldap_config):
    """Test LDAP login with missing credentials"""
    # Test missing username
    response = client.post(
        "/api/auth/ldap-login",
        data={
            "password": TEST_USER["password"],
            "grant_type": "password"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # Test missing password
    response = client.post(
        "/api/auth/ldap-login",
        data={
            "username": TEST_USER["username"],
            "grant_type": "password"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@patch('app.auth.ldap_auth.LDAPAuth')
def test_ldap_login_server_error(mock_ldap_auth, client: TestClient, db: Session, mock_ldap_config):
    """Test LDAP login with server error"""
    # Configure mock to raise an exception
    mock_ldap_instance = MagicMock()
    mock_ldap_instance.authenticate.side_effect = Exception("LDAP Server Error")
    mock_ldap_auth.return_value = mock_ldap_instance
    
    # Test with server error
    response = client.post(
        "/api/auth/ldap-login",
        data={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"],
            "grant_type": "password"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    # Verify error response
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert "LDAP authentication service is currently unavailable" in response.text
    assert "Incorrect username or password" in response.text

@patch('app.auth.ldap_auth.ldap_authenticate')
def test_ldap_login(mock_ldap_auth, client: TestClient, db: Session):
    """Test LDAP login endpoint"""
    # Mock successful LDAP authentication
    mock_ldap_auth.return_value = {
        "username": "ldapuser",
        "email": "ldapuser@example.com",
        "full_name": "LDAP User",
        "is_admin": False
    }
    
    # Test successful LDAP login
    response = client.post(
        "/api/auth/ldap/token",
        data={
            "username": "ldapuser",
            "password": "ldappassword"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Verify user was created in the database
    user = db.query(models.User).filter(models.User.username == "ldapuser").first()
    assert user is not None
    assert user.email == "ldapuser@example.com"
    assert user.is_admin is False

def test_read_users_me(client: TestClient, db: Session, test_user: models.User):
    """Test getting current user info"""
    # Get access token
    token = auth.create_access_token({"sub": test_user.username})
    
    # Test with valid token
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email
    assert "hashed_password" not in data
    
    # Test with invalid token
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# Fixture for authenticated client
@pytest.fixture
def auth_client(client: TestClient, test_user: models.User):
    """Return an authenticated test client"""
    # Create access token
    token = auth.create_access_token(data={"sub": test_user.username})
    
    # Clone the client to avoid modifying the original
    auth_client = client.__class__(app=client.app)
    auth_client.headers.update({
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    })
    
    # Also set cookies if using cookie-based auth
    auth_client.cookies.set("access_token", token)
    
    return auth_client

@pytest.fixture
def auth_admin_client(client: TestClient, admin_user: models.User):
    """Return an authenticated test client with admin privileges"""
    # Create access token for admin user
    token = auth.create_access_token(
        data={"sub": admin_user.username},
        scopes=["admin"]
    )
    
    # Clone the client to avoid modifying the original
    admin_client = client.__class__(app=client.app)
    admin_client.headers.update({
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    })
    
    # Also set cookies if using cookie-based auth
    admin_client.cookies.set("access_token", token)
    
    return admin_client

# Test protected endpoints with authentication
class TestProtectedEndpoints:
    def test_protected_endpoint(self, auth_client: TestClient, test_user: models.User):
        """Test accessing a protected endpoint with valid token"""
        response = auth_client.get("/api/users/me")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
        assert "hashed_password" not in data
        
    def test_protected_endpoint_no_token(self, client: TestClient):
        """Test accessing a protected endpoint without token"""
        response = client.get("/api/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Not authenticated" in response.text
        
    def test_protected_endpoint_invalid_token(self, client: TestClient):
        """Test accessing a protected endpoint with invalid token"""
        response = client.get(
            "/api/users/me",
            headers={"Authorization": "Bearer invalidtoken"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid authentication credentials" in response.text
        
    def test_protected_endpoint_expired_token(self, client: TestClient, test_user: models.User):
        """Test accessing a protected endpoint with expired token"""
        # Create an expired token
        token = auth.create_access_token(
            data={"sub": test_user.username},
            expires_delta=timedelta(seconds=-1)  # Expired token
        )
        
        response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Token has expired" in response.text

    def test_protected_endpoint_inactive_user(self, client: TestClient, db: Session, test_user: models.User):
        """Test accessing a protected endpoint with an inactive user"""
        # Deactivate the test user
        test_user.is_active = False
        db.commit()
        
        # Create a valid token for the inactive user
        token = auth.create_access_token(data={"sub": test_user.username})
        
        response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Inactive user" in response.text
