import os
from dotenv import load_dotenv

load_dotenv()

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
DATABASE_URL = os.getenv("DATABASE_URL")

if not SARVAM_API_KEY:
    raise ValueError("Missing SARVAM_API_KEY")

if not GMAIL_EMAIL or not GMAIL_APP_PASSWORD:
    raise ValueError("Missing Gmail credentials")

if not DATABASE_URL:
    raise ValueError("Missing DATABASE_URL")