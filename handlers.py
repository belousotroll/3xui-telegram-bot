# handlers.py
import io
import qrcode
from logger import api_logger as logger
from telebot import types
from bot import bot
from api_client import add_client, get_connection_string

kb = types.InlineKeyboardMarkup()
kb.add(types.InlineKeyboardButton(text="📱 Получить QR-код", callback_data="get_qr"))
kb.add(types.InlineKeyboardButton(text="ℹ️ Информация об учётной записи", callback_data="get_info"))

@bot.message_handler(commands=["start"])
def cmd_start(message: types.Message) -> None:
    user_id = message.chat.id
    username = message.from_user.username or "[[unknown]]"
    logger.info(f'Incoming command /start from user_id={user_id} and username={username}')
    bot.send_chat_action(message.chat.id, "typing")
    if add_client(user_id, username):
        bot.send_message(
            message.chat.id,
            "✅ Вы успешно зарегистрированы! Выберите действие ниже:",
            reply_markup=kb
        )
    else:
        bot.send_message(
            message.chat.id,
            "❌ Не удалось зарегистрировать вас. Попробуйте позже."
        )

@bot.callback_query_handler(func=lambda call: call.data == "get_qr")
def send_qr(call: types.CallbackQuery) -> None:
    user_id = call.message.chat.id
    logger.info(f'Incoming command /get_qr from user_id={user_id}')

    conn_str = get_connection_string(user_id)
    if conn_str is None:
        bot.send_message(
            call.message.chat.id,
            "❗ Не удалось найти параметры подключения. "
            "Возможно, вы ещё не зарегистрированы в системе."
        )
        bot.answer_callback_query(call.id)
        return

    # Генерируем QR-код из полученной строки
    img = qrcode.make(conn_str)
    buf = io.BytesIO()
    buf.name = 'qrcode.png'
    img.save(buf, 'PNG')
    buf.seek(0)

    bot.send_photo(call.message.chat.id, photo=buf)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "get_info")
def send_info(call: types.CallbackQuery) -> None:
    user_id = call.message.chat.id
    logger.info(f'Incoming command /get_info from user_id={user_id}')
    bot.send_message(call.message.chat.id, "ℹ️ Здесь будет информация об аккаунте.")
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def fallback(message: types.Message) -> None:
    bot.send_message(
        message.chat.id,
        "Не понимаю. Используйте кнопки ниже.",
        reply_markup=kb
    )
