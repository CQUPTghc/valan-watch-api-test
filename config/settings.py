import os

from dotenv import load_dotenv


load_dotenv()


BASE_URL = os.getenv("BASE_URL")
VALAN_PHONE = os.getenv("VALAN_PHONE")
VALAN_PASSWORD = os.getenv("VALAN_PASSWORD")
VALAN_NONEXISTENT_PHONE = os.getenv("VALAN_NONEXISTENT_PHONE")