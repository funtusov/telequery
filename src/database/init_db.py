"""Database initialization script."""
import os
from .connection import create_tables, DATABASE_URL


def init_database():
    """Initialize the database with required tables."""
    print(f"Initializing database at: {DATABASE_URL}")
    
    # Ensure the directory exists
    db_path = DATABASE_URL.replace("sqlite:///", "")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Create tables
    create_tables()
    print("Database tables created successfully!")


if __name__ == "__main__":
    init_database()