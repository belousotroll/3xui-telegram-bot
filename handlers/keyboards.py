from telebot import types


def make_user_keyboard() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(text="📱 Получить QR-код", callback_data="get_qr")
    )
    kb.add(
        types.InlineKeyboardButton(
            text="ℹ️ Информация об учётной записи", callback_data="get_info"
        )
    )
    kb.add(
        types.InlineKeyboardButton(
            text="⭐ Продлить подписку (30 дней)", callback_data="buy_subscription"
        )
    )
    return kb

# def make_subscription_keyboard() -> types.InlineKeyboardMarkup:
#     kb = types.InlineKeyboardMarkup()
#     kb.add(
#         types.InlineKeyboardButton(
#             text="⭐ Продлить подписку (1 звезда)", callback_data="buy_subscription"
#         )
#     )
#     return kb

def make_approve_management_keyboard(user_id: int) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton(
            text="✅ Одобрить", callback_data=f"approve:{user_id}"
        )
    )
    kb.add(
        types.InlineKeyboardButton(
            text="❌ Отклонить", callback_data=f"reject:{user_id}"
        )
    )
    return kb
