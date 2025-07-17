import pytest
from pydantic import ValidationError
from app.ldap_auth import LDAPConfig, LDAPUser

def test_ldap_config_defaults():
    """Test LDAPConfig with default values"""
    config = LDAPConfig(
        server_uri="ldap://localhost:389",
        bind_dn="cn=admin,dc=example,dc=com",
        bind_password="adminpassword",
        user_search_base="ou=users,dc=example,dc=com",
        user_dn_template="uid={username},ou=users,dc=example,dc=com"
    )
    
    # Check default values
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

def test_ldap_config_validation():
    """Test LDAPConfig validation"""
    # Test valid configuration
    valid_config = {
        "server_uri": "ldap://localhost:389",
        "bind_dn": "cn=admin,dc=example,dc=com",
        "bind_password": "adminpassword",
        "user_search_base": "ou=users,dc=example,dc=com",
        "user_dn_template": "uid={username},ou=users,dc=example,dc=com"
    }
    
    config = LDAPConfig(**valid_config)
    assert config.server_uri == "ldap://localhost:389"
    
    # Test missing required fields
    with pytest.raises(ValidationError):
        LDAPConfig()  # Missing all required fields
    
    # Test invalid URL
    with pytest.raises(ValidationError):
        LDAPConfig(**{**valid_config, "server_uri": "invalid-url"})
    
    # Test invalid port
    with pytest.raises(ValidationError):
        LDAPConfig(**{**valid_config, "server_uri": "ldap://localhost:999999"})

class TestLDAPUser:
    def test_ldap_user_creation(self):
        """Test LDAPUser model creation"""
        user = LDAPUser(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            groups=["users", "developers"],
            is_admin=False
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert set(user.groups) == {"users", "developers"}
        assert user.is_admin is False
    
    def test_ldap_user_defaults(self):
        """Test LDAPUser default values"""
        user = LDAPUser(
            username="testuser",
            email="test@example.com"
        )
        
        assert user.full_name == "testuser"
        assert user.groups == []
        assert user.is_admin is False
    
    def test_ldap_user_validation(self):
        """Test LDAPUser validation"""
        # Test valid user
        valid_user = {
            "username": "testuser",
            "email": "test@example.com"
        }
        user = LDAPUser(**valid_user)
        assert user.username == "testuser"
        
        # Test missing required fields
        with pytest.raises(ValueError):
            LDAPUser(username="testuser")  # Missing email
        
        with pytest.raises(ValueError):
            LDAPUser(email="test@example.com")  # Missing username
        
        # Test invalid email
        with pytest.raises(ValueError):
            LDAPUser(username="testuser", email="invalid-email")
    
    def test_ldap_user_has_group(self):
        """Test LDAPUser group membership"""
        user = LDAPUser(
            username="testuser",
            email="test@example.com",
            groups=["users", "developers"]
        )
        
        assert user.has_group("users") is True
        assert user.has_group("developers") is True
        assert user.has_group("admins") is False
        assert user.has_group("AdMiNs") is False  # Case-sensitive by default
        
        # Test case-insensitive matching
        assert user.has_group("USERS", case_sensitive=False) is True
        
        # Test with different group formats
        user_with_dn = LDAPUser(
            username="testuser",
            email="test@example.com",
            groups=["cn=Domain Admins,ou=groups,dc=example,dc=com"]
        )
        
        assert user_with_dn.has_group("Domain Admins") is True
        assert user_with_dn.has_group("domain admins", case_sensitive=False) is True
        assert user_with_dn.has_group("cn=Domain Admins,ou=groups,dc=example,dc=com") is True
