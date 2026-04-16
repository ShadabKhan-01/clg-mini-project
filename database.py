from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# --- Add this safety check ---
if DATABASE_URL is None:
    raise ValueError("DATABASE_URL is missing from the environment. Please check your .env file.")
# -----------------------------

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the Leads Table
class Lead(Base):
    __tablename__ = "leads"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    phone = Column(String)
    email = Column(String, index=True)
    purpose = Column(String)
    meet_link = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# Automatically create the table in Neon if it doesn't exist yet
Base.metadata.create_all(bind=engine)

def save_lead_to_postgres(name: str, phone: str, email: str, purpose: str, meet_link: str):
    db = SessionLocal()
    try:
        new_lead = Lead(
            name=name, 
            phone=phone, 
            email=email, 
            purpose=purpose, 
            meet_link=meet_link
        )
        db.add(new_lead)
        db.commit()
        db.refresh(new_lead)
        return True
    except Exception as e:
        print(f"Database Error: {e}")
        return False
    finally:
        db.close()