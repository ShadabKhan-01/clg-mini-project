import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")

import google.generativeai as genai
from config import GEMINI_API_KEY
from cal_integration import book_cal_meeting
from database import save_lead_to_postgres
from airtable_sync import save_lead_to_airtable
import datetime

# Configure the SDK
genai.configure(api_key=GEMINI_API_KEY)

def schedule_meeting(name: str, phone: str, email: str, purpose: str, preferred_datetime: str):
    """
    Schedules a meeting with the client once all details are gathered.
    
    Args:
        name: The client's name.
        phone: The client's phone number.
        email: The client's email address.
        purpose: The reason for the meeting.
        preferred_datetime: The date and time of the meeting. This MUST be converted into strict ISO 8601 format with the Asia/Kolkata timezone offset (e.g., "2026-04-17T16:00:00+05:30").
    """
    # 1. Book the meeting via Cal.com API (V2)
    meet_link = book_cal_meeting(name, email, preferred_datetime, purpose)
    
    if meet_link:
        # 2. Save to Neon Postgres
        save_lead_to_postgres(name, phone, email, purpose, meet_link)
        
        # 3. Sync to Airtable CRM
        save_lead_to_airtable(name, phone, email, purpose, preferred_datetime)
        
        # Return the final message that will be sent directly to Telegram
        return f"Success! Meeting booked. Here is the calendar/meet link: {meet_link}"
        
    return "Failed to book meeting. Please try again later or contact support."

# Calculate the current time every time this file is loaded
current_time = datetime.datetime.now().strftime("%A, %d %B %Y %I:%M %p")

# Initialize the Model with tools and a System Prompt
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash-latest',
    tools=[schedule_meeting],
    system_instruction=(
        "You are a highly efficient AI scheduling assistant for Yunite Automations. "
        f"The current system date and time is {current_time} IST. "
        "Your ONLY goal is to book a meeting by collecting these 5 details: "
        "Name, Phone, Email, Purpose of meeting, and Preferred Date/Time. "
        "STRICT RULES: "
        "1. Keep responses extremely short and direct (1-2 sentences maximum). "
        "2. Do not write paragraphs or over-explain services unless explicitly asked. "
        "3. Ask for multiple missing details at once to speed up the process. "
        "4. As soon as you have all 5 details, IMMEDIATELY call the schedule_meeting function. "
        "5. CRITICAL: When calling schedule_meeting, you MUST calculate the correct future date using the current system date provided, and you MUST format the 'preferred_datetime' argument strictly as ISO 8601 with the +05:30 timezone offset (e.g., YYYY-MM-DDTHH:MM:SS+05:30)."
    )
)

def get_ai_response(chat_history: list, user_message: str):
    # 1. Start chat WITHOUT automatic function calling
    chat = model.start_chat(history=chat_history)
    
    # 2. Send the message (Cost: 1 API Call)
    response = chat.send_message(user_message)
    
    # 3. Look inside the response parts to see if Gemini triggered a tool
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.function_call:
                fc = part.function_call
                
                if fc.name == "schedule_meeting":
                    args = dict(fc.args)
                    
                    booking_result = schedule_meeting(**args)
                    
                    return booking_result, chat.history

    return response.text, chat.history