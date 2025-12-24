#!/bin/bash
set -e

# Initialize database if it doesn't exist
if [ ! -f /app/database/pharmacy.db ]; then
    echo "Initializing database..."
    cd /app/database
    python init_db.py
    cd /app/backend
else
    echo "Database already exists, skipping initialization..."
fi

# Execute the main command (uvicorn)
exec "$@"
