import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def reset_expansion_database():
    """
    Resets the expansion database by deleting the database file.
    """
    load_dotenv()
    
    # Get the path to the expansion database from environment variables
    # Default to the same path used in the expansion_service
    expansion_db_path = os.getenv("EXPANSION_DB_PATH", "./data/telequery_expansions.db")
    
    # Get the absolute path
    db_abs_path = os.path.abspath(expansion_db_path)
    
    if os.path.exists(db_abs_path):
        try:
            os.remove(db_abs_path)
            print(f"✅ Successfully deleted expansion database: {db_abs_path}")
        except OSError as e:
            print(f"❌ Error deleting file: {db_abs_path}")
            print(f"   Reason: {e}")
    else:
        print(f"ℹ️ Expansion database not found at: {db_abs_path}")
        print("   Nothing to do.")

if __name__ == "__main__":
    # Ask for confirmation before proceeding
    print("⚠️ This script will delete the message expansion database.")
    print("   The database will be recreated on the next application run.")
    
    confirm = input("   Are you sure you want to continue? (y/n): ")
    
    if confirm.lower() == 'y':
        reset_expansion_database()
    else:
        print("🚫 Operation cancelled.")
