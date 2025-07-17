# Py-Connect Test Suite

This directory contains the test suite for the Py-Connect application. The tests are organized into different categories to ensure comprehensive coverage of the application's functionality.

## Test Structure

```
tests/
├── integration/           # Integration tests
│   ├── __init__.py
│   ├── test_auth_endpoints.py  # Authentication endpoint tests
│   ├── test_endpoints.py       # General API endpoint tests
│   └── test_ldap_endpoints.py  # LDAP-specific endpoint tests
├── unit/                  # Unit tests
│   ├── __init__.py
│   ├── test_auth.py       # Authentication unit tests
│   ├── test_ldap_auth.py  # LDAP authentication tests
│   ├── test_ldap_config.py # LDAP configuration tests
│   ├── test_ldap_utils.py  # LDAP utility function tests
│   ├── test_models.py     # Database model tests
│   └── test_services.py   # Service layer tests
├── conftest.py           # Pytest fixtures and configuration
└── README.md             # This file
```

## Running Tests

### Prerequisites

1. Install the test requirements:
   ```bash
   pip install -r test-requirements.txt
   ```

2. Ensure you have Python 3.8+ installed.

### Running All Tests

To run all tests with coverage:

```bash
# From the backend directory
pytest --cov=app --cov-report=term-missing
```

### Running Specific Test Categories

Run unit tests only:
```bash
pytest tests/unit/
```

Run integration tests only:
```bash
pytest tests/integration/
```

Run a specific test file:
```bash
pytest tests/unit/test_ldap_auth.py
```

Run a specific test function:
```bash
pytest tests/unit/test_ldap_auth.py::TestLDAPAuth::test_authenticate_success
```

### Test Coverage

To generate an HTML coverage report:

```bash
pytest --cov=app --cov-report=html
```

Open `htmlcov/index.html` in your browser to view the coverage report.

## Test Configuration

Test configuration is handled through:

- `pytest.ini`: Main pytest configuration
- `conftest.py`: Fixtures and test configuration
- `.env.test`: Test environment variables

## Writing Tests

### Unit Tests

Unit tests should:
- Test individual functions or methods in isolation
- Mock external dependencies
- Be fast and independent
- Follow the naming convention `test_*.py`

### Integration Tests

Integration tests should:
- Test interactions between components
- Use the test database
- Test API endpoints with the test client
- Be placed in the `integration/` directory

### Fixtures

Common test fixtures are defined in `conftest.py`. Available fixtures include:

- `db_session`: Database session with transaction rollback
- `client`: Test client for making HTTP requests
- `test_user`: A regular test user
- `admin_user`: An admin test user
- `auth_headers`: Authentication headers for the test user
- `admin_auth_headers`: Authentication headers for the admin user
- `mock_ldap_auth`: Mock LDAP authentication
- `ldap_client`: Test client with LDAP support

## Continuous Integration

Tests are automatically run on pull requests and merges to the main branch. The CI pipeline includes:

1. Unit tests
2. Integration tests
3. Code coverage reporting
4. Code style checks (flake8, black, isort)
5. Type checking (mypy)

## Debugging Tests

To debug a failing test:

1. Run the test with `-v` for verbose output:
   ```bash
   pytest -v tests/unit/test_example.py::test_function
   ```

2. Use `pdb` for interactive debugging:
   ```bash
   pytest --pdb tests/unit/test_example.py::test_function
   ```

3. Add print statements or use logging:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

## Best Practices

- Write small, focused tests
- Use descriptive test names
- Test edge cases and error conditions
- Keep tests independent and idempotent
- Mock external services
- Avoid testing implementation details
- Keep test data isolated
- Clean up after tests

## License

This test suite is part of the Py-Connect project and is licensed under the same terms.
