#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Docker is running
docker_running() {
    docker info >/dev/null 2>&1
    return $?
}

echo -e "${GREEN}Starting Py-Connect with Docker Compose...${NC}"

# Check if Docker is installed and running
if ! command_exists docker; then
    echo -e "${RED}Error: Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! docker_running; then
    echo -e "${RED}Error: Docker daemon is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if docker-compose is installed
if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
    echo -e "${RED}Error: Docker Compose is not installed. Please install Docker Compose.${NC}"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Start services with docker-compose
if command_exists docker-compose; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    DOCKER_COMPOSE_CMD="docker compose"
fi

# Build and start containers in detached mode
echo -e "${BLUE}Building and starting containers...${NC}"
$DOCKER_COMPOSE_CMD up --build -d

# Check if containers started successfully
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to start containers. Check the logs above for errors.${NC}"
    exit 1
fi

# Show container status
echo -e "\n${GREEN}Containers status:${NC}"
$DOCKER_COMPOSE_CMD ps

# Get the frontend URL
FRONTEND_URL="http://localhost:5173"
BACKEND_URL="http://localhost:8000"

# Open the application in the default browser
echo -e "\n${GREEN}Py-Connect is now running!${NC}"
echo -e "- Frontend: ${BLUE}${FRONTEND_URL}${NC}"
echo -e "- Backend API: ${BLUE}${BACKEND_URL}${NC}"
echo -e "- API Documentation: ${BLUE}${BACKEND_URL}/api/docs${NC}"
echo -e "\n${YELLOW}To stop the application, run: ./stop.sh${NC}"

# Try to open the frontend in the default browser
if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "${FRONTEND_URL}" &
elif command -v open >/dev/null 2>&1; then
    open "${FRONTEND_URL}" &
fi

echo -e "\n${BLUE}View logs with: docker-compose logs -f${NC}"
