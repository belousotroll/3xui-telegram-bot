"""
Логика работы с API 3X-UI:
 - Авторизация (login)
 - Список inbound-ов
 - Добавление клиента
 - Получение строки подключения VLESS
"""
import requests
import json
import uuid
import urllib3
from logger import api_logger as logger

from urllib.parse import urlparse, quote_plus
from config import API_URL, API_AUTH_LOGIN, API_AUTH_PASSWORD, VERIFY

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_authorized_session():
    session = requests.Session()
    session.verify = VERIFY
    resp = session.post(
        f"{API_URL}/login",
        data={"username": f'{API_AUTH_LOGIN}', "password": f'{API_AUTH_PASSWORD}'},
        timeout=5
    )
    resp.raise_for_status()
    logger.info("Authenticated successfully")
    return session


def list_inbounds(session: requests.Session) -> list:
    """Возвращает список inbound-конфигураций"""
    resp = session.get(
        f"{API_URL}/panel/api/inbounds/list",
        timeout=5
    )
    resp.raise_for_status()
    data = resp.json()
    inbounds = data.get("obj", [])
    logger.info(f"Found {len(inbounds)} active inbounds")
    return inbounds


def get_first_inbound(session: requests.Session) -> int:
    inbound = list_inbounds(session)[0]
    logger.info(f"Using inbound with id={inbound['id']}")
    return inbound['id']


def add_client(user_id: int) -> bool:
    """Добавляет клиента в первый inbound по Telegram ID"""
    try:
        session = get_authorized_session()
        inbound_id = get_first_inbound(session)

        logger.info(f'Registering user with id={user_id} to inbound with id={inbound_id}')

        client_uuid = str(uuid.uuid4())
        client_info = {
            "clients": [{
                "id": client_uuid,
                "flow": "xtls-rprx-vision",
                "email": str(user_id),
                "limitIp": 0,
                "totalGB": 0,
                "expiryTime": 0,
                "enable": True,
                "tgId": str(user_id),
                "subId": "",
                "comment": "",
                "reset": 0
            }]
        }
        payload = {"id": inbound_id, "settings": json.dumps(client_info)}
        resp = session.post(
            f"{API_URL}/panel/api/inbounds/addClient",
            json=payload,
            timeout=5
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("success"):
            logger.info(f"User with id={user_id} has been registerated successfully")
            return True
        else:
            logger.error(f"Registering user with id={user_id} to inbound with id={inbound_id} failed: {data.get('msg')}")
            return False
    except Exception as e:
        logger.error(f"Exception")
        return False


def get_connection_string(user_id: int) -> str | None:
    """
    Формирует VLESS строку подключения для клиента с данным Telegram ID,
    ищет клиента по полю email в настройках.
    """
    session = get_authorized_session()
    inbounds = list_inbounds(session)

    target = str(user_id)
    found_client = None
    found_inbound = None
    for inbound in inbounds:
        settings = json.loads(inbound.get("settings", "{}"))
        for client in settings.get("clients", []):
            # Ищем клиента по email (Telegram ID хранится в email)
            if client.get("email") == target:
                found_client = client
                found_inbound = inbound
                break
        if found_client:
            break

    if not found_client:
        logger.warning(f"User with id={target} not found")
        return None

    # Собираем параметры подключения из found_inbound и found_client
    client_id   = found_client["id"]
    email       = found_client.get("email", "")
    remark      = found_inbound.get("remark", "")
    host        = urlparse(API_URL).hostname or ""
    port        = found_inbound.get("port", "")
    stream      = json.loads(found_inbound.get("streamSettings", "{}"))
    reality     = stream.get("realitySettings", {})

    public_key  = reality.get("publicKey", "")
    fingerprint = reality.get("fingerprint", "")
    sni         = reality.get("serverName") or (reality.get("serverNames", [""])[0])
    short_id    = reality.get("shortId") or (reality.get("shortIds", [""])[0])
    spider_x    = reality.get("spiderX", "")

    # Кодируем параметры для URL
    pk_enc  = quote_plus(public_key, safe="")
    fp_enc  = quote_plus(fingerprint, safe="")
    sni_enc = quote_plus(sni or "", safe="")
    sid_enc = quote_plus(short_id or "", safe="")
    spx_enc = quote_plus(spider_x or "", safe="")

    query = (
        f"type=tcp&security=reality&pbk={pk_enc}&fp={fp_enc}"
        f"&sni={sni_enc}&sid={sid_enc}&spx={spx_enc}&flow=xtls-rprx-vision"
    )
    url = f"vless://{client_id}@{host}:{port}?{query}#{remark}-{email}"
    return url
