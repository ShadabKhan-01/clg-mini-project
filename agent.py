import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
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
        "You are a highly efficient AI scheduling assistant for Yunite Automations. "
        "Your ONLY goal is to book a meeting by collecting these 5 details: "
        "Name, Phone, Email, Purpose of meeting, and Preferred Date/Time. "
        "STRICT RULES: "
        "1. Keep responses extremely short and direct (1-2 sentences maximum). "
        "2. Do not write paragraphs or over-explain services unless the user explicitly asks. "
        "3. You may ask for multiple missing details at once to speed up the process (e.g., 'Great, can I get your name, email, and phone number?'). "
        "4. As soon as you have all 5 details, IMMEDIATELY call the schedule_meeting function. Do not ask for final confirmation."
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
            # Check if this specific part is a function call
            if part.function_call:
                fc = part.function_call
                
                # Verify it is our scheduling tool
                if fc.name == "schedule_meeting":
                    # Convert the Google Protobuf object into a standard Python dictionary
                    args = dict(fc.args)
                    
                    # Execute the function locally (Talks to Cal.com, Neon, Airtable)
                    booking_result = schedule_meeting(**args)
                    
                    # RETURN IMMEDIATELY! Do not send the result back to Gemini.
                    return booking_result, chat.history

    # 4. If no function call was found, safely return the normal text
    return response.text, chat.history