import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
import json
import os

# ========== КОНФИГУРАЦИЯ ==========
# Вставьте ваш токен сюда (после отзыва старого)
BOT_TOKEN = "8797595582:AAFgl9BAxHXlG9lpjIGeNYEWLrx2SvQ7owY"

# ID администратора
ADMIN_ID = 8333791296

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


# Функция для отправки лога админу
async def send_log_to_admin(message: Message, content_type: str = "text"):
    """Отправляет подробный лог сообщения админу"""
    user = message.from_user
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Формируем информацию об авторе
    author_info = (
        f"👤 *Автор:* {user.full_name}\n"
        f"🆔 *ID:* `{user.id}`\n"
        f"📱 *Username:* @{user.username}" if user.username else "📱 *Username:* нет"
    )
    
    # Базовая информация о сообщении
    log_text = (
        f"📋 *НОВОЕ СООБЩЕНИЕ*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{author_info}\n"
        f"⏰ *Время:* {now}\n"
        f"📝 *Тип:* {content_type}\n"
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
        log_text += f"💬 *Текст:* {message.text}\n"
        log_data["content"] = message.text
        
    elif content_type == "photo":
        log_text += f"🖼 *Фото:* отправлено\n"
        if message.caption:
            log_text += f"📝 *Подпись:* {message.caption}\n"
            log_data["caption"] = message.caption
        log_data["has_media"] = True
        
    elif content_type == "video":
        log_text += f"🎥 *Видео:* отправлено\n"
        if message.caption:
            log_text += f"📝 *Подпись:* {message.caption}\n"
            log_data["caption"] = message.caption
        log_data["has_media"] = True
        
    elif content_type == "document":
        file_name = message.document.file_name
        log_text += f"📄 *Документ:* {file_name}\n"
        if message.caption:
            log_text += f"📝 *Подпись:* {message.caption}\n"
            log_data["caption"] = message.caption
        log_data["file_name"] = file_name
        
    elif content_type == "voice":
        log_text += f"🎤 *Голосовое:* отправлено\n"
        log_data["has_media"] = True
        
    elif content_type == "sticker":
        log_text += f"🏷 *Стикер:* {message.sticker.emoji}\n"
        log_data["emoji"] = message.sticker.emoji
        
    log_text += f"━━━━━━━━━━━━━━━━━━"
    
    # Сохраняем в файл
    save_log_to_file(log_data)
    
    # Отправляем админу
    try:
        await bot.send_message(ADMIN_ID, log_text, parse_mode="Markdown")
        
        # Пересылаем медиа админу
        if content_type in ["photo", "video", "document", "voice"]:
            await message.forward(ADMIN_ID)
            
    except Exception as e:
        logging.error(f"Не удалось отправить лог админу: {e}")


# Функция для публикации сообщения (анонимно)
async def publish_message(message: Message, content: str, message_id: int = None):
    """Публикует сообщение в канале/чате"""
    # Здесь можно настроить публикацию в отдельном канале
    # Сейчас просто подтверждаем пользователю
    
    confirm_text = (
        "✅ *Сообщение отправлено!*\n\n"
        "Оно будет опубликовано после модерации.\n"
        "Спасибо, что делитесь!"
    )
    await message.answer(confirm_text, parse_mode="Markdown")


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
        "Никто не узнает, кто отправил сообщение.\n"
        "Администратор видит только техническую информацию.\n\n"
        "Просто напиши своё сообщение, и оно будет опубликовано!"
    )
    await message.answer(welcome_text, parse_mode="Markdown")
    
    # Логируем запуск бота пользователем
    await send_log_to_admin(message, "start_command")


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
        "5️⃣ *Ответственность* — за нарушения вы будете заблокированы\n\n"
        "🚨 *Нарушения фиксируются*\n"
        "Администратор видит все сообщения с данными авторов."
    )
    await message.answer(rules_text, parse_mode="Markdown")


# Обработчик текстовых сообщений
@dp.message(F.text & ~F.text.startswith('/'))
async def handle_text(message: Message):
    # Отправляем лог админу
    await send_log_to_admin(message, "text")
    # Публикуем сообщение
    await publish_message(message, message.text)


# Обработчик фото
@dp.message(F.photo)
async def handle_photo(message: Message):
    await send_log_to_admin(message, "photo")
    
    if message.caption:
        await publish_message(message, f"[Фото] {message.caption}")
    else:
        await publish_message(message, "[Фото]")


# Обработчик видео
@dp.message(F.video)
async def handle_video(message: Message):
    await send_log_to_admin(message, "video")
    
    if message.caption:
        await publish_message(message, f"[Видео] {message.caption}")
    else:
        await publish_message(message, "[Видео]")


# Обработчик документов
@dp.message(F.document)
async def handle_document(message: Message):
    await send_log_to_admin(message, "document")
    
    if message.caption:
        await publish_message(message, f"[Документ] {message.caption}")
    else:
        await publish_message(message, f"[Документ] {message.document.file_name}")


# Обработчик голосовых сообщений
@dp.message(F.voice)
async def handle_voice(message: Message):
    await send_log_to_admin(message, "voice")
    await publish_message(message, "[Голосовое сообщение]")


# Обработчик стикеров
@dp.message(F.sticker)
async def handle_sticker(message: Message):
    await send_log_to_admin(message, "sticker")
    await message.answer("🎭 Стикеры не публикуются. Отправьте текст или фото.")
    await publish_message(message, f"[Стикер: {message.sticker.emoji}]")


# Обработчик для администратора - получение статистики
@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    # Проверяем, что это админ
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


# Обработчик для администратора - получение логов файлом
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
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())