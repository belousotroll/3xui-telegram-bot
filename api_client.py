import requests
import json
import urllib3
from logger import api_logger as logger
from urllib.parse import quote_plus, quote, urlencode, urlparse
from config import API_URL, API_AUTH_LOGIN, API_AUTH_PASSWORD, VERIFY
from typing import Optional

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def _ensure_dict(value):
    """Если value — строка, раскодирует из JSON, иначе возвращает как есть"""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON: {value}")
            return {}
    return value or {}

def _extract_client_and_inbound(inbounds, user_id: str):
    """
    Находит inbound и client по tgId.
    """
    for inbound in inbounds:
        settings = _ensure_dict(inbound.get("settings", {}))
        clients  = settings.get("clients", [])
        for client in clients:
            if client.get("tgId") == user_id:
                return inbound, client
    return None, None

def _parse_stream_settings(stream_settings):
    ss = _ensure_dict(stream_settings)
    reality = _ensure_dict(ss.get("realitySettings", {}))
    real_settings = _ensure_dict(reality.get("settings", {}))
    return {
        "network": ss.get("network", ""),
        "security": ss.get("security", ""),
        "public_key": real_settings.get("publicKey", ""),
        "fingerprint": real_settings.get("fingerprint", ""),
        "sni": (reality.get("serverNames", []) or [real_settings.get("serverName", "")])[0],
        "short_id": (reality.get("shortIds", []) or [""])[0],
        "spider_x": real_settings.get("spiderX", ""),
    }


def _build_client_info(user_id: int, username: str) -> dict:
    """Строит dict с данными клиента для API."""
    return {
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

        client_info = _build_client_info(user_id, username)
        payload = {
            "id": inbound_id,
            "settings": json.dumps(client_info)
        }
        resp = session.post(
            f"{API_URL}/panel/api/inbounds/addClient",
            json=payload,
            timeout=5
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("success"):
            logger.info(f"User with id={user_id} has been registered successfully")
            return True
        else:
            logger.error(f"Registering user with id={user_id} to inbound with id={inbound_id} failed: {data.get('msg')}")
            return False
    except Exception as e:
        logger.error(f"Exception while adding client: {e}", exc_info=True)
        return False

def get_connection_string(user_id: int) -> Optional[str]:
    """Возвращает строку подключения для пользователя по Telegram ID"""
    try:
        session = get_authorized_session()
        inbounds = list_inbounds(session)
        target = str(user_id)

        inbound, client = _extract_client_and_inbound(inbounds, target)
        if not inbound or not client:
            logger.warning(f"User with id={target} not found in any inbound")
            return None

        logger.debug(f"Found client in inbound id={inbound.get('id')}")
        protocol = inbound.get("protocol", "")
        host = urlparse(API_URL).hostname or ""
        port = inbound.get("port", "")

        settings = _parse_stream_settings(inbound.get("streamSettings", {}))

        params = {
            "type":     settings["network"],
            "security": settings["security"],
            "pbk":      settings["public_key"],
            "fp":       settings["fingerprint"],
            "sni":      settings["sni"],
            "sid":      settings["short_id"],
            "spx":      settings["spider_x"],
        }
        flow = client.get("flow") or ""
        if flow:
            params["flow"] = flow

        query = urlencode(params, quote_via=quote_plus, safe="")
        remark = inbound.get("remark", "")
        email = client.get("email", "")
        fragment = f"{remark}-{email}"
        fragment_enc = quote(fragment, safe="")

        client_id = client.get("id", "")
        conn_string = f"{protocol}://{client_id}@{host}:{port}?{query}#{fragment_enc}"

        logger.info(f"Connection string for user with id={user_id} generated")
        logger.debug(f"Connection string: {conn_string}")

        return conn_string

    except Exception as e:
        logger.error(f"Failed to generate connection string for user {user_id}: {e}", exc_info=True)
        return None