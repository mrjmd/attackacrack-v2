#!/bin/sh

# Exit on error
set -e

echo "Starting Attack-a-Crack v2 Backend..."

# Wait for database to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z ${DB_HOST:-db} ${DB_PORT:-5432}; do
    sleep 1
done
echo "PostgreSQL is ready!"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head || echo "No migrations to run or Alembic not configured yet"

# Start the FastAPI application with Uvicorn
echo "Starting Uvicorn server..."
if [ "${ENVIRONMENT}" = "development" ] || [ "${DEBUG}" = "true" ]; then
    echo "Running in development mode with hot-reload..."
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload \
        --reload-dir /app \
        --log-level ${LOG_LEVEL:-info} \
        --access-log
else
    echo "Running in production mode..."
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers ${WORKERS:-4} \
        --log-level ${LOG_LEVEL:-info} \
        --access-log
fi