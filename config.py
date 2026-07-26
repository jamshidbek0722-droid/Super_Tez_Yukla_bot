import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "instagram120.p.rapidapi.com")
RAPIDAPI_URL = os.getenv("RAPIDAPI_URL", "https://instagram120.p.rapidapi.com/api/instagram/links")

YOUTUBE_RAPIDAPI_KEY = os.getenv("YOUTUBE_RAPIDAPI_KEY", RAPIDAPI_KEY)
YOUTUBE_RAPIDAPI_HOST = os.getenv("YOUTUBE_RAPIDAPI_HOST", "youtube138.p.rapidapi.com")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot.db")
