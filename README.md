# Py-Connect

A modern web application for managing and deploying Python web applications with a user-friendly interface. Supports both local and LDAP authentication.

![Py-Connect Screenshot](https://via.placeholder.com/800x400?text=Py-Connect+Screenshot)

## Features

- 🚀 Deploy Python web applications (FastAPI, Streamlit, Shiny, etc.)
- 🎨 Modern, responsive web interface
- 🔄 Real-time application status updates
- 📦 Containerized deployment with Docker
- 🔒 Secure authentication with JWT tokens
  - Local user database
  - LDAP/Active Directory integration
  - Role-based access control
- 🔄 Automatic HTTPS with Let's Encrypt
- 📊 Application monitoring and logging
- 🔄 WebSocket support for real-time updates
- 🔄 Background task processing

## Prerequisites

- Docker and Docker Compose
- Git
- Node.js 16+ (for local frontend development)
- Python 3.10+ (for local backend development)

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/cherifM/py-connect.git
   cd py-connect
   ```

2. **Start the application**
   ```bash
   # Basic start (local development)
   ./run-all.sh
   
   # Start with Docker
   ./run-all.sh --docker
   
   # Start with full container architecture
   ./run-all.sh --container
   
   # Start with custom ports
   ./run-all.sh --backend-port 8080 --frontend-port 3001
   
   # Start with LDAP authentication
   ./run-all.sh --ldap
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/api/docs
   - LDAP Admin (if enabled): http://localhost:8080
     - Login DN: cn=admin,dc=example,dc=com
     - Password: admin

4. **Default Admin User**
   - Username: admin
   - Password: admin

5. **Stop the application**
   ```bash
   ./stop.sh
   ```

## Project Structure

```
py-connect/
├── backend/              # FastAPI backend
│   ├── app/             # Application code
│   ├── tests/           # Backend tests
│   ├── Dockerfile       # Backend Dockerfile
│   └── requirements.txt # Python dependencies
├── frontend/            # React frontend
│   ├── src/             # Source code
│   ├── public/          # Static files
│   └── Dockerfile       # Frontend Dockerfile
├── docker-compose.yml   # Docker Compose configuration
├── run.sh               # Start script
└── stop.sh              # Stop script
```

## Development

### Backend Development

1. Set up a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt -r test-requirements.txt
   ```

2. Create a `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Run the development server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Development

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   VITE_API_URL=http://localhost:8000/api npm run dev
   ```

## Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Deployment

### Production with Docker Compose

1. Copy the example environment file:
   ```bash
   cp backend/.env.example .env
   # Edit .env with your production settings
   ```

2. Start the application:
   ```bash
   # For production with Let's Encrypt
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   
   # For development with hot-reload
   docker-compose up --build
   ```

3. View logs:
   ```bash
   docker-compose logs -f
   ```

### Kubernetes Deployment

1. Create a Kubernetes secret for environment variables:
   ```bash
   kubectl create secret generic py-connect-secrets --from-env-file=backend/.env
   ```

2. Deploy the application:
   ```bash
   kubectl apply -f k8s/
   ```

3. Access the application:
   ```bash
   kubectl port-forward svc/py-connect-frontend 3000:80
   ```

### Environment Variables

Create a `.env` file in the backend directory with the following variables:

```env
# Application
ENVIRONMENT=production
SECRET_KEY=generate-a-secure-secret-key

# Database
DATABASE_URL=postgresql://user:password@db:5432/pyconnect

# CORS
CORS_ORIGINS=https://your-domain.com,http://localhost:3000

# Authentication
AUTH_METHOD=ldap  # or 'local'

# LDAP Configuration (if AUTH_METHOD=ldap)
LDAP_SERVER_URI=ldap://ldap.example.com:389
LDAP_BIND_DN=cn=admin,dc=example,dc=com
LDAP_BIND_PASSWORD=your-ldap-password
LDAP_USER_SEARCH_BASE=ou=users,dc=example,dc=com
LDAP_USER_DN_TEMPLATE=uid=%(user)s,ou=users,dc=example,dc=com

# Session
SESSION_SECRET=generate-a-secure-session-secret
SESSION_LIFETIME=3600

# Frontend
VITE_API_URL=/api
```

## CI/CD

This project uses GitHub Actions for continuous integration and deployment. The workflow includes:

- Linting and type checking
- Unit and integration tests
- Docker image building and pushing
- Deployment to production (on main branch)

## API Documentation

Once the application is running, you can access the following endpoints:

- `GET /api/docs` - Interactive API documentation (Swagger UI)
- `GET /api/redoc` - Alternative API documentation (ReDoc)
- `POST /api/token` - Obtain an access token
- `GET /api/me` - Get current user information
- `GET /api/health` - Health check endpoint

### Example API Requests

**Login**
```bash
curl -X POST "http://localhost:8000/api/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"
```

**Get Current User**
```bash
curl -X GET "http://localhost:8000/api/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup

1. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

2. Run tests:
   ```bash
   cd backend
   pytest
   ```

3. Run linters:
   ```bash
   # Backend
   black .
   isort .
   flake8
   mypy .
   
   # Frontend
   cd frontend
   npm run lint
   ```

## Monitoring and Logging

### Prometheus Metrics
Metrics are available at `/metrics` when running in production mode.

### Logging
Logs are written to `logs/app.log` in JSON format for easy parsing by log aggregators.

## Security

### Reporting Security Issues
Please report security issues to security@example.com. We appreciate your help in making Py-Connect secure.

### Best Practices
- Always use HTTPS in production
- Rotate your SECRET_KEY and SESSION_SECRET regularly
- Use strong passwords for all accounts
- Keep your dependencies up to date
- Follow the principle of least privilege

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

Cherif - [@your_twitter](https://twitter.com/your_twitter)

Project Link: [https://github.com/cherifM/py-connect](https://github.com/cherifM/py-connect)

## Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/) - The web framework used
- [React](https://reactjs.org/) - Frontend library
- [Docker](https://www.docker.com/) - Container platform
- [LDAP](https://ldap.com/) - Lightweight Directory Access Protocol
