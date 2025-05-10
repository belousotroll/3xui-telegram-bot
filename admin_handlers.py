from handlers import *
from api_client import *
from logger import api_logger as logger
from telebot import types
from bot import bot

@bot.message_handler(commands=["admin"])
def cmd_admin(message: types.Message) -> None:
    user_id = message.chat.id
    # @todo: move validation to query handler

    if is_admin(user_id):
        bot.send_message(user_id, "⛔ Доступ запрещён")
        return

    requests = load_approval_requests()
    users = load_approved_users()

    lines = []
    if requests:
        lines.append("**Ожидают:**")
        for r in requests:
            lines.append(f"- @{r['username']} (ID: {r['user_id']})")
    if users:
        lines.append("**Одобрены:**")
        for a in users:
            lines.append(f"- @{a['username']} (ID: {a['user_id']})")
    text = "\n".join(lines) if lines else "Заявок нет"

    markup = types.InlineKeyboardMarkup()
    for r in requests:
        uid = r['user_id']
        markup.add(
            types.InlineKeyboardButton(
                text=f"Одобрить @{r['username']}",
                callback_data=f"approve:{uid}"
            )
        )
    bot.send_message(user_id, text, reply_markup=markup, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("approve:"))
def handle_approve(call: types.CallbackQuery) -> None:
    caller_id = call.from_user.id
    if not is_admin(caller_id):
        bot.answer_callback_query(call.id, "Нет прав", show_alert=True)
        return

    _, uid = call.data.split(":", 1)
    user_id = int(uid)

    requests = load_approval_requests()
    req = next((r for r in requests if r['user_id'] == user_id), None)
    if not req:
        bot.answer_callback_query(call.id, "Заявка не найдена или уже обработана", show_alert=True)
        return

    username = req['username']
    if add_client(user_id, username):
        users = load_approved_users()
        users.append(req)
        save_approved_users(users)
        logger.info(f"Approved user {user_id} by admin {caller_id}")
        bot.send_message(
            user_id,
            "✅ Ваша заявка одобрена! Вы зарегистрированы",
            reply_markup=make_user_keyboard()
        )
        bot.answer_callback_query(call.id, "Пользователь одобрен")
    else:
        bot.answer_callback_query(call.id, "Ошибка при регистрации API", show_alert=True)

    # Удаление обработанной заявки
    remaining = [r for r in requests if r['user_id'] != user_id]
    save_approval_requests(remaining)


@bot.callback_query_handler(func=lambda c: c.data and c.data.startswith("reject:"))
def handle_reject(call: types.CallbackQuery) -> None:
    caller_id = call.from_user.id
    if not is_admin(caller_id):
        bot.answer_callback_query(call.id, "Нет прав", show_alert=True)
        return

    _, uid = call.data.split(":", 1)
    user_id = int(uid)

    requests = load_approval_requests()
    req = next((r for r in requests if r['user_id'] == user_id), None)
    if not req:
        bot.answer_callback_query(call.id, "Заявка не найдена или уже обработана", show_alert=True)
        return

    username = req['username']
    bot.send_message(user_id, "❌ Ваша заявка отклонена администратором")
    bot.send_message(
        caller_id,
        f"🗑️ Вы отклонили заявку пользователя @{username} (id={user_id})"
    )
    bot.answer_callback_query(call.id, "Заявка отклонена")
    logger.info(f"Rejected user {user_id} by admin {caller_id}")

    # Удаление обработанной заявки
    remaining = [r for r in requests if r['user_id'] != user_id]
    save_approval_requests(remaining)