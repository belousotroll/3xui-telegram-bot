from handlers import load_approved_users
from handlers import load_admins

def is_approved_user(user_id: int):
    """Валидируем пользователя, сверяя его со списком подтвержденных пользователей"""
    approved_list = load_approved_users()
    return any(entry['user_id'] == user_id for entry in approved_list)

def is_admin(user_id: int):
    """Валидируем пользователя, сверяя его со списком подтвержденных пользователей"""
    admins = load_admins()
    return any(entry['user_id'] == user_id for entry in admins)
