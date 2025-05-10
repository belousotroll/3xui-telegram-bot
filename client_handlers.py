# handlers.py
import io
import qrcode
from logger import api_logger as logger
from api_client import get_connection_string
from telebot import types
from bot import bot

from handlers import *

@bot.message_handler(commands=["start"])
def cmd_start(message: types.Message) -> None:
    user_id  = message.chat.id
    username = message.from_user.username or "[unknown]"

    logger.info(f"Received /start from user_id={user_id}, username={username}")

    # Если уже одобрен
    if is_approved_user(user_id):
        bot.send_message(
            user_id,
            "✅ Вы уже зарегистрированы! Выберите действие ниже:",
            reply_markup=make_user_keyboard()
        )
        return

    # Если заявка уже ожидает
    requests = load_approval_requests()
    if any(entry['user_id'] == user_id for entry in requests):
        bot.send_message(
            user_id,
            "⌛ Ваша заявка уже принята и ожидает одобрения",
        )
        return

    # Новая заявка
    requests.append({"user_id": user_id, "username": username})
    save_approval_requests(requests)
    logger.info(f"Saved request for user with id={user_id}")

    admins = load_admins()
    for admin_id in admins:
        try:
            bot.send_message(
                admin_id,
                f"🆕 Новая заявка от @{username} with id={user_id})",
                reply_markup=make_approve_management_keyboard(user_id)
            )
        except Exception as e:
            logger.error(f"Failed to notify admin with id={admin_id}: {e}")\

    logger.info(f'Отправлен запрос на одобрение администраторам: {admins}')

    bot.send_message(
        user_id,
        "📝 Ваша заявка принята и отправлена на рассмотрение администраторам"
    )


@bot.callback_query_handler(func=lambda call: call.data == "get_qr")
def cmd_send_qr(call: types.CallbackQuery) -> None:
    """Отправляет пользователю QR для подключения к VPN серверу"""
    user_id = call.message.chat.id

    # Проверяем, одобрен ли пользователь
    if not is_approved_user(user_id):
        bot.answer_callback_query(call.id, "❌ Доступ запрещён: заявка не одобрена", show_alert=True)
        logger.warning(f"User {user_id} tried to get QR without approval")
        return

    logger.info(f'Incoming command /get_qr from approved user_id={user_id}')

    # Формируем строку для подключения
    cs = get_connection_string(user_id)
    if cs is None:
        bot.send_message(
            user_id,
            "❗ Не удалось найти параметры подключения"
        )
        bot.answer_callback_query(call.id)
        logger.error(f"Can't find configuration for user with id={user_id}")
        return

    # Делаем из нее QR
    img = qrcode.make(cs)
    buf = io.BytesIO()
    buf.name = 'qrcode.png'
    img.save(buf, 'PNG')
    buf.seek(0)

    bot.send_photo(user_id, photo=buf)
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "get_info")
def cmd_send_info(call: types.CallbackQuery) -> None:
    user_id = call.message.chat.id

    if not is_approved_user(user_id):
        bot.answer_callback_query(call.id, "❌ Доступ запрещён: заявка не одобрена", show_alert=True)
        logger.warning(f"User {user_id} tried to get info without approval")
        return

    logger.info(f'Incoming command /get_info from approved user with id={user_id}')
    bot.send_message(user_id, "ℹ️ Здесь будет информация об аккаунте")
    bot.answer_callback_query(call.id)


@bot.message_handler(func=lambda message: True)
def fallback(message: types.Message) -> None:
    bot.send_message(
        message.chat.id,
        "Не понимаю"
    )
