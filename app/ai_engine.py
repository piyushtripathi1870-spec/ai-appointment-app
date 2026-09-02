import requests
import json
import logging
from datetime import datetime
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AIEngine")

class AIEngine:
    def __init__(self, model="gemma4", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = f"{base_url}/api/generate"

    def extract_appointment_details(self, user_text):
        """
        Sends text to Ollama and asks it to extract booking details in JSON format.
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # The System Prompt: Refined to be more explicit and reduce conversational noise.
        system_prompt = (
            f"You are a scheduling assistant. Today's date is {today}. "
            "Extract the customer name, date, and time from the user's request. "
            "Format the date as YYYY-MM-DD and time as HH:MM (24h). "
            "Return ONLY a valid JSON object. No preamble, no conversational text, no markdown blocks. "
            "If a detail is missing, use null. "
            "Example: {\"name\": \"Alice\", \"date\": \"2026-09-05\", \"time\": \"10:30\"}"
        )

        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\nUser request: {user_text}",
            "stream": False,
            "format": "json"
        }

        try:
            response = requests.post(self.base_url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            response_text = result.get('response', '').strip()

            # Log the raw response for debugging
            logger.debug(f"AI Raw Response: {response_text}")

            return json.loads(response_text)
        except RequestException as e:
            logger.error(f"AI Network Error: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"AI Parsing Error (Invalid JSON): {e}. Response text: {response_text if 'response_text' in locals() else 'N/A'}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected AI Engine Error: {e}")
            return None
