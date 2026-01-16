import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./rammstein_shop.db")
    SESSION_COOKIE_NAME = "session_id"
    SESSION_MAX_AGE = 60 * 60 * 24 * 7 
    SHOP_NAME = "Rammstein Fan Shop"
    CURRENCY = "€"
    FREE_SHIPPING_THRESHOLD = 100.00
    SHIPPING_COST = 9.99
    
config = Config()