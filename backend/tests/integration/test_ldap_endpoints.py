"""Integration tests for LDAP authentication endpoints."""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from app import models, schemas, ldap_auth
from app.core.config import settings

# Test data
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpassword"
TEST_EMAIL = "test@example.com"
TEST_FULL_NAME = "Test User"

# Test LDAP user data
TEST_LDAP_USER = ldap_auth.LDAPUser(
    username=TEST_USERNAME,
    email=TEST_EMAIL,
    full_name=TEST_FULL_NAME,
    groups=["users"],
    is_admin=False
)

TEST_LDAP_ADMIN = ldap_auth.LDAPUser(
    username="admin",
    email="admin@example.com",
    full_name="Admin User",
    groups=["admins"],
    is_admin=True
)

class TestLDAPLogin:
    """Test LDAP login endpoint."""
    
    def test_ldap_login_success(self, client: TestClient, mock_ldap_auth):
        """Test successful LDAP login."""
        # Setup mock
        mock_ldap_auth.authenticate.return_value = TEST_LDAP_USER
        
        # Test login
        response = client.post(
            "/api/auth/ldap-login",
            data={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD,
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
        assert data["username"] == TEST_USERNAME
        assert data["email"] == TEST_EMAIL
        assert data["is_admin"] is False
        
        # Verify LDAP auth was called
        mock_ldap_auth.authenticate.assert_called_once_with(
            TEST_USERNAME, 
            TEST_PASSWORD
        )
    
    def test_ldap_login_admin(self, client: TestClient, mock_ldap_auth):
        """Test LDAP login for admin user."""
        # Setup mock
        mock_ldap_auth.authenticate.return_value = TEST_LDAP_ADMIN
        
        # Test login
        response = client.post(
            "/api/auth/ldap-login",
            data={
                "username": "admin",
                "password": "adminpassword",
                "grant_type": "password"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_admin"] is True
    
    def test_ldap_login_invalid_credentials(self, client: TestClient, mock_ldap_auth):
        """Test LDAP login with invalid credentials."""
        # Setup mock to return None (invalid credentials)
        mock_ldap_auth.authenticate.return_value = None
        
        # Test login
        response = client.post(
            "/api/auth/ldap-login",
            data={
                "username": TEST_USERNAME,
                "password": "wrongpassword",
                "grant_type": "password"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        # Verify response
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect username or password" in response.text
    
    def test_ldap_login_missing_fields(self, client: TestClient):
        """Test LDAP login with missing required fields."""
        # Missing username
        response = client.post(
            "/api/auth/ldap-login",
            data={"password": TEST_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Missing password
        response = client.post(
            "/api/auth/ldap-login",
            data={"username": TEST_USERNAME},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_ldap_login_server_error(self, client: TestClient, mock_ldap_auth):
        """Test LDAP login when LDAP server is unavailable."""
        # Setup mock to raise an exception
        mock_ldap_auth.authenticate.side_effect = Exception("LDAP Server Error")
        
        # Test login
        response = client.post(
            "/api/auth/ldap-login",
            data={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD,
                "grant_type": "password"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        # Verify response
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "LDAP authentication service is currently unavailable" in response.text


class TestLDAPUserEndpoints:
    """Test LDAP user-related endpoints."""
    
    def test_get_ldap_user(self, ldap_client, mock_ldap_auth):
        """Test getting LDAP user information."""
        # Setup mock
        mock_ldap_auth.get_user.return_value = TEST_LDAP_USER
        
        # Test endpoint
        response = ldap_client.get(f"/api/ldap/users/{TEST_USERNAME}")
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == TEST_USERNAME
        assert data["email"] == TEST_EMAIL
        assert data["full_name"] == TEST_FULL_NAME
        assert "groups" in data
        
        # Verify LDAP get_user was called
        mock_ldap_auth.get_user.assert_called_once_with(TEST_USERNAME)
    
    def test_search_ldap_users(self, ldap_client, mock_ldap_auth):
        """Test searching LDAP users."""
        # Setup mock
        mock_ldap_auth.search_users.return_value = [TEST_LDAP_USER]
        
        # Test endpoint
        response = ldap_client.get("/api/ldap/users/", params={"query": TEST_USERNAME})
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["username"] == TEST_USERNAME
        
        # Verify LDAP search_users was called
        mock_ldap_auth.search_users.assert_called_once_with(TEST_USERNAME, limit=50)
    
    def test_check_ldap_group_membership(self, ldap_client, mock_ldap_auth):
        """Test checking LDAP group membership."""
        # Setup mock
        mock_ldap_auth.is_user_in_group.return_value = True
        
        # Test endpoint
        response = ldap_client.get(
            f"/api/ldap/users/{TEST_USERNAME}/groups/users"
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_member"] is True
        
        # Verify LDAP is_user_in_group was called
        mock_ldap_auth.is_user_in_group.assert_called_once_with(
            TEST_USERNAME, 
            "users"
        )


class TestLDAPConfigEndpoints:
    """Test LDAP configuration endpoints."""
    
    def test_get_ldap_config(self, admin_auth_headers, client: TestClient):
        """Test getting LDAP configuration (admin only)."""
        # Test as admin
        response = client.get(
            "/api/ldap/config",
            headers=admin_auth_headers
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "server_uri" in data
        assert "user_search_base" in data
        
        # Test as regular user (should be forbidden)
        regular_headers = {"Authorization": "Bearer regularusertoken"}
        response = client.get(
            "/api/ldap/config",
            headers=regular_headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_test_ldap_connection(self, client: TestClient, mock_ldap_auth):
        """Test LDAP connection testing endpoint."""
        # Setup mock
        mock_ldap_auth.test_connection.return_value = True
        
        # Test endpoint
        response = client.post("/api/ldap/test-connection")
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["connected"] is True
        
        # Verify test_connection was called
        mock_ldap_auth.test_connection.assert_called_once()
    
    def test_test_ldap_connection_failure(self, client: TestClient, mock_ldap_auth):
        """Test LDAP connection testing endpoint with connection failure."""
        # Setup mock to raise an exception
        mock_ldap_auth.test_connection.side_effect = Exception("Connection failed")
        
        # Test endpoint
        response = client.post("/api/ldap/test-connection")
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["connected"] is False
        assert "error" in data


class TestLDAPSync:
    """Test LDAP synchronization endpoints."""
    
    def test_sync_ldap_user(self, admin_auth_headers, client: TestClient, db: Session, mock_ldap_auth):
        """Test syncing a single LDAP user to the local database."""
        # Setup mock
        mock_ldap_auth.get_user.return_value = TEST_LDAP_USER
        
        # Test endpoint
        response = client.post(
            f"/api/ldap/sync/user/{TEST_USERNAME}",
            headers=admin_auth_headers
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == TEST_USERNAME
        assert data["email"] == TEST_EMAIL
        
        # Verify user was created in the database
        user = db.query(models.User).filter(models.User.username == TEST_USERNAME).first()
        assert user is not None
        assert user.email == TEST_EMAIL
    
    def test_sync_ldap_group(self, admin_auth_headers, client: TestClient, db: Session, mock_ldap_auth):
        """Test syncing an LDAP group to the local database."""
        # Setup mock
        mock_ldap_auth.get_group_users.return_value = [TEST_LDAP_USER]
        
        # Test endpoint
        response = client.post(
            "/api/ldap/sync/group/users",
            headers=admin_auth_headers
        )
        
        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["username"] == TEST_USERNAME
        
        # Verify user was created in the database
        user = db.query(models.User).filter(models.User.username == TEST_USERNAME).first()
        assert user is not None
        assert user.email == TEST_EMAIL
