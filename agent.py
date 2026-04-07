import google.generativeai as genai
from config import GEMINI_API_KEY
from cal_integration import book_cal_meeting
from database import save_lead_to_postgres
from airtable_sync import save_lead_to_airtable

genai.configure(api_key=GEMINI_API_KEY)

# Define the function Gemini can call
def schedule_meeting(name: str, phone: str, email: str, purpose: str, preferred_datetime: str):
    """
    Schedules a meeting with the client once all details are gathered.
    """
    # 1. Book the meeting via Cal.com API
    meet_link = book_cal_meeting(name, email, preferred_datetime, purpose)
    
    if meet_link:
        # 2. Save to Neon Postgres
        save_lead_to_postgres(name, phone, email, purpose, meet_link)
        
        # 3. Sync to Airtable CRM
        save_lead_to_airtable(name, phone, email, purpose, preferred_datetime)
        
        # 4. Notify You (The Admin) via Telegram
        notify_admin(f"New Meeting! {name} - {purpose}. Link: {meet_link}")
        
        return f"Success! Meeting booked. Here is the Google Meet link: {meet_link}"
    return "Failed to book meeting. Please ask the user to try again later."

# Initialize the Model with tools and a System Prompt
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    tools=[schedule_meeting],
    system_instruction=(
        "You are an expert AI representative for my automation services. "
        "Your goal is to explain how our services help businesses scale, and ultimately schedule a meeting. "
        "You must collect the user's Name, Phone, Email, Purpose of the meeting, and Preferred Date/Time. "
        "Be conversational. Do not ask for all details at once. Once you have all 5 details, "
        "call the schedule_meeting function to finalize the booking."
    )
)

def get_ai_response(chat_history: list, user_message: str):
    # Pass Redis chat history to Gemini
    chat = model.start_chat(history=chat_history)
    response = chat.send_message(user_message)
    return response.text, chat.history