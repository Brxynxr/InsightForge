#!/bin/bash
set -e

echo "Starting PostgreSQL and Redis containers..."
docker compose -f docker/docker-compose.yml up db redis -d

echo "Waiting for services to be ready..."
sleep 5

echo "Starting all services..."
docker compose -f docker/docker-compose.yml up -d

echo "Services started!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "API Docs: http://localhost:8000/docs"
echo "Database: localhost:5432"
echo "Redis: localhost:6379"
