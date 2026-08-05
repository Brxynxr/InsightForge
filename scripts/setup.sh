#!/bin/bash
set -e

echo "Setting up PromptForge development environment..."

cd "$(dirname "$0")/.."

echo "Installing Poetry dependencies..."
poetry install

echo "Setting up environment files..."
cp backend/.env.example backend/.env

echo "Running database migrations..."
cd backend
poetry run alembic upgrade head
cd ..

echo "Setup complete!"
echo "Backend: cd backend && poetry run python -m app"
echo "Frontend: cd frontend && npm install && npm run dev"
