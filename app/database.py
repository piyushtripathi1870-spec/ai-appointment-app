import sqlite3
from datetime import datetime

class AppointmentDB:
    def __init__(self, db_path="appointments.db"):
        self.db_path = db_path
        self._create_table()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        """Creates the appointments table if it doesn't exist."""
        query = """
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            appointment_time DATETIME NOT NULL,
            notes TEXT,
            UNIQUE(appointment_time)
        );
        """
        with self._get_connection() as conn:
            conn.execute(query)

    def add_appointment(self, name, time_str, notes=""):
        """Adds an appointment. Raises sqlite3.IntegrityError if time is taken."""
        query = "INSERT INTO appointments (customer_name, appointment_time, notes) VALUES (?, ?, ?)"
        with self._get_connection() as conn:
            conn.execute(query, (name, time_str, notes))
            conn.commit()

    def check_availability(self, time_str):
        """Returns True if the time slot is available."""
        query = "SELECT 1 FROM appointments WHERE appointment_time = ?"
        with self._get_connection() as conn:
            cursor = conn.execute(query, (time_str,))
            return cursor.fetchone() is None

    def get_all_appointments(self):
        """Returns a list of all scheduled appointments."""
        query = "SELECT * FROM appointments ORDER BY appointment_time ASC"
        with self._get_connection() as conn:
            return conn.execute(query).fetchall()
