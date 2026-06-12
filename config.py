import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY     = os.environ.get("GROQ_API_KEY", "")
FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "wandr-secret-key")