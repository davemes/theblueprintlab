from dotenv import load_dotenv
import os

load_dotenv()  # sucht automatisch nach .env im aktuellen Ordner

hubspot_key = os.getenv("HUBSPOT_API_KEY")
openai_key = os.getenv("OPENAI_API_KEY")