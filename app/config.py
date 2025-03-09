import os
from dotenv import load_dotenv

load_dotenv()

# ArangoDB Configuration
ARANGO_HOST = os.getenv("HOST")
ARANGO_USER = os.getenv("USER")
ARANGO_PASSWORD = os.getenv("PASSWORD", "")

# Groq Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set")

# Constants for the application
EVENT_CODES = {
    "01": "MAKE PUBLIC STATEMENT",
    "02": "APPEAL",
    "03": "EXPRESS INTENT TO COOPERATE",
    "04": "CONSULT",
    "05": "ENGAGE IN DIPLOMATIC COOPERATION",
    "06": "ENGAGE IN MATERIAL COOPERATION",
    "07": "PROVIDE AID",
    "08": "YIELD",
    "09": "INVESTIGATE",
    "10": "DEMAND",
    "11": "DISAPPROVE",
    "12": "REJECT",
    "13": "THREATEN",
    "14": "PROTEST",
    "15": "EXHIBIT MILITARY POSTURE",
    "16": "REDUCE RELATIONS",
    "17": "COERCE",
    "18": "ASSAULT",
    "19": "FIGHT",
    "20": "ENGAGE IN UNCONVENTIONAL MASS VIOLENCE"
}