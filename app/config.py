import os

# load .env file
from dotenv import load_dotenv

load_dotenv()

# Config class to store configuration variables
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'app.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RATELIMIT_DEFAULT = "30 per minute"
