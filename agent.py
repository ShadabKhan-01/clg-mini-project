import json
import datetime
from groq import Groq
from config import GROQ_API_KEY
from cal_integration import book_cal_meeting
from database import save_lead_to_postgres
from airtable_sync import save_lead_to_airtable

# Initialize Groq Client
client = Groq(api_key=GROQ_API_KEY)

def schedule_meeting(name: str, phone: str, email: str, purpose: str, preferred_datetime: str):
    """Executes the local booking logic."""
    meet_link = book_cal_meeting(name, email, preferred_datetime, purpose)
    
    if meet_link:
        save_lead_to_postgres(name, phone, email, purpose, meet_link)
        save_lead_to_airtable(name, phone, email, purpose, preferred_datetime)
        return f"Success! Meeting booked. Here is the calendar/meet link: {meet_link}"
        
    return "Failed to book meeting. Please try again later or contact support."

# Groq requires tools to be defined as strict JSON schemas
tools = [
    {
        "type": "function",
        "function": {
            "name": "schedule_meeting",
            "description": "Schedules a meeting with the client once all details are gathered.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "The client's name."},
                    "phone": {"type": "string", "description": "The client's phone number."},
                    "email": {"type": "string", "description": "The client's email address."},
                    "purpose": {"type": "string", "description": "The reason for the meeting."},
                    "preferred_datetime": {
                        "type": "string", 
                        "description": "The date and time of the meeting strictly in ISO 8601 format with the +05:30 timezone offset (e.g., '2026-04-17T16:00:00+05:30')."
                    }
                },
                "required": ["name", "phone", "email", "purpose", "preferred_datetime"]
            }
        }
    }
]

def get_ai_response(chat_history: list, user_message: str):
    current_time = datetime.datetime.now().strftime("%A, %d %B %Y %I:%M %p")
    
    system_prompt = {
        "role": "system",
        "content": (
            "You are a highly efficient AI scheduling assistant for Yunite Automations. "
            f"The current system date and time is {current_time} IST. "
            "Your ONLY goal is to book a meeting by collecting these 5 details: "
            "Name, Phone, Email, Purpose of meeting, and Preferred Date/Time. "
            "STRICT RULES: "
            "1. Keep responses extremely short and direct (1-2 sentences maximum). "
            "2. Do not write paragraphs or over-explain services unless explicitly asked. "
            "3. Ask for multiple missing details at once to speed up the process. "
            "4. As soon as you have all 5 details, IMMEDIATELY call the schedule_meeting function. "
        )
    }
    
    # Compile the full message list: System Prompt + Past History + New Message
    messages = [system_prompt] + chat_history + [{"role": "user", "content": user_message}]
    
    # We use llama-3.3-70b-versatile as it is Groq's best model for tool calling
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        tools=tools,
        tool_choice="auto",
        max_tokens=256
    )
    
    response_message = response.choices[0].message
    
    # Check if Groq wants to use the scheduling tool
    if response_message.tool_calls:
        for tool_call in response_message.tool_calls:
            if tool_call.function.name == "schedule_meeting":
                # Extract the arguments from the AI's JSON output
                args = json.loads(tool_call.function.arguments)
                
                # Execute the local function
                booking_result = schedule_meeting(**args)
                
                # Update history so the bot remembers the user's request
                chat_history.append({"role": "user", "content": user_message})
                
                # Return the final message immediately to save API calls
                return booking_result, chat_history

    # If no tool was called, append the conversation normally
    chat_history.append({"role": "user", "content": user_message})
    chat_history.append({"role": "assistant", "content": response_message.content})
    
    return response_message.content, chat_history