import requests
from typing import List, Dict

import os
from app.generation.prompts import SYSTEM_PROMPT, build_user_prompt
from dotenv import load_dotenv

load_dotenv()

from groq import Groq

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
