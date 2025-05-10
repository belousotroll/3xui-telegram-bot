import os
from dotenv import load_dotenv

load_dotenv()

API_URL                = os.getenv("API_URL")
API_AUTH_LOGIN         = os.getenv("API_AUTH_LOGIN")
API_AUTH_PASSWORD      = os.getenv("API_AUTH_PASSWORD")
VERIFY                 = False   # или путь к server.crt для проверки сертификата
BOT_TOKEN              = os.getenv("BOT_TOKEN")
APPROVED_USERS_FILE    = os.getenv("APPROVED_USERS_FILE")
APPROVAL_REQUESTS_FILE = os.getenv("APPROVAL_REQUESTS_FILE")
ADMIN_IDS_FILE         = os.getenv("ADMIN_IDS_FILE")
