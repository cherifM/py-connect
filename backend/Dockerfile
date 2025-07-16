FROM python:3.10-slim

WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ./app ./app

# Expose the port the app runs on
EXPOSE 8000

# The command will be provided by docker-compose
