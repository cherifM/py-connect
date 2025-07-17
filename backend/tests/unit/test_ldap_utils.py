import pytest
import ldap
from unittest.mock import patch, MagicMock
from app.ldap_auth import LDAPAuth, LDAPConfig, LDAPUser

# Test configuration
TEST_CONFIG = LDAPConfig(
    server_uri="ldap://test-ldap:389",
    bind_dn="cn=admin,dc=example,dc=com",
    bind_password="adminpassword",
    user_search_base="ou=users,dc=example,dc=com",
    user_dn_template="uid={username},ou=users,dc=example,dc=com"
)

# Test data
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpassword"
TEST_EMAIL = "test@example.com"
TEST_FULL_NAME = "Test User"

# Mock LDAP response data
MOCK_LDAP_ATTRS = {
    'uid': [TEST_USERNAME.encode()],
    'cn': [TEST_FULL_NAME.encode()],
    'mail': [TEST_EMAIL.encode()],
    'memberOf': [
        b'cn=users,ou=groups,dc=example,dc=com',
        b'cn=admins,ou=groups,dc=example,dc=com'
    ]
}

class TestLDAPAuthUtils:
    @patch('ldap.initialize')
    def test_extract_username_from_dn(self, mock_ldap_init):
        """Test extracting username from DN"""
        ldap_auth = LDAPAuth(TEST_CONFIG)
        
        # Test standard DN format
        dn = f"uid={TEST_USERNAME},ou=users,dc=example,dc=com"
        assert ldap_auth._extract_username(dn) == TEST_USERNAME
        
        # Test with different attribute name
        dn = f"cn={TEST_USERNAME},ou=users,dc=example,dc=com"
        assert ldap_auth._extract_username(dn) == TEST_USERNAME
        
        # Test with escaped characters
        dn = "uid=test\,user,ou=users,dc=example,dc=com"
        assert ldap_auth._extract_username(dn) == "test,user"
        
        # Test invalid DN
        assert ldap_auth._extract_username("invalid-dn") == "invalid-dn"
    
    @patch('ldap.initialize')
    def test_extract_group_name(self, mock_ldap_init):
        """Test extracting group name from DN"""
        ldap_auth = LDAPAuth(TEST_CONFIG)
        
        # Test standard group DN
        group_dn = "cn=admins,ou=groups,dc=example,dc=com"
        assert ldap_auth._extract_group_name(group_dn) == "admins"
        
        # Test with different DN format
        group_dn = "ou=developers,dc=example,dc=com"
        assert ldap_auth._extract_group_name(group_dn) == "developers"
        
        # Test with escaped characters
        group_dn = "cn=domain\, admins,ou=groups,dc=example,dc=com"
        assert ldap_auth._extract_group_name(group_dn) == "domain, admins"
        
        # Test invalid DN
        assert ldap_auth._extract_group_name("invalid-dn") == "invalid-dn"
    
    @patch('ldap.initialize')
    def test_is_admin_user(self, mock_ldap_init):
        """Test admin user detection"""
        # Test with default admin groups
        ldap_auth = LDAPAuth(TEST_CONFIG)
        
        # User with admin group
        admin_user = LDAPUser(
            username=TEST_USERNAME,
            email=TEST_EMAIL,
            groups=["users", "admins"]
        )
        assert ldap_auth._is_admin_user(admin_user) is True
        
        # User without admin group
        regular_user = LDAPUser(
            username=TEST_USERNAME,
            email=TEST_EMAIL,
            groups=["users"]
        )
        assert ldap_auth._is_admin_user(regular_user) is False
        
        # Test with custom admin groups
        custom_config = LDAPConfig(
            **{**TEST_CONFIG.dict(), "admin_groups": ["superusers"]}
        )
        ldap_auth = LDAPAuth(custom_config)
        
        # User with custom admin group
        custom_admin = LDAPUser(
            username=TEST_USERNAME,
            email=TEST_EMAIL,
            groups=["users", "superusers"]
        )
        assert ldap_auth._is_admin_user(custom_admin) is True
    
    @patch('ldap.initialize')
    def test_extract_user_info(self, mock_ldap_init):
        """Test extracting user info from LDAP attributes"""
        ldap_auth = LDAPAuth(TEST_CONFIG)
        
        # Test standard attributes
        user_info = ldap_auth._extract_user_info(TEST_USERNAME, MOCK_LDAP_ATTRS)
        
        assert user_info.username == TEST_USERNAME
        assert user_info.email == TEST_EMAIL
        assert user_info.full_name == TEST_FULL_NAME
        assert set(user_info.groups) == {"users", "admins"}
        assert user_info.is_admin is True
        
        # Test with missing optional attributes
        minimal_attrs = {
            'uid': [TEST_USERNAME.encode()],
            'mail': [TEST_EMAIL.encode()]
        }
        user_info = ldap_auth._extract_user_info(TEST_USERNAME, minimal_attrs)
        
        assert user_info.username == TEST_USERNAME
        assert user_info.email == TEST_EMAIL
        assert user_info.full_name == TEST_USERNAME  # Falls back to username
        assert user_info.groups == []
        assert user_info.is_admin is False
    
    @patch('ldap.initialize')
    def test_extract_user_info_custom_attrs(self, mock_ldap_init):
        """Test extracting user info with custom attribute mappings"""
        # Create config with custom attribute mappings
        custom_config = LDAPConfig(
            **{
                **TEST_CONFIG.dict(),
                "username_attribute": "sAMAccountName",
                "email_attribute": "userPrincipalName",
                "full_name_attribute": "displayName",
                "group_attribute": "memberOf"
            }
        )
        
        ldap_auth = LDAPAuth(custom_config)
        
        # Test with custom attributes
        custom_attrs = {
            'sAMAccountName': [TEST_USERNAME.encode()],
            'userPrincipalName': [TEST_EMAIL.encode()],
            'displayName': [TEST_FULL_NAME.encode()],
            'memberOf': [
                b'CN=Domain Admins,CN=Users,DC=example,DC=com',
                b'CN=Users,DC=example,DC=com'
            ]
        }
        
        user_info = ldap_auth._extract_user_info(TEST_USERNAME, custom_attrs)
        
        assert user_info.username == TEST_USERNAME
        assert user_info.email == TEST_EMAIL
        assert user_info.full_name == TEST_FULL_NAME
        assert set(user_info.groups) == {"Domain Admins", "Users"}
        assert user_info.is_admin is True  # Because of Domain Admins group
