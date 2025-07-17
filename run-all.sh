#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
MODE="local"  # local, docker, container
BACKEND_PORT=8000
FRONTEND_PORT=3000
SKIP_INSTALL=false
LDAP_ENABLED=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --docker)
      MODE="docker"
      shift
      ;;
    --container)
      MODE="container"
      shift
      ;;
    --skip-install)
      SKIP_INSTALL=true
      shift
      ;;
    --backend-port)
      BACKEND_PORT="$2"
      shift 2
      ;;
    --frontend-port)
      FRONTEND_PORT="$2"
      shift 2
      ;;
    --ldap)
      LDAP_ENABLED=true
      shift
      ;;
    *)
      echo "Unknown parameter: $1"
      exit 1
      ;;
  esac
done

# Print header
print_header() {
  echo -e "${GREEN}"
  echo "=================================================="
  echo "            Py-Connect Startup Script"
  echo "=================================================="
  echo -e "${NC}"
  echo -e "Mode: ${YELLOW}${MODE}${NC}"
  echo -e "Backend Port: ${YELLOW}${BACKEND_PORT}${NC}"
  echo -e "Frontend Port: ${YELLOW}${FRONTEND_PORT}${NC}"
  echo -e "LDAP Auth: ${YELLOW}${LDAP_ENABLED}${NC}"
  echo -e "${GREEN}==================================================${NC}"
}

# Check if command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Generate random secret key
generate_secret_key() {
  python3 -c "import secrets; print(secrets.token_urlsafe(32))"
}

# Setup Python virtual environment
setup_python_env() {
  echo -e "\n${GREEN}Setting up Python virtual environment...${NC}"
  if [ ! -d "venv" ]; then
    python3 -m venv venv
  fi
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r backend/requirements.txt
  if [ "$LDAP_ENABLED" = true ]; then
    pip install python-ldap django-auth-ldap
  fi
}

# Setup Node.js dependencies
setup_node_deps() {
  echo -e "\n${GREEN}Installing Node.js dependencies...${NC}"
  cd frontend
  npm install
  cd ..
}

# Initialize database
init_database() {
  echo -e "\n${GREEN}Initializing database...${NC}"
  cd backend
  if [ ! -f "pyconnect.db" ]; then
    python -c "from app.database import init_db; init_db()"
    echo -e "${YELLOW}Database initialized${NC}"
  else
    echo -e "${YELLOW}Database already exists, skipping initialization${NC}"
  fi
  cd ..
}

# Configure LDAP
configure_ldap() {
  if [ "$LDAP_ENABLED" = true ]; then
    echo -e "\n${GREEN}Configuring LDAP authentication...${NC}"
    # Create LDAP config if it doesn't exist
    if [ ! -f "backend/app/ldap_config.py" ]; then
      cat > backend/app/ldap_config.py <<EOL
# LDAP Configuration
LDAP_SERVER_URI = "ldap://your-ldap-server:389"
LDAP_BIND_DN = "cn=admin,dc=example,dc=com"
LDAP_BIND_PASSWORD = "your-ldap-password"
LDAP_USER_SEARCH_BASE = "ou=users,dc=example,dc=com"
LDAP_GROUP_SEARCH_BASE = "ou=groups,dc=example,dc=com"
LDAP_USER_DN_TEMPLATE = "uid=%(user)s,ou=users,dc=example,dc=com"
EOL
      echo -e "${YELLOW}LDAP configuration created. Please edit backend/app/ldap_config.py with your LDAP settings.${NC}"
    fi
  fi
}

# Start services based on mode
start_services() {
  case $MODE in
    "local")
      start_local_services
      ;;
    "docker")
      start_docker_services
      ;;
    "container")
      start_container_services
      ;;
  esac
}

# Start services in local mode
start_local_services() {
  echo -e "\n${GREEN}Starting services in local mode...${NC}"
  
  # Start backend
  echo -e "${YELLOW}Starting backend on port ${BACKEND_PORT}...${NC}"
  cd backend
  export PORT=$BACKEND_PORT
  if [ "$LDAP_ENABLED" = true ]; then
    export AUTH_METHOD="ldap"
  fi
  uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT &
  BACKEND_PID=$!
  cd ..

  # Start frontend
  echo -e "${YELLOW}Starting frontend on port ${FRONTEND_PORT}...${NC}"
  cd frontend
  export PORT=$FRONTEND_PORT
  export VITE_API_URL="http://localhost:${BACKEND_PORT}/api"
  npm run dev &
  FRONTEND_PID=$!
  cd ..

  # Wait for services to be ready
  wait_for_service "http://localhost:${BACKEND_PORT}/health" "Backend"
  wait_for_service "http://localhost:${FRONTEND_PORT}" "Frontend"

  echo -e "\n${GREEN}🎉 Py-Connect is now running!${NC}"
  echo -e "${YELLOW}Backend:${NC} http://localhost:${BACKEND_PORT}"
  echo -e "${YELLOW}Frontend:${NC} http://localhost:${FRONTEND_PORT}"
  echo -e "${YELLOW}API Docs:${NC} http://localhost:${BACKEND_PORT}/docs"
  echo -e "\n${YELLOW}Press Ctrl+C to stop all services${NC}"

  # Keep script running
  wait $BACKEND_PID $FRONTEND_PID
}

# Start services with Docker
start_docker_services() {
  echo -e "\n${GREEN}Starting services with Docker...${NC}"
  
  # Set environment variables
  export BACKEND_PORT=$BACKEND_PORT
  export FRONTEND_PORT=$FRONTEND_PORT
  
  if [ "$LDAP_ENABLED" = true ]; then
    export AUTH_METHOD="ldap"
  fi
  
  # Start services
  docker-compose up --build
}

# Start services with full container architecture
start_container_services() {
  echo -e "\n${GREEN}Starting services with full container architecture...${NC}"
  
  # Set environment variables
  export BACKEND_PORT=$BACKEND_PORT
  export FRONTEND_PORT=$FRONTEND_PORT
  
  if [ "$LDAP_ENABLED" = true ]; then
    export AUTH_METHOD="ldap"
  fi
  
  # Start services with docker-compose.override.yml if it exists
  if [ -f "docker-compose.override.yml" ]; then
    docker-compose -f docker-compose.yml -f docker-compose.override.yml up --build
  else
    docker-compose up --build
  fi
}

# Wait for a service to be available
wait_for_service() {
  local url=$1
  local service=$2
  local max_attempts=30
  local attempt=1

  echo -e "${YELLOW}Waiting for ${service} to be ready...${NC}"
  
  while [ $attempt -le $max_attempts ]; do
    if curl --output /dev/null --silent --head --fail "$url"; then
      echo -e "${GREEN}${service} is ready!${NC}"
      return 0
    fi
    
    echo -n "."
    attempt=$((attempt + 1))
    sleep 1
  done
  
  echo -e "\n${RED}Timed out waiting for ${service} to start${NC}"
  return 1
}

# Cleanup function
cleanup() {
  echo -e "\n${YELLOW}Shutting down services...${NC}"
  
  if [ -n "$BACKEND_PID" ]; then
    kill $BACKEND_PID 2>/dev/null
  fi
  
  if [ -n "$FRONTEND_PID" ]; then
    kill $FRONTEND_PID 2>/dev/null
  fi
  
  if [ "$MODE" = "docker" ] || [ "$MODE" = "container" ]; then
    docker-compose down
  fi
  
  echo -e "${GREEN}All services have been stopped.${NC}"
  exit 0
}

# Set up trap to catch Ctrl+C
trap cleanup INT TERM

# Main execution
main() {
  print_header
  
  if [ "$SKIP_INSTALL" = false ]; then
    setup_python_env
    setup_node_deps
    init_database
    configure_ldap
  fi
  
  start_services
}

# Run main function
main
