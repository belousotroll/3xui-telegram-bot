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
from urllib.parse import quote_plus, quote, urlencode, urlparse
from config import API_URL, API_AUTH_LOGIN, API_AUTH_PASSWORD, VERIFY
from typing import Optional

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def _ensure_dict(value):
    """Если value — строка, раскодирует из JSON, иначе возвращает как есть."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON: {value}")
            return {}
    return value or {}

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


def add_client(user_id: int, username: str) -> bool:
    """Добавляет клиента в первый inbound по Telegram ID"""
    try:
        session = get_authorized_session()
        inbound_id = get_first_inbound(session)

        logger.info(f'Registering user with id={user_id} to inbound with id={inbound_id}')

        client_info = {
            "clients": [{
                "id": str(user_id),
                "flow": "xtls-rprx-vision",
                "email": username,
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

def get_connection_string(user_id: int) -> Optional[str]:
    session = get_authorized_session()
    inbounds = list_inbounds(session)  # список dict, но внутри fields могут быть JSON-строками

    target = str(user_id)
    for inbound in inbounds:
        # Грузим settings как dict
        settings = _ensure_dict(inbound.get("settings", {}))
        clients  = settings.get("clients", [])
        for client in clients:
            if client.get("tgId") != target:
                continue

            # нашли
            client_id = client.get("id", "")
            email     = client.get("email", "")
            remark    = inbound.get("remark", "")

            protocol = inbound.get("protocol", "")

            # Парсим streamSettings
            ss            = _ensure_dict(inbound.get("streamSettings", {}))
            network       = ss.get("network", "")
            security      = ss.get("security", "")

            reality       = _ensure_dict(ss.get("realitySettings", {}))
            real_settings = _ensure_dict(reality.get("settings", {}))

            public_key  = real_settings.get("publicKey", "")
            fingerprint = real_settings.get("fingerprint", "")

            # SNI
            server_names = reality.get("serverNames", [])
            sni = server_names[0] if server_names else real_settings.get("serverName", "")

            # shortId
            short_ids = reality.get("shortIds", [])
            short_id  = short_ids[0] if short_ids else ""

            spider_x = real_settings.get("spiderX", "")

            # flow может лежать и в client
            flow = client.get("flow") or ""

            # Собираем query-параметры
            params = {
                "type":     network,
                "security": security,
                "pbk":      public_key,
                "fp":       fingerprint,
                "sni":      sni,
                "sid":      short_id,
                "spx":      spider_x,
            }
            if flow:
                params["flow"] = flow

            query = urlencode(params, quote_via=quote_plus, safe="")

            # Собираем фрагмент remark-email
            fragment = f"{remark}-{email}"
            fragment_enc = quote(fragment, safe="")

            # Хост и порт
            host = urlparse(API_URL).hostname or ""
            port = inbound.get("port", "")

            conn_string = f"{protocol}://{client_id}@{host}:{port}?{query}#{fragment_enc}"
            logger.debug(f"Connection string for user with id={user_id}: {conn_string}")

            return conn_string

    logger.warning(f"User with id={target} not found")
    return None