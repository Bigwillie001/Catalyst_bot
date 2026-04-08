import os
from dotenv import load_dotenv
from llama_index.llms.groq import Groq
from llama_index.core import Settings

Settings.llm = Groq(api_key=os.getenv("GROQ_API_KEY"))

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CHROMA_PATH = "./storage/chroma_db"
UPLOADS_PATH = "./storage/uploads"
EMBED_MODEL = "all-MiniLM-L6-v2"