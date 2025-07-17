#!/bin/bash

# Exit on error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="unit"
PARALLEL=true
COVERAGE=true
VERBOSE=false
KEEP_DB=false
ENV_FILE=".env.test"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --type)
      TEST_TYPE="$2"
      shift # past argument
      shift # past value
      ;;
    --sequential)
      PARALLEL=false
      shift # past argument
      ;;
    --no-cov)
      COVERAGE=false
      shift # past argument
      ;;
    --verbose|-v)
      VERBOSE=true
      shift # past argument
      ;;
    --keep-db)
      KEEP_DB=true
      shift # past argument
      ;;
    --env-file)
      ENV_FILE="$2"
      shift # past argument
      shift # past value
      ;;
    --help|-h)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --type TYPE          Type of tests to run (unit, integration, e2e, all). Default: unit"
      echo "  --sequential         Run tests sequentially instead of in parallel"
      echo "  --no-cov             Disable coverage reporting"
      echo "  --verbose, -v        Enable verbose output"
      echo "  --keep-db            Keep test database after running tests"
      echo "  --env-file FILE      Path to environment file. Default: .env.test"
      echo "  --help, -h           Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Set environment variables
if [ -f "$ENV_FILE" ]; then
  echo -e "${YELLOW}Loading environment variables from $ENV_FILE${NC}"
  export $(grep -v '^#' "$ENV_FILE" | xargs)
else
  echo -e "${YELLOW}No $ENV_FILE found, using default environment variables${NC}"
fi

# Set test paths based on test type
case $TEST_TYPE in
  unit)
    TEST_PATH="tests/unit"
    MARKERS="not integration and not e2e and not slow"
    ;;
  integration)
    TEST_PATH="tests/integration"
    MARKERS="integration and not e2e and not slow"
    ;;
  e2e)
    TEST_PATH="tests/e2e"
    MARKERS="e2e and not slow"
    ;;
  all)
    TEST_PATH="tests"
    MARKERS="not slow"
    ;;
  *)
    echo -e "${RED}Error: Unknown test type: $TEST_TYPE${NC}"
    exit 1
    ;;
esac

# Build the test command
CMD="pytest $TEST_PATH"

# Add markers if specified
if [ -n "$MARKERS" ]; then
  CMD="$CMD -m \"$MARKERS\""
fi

# Add parallel execution if enabled
if [ "$PARALLEL" = true ]; then
  CMD="$CMD -n auto"
fi

# Add coverage if enabled
if [ "$COVERAGE" = true ]; then
  CMD="$CMD --cov=app --cov-report=term-missing --cov-report=html:coverage_html --cov-report=xml:coverage.xml --cov-fail-under=80"
fi

# Add verbose output if enabled
if [ "$VERBOSE" = true ]; then
  CMD="$CMD -v"
fi

# Add JUnit XML output for CI
if [ -n "$CI" ]; then
  CMD="$CMD --junitxml=junit/test-results.xml"
fi

# Clean up test database if not keeping it
if [ "$KEEP_DB" = false ]; then
  trap 'rm -f test.db' EXIT
fi

# Print test configuration
echo -e "${GREEN}Running $TEST_TYPE tests${NC}"
echo -e "  Test path: $TEST_PATH"
echo -e "  Markers: ${MARKERS:-none}"
echo -e "  Parallel: $PARALLEL"
echo -e "  Coverage: $COVERAGE"
echo -e "  Verbose: $VERBOSE"
echo -e "  Keep DB: $KEEP_DB"
echo -e "  Environment: $ENV_FILE"

# Run the tests
echo -e "\n${YELLOW}Executing: $CMD${NC}\n"
eval $CMD

# Check test results
TEST_RESULT=$?
if [ $TEST_RESULT -eq 0 ]; then
  echo -e "\n${GREEN}All tests passed! 🎉${NC}"
else
  echo -e "\n${RED}Some tests failed. Check the output above for details.${NC}"
fi

exit $TEST_RESULT
