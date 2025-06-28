import os 
from os.path import join, dirname
from dotenv import load_dotenv


load_dotenv()

OBS = os.environ.get("OBS_PASSWORD")
RIOT_API = os.environ.get("RIOT_KEY")