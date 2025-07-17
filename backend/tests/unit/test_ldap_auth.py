import pytest
from unittest.mock import patch, MagicMock
import ldap
from app.ldap_auth import LDAPAuth, LDAPConfig, LDAPUser
from app.config import settings

# Test configuration
TEST_CONFIG = LDAPConfig(
    server_uri="ldap://test-ldap-server:389",
    bind_dn="cn=admin,dc=example,dc=com",
    bind_password="adminpassword",
    user_search_base="ou=users,dc=example,dc=com",
    user_dn_template="uid={username},ou=users,dc=example,dc=com"
)

# Test user data
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpassword"
TEST_EMAIL = "test@example.com"
TEST_FULL_NAME = "Test User"

# Mock LDAP response
MOCK_LDAP_RESPONSE = [
    (
        f"uid={TEST_USERNAME},ou=users,dc=example,dc=com",
        {
            "uid": [TEST_USERNAME.encode()],
            "cn": [TEST_FULL_NAME.encode()],
            "mail": [TEST_EMAIL.encode()],
            "memberOf": [
                b"cn=users,ou=groups,dc=example,dc=com",
                b"cn=admins,ou=groups,dc=example,dc=com"
            ]
        }
    )
]

class TestLDAPAuth:
    @patch('ldap.initialize')
    def test_initialization(self, mock_ldap_init):
        """Test LDAPAuth initialization"""
        mock_conn = MagicMock()
        mock_ldap_init.return_value = mock_conn
        
        # Initialize LDAP auth
        ldap_auth = LDAPAuth(TEST_CONFIG)
        
        # Verify connection was initialized correctly
        mock_ldap_init.assert_called_once_with(TEST_CONFIG.server_uri)
        mock_conn.set_option.assert_called()
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
        mock_conn.search_s.return_value = MOCK_LDAP_RESPONSE
        
        # Test authentication
        ldap_auth = LDAPAuth(TEST_CONFIG)
        result = ldap_auth.authenticate(TEST_USERNAME, TEST_PASSWORD)
        
        # Verify results
        assert result is not None
        assert result.username == TEST_USERNAME
        assert result.email == TEST_EMAIL
        assert result.full_name == TEST_FULL_NAME
        assert set(result.groups) == {"users", "admins"}
        assert result.is_admin is True
        
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
        result = ldap_auth.authenticate(TEST_USERNAME, "wrongpassword")
        
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
        result = ldap_auth.authenticate("nonexistent", TEST_PASSWORD)
        
        # Should return None for non-existent user
        assert result is None
    
    @patch('ldap.initialize')
    def test_authenticate_connection_error(self, mock_ldap_init):
        """Test LDAP authentication with connection error"""
        # Setup mock to raise connection error
        mock_ldap_init.side_effect = ldap.SERVER_DOWN()
        
        # Test authentication
        ldap_auth = LDAPAuth(TEST_CONFIG)
        result = ldap_auth.authenticate(TEST_USERNAME, TEST_PASSWORD)
        
        # Should return None for connection errors
        assert result is None
    
    @patch('ldap.initialize')
    def test_is_user_in_group(self, mock_ldap_init):
        """Test checking if user is in a specific group"""
        # Setup mock
        mock_conn = MagicMock()
        mock_ldap_init.return_value = mock_conn
        mock_conn.search_s.return_value = MOCK_LDAP_RESPONSE
        
        # Test group membership
        ldap_auth = LDAPAuth(TEST_CONFIG)
        
        # User should be in these groups
        assert ldap_auth.is_user_in_group(TEST_USERNAME, "admins") is True
        assert ldap_auth.is_user_in_group(TEST_USERNAME, "users") is True
        
        # User should not be in these groups
        assert ldap_auth.is_user_in_group(TEST_USERNAME, "developers") is False
        assert ldap_auth.is_user_in_group(TEST_USERNAME, "managers") is False
    
    @patch('ldap.initialize')
    def test_extract_user_info(self, mock_ldap_init):
        """Test extracting user info from LDAP response"""
        # Setup mock
        mock_conn = MagicMock()
        mock_ldap_init.return_value = mock_conn
        
        # Test user info extraction
        ldap_auth = LDAPAuth(TEST_CONFIG)
        user_info = ldap_auth._extract_user_info(TEST_USERNAME, MOCK_LDAP_RESPONSE[0][1])
        
        # Verify extracted info
        assert user_info.username == TEST_USERNAME
        assert user_info.email == TEST_EMAIL
        assert user_info.full_name == TEST_FULL_NAME
        assert set(user_info.groups) == {"users", "admins"}
        assert user_info.is_admin is True

    @patch('ldap.initialize')
    def test_authenticate_with_custom_attributes(self, mock_ldap_init):
        """Test LDAP authentication with custom attributes"""
        # Setup custom config with different attribute names
        custom_config = LDAPConfig(
            server_uri=TEST_CONFIG.server_uri,
            bind_dn=TEST_CONFIG.bind_dn,
            bind_password=TEST_CONFIG.bind_password,
            user_search_base=TEST_CONFIG.user_search_base,
            user_dn_template=TEST_CONFIG.user_dn_template,
            username_attribute="sAMAccountName",
            email_attribute="userPrincipalName",
            full_name_attribute="displayName",
            group_attribute="memberOf"
        )
        
        # Setup mock
        mock_conn = MagicMock()
        mock_ldap_init.return_value = mock_conn
        
        # Mock LDAP response with custom attributes
        mock_conn.search_s.return_value = [
            (
                f"sAMAccountName={TEST_USERNAME},ou=users,dc=example,dc=com",
                {
                    "sAMAccountName": [TEST_USERNAME.encode()],
                    "userPrincipalName": [TEST_EMAIL.encode()],
                    "displayName": [TEST_FULL_NAME.encode()],
                    "memberOf": [
                        b"CN=Domain Admins,CN=Users,DC=example,DC=com",
                        b"CN=Enterprise Admins,CN=Users,DC=example,DC=com"
                    ]
                }
            )
        ]
        
        # Test authentication with custom config
        ldap_auth = LDAPAuth(custom_config)
        result = ldap_auth.authenticate(TEST_USERNAME, TEST_PASSWORD)
        
        # Verify results
        assert result is not None
        assert result.username == TEST_USERNAME
        assert result.email == TEST_EMAIL
        assert result.full_name == TEST_FULL_NAME
        assert set(result.groups) == {"Domain Admins", "Enterprise Admins"}
        assert result.is_admin is True

    def test_ldap_config_defaults(self):
        """Test LDAPConfig with default values"""
        # Create config with only required parameters
        config = LDAPConfig(
            server_uri=TEST_CONFIG.server_uri,
            bind_dn=TEST_CONFIG.bind_dn,
            bind_password=TEST_CONFIG.bind_password,
            user_search_base=TEST_CONFIG.user_search_base,
            user_dn_template=TEST_CONFIG.user_dn_template
        )
        
        # Verify default values
        assert config.username_attribute == "uid"
        assert config.email_attribute == "mail"
        assert config.full_name_attribute == "cn"
        assert config.group_attribute == "memberOf"
        assert config.admin_groups == ["admins", "administrators"]
        assert config.use_ssl is False
        assert config.require_cert is False
        assert config.cert_file is None
        assert config.key_file is None
        assert config.ca_cert_file is None
        assert config.timeout == 5
        assert config.retries == 3
        assert config.page_size == 1000
        assert config.nested_groups is False
