"""
Database migration script to add allergies and dietary_goals columns to users table
"""
import sqlite3
import os
import sys

# Set UTF-8 encoding for Windows compatibility
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Get the project directory
project_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(project_dir, "app.db")

print(f"Database path: {db_path}")

if not os.path.exists(db_path):
    print(f"WARNING: Database file {db_path} not found.")
    print("Creating new database with all tables...")
    try:
        from app.database import Base, engine
        from app import models
        Base.metadata.create_all(bind=engine)
        print("SUCCESS: New database created with all columns!")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: Error creating database: {e}")
        sys.exit(1)

print(f"Migrating existing database: {db_path}")

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Get existing columns
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Existing columns: {', '.join(columns)}")
    
    # Add allergies column if it doesn't exist
    if 'allergies' not in columns:
        print("\nAdding 'allergies' column...")
        cursor.execute("ALTER TABLE users ADD COLUMN allergies TEXT")
        print("SUCCESS: Added 'allergies' column")
    else:
        print("OK: 'allergies' column already exists")
    
    # Add dietary_goals column if it doesn't exist
    if 'dietary_goals' not in columns:
        print("Adding 'dietary_goals' column...")
        cursor.execute("ALTER TABLE users ADD COLUMN dietary_goals TEXT")
        print("SUCCESS: Added 'dietary_goals' column")
    else:
        print("OK: 'dietary_goals' column already exists")
    
    # Commit changes
    conn.commit()
    print("\nSUCCESS: Database migration completed successfully!")
    
    # Verify the migration
    cursor.execute("PRAGMA table_info(users)")
    updated_columns = [row[1] for row in cursor.fetchall()]
    print(f"\nUpdated columns: {', '.join(updated_columns)}")
    
except Exception as e:
    conn.rollback()
    print(f"\nERROR: Error during migration: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    conn.close()

