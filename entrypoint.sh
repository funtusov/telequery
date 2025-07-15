#!/bin/bash

# Initialize the database
echo "Initializing database..."
python -c "from src.database.init_db import init_database; init_database()"
echo "Database initialization complete."

# Execute the command passed to the script
exec "$@"
