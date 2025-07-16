# Py-Connect

A modern web application for managing and deploying Python web applications with a user-friendly interface.

![Py-Connect Screenshot](https://via.placeholder.com/800x400?text=Py-Connect+Screenshot)

## Features

- 🚀 Deploy Python web applications (FastAPI, Streamlit, Shiny, etc.)
- 🎨 Modern, responsive web interface
- 🔄 Real-time application status updates
- 📦 Containerized deployment with Docker
- 🔒 Secure authentication and authorization
- 📊 Application monitoring and logging

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
   ./run.sh
   ```

3. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/api/docs

4. **Stop the application**
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

2. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Development

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
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

### Production

1. Build and start the application:
   ```bash
   docker-compose up --build -d
   ```

2. View logs:
   ```bash
   docker-compose logs -f
   ```

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Backend
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///app/pyconnect.db

# Frontend
VITE_API_URL=http://localhost:8000/api
```

## CI/CD

This project uses GitHub Actions for continuous integration and deployment. The workflow includes:

- Linting and type checking
- Unit and integration tests
- Docker image building and pushing
- Deployment to production (on main branch)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

Cherif - [@your_twitter](https://twitter.com/your_twitter)

Project Link: [https://github.com/cherifM/py-connect](https://github.com/cherifM/py-connect)
