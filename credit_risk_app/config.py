import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-not-for-production")
    DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"
    PAGE_SIZE = 25
