import sqlite3
import shutil
import os
from app.models import Base

# Use absolute path relative to this script's location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "appointments.db")
BACKUP_PATH = os.path.join(BASE_DIR, "appointments.db.bak")

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    print(f"Backing up database to {BACKUP_PATH}...")
    shutil.copy2(DB_PATH, BACKUP_PATH)

    # We will use a temporary database to migrate data
    TEMP_DB = os.path.join(BASE_DIR, "appointments_temp.db")

    # Create new schema in temporary DB
    from app.db import engine
    import sqlalchemy
    temp_engine = sqlalchemy.create_engine(f"sqlite:///{TEMP_DB}")
    Base.metadata.create_all(temp_engine)

    # Connect to both databases
    old_conn = sqlite3.connect(DB_PATH)
    new_conn = sqlite3.connect(TEMP_DB)

    try:
        # Migrate Companies
        print("Migrating companies...")
        companies = old_conn.execute("SELECT id, name, logo_url, brand_color, description FROM companies").fetchall()
        for c in companies:
            new_conn.execute(
                "INSERT INTO companies (id, name, logo_url, brand_color, description, subscription_tier, custom_domain) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (c[0], c[1], c[2], c[3], c[4], "starter", None)
            )

        # Migrate Users
        print("Migrating users...")
        users = old_conn.execute("SELECT id, email, hashed_password, role, company_id FROM users").fetchall()
        for u in users:
            new_conn.execute(
                "INSERT INTO users (id, email, hashed_password, role, company_id) VALUES (?, ?, ?, ?, ?)",
                (u[0], u[1], u[2], u[3], u[4])
            )

        # Migrate Appointments
        print("Migrating appointments...")
        appointments = old_conn.execute("SELECT id, customer_id, company_id, appointment_time, notes FROM appointments").fetchall()
        for a in appointments:
            new_conn.execute(
                "INSERT INTO appointments (id, customer_id, company_id, appointment_time, notes) VALUES (?, ?, ?, ?, ?)",
                (a[0], a[1], a[2], a[3], a[4])
            )

        new_conn.commit()
    except Exception as e:
        print(f"Migration failed: {e}")
        return
    finally:
        old_conn.close()
        new_conn.close()

    # Ensure connections are fully closed before moving files
    try:
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        os.rename(TEMP_DB, DB_PATH)
    except PermissionError as e:
        print(f"Permission error during file swap: {e}")
        print("Trying to move file using shutil.move...")
        shutil.move(TEMP_DB, DB_PATH)

    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
