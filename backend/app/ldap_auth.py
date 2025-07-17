from typing import Optional, Dict, Any
import ldap
from ldap.filter import filter_format
from fastapi import HTTPException, status

class LDAPAuth:
    def __init__(self, config: Dict[str, Any]):
        self.ldap_server = config.get("LDAP_SERVER_URI", "ldap://localhost:389")
        self.bind_dn = config.get("LDAP_BIND_DN")
        self.bind_password = config.get("LDAP_BIND_PASSWORD")
        self.user_search_base = config.get("LDAP_USER_SEARCH_BASE")
        self.user_dn_template = config.get("LDAP_USER_DN_TEMPLATE")
        self.conn = None

    def connect(self):
        """Establish connection to LDAP server"""
        try:
            self.conn = ldap.initialize(self.ldap_server)
            self.conn.protocol_version = ldap.VERSION3
            self.conn.set_option(ldap.OPT_REFERRALS, 0)
            self.conn.simple_bind_s(self.bind_dn, self.bind_password)
            return True
        except ldap.LDAPError as e:
            print(f"LDAP Connection Error: {e}")
            return False

    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user against LDAP
        
        Args:
            username: The username to authenticate
            password: The password to verify
            
        Returns:
            Dict containing user info if authentication successful, None otherwise
        """
        if not self.connect():
            return None

        try:
            # Try to bind as the user
            user_dn = self.user_dn_template % {"user": username}
            self.conn.simple_bind_s(user_dn, password)
            
            # Search for user details
            search_filter = f"(uid={username})"
            result = self.conn.search_s(
                self.user_search_base,
                ldap.SCOPE_SUBTREE,
                search_filter,
                ['cn', 'mail', 'givenName', 'sn', 'uid', 'memberOf']
            )
            
            if not result:
                return None
                
            # Extract user attributes
            _, user_attrs = result[0]
            
            return {
                'username': username,
                'email': user_attrs.get('mail', [b''])[0].decode('utf-8'),
                'first_name': user_attrs.get('givenName', [b''])[0].decode('utf-8'),
                'last_name': user_attrs.get('sn', [b''])[0].decode('utf-8'),
                'is_active': True,
                'is_superuser': self._is_admin(user_attrs.get('memberOf', []))
            }
            
        except ldap.INVALID_CREDENTIALS:
            return None
        except Exception as e:
            print(f"LDAP Authentication Error: {e}")
            return None
        finally:
            if self.conn:
                self.conn.unbind()
    
    def _is_admin(self, member_of: list) -> bool:
        """Check if user is in admin group"""
        if not member_of:
            return False
            
        admin_groups = [b'cn=admins,ou=groups,dc=example,dc=com']
        return any(group in admin_groups for group in member_of)

# Example usage:
if __name__ == "__main__":
    config = {
        "LDAP_SERVER_URI": "ldap://localhost:389",
        "LDAP_BIND_DN": "cn=admin,dc=example,dc=com",
        "LDAP_BIND_PASSWORD": "admin",
        "LDAP_USER_SEARCH_BASE": "ou=users,dc=example,dc=com",
        "LDAP_USER_DN_TEMPLATE": "uid=%(user)s,ou=users,dc=example,dc=com"
    }
    
    ldap_auth = LDAPAuth(config)
    user = ldap_auth.authenticate("testuser", "password")
    print(f"Authentication successful: {user is not None}")
    if user:
        print(f"User details: {user}")
