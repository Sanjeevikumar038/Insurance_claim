import os
from dotenv import load_dotenv

def load_config():
    """
    Loads environment variables from a .env file into os.environ.
    If the .env file does not exist, it silently continues,
    ensuring that the app still works when variables are supplied directly.
    """
    load_dotenv()
