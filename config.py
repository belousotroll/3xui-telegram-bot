import os
import logging
from dotenv import load_dotenv

load_dotenv()

API_URL           = os.getenv("API_URL")
API_AUTH_LOGIN    = os.getenv("API_AUTH_LOGIN")
API_AUTH_PASSWORD = os.getenv("API_AUTH_PASSWORD")
VERIFY            = False   # или путь к server.crt для проверки сертификата
BOT_TOKEN         = os.getenv("BOT_TOKEN")
#VERIFY_CERT = os.path.join(os.getcwd(), "./admin.crt")
