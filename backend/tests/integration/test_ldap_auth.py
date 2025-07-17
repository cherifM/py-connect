import pytest
import ldap
from unittest.mock import patch, MagicMock
from app.ldap_auth import LDAPAuth, LDAPConfig, LDAPUser

# Test LDAP configuration
TEST_CONFIG = LDAPConfig(
    server_uri="ldap://test-ldap-server:389",
    bind_dn="cn=admin,dc=example,dc=com",
    bind_password="adminpassword",
    user_search_base="ou=users,dc=example,dc=com",
    user_dn_template="uid={username},ou=users,dc=example,dc=com"
)

# Mock LDAP user data
MOCK_LDAP_USER = {
    "uid": [b"testuser"],
    "cn": [b"Test User"],
    "mail": [b"test@example.com"],
    "memberOf": [
        b"cn=users,ou=groups,dc=example,dc=com",
        b"cn=admins,ou=groups,dc=example,dc=com"
    ]
}

class TestLDAPAuth:
    @patch('ldap.initialize')
    def test_ldap_connection(self, mock_ldap_init):
        """Test LDAP connection and binding"""
        # Setup mock
        mock_conn = MagicMock()
        mock_ldap_init.return_value = mock_conn
        
        # Test connection
        ldap_auth = LDAPAuth(TEST_CONFIG)
        assert ldap_auth is not None
        mock_ldap_init.assert_called_once_with(TEST_CONFIG.server_uri)
        mock_conn.simple_bind_s.assert_called_once_with(
            TEST_CONFIG.bind_dn, 
            TEST_CONFIG.bind_password
        )
    
    @patch('ldap.initialize')
    def test_authenticate_success(self, mock_ldap_init):
        """Test successful LDAP authentication"""
        # Setup mock
        mock_conn = MagicMock()
        mock_ldap_init.return_value = mock_conn
        
        # Mock search results
        mock_conn.search_s.return_value = [
            ("uid=testuser,ou=users,dc=example,dc=com", MOCK_LDAP_USER)
        ]
        
        # Test authentication
        ldap_auth = LDAPAuth(TEST_CONFIG)
        result = ldap_auth.authenticate("testuser", "password")
        
        # Verify results
        assert result is not None
        assert result.username == "testuser"
        assert result.email == "test@example.com"
        assert result.full_name == "Test User"
        assert result.is_admin is True  # Because memberOf contains 'admins' group
        
        # Verify LDAP search was called with correct parameters
        mock_conn.search_s.assert_called_once()
        
    @patch('ldap.initialize')
    def test_authenticate_invalid_credentials(self, mock_ldap_init):
        """Test LDAP authentication with invalid credentials"""
        # Setup mock to raise INVALID_CREDENTIALS
        mock_conn = MagicMock()
        mock_ldap_init.return_value = mock_conn
        mock_conn.simple_bind_s.side_effect = ldap.INVALID_CREDENTIALS()
        
        # Test authentication
        ldap_auth = LDAPAuth(TEST_CONFIG)
        result = ldap_auth.authenticate("testuser", "wrongpassword")
        
        # Should return None for invalid credentials
        assert result is None
    
    @patch('ldap.initialize')
    def test_authenticate_user_not_found(self, mock_ldap_init):
        """Test LDAP authentication for non-existent user"""
        # Setup mock - empty search results
        mock_conn = MagicMock()
        mock_ldap_init.return_value = mock_conn
        mock_conn.search_s.return_value = []
        
        # Test authentication
        ldap_auth = LDAPAuth(TEST_CONFIG)
        result = ldap_auth.authenticate("nonexistent", "password")
        
        # Should return None for non-existent user
        assert result is None
        
    @patch('ldap.initialize')
    def test_authenticate_connection_error(self, mock_ldap_init):
        """Test LDAP authentication with connection error"""
        # Setup mock to raise connection error
        mock_ldap_init.side_effect = ldap.SERVER_DOWN()
        
        # Test authentication
        ldap_auth = LDAPAuth(TEST_CONFIG)
        result = ldap_auth.authenticate("testuser", "password")
        
        # Should return None for connection errors
        assert result is None

    @patch('ldap.initialize')
    def test_is_user_in_group(self, mock_ldap_init):
        """Test checking if user is in a specific group"""
        # Setup mock
        mock_conn = MagicMock()
        mock_ldap_init.return_value = mock_conn
        
        # Create test user
        user = LDAPUser(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            groups=["users", "admins"]
        )
        
        # Test group membership
        ldap_auth = LDAPAuth(TEST_CONFIG)
        assert ldap_auth.is_user_in_group(user, "admins") is True
        assert ldap_auth.is_user_in_group(user, "developers") is False

    @patch('ldap.initialize')
    def test_get_user_groups(self, mock_ldap_init):
        """Test extracting groups from LDAP response"""
        # Setup mock
        mock_conn = MagicMock()
        mock_ldap_init.return_value = mock_conn
        
        # Mock search results with group membership
        mock_conn.search_s.return_value = [
            ("uid=testuser,ou=users,dc=example,dc=com", MOCK_LDAP_USER)
        ]
        
        # Test group extraction
        ldap_auth = LDAPAuth(TEST_CONFIG)
        result = ldap_auth.authenticate("testuser", "password")
        
        # Verify groups
        assert result is not None
        assert set(result.groups) == {"users", "admins"}

    @patch('ldap.initialize')
    def test_extract_user_info(self, mock_ldap_init):
        """Test extracting user info from LDAP response"""
        # Setup mock
        mock_conn = MagicMock()
        mock_ldap_init.return_value = mock_conn
        
        # Create LDAP auth instance
        ldap_auth = LDAPAuth(TEST_CONFIG)
        
        # Test user info extraction
        user_info = ldap_auth._extract_user_info("testuser", MOCK_LDAP_USER)
        
        # Verify extracted info
        assert user_info.username == "testuser"
        assert user_info.email == "test@example.com"
        assert user_info.full_name == "Test User"
        assert set(user_info.groups) == {"users", "admins"}
        assert user_info.is_admin is True
