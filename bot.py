# bot.py
from telebot import TeleBot, types
from config import BOT_TOKEN
from handlers import load_admins

user_commands= [
    types.BotCommand('start', 'Запустить бота'),
    types.BotCommand('help', 'Помощь')
]

admin_commands = [
    types.BotCommand('admin', 'Панель администратора'),
]

def init_bot() -> TeleBot:
    bot = TeleBot(BOT_TOKEN)
    bot.set_my_commands(
        commands=user_commands,
        scope=types.BotCommandScopeDefault()
    )
    for admin_id in load_admins():
        bot.set_my_commands(
            commands=admin_commands,
            scope=types.BotCommandScopeChat(admin_id)
        )
    return bot

bot = init_bot()
