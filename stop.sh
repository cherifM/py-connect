#!/bin/bash

# Colors for output
RED='\033[0;31m'
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${RED}Stopping Py-Connect Application...${NC}"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to safely kill a process if it exists
safe_kill() {
    local pid=$1
    local name=$2
    if [ -n "$pid" ] && ps -p $pid > /dev/null; then
        echo -e "${BLUE}Stopping $name (PID: $pid)...${NC}"
        kill $pid
        echo -e "${RED}$name stopped${NC}"
        return 0
    fi
    echo -e "${BLUE}No $name process found${NC}"
    return 1
}

# Stop backend if running
if [ -f "/tmp/backend.pid" ]; then
    BACKEND_PID=$(cat /tmp/backend.pid)
    safe_kill $BACKEND_PID "Backend"
    rm -f /tmp/backend.pid
else
    echo -e "${BLUE}No backend PID file found${NC}"
fi

# Stop frontend (look for Vite process on port 5173)
FRONTEND_PID=$(lsof -ti:5173 -sTCP:LISTEN)
if [ -n "$FRONTEND_PID" ]; then
    safe_kill $FRONTEND_PID "Frontend"
else
    echo -e "${BLUE}No frontend process found on port 5173${NC}"
fi

# Stop Docker Compose services if docker-compose.yml exists
if [ -f "docker-compose.yml" ] || [ -f "docker-compose.yaml" ] || [ -f "docker-compose.override.yml" ] || [ -f "docker-compose.override.yaml" ]; then
    # Determine the correct docker-compose command
    if command_exists docker-compose; then
        DOCKER_COMPOSE_CMD="docker-compose"
    elif command_exists docker && docker compose version >/dev/null 2>&1; then
        DOCKER_COMPOSE_CMD="docker compose"
    else
        echo -e "${YELLOW}Warning: docker-compose or 'docker compose' not found. Trying to stop containers directly...${NC}"
        DOCKER_COMPOSE_CMD=""
    fi

    if [ -n "$DOCKER_COMPOSE_CMD" ]; then
        echo -e "${BLUE}Stopping and removing containers...${NC}"
        $DOCKER_COMPOSE_CMD down --remove-orphans
        
        # Check if there are any remaining containers
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ All containers stopped and removed${NC}"
        else
            echo -e "${YELLOW}Warning: Failed to stop some containers. Trying force removal...${NC}"
            $DOCKER_COMPOSE_CMD down --remove-orphans --rmi local --volumes --remove-orphans
        fi
    fi

    # Additional check for any remaining containers
    RUNNING_CONTAINERS=$(docker ps -a -q --filter "name=py-connect" 2>/dev/null)
    if [ -n "$RUNNING_CONTAINERS" ]; then
        echo -e "${YELLOW}Removing any remaining containers...${NC}"
        docker stop $RUNNING_CONTAINERS 2>/dev/null
        docker rm $RUNNING_CONTAINERS 2>/dev/null
    fi

    # Clean up unused resources
    echo -e "${BLUE}Cleaning up Docker resources...${NC}"
    docker system prune -f --volumes >/dev/null
else
    echo -e "${YELLOW}No docker-compose.yml file found. No containers to stop.${NC}"
fi

# Clean up any temporary files
rm -f /tmp/backend.pid /tmp/frontend.pid 2>/dev/null

# Check if ports are still in use
check_port() {
    local port=$1
    local service=$2
    if lsof -i ":${port}" >/dev/null 2>&1; then
        echo -e "${YELLOW}Warning: Port ${port} is still in use by another process${NC}"
        echo -e "  Run 'sudo lsof -i :${port}' to identify the process"
        echo -e "  or 'kill -9 \$(lsof -t -i:${port})' to force stop it"
    fi
}

check_port 5173 "Frontend"
check_port 8000 "Backend"

echo -e "\n${GREEN}✓ Py-Connect has been stopped and cleaned up${NC}"
echo -e "${BLUE}Note:${NC} Run './run.sh' to start the application again"
