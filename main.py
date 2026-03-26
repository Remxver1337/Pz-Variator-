import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
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


# Функция для поиска сообщений пользователя
def get_user_messages(user_identifier):
    """Возвращает все сообщения пользователя по ID, имени или username"""
    try:
        if not os.path.exists(LOG_FILE):
            return []
        
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            all_logs = json.load(f)
        
        user_messages = []
        
        # Пробуем найти по ID (если identifier - число)
        try:
            user_id = int(user_identifier)
            user_messages = [log for log in all_logs if log.get('user_id') == user_id]
            if user_messages:
                return user_messages
        except ValueError:
            pass
        
        # Поиск по имени или username (частичное совпадение)
        for log in all_logs:
            user_name = log.get('user_name', '').lower()
            username = log.get('username', '').lower()
            identifier_lower = user_identifier.lower()
            
            if identifier_lower in user_name or identifier_lower in username:
                user_messages.append(log)
        
        return user_messages
    except Exception as e:
        logging.error(f"Ошибка поиска сообщений: {e}")
        return []


# Функция для форматирования сообщений пользователя с пагинацией
def format_user_messages_page(messages, page=0, per_page=5):
    """Форматирует страницу с сообщениями пользователя"""
    if not messages:
        return "❌ Пользователь не найден или нет сообщений.", 0, 0
    
    total_pages = (len(messages) + per_page - 1) // per_page
    
    if page >= total_pages:
        page = total_pages - 1
    
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, len(messages))
    
    # Информация о пользователе
    user_info = messages[0]
    user_name = user_info.get('user_name', 'Неизвестно')
    user_id = user_info.get('user_id', 'Неизвестно')
    username = user_info.get('username', 'Нет')
    
    text = (
        f"👤 **Информация о пользователе**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📛 Имя: {user_name}\n"
        f"🆔 ID: `{user_id}`\n"
        f"📱 Username: @{username}" if username != 'Нет' else "📱 Username: нет\n"
        f"\n📊 **Сообщения ({len(messages)} шт.)**\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    for i in range(start_idx, end_idx):
        msg = messages[i]
        timestamp = msg.get('timestamp', 'Неизвестно')
        msg_type = msg.get('type', 'text')
        content = ""
        
        if msg_type == 'text':
            content = msg.get('content', '')[:100]
            if len(msg.get('content', '')) > 100:
                content += "..."
        elif msg_type == 'photo':
            content = f"[Фото] {msg.get('caption', 'без подписи')[:50]}"
        elif msg_type == 'video':
            content = f"[Видео] {msg.get('caption', 'без подписи')[:50]}"
        elif msg_type == 'document':
            content = f"[Документ] {msg.get('file_name', 'файл')}"
        elif msg_type == 'voice':
            content = "[Голосовое сообщение]"
        else:
            content = f"[{msg_type}]"
        
        text += (
            f"**{i+1}.** 🕒 {timestamp}\n"
            f"📝 {content}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
        )
    
    return text, page, total_pages


# Функция для создания клавиатуры пагинации
def create_pagination_keyboard(user_identifier, page, total_pages):
    """Создает инлайн клавиатуру для пагинации"""
    buttons = []
    
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"user_page:{user_identifier}:{page-1}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton(text="Вперед ▶️", callback_data=f"user_page:{user_identifier}:{page+1}"))
        
        if nav_buttons:
            buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton(text="❌ Закрыть", callback_data="close_user_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


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


# Функция для публикации сообщения в канал
async def publish_to_channel(message: Message, content_type: str = "text"):
    """Публикует анонимное сообщение в канал"""
    try:
        if content_type == "text":
            # Форматируем текст сообщения
            formatted_text = (
                f"📢 Новое сообщение!\n\n"
                f"{message.text}"
            )
            await bot.send_message(PUBLIC_CHANNEL_ID, formatted_text)
            
        elif content_type == "photo":
            # Отправляем фото с подписью
            caption = f"📢 Новое сообщение!\n\n{message.caption}" if message.caption else "📢 Новое сообщение!"
            await bot.send_photo(
                PUBLIC_CHANNEL_ID,
                message.photo[-1].file_id,
                caption=caption
            )
            
        elif content_type == "video":
            # Отправляем видео с подписью
            caption = f"📢 Новое сообщение!\n\n{message.caption}" if message.caption else "📢 Новое сообщение!"
            await bot.send_video(
                PUBLIC_CHANNEL_ID,
                message.video.file_id,
                caption=caption
            )
            
        elif content_type == "document":
            # Отправляем документ с подписью
            caption = f"📢 Новое сообщение!\n\n{message.caption}" if message.caption else "📢 Новое сообщение!"
            await bot.send_document(
                PUBLIC_CHANNEL_ID,
                message.document.file_id,
                caption=caption
            )
            
        elif content_type == "voice":
            # Отправляем голосовое
            await bot.send_voice(
                PUBLIC_CHANNEL_ID,
                message.voice.file_id,
                caption="📢 Новое сообщение!"
            )
            
    except Exception as e:
        logging.error(f"Не удалось опубликовать в канал: {e}")
        await message.answer("❌ Ошибка при публикации")


# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    welcome_text = (
        "👋 Привет! Я бот для «Подслушано школы»\n\n"
        "📝 Как это работает:\n"
        "Ты отправляешь мне сообщение, а я публикую его анонимно.\n\n"
        "✏️ Что можно отправлять:\n"
        "• Текстовые сообщения\n"
        "• Фото и видео\n"
        "• Документы\n"
        "• Голосовые сообщения\n\n"
        "🚫 Что запрещено:\n\n"
        "• Реклама\n"
        "• Спам\n\n"
        "Просто напиши своё сообщение, и оно будет опубликовано и никто не узнает, кто автор!"
    )
    await message.answer(welcome_text)
    
    # Логируем запуск бота пользователем
    await send_log_to_channel(message, "start_command")


# Обработчик команды /help
@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "📖 Помощь\n\n"
        "Отправь мне любое сообщение, и я опубликую его анонимно\n"
        "Доступные команды:\n"
        "/start - Начать работу\n"
        "/help - Помощь"
    )
    await message.answer(help_text)


# Обработчик команды /user (только для админа)
@dp.message(Command("user"))
async def cmd_user(message: Message):
    # Проверяем, что это админ
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав для этой команды.")
        return
    
    # Получаем аргумент (имя/айди/тег)
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ Укажите ID, имя или username пользователя\n\n"
            "Примеры:\n"
            "/user 123456789\n"
            "/user Иван\n"
            "/user @ivan"
        )
        return
    
    user_identifier = args[1].strip()
    
    # Ищем сообщения пользователя
    user_messages = get_user_messages(user_identifier)
    
    if not user_messages:
        await message.answer(f"❌ Пользователь «{user_identifier}» не найден или нет сообщений.")
        return
    
    # Форматируем первую страницу
    text, page, total_pages = format_user_messages_page(user_messages, 0)
    
    # Создаем клавиатуру
    keyboard = create_pagination_keyboard(user_identifier, page, total_pages)
    
    await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)


# Обработчик инлайн кнопок пагинации
@dp.callback_query(F.data.startswith("user_page:"))
async def handle_user_page(callback: CallbackQuery):
    # Проверяем, что это админ
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ У вас нет прав", show_alert=True)
        return
    
    # Разбираем данные
    _, user_identifier, page_str = callback.data.split(":")
    page = int(page_str)
    
    # Получаем сообщения пользователя
    user_messages = get_user_messages(user_identifier)
    
    if not user_messages:
        await callback.message.edit_text(f"❌ Пользователь не найден")
        await callback.answer()
        return
    
    # Форматируем страницу
    text, current_page, total_pages = format_user_messages_page(user_messages, page)
    
    # Создаем клавиатуру
    keyboard = create_pagination_keyboard(user_identifier, current_page, total_pages)
    
    # Редактируем сообщение
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()


# Обработчик закрытия меню пользователя
@dp.callback_query(F.data == "close_user_menu")
async def close_user_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ У вас нет прав", show_alert=True)
        return
    
    await callback.message.delete()
    await callback.answer("Меню закрыто")


# Обработчик текстовых сообщений
@dp.message(F.text & ~F.text.startswith('/'))
async def handle_text(message: Message):
    # Отправляем лог в канал логов
    await send_log_to_channel(message, "text")
    # Публикуем в публичный канал
    await publish_to_channel(message, "text")
    # Простое подтверждение
    await message.answer("✅ Сообщение отправлено")


# Обработчик фото
@dp.message(F.photo)
async def handle_photo(message: Message):
    await send_log_to_channel(message, "photo")
    await publish_to_channel(message, "photo")
    await message.answer("✅ Сообщение отправлено")


# Обработчик видео
@dp.message(F.video)
async def handle_video(message: Message):
    await send_log_to_channel(message, "video")
    await publish_to_channel(message, "video")
    await message.answer("✅ Сообщение отправлено")


# Обработчик документов
@dp.message(F.document)
async def handle_document(message: Message):
    await send_log_to_channel(message, "document")
    await publish_to_channel(message, "document")
    await message.answer("✅ Сообщение отправлено")


# Обработчик голосовых сообщений
@dp.message(F.voice)
async def handle_voice(message: Message):
    await send_log_to_channel(message, "voice")
    await publish_to_channel(message, "voice")
    await message.answer("✅ Сообщение отправлено")


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
                f"📊 Статистика\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"Сообщений: {total_messages}\n"
                f"Пользователей: {unique_users}"
            )
            await message.answer(stats_text)
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
        await bot.send_message(LOG_CHANNEL_ID, "✅ Бот запущен")
        await bot.send_message(PUBLIC_CHANNEL_ID, "✅ Бот запущен")
    except Exception as e:
        logging.error(f"Ошибка подключения к каналам: {e}")
        logging.error("Убедитесь, что бот добавлен в оба канала как администратор!")
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())