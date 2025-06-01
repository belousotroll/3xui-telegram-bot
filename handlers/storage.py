import json
import os
from logger import api_logger as logger
from typing import List, Dict, Any
from config import APPROVAL_REQUESTS_FILE, APPROVED_USERS_FILE, ADMIN_IDS_FILE


def _validate_path(path: str, description: str) -> bool:
    if not path:
        logger.error(f"{description} path is not set in config")
        return False
    return True


def _ensure_dir(path: str) -> None:
    """Создаёт директорию, если указана папка в пути файла."""
    dir_path = os.path.dirname(path)
    if dir_path:
        try:
            os.makedirs(dir_path, exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")


def load_approval_requests() -> List[Dict[str, Any]]:
    """
    Читает ожидающие подтверждения заявки из файла как список словарей.
    При отсутствии файла создаёт файл со списком [] и возвращает пустой список.
    При ошибке парсинга возвращает пустой список.
    """
    if not _validate_path(APPROVAL_REQUESTS_FILE, "Approval requests file"):
        return []

    if not os.path.exists(APPROVAL_REQUESTS_FILE):
        _ensure_dir(APPROVAL_REQUESTS_FILE)
        try:
            with open(APPROVAL_REQUESTS_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=4)
            logger.warning(
                f"{APPROVAL_REQUESTS_FILE} not found, created new file with empty list"
            )
        except OSError as e:
            logger.error(f"Failed to create {APPROVAL_REQUESTS_FILE}: {e}")
        return []

    try:
        with open(APPROVAL_REQUESTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            logger.error(f"Expected list in {APPROVAL_REQUESTS_FILE}, got {type(data)}")
    except json.JSONDecodeError:
        logger.error(f"Не удалось разобрать JSON в {APPROVAL_REQUESTS_FILE}")
    except OSError as e:
        logger.error(f"Error reading {APPROVAL_REQUESTS_FILE}: {e}")
    return []


def save_approval_requests(requests: List[Dict[str, Any]]) -> None:
    if not _validate_path(APPROVAL_REQUESTS_FILE, "Approval requests file"):
        return
    _ensure_dir(APPROVAL_REQUESTS_FILE)
    try:
        with open(APPROVAL_REQUESTS_FILE, "w", encoding="utf-8") as f:
            json.dump(requests, f, ensure_ascii=False, indent=4)
    except OSError as e:
        logger.error(f"Failed to save requests to {APPROVAL_REQUESTS_FILE}: {e}")


def load_approved_users() -> List[Dict[str, Any]]:
    """
    Читает список одобренных пользователей из файла как список словарей.
    При отсутствии файла создаёт файл с [] и возвращает пустой список.
    При ошибке парсинга возвращает пустой список.
    """
    if not _validate_path(APPROVED_USERS_FILE, "Approved users file"):
        return []

    if not os.path.exists(APPROVED_USERS_FILE):
        _ensure_dir(APPROVED_USERS_FILE)
        try:
            with open(APPROVED_USERS_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=4)
            logger.warning(
                f"{APPROVED_USERS_FILE} not found, created new file with empty list"
            )
        except OSError as e:
            logger.error(f"Failed to create {APPROVED_USERS_FILE}: {e}")
        return []

    try:
        with open(APPROVED_USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            logger.error(f"Expected list in {APPROVED_USERS_FILE}, got {type(data)}")
    except json.JSONDecodeError:
        logger.error(f"Не удалось разобрать JSON в {APPROVED_USERS_FILE}")
    except OSError as e:
        logger.error(f"Error reading {APPROVED_USERS_FILE}: {e}")
    return []


def save_approved_users(users: List[Dict[str, Any]]) -> None:
    if not _validate_path(APPROVED_USERS_FILE, "Approved users file"):
        return
    _ensure_dir(APPROVED_USERS_FILE)
    try:
        with open(APPROVED_USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=4)
    except OSError as e:
        logger.error(f"Failed to save approved users to {APPROVED_USERS_FILE}: {e}")


def load_admins() -> List[Dict[str, Any]]:
    """
    Читает список администраторов из файла как список словарей
    """
    if not _validate_path(ADMIN_IDS_FILE, "Approved users file"):
        return []

    if not os.path.exists(ADMIN_IDS_FILE):
        _ensure_dir(ADMIN_IDS_FILE)
        try:
            with open(ADMIN_IDS_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=4)
            logger.warning(
                f"{ADMIN_IDS_FILE} not found, created new file with empty list"
            )
        except OSError as e:
            logger.error(f"Failed to create {ADMIN_IDS_FILE}: {e}")
        return []

    try:
        with open(ADMIN_IDS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            logger.error(f"Expected list in {ADMIN_IDS_FILE}, got {type(data)}")
    except json.JSONDecodeError:
        logger.error(f"Не удалось разобрать JSON в {ADMIN_IDS_FILE}")
    except OSError as e:
        logger.error(f"Error reading {ADMIN_IDS_FILE}: {e}")
    return []
