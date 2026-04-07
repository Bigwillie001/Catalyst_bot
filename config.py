import os
from dotenv import load_dotenv
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core import Settings

Settings.llm = GoogleGenAI(model_name="models/gemini-2.0-flash", api_key=os.getenv("GEMINI_API_KEY"))

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CHROMA_PATH = "./storage/chroma_db"
UPLOADS_PATH = "./storage/uploads"
EMBED_MODEL = "all-MiniLM-L6-v2"