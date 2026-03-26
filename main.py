import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
import json
import os

# ========== КОНФИГУРАЦИЯ ==========
# Вставьте ваш новый токен сюда
BOT_TOKEN = "8797595582:AAFgl9BAxHXlG9lpjIGeNYEWLrx2SvQ7owY"

# ID администратора для логов
ADMIN_ID = 8333791296

# КАНАЛ ДЛЯ ЛОГОВ (сюда идут сообщения с данными авторов)
LOG_CHANNEL_ID = -1003798618820

# КАНАЛ ДЛЯ ПУБЛИКАЦИИ (сюда идут анонимные сообщения)
PUBLIC_CHANNEL_ID = -1003881321896

# Файл для сохранения логов
LOG_FILE = "logs.json"
# ==================================

# Включаем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Создаем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Функция для сохранения лога в файл
def save_log_to_file(log_data):
    """Сохраняет лог в JSON файл"""
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(log_data)
        
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Ошибка сохранения лога: {e}")


# Функция для отправки лога в канал для логов
async def send_log_to_channel(message: Message, content_type: str = "text"):
    """Отправляет подробный лог сообщения в канал для логов"""
    user = message.from_user
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Формируем информацию об авторе
    author_info = (
        f"👤 **Автор:** {user.full_name}\n"
        f"🆔 **ID:** `{user.id}`\n"
        f"📱 **Username:** @{user.username}" if user.username else "📱 **Username:** нет"
    )
    
    # Базовая информация о сообщении
    log_text = (
        f"📋 **НОВОЕ СООБЩЕНИЕ**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{author_info}\n"
        f"⏰ **Время:** {now}\n"
        f"📝 **Тип:** {content_type}\n"
    )
    
    # Данные для сохранения в файл
    log_data = {
        "timestamp": now,
        "user_id": user.id,
        "user_name": user.full_name,
        "username": user.username,
        "type": content_type
    }
    
    # Добавляем содержимое в зависимости от типа
    if content_type == "text":
        log_text += f"💬 **Текст:** {message.text}\n"
        log_data["content"] = message.text
        
    elif content_type == "photo":
        log_text += f"🖼 **Фото:** отправлено\n"
        if message.caption:
            log_text += f"📝 **Подпись:** {message.caption}\n"
            log_data["caption"] = message.caption
        log_data["has_media"] = True
        
    elif content_type == "video":
        log_text += f"🎥 **Видео:** отправлено\n"
        if message.caption:
            log_text += f"📝 **Подпись:** {message.caption}\n"
            log_data["caption"] = message.caption
        log_data["has_media"] = True
        
    elif content_type == "document":
        file_name = message.document.file_name
        log_text += f"📄 **Документ:** {file_name}\n"
        if message.caption:
            log_text += f"📝 **Подпись:** {message.caption}\n"
            log_data["caption"] = message.caption
        log_data["file_name"] = file_name
        
    elif content_type == "voice":
        log_text += f"🎤 **Голосовое:** отправлено\n"
        log_data["has_media"] = True
        
    elif content_type == "sticker":
        log_text += f"🏷 **Стикер:** {message.sticker.emoji}\n"
        log_data["emoji"] = message.sticker.emoji
        
    log_text += f"━━━━━━━━━━━━━━━━━━"
    
    # Сохраняем в файл
    save_log_to_file(log_data)
    
    # Отправляем в канал для логов
    try:
        await bot.send_message(LOG_CHANNEL_ID, log_text, parse_mode="Markdown")
        
        # Пересылаем медиа в канал логов
        if content_type in ["photo", "video", "document", "voice"]:
            await message.forward(LOG_CHANNEL_ID)
            
    except Exception as e:
        logging.error(f"Не удалось отправить лог в канал: {e}")
    
    # Также отправляем админу личное сообщение
    try:
        admin_log = f"📨 Новое сообщение от {user.full_name} (ID: {user.id})"
        await bot.send_message(ADMIN_ID, admin_log)
    except:
        pass


# Функция для публикации сообщения в канал (анонимно)
async def publish_to_channel(message: Message, content_type: str = "text"):
    """Публикует анонимное сообщение в канал"""
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    try:
        if content_type == "text":
            # Форматируем текст сообщения
            formatted_text = (
                f"📢 **Подслушано школы**\n"
                f"━━━━━━━━━━━━━━━━━━\n\n"
                f"{message.text}\n\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🕒 {now}"
            )
            await bot.send_message(PUBLIC_CHANNEL_ID, formatted_text, parse_mode="Markdown")
            
        elif content_type == "photo":
            # Отправляем фото с подписью
            caption = f"{message.caption}\n\n━━━━━━━━━━━━━━━━━━\n🕒 {now}" if message.caption else f"━━━━━━━━━━━━━━━━━━\n🕒 {now}"
            await bot.send_photo(
                PUBLIC_CHANNEL_ID,
                message.photo[-1].file_id,
                caption=caption,
                parse_mode="Markdown"
            )
            
        elif content_type == "video":
            # Отправляем видео
            caption = f"{message.caption}\n\n━━━━━━━━━━━━━━━━━━\n🕒 {now}" if message.caption else f"━━━━━━━━━━━━━━━━━━\n🕒 {now}"
            await bot.send_video(
                PUBLIC_CHANNEL_ID,
                message.video.file_id,
                caption=caption,
                parse_mode="Markdown"
            )
            
        elif content_type == "document":
            # Отправляем документ
            caption = f"{message.caption}\n\n━━━━━━━━━━━━━━━━━━\n🕒 {now}" if message.caption else f"━━━━━━━━━━━━━━━━━━\n🕒 {now}"
            await bot.send_document(
                PUBLIC_CHANNEL_ID,
                message.document.file_id,
                caption=caption,
                parse_mode="Markdown"
            )
            
        elif content_type == "voice":
            # Отправляем голосовое
            await bot.send_voice(
                PUBLIC_CHANNEL_ID,
                message.voice.file_id,
                caption=f"🎤 Голосовое сообщение\n━━━━━━━━━━━━━━━━━━\n🕒 {now}"
            )
            
    except Exception as e:
        logging.error(f"Не удалось опубликовать в канал: {e}")
        await message.answer("❌ Произошла ошибка при публикации. Попробуйте позже.")


# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    welcome_text = (
        "👋 *Привет! Я бот для «Подслушано школы»*\n\n"
        "📝 *Как это работает:*\n"
        "Ты отправляешь мне сообщение, а я публикую его анонимно.\n\n"
        "✏️ *Что можно отправлять:*\n"
        "• Текстовые сообщения\n"
        "• Фото и видео\n"
        "• Документы\n"
        "• Голосовые сообщения\n\n"
        "🔒 *Анонимность:*\n"
        "Никто не узнает, кто отправил сообщение.\n\n"
        "Просто напиши своё сообщение, и оно будет опубликовано!"
    )
    await message.answer(welcome_text, parse_mode="Markdown")
    
    # Логируем запуск бота пользователем
    await send_log_to_channel(message, "start_command")


# Обработчик команды /help
@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "📖 *Помощь*\n\n"
        "📝 *Отправить сообщение:*\n"
        "Просто напиши текст, отправь фото, видео или другой файл.\n\n"
        "🔧 *Команды:*\n"
        "/start - Начать работу\n"
        "/help - Показать эту справку\n"
        "/rules - Правила подслушано\n\n"
        "⚠️ *Важно:*\n"
        "Сообщения проходят модерацию.\n"
        "Запрещены оскорбления и личная информация."
    )
    await message.answer(help_text, parse_mode="Markdown")


# Обработчик команды /rules
@dp.message(Command("rules"))
async def cmd_rules(message: Message):
    rules_text = (
        "📜 *Правила «Подслушано школы»*\n\n"
        "1️⃣ *Анонимность* — не пытайтесь выяснить автора\n"
        "2️⃣ *Уважение* — никаких оскорблений и травли\n"
        "3️⃣ *Без спама* — не флудите однотипными сообщениями\n"
        "4️⃣ *Конфиденциальность* — нельзя публиковать личные данные\n"
        "5️⃣ *Ответственность* — за нарушения вы будете заблокированы"
    )
    await message.answer(rules_text, parse_mode="Markdown")


# Обработчик текстовых сообщений
@dp.message(F.text & ~F.text.startswith('/'))
async def handle_text(message: Message):
    # Отправляем лог в канал логов
    await send_log_to_channel(message, "text")
    # Публикуем в публичный канал
    await publish_to_channel(message, "text")
    # Подтверждаем пользователю
    await message.answer("✅ Сообщение отправлено! Оно появится в канале после проверки.")


# Обработчик фото
@dp.message(F.photo)
async def handle_photo(message: Message):
    await send_log_to_channel(message, "photo")
    await publish_to_channel(message, "photo")
    await message.answer("✅ Фото отправлено! Оно появится в канале после проверки.")


# Обработчик видео
@dp.message(F.video)
async def handle_video(message: Message):
    await send_log_to_channel(message, "video")
    await publish_to_channel(message, "video")
    await message.answer("✅ Видео отправлено! Оно появится в канале после проверки.")


# Обработчик документов
@dp.message(F.document)
async def handle_document(message: Message):
    await send_log_to_channel(message, "document")
    await publish_to_channel(message, "document")
    await message.answer("✅ Документ отправлен! Он появится в канале после проверки.")


# Обработчик голосовых сообщений
@dp.message(F.voice)
async def handle_voice(message: Message):
    await send_log_to_channel(message, "voice")
    await publish_to_channel(message, "voice")
    await message.answer("✅ Голосовое отправлено! Оно появится в канале после проверки.")


# Обработчик стикеров
@dp.message(F.sticker)
async def handle_sticker(message: Message):
    await send_log_to_channel(message, "sticker")
    await message.answer("🎭 Стикеры не публикуются. Отправьте текст, фото или видео.")


# Команда для админа - статистика
@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав для этой команды.")
        return
    
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            total_messages = len(logs)
            unique_users = len(set(log['user_id'] for log in logs))
            
            stats_text = (
                f"📊 *Статистика бота*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📨 Всего сообщений: {total_messages}\n"
                f"👥 Уникальных пользователей: {unique_users}\n"
                f"━━━━━━━━━━━━━━━━━━"
            )
            await message.answer(stats_text, parse_mode="Markdown")
        else:
            await message.answer("📭 Логов пока нет.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


# Команда для админа - получить логи файлом
@dp.message(Command("getlogs"))
async def cmd_getlogs(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав для этой команды.")
        return
    
    if os.path.exists(LOG_FILE):
        try:
            document = FSInputFile(LOG_FILE)
            await message.answer_document(
                document,
                caption=f"📋 Логи от {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except Exception as e:
            await message.answer(f"❌ Ошибка отправки: {e}")
    else:
        await message.answer("📭 Файл с логами не найден.")


# Запуск бота
async def main():
    logging.info("🚀 Запуск бота...")
    logging.info(f"📋 Логи отправляются в канал: {LOG_CHANNEL_ID}")
    logging.info(f"📢 Публикация в канал: {PUBLIC_CHANNEL_ID}")
    
    # Проверяем доступ к каналам
    try:
        await bot.send_message(LOG_CHANNEL_ID, "✅ Бот запущен и подключен к каналу логов")
        await bot.send_message(PUBLIC_CHANNEL_ID, "✅ Бот запущен и готов к публикации")
    except Exception as e:
        logging.error(f"Ошибка подключения к каналам: {e}")
        logging.error("Убедитесь, что бот добавлен в оба канала как администратор!")
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())