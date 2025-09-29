import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()  # Добавляем logger

# Получаем из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
TOPIC_ID = 865

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone=pytz.timezone("Europe/Moscow"))

async def send_morning_poll():
    question = "Сегодня"
    options = [
        "я есть",
        "нет по уважу", 
        "нет по неуважу",
        "опаздываю"
    ]
    
    try:
        await bot.send_poll(
            chat_id=CHAT_ID,
            message_thread_id=TOPIC_ID,
            question=question,
            options=options,
            is_anonymous=False,
            allows_multiple_answers=False
        )
        logger.info("✅ Опрос отправлен успешно!")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки опроса: {e}")

@dp.message(Command("getid"))
async def get_chat_id(message: types.Message):
    chat_id = message.chat.id
    topic_id = message.message_thread_id
    reply_text = f"Chat ID: {chat_id}"
    if topic_id:
        reply_text += f"\nTopic ID: {topic_id}"
    else:
        reply_text += "\nTopic ID: нет (обычная группа)"
    await message.reply(reply_text)
    logger.info(f"Запрошен Chat ID: {chat_id}, Topic ID: {topic_id}")

# КОМАНДА POOL ДОЛЖНА БЫТЬ ВНЕ ФУНКЦИИ MAIN!
@dp.message(Command("poll"))
async def manual_poll(message: types.Message):
    logger.info(f"Получена команда /poll от пользователя {message.from_user.id}")
    try:
        await send_morning_poll()
        await message.reply("Опрос отправлен!")
        logger.info("Опрос успешно отправлен по команде /poll")
    except Exception as e:
        error_msg = f"Ошибка при отправке опроса: {e}"
        logger.error(error_msg)
        await message.reply(f"Ошибка: {e}")

async def main():
    # Проверка переменных
    if not BOT_TOKEN or not CHAT_ID:
        logger.error("❌ Не установлены BOT_TOKEN или CHAT_ID")
        return
        
    try:
        # Проверка подключения
        me = await bot.get_me()
        logger.info(f"✅ Бот @{me.username} запущен!")
        
        # Настройка планировщика - отправка каждый день в 8:00 по Москве
        scheduler.add_job(
            send_morning_poll,
            trigger=CronTrigger(hour=5, minute=0),  # 8:00 по Москве (UTC+3)
            misfire_grace_time=300
        )
        scheduler.start()
        logger.info("⏰ Планировщик запущен - опрос будет в 8:00 по Москве")
        
        # Тестовая отправка при запуске
        await send_morning_poll()
        
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
    finally:
        if scheduler.running:
            scheduler.shutdown()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
