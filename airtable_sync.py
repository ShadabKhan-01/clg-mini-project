import requests
import os
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Appointment Leads")

def save_lead_to_airtable(name: str, phone: str, email: str, purpose: str, preferred_datetime: str):
    # Skip if Airtable isn't configured yet
    if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
        print("Airtable not configured. Skipping CRM sync.")
        return False
        
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "records": [
            {
                "fields": {
                    "Name": name,
                    "Phone": phone,
                    "Email": email,
                    "Purpose": purpose,
                    "Preferred DateTime": preferred_datetime
                }
            }
        ]
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Airtable Sync Error: {e}")
        return False