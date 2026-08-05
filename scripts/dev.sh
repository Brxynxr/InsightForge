#!/bin/bash
set -e

echo "Starting all services..."
docker compose up -d

echo "Services started!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "API Docs: http://localhost:8000/docs"
echo "Database: localhost:5432"
echo "Redis: localhost:6379"
