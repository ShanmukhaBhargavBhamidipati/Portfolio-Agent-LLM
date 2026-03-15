import os
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


def load_config():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing in your .env file")

    return OpenAI(api_key=api_key)