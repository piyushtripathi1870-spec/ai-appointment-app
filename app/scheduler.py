import os

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .ai_engine import AIEngine
from .models import Appointment
from datetime import datetime

class AppointmentScheduler:
    def __init__(self):
        self.ai = AIEngine(
            model=os.getenv("OLLAMA_MODEL", "gemma4"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )

    def process_request(self, db: Session, user_text: str, customer_id: int, company_id: str):
        """
        Main pipeline: User Text -> AI Extraction -> DB Check -> Result
        """
        # 1. Extract details using AI
        details = self.ai.extract_appointment_details(user_text)

        if not details or not details.get('date') or not details.get('time'):
            return "I'm sorry, I couldn't quite catch the date and time. Could you please tell me when you'd like the appointment?"

        name = details.get('name', 'Unknown Guest')
        date = details.get('date')
        time = details.get('time')

        # Convert string date/time to python datetime object
        try:
            appointment_timestamp = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        except ValueError:
            return "The date or time format provided by the AI was invalid. Please try again."

        # 2. Attempt to book it immediately (Rely on DB UniqueConstraint for atomicity)
        try:
            new_appt = Appointment(
                customer_id=customer_id,
                company_id=company_id,
                appointment_time=appointment_timestamp,
                notes=f"Booked via AI for {name}"
            )
            db.add(new_appt)
            db.commit()
            return f"Great news, {name}! Your appointment is confirmed for {date} at {time}."
        except IntegrityError:
            db.rollback()
            return f"I'm sorry, the slot for {date} at {time} is already taken for this service. Could you suggest another time?"
        except Exception as e:
            db.rollback()
            return f"I ran into a technical issue while saving your booking: {e}"

    def list_appointments(self, db: Session, company_id: str = None, customer_id: int = None):
        """Returns a list of appointments as objects."""
        query = db.query(Appointment)

        if company_id:
            query = query.filter(Appointment.company_id == company_id)
        elif customer_id:
            query = query.filter(Appointment.customer_id == customer_id)
        else:
            return []

        appointments = query.order_by(Appointment.appointment_time.asc()).all()

        # Return a list of dictionaries for JSON serialization
        return [
            {
                "id": appt.id,
                "time": appt.appointment_time.strftime("%Y-%m-%d %H:%M"),
                "notes": appt.notes,
                "customer": appt.customer.email if appt.customer else "Unknown"
            }
            for appt in appointments
        ]
