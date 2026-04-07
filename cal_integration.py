import requests
from config import CAL_API_KEY, CAL_EVENT_TYPE_ID

def book_cal_meeting(name, email, preferred_datetime, purpose):
    url = "https://api.cal.com/v1/bookings"
    
    payload = {
        "eventTypeId": CAL_EVENT_TYPE_ID,
        "start": preferred_datetime, # Must be formatted correctly (ISO 8601)
        "responses": {
            "name": name,
            "email": email,
            "notes": purpose
        },
        "timeZone": "Asia/Kolkata", 
        "language": "en"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Pass API key via query param or headers based on Cal.com's latest docs
    response = requests.post(f"{url}?apiKey={CAL_API_KEY}", json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return data['booking']['videoCallUrl'] # Returns the Google Meet link
    else:
        print("Cal.com Error:", response.text)
        return None