import requests
from config import CAL_API_KEY, CAL_EVENT_TYPE_ID

def book_cal_meeting(name, email, preferred_datetime, purpose):
    # 1. Update Endpoint to V2
    url = "https://api.cal.com/v2/bookings"
    
    # 2. Update Payload structure for V2
    payload = {
        "eventTypeId": int(CAL_EVENT_TYPE_ID),
        "start": preferred_datetime, 
        "attendee": {
            "name": name,
            "email": email,
            "timeZone": "Asia/Kolkata", 
            "language": "en"
        },
        # Custom notes like 'purpose' now safely go into metadata
        "metadata": {
            "purpose": purpose
        }
    }
    
    # 3. Securely pass API Key and Version via Headers
    headers = {
        "Authorization": f"Bearer {CAL_API_KEY}",
        "cal-api-version": "2024-08-13", # Required by Cal.com V2
        "Content-Type": "application/json"
    }
    
    # 4. Fire the request without the apiKey in the URL
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code in [200, 201]:
        data = response.json()
        
        # V2 wraps the response inside a 'data' object
        booking_data = data.get('data', {})
        meet_link = booking_data.get('videoCallUrl')
        
        if meet_link:
            return meet_link
        return "Meeting booked successfully! Please check your email for the calendar invite."
    else:
        print("Cal.com V2 Error:", response.text)
        return None