import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import json
import os

# ========== КОНФИГУРАЦИЯ ==========
# ВСТАВЬТЕ ВАШ НОВЫЙ ТОКЕН (после отзыва старого)
BOT_TOKEN = "8797595582:AAFgl9BAxHXlG9lpjIGeNYEWLrx2SvQ7owY"

# ID администратора
ADMIN_ID = 8333791296

# КАНАЛ ДЛЯ ЛОГОВ (сюда идут сообщения с данными авторов)
LOG_CHANNEL_ID = -1003798618820

# КАНАЛ ДЛЯ ПУБЛИКАЦИИ (сюда идут анонимные сообщения)
PUBLIC_CHANNEL_ID = -1003881321896

# Файл для сохранения логов
LOG_FILE = "logs.json"

# НАСТРОЙКИ КУЛДАУНА
COOLDOWN_MINUTES = 2  # Задержка между сообщениями в минутах
# ==================================

# Включаем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Создаем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Словарь для хранения времени последнего сообщения пользователя
# {user_id: datetime_last_message}
user_last_message = {}


# Функция проверки кулдауна
def check_cooldown(user_id: int) -> tuple:
    """
    Проверяет, может ли пользователь отправить сообщение
    Возвращает (can_send: bool, remaining_seconds: int)
    """
    if user_id == ADMIN_ID:
        # Администратор не имеет ограничений
        return True, 0
    
    if user_id in user_last_message:
        last_time = user_last_message[user_id]
        time_diff = datetime.now() - last_time
        cooldown = timedelta(minutes=COOLDOWN_MINUTES)
        
        if time_diff < cooldown:
            remaining = cooldown - time_diff
            remaining_seconds = int(remaining.total_seconds())
            return False, remaining_seconds
    
    return True, 0


# Функция обновления времени последнего сообщения
def update_cooldown(user_id: int):
    """Обновляет время последнего сообщения пользователя"""
    user_last_message[user_id] = datetime.now()


# Функция форматирования времени ожидания
def format_cooldown_time(seconds: int) -> str:
    """Форматирует секунды в читаемый вид"""
    minutes = seconds // 60
    secs = seconds % 60
    
    if minutes > 0:
        return f"{minutes} мин {secs} сек"
    else:
        return f"{secs} сек"


# Функция для получения полной информации о пользователе (ID и имя ВСЕГДА есть)
def get_user_info(user) -> dict:
    """Возвращает полную информацию о пользователе"""
    return {
        "user_id": user.id,  # ✅ Всегда доступен
        "first_name": user.first_name,  # ✅ Всегда доступен
        "last_name": user.last_name if user.last_name else "",  # Может быть None
        "full_name": f"{user.first_name} {user.last_name}".strip() if user.last_name else user.first_name,
        "username": user.username if user.username else "❌ скрыт или не задан",  # Может быть скрыт
        "language": user.language_code if user.language_code else "неизвестно"
    }


# Функция для форматирования лога (ВСЕГДА с ID и именем)
def format_log_message(user_info: dict, content_type: str, content: str = "", caption: str = "") -> str:
    """Форматирует сообщение для лога с ОБЯЗАТЕЛЬНЫМ отображением ID и имени"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_text = (
        f"📋 **НОВОЕ СООБЩЕНИЕ**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🆔 **ID:** `{user_info['user_id']}`\n"
        f"👤 **Имя:** {user_info['full_name']}\n"
    )
    
    # Добавляем username, если есть
    if user_info['username'] != "❌ скрыт или не задан":
        log_text += f"📱 **Username:** @{user_info['username']}\n"
    else:
        log_text += f"📱 **Username:** {user_info['username']}\n"
    
    log_text += (
        f"⏰ **Время:** {now}\n"
        f"📝 **Тип:** {content_type}\n"
    )
    
    # Добавляем содержимое
    if content_type == "text":
        log_text += f"💬 **Текст:** {content}\n"
    elif content_type == "photo":
        log_text += f"🖼 **Фото:** отправлено\n"
        if caption:
            log_text += f"📝 **Подпись:** {caption}\n"
    elif content_type == "video":
        log_text += f"🎥 **Видео:** отправлено\n"
        if caption:
            log_text += f"📝 **Подпись:** {caption}\n"
    elif content_type == "document":
        log_text += f"📄 **Документ:** {content}\n"
        if caption:
            log_text += f"📝 **Подпись:** {caption}\n"
    elif content_type == "voice":
        log_text += f"🎤 **Голосовое:** отправлено\n"
    elif content_type == "sticker":
        log_text += f"🏷 **Стикер:** {content}\n"
    
    log_text += f"━━━━━━━━━━━━━━━━━━"
    
    return log_text


# Функция для сохранения лога в файл (ВСЕГДА с ID и именем)
def save_log_to_file(user_info: dict, content_type: str, content: str = "", caption: str = ""):
    """Сохраняет лог в JSON файл с обязательными ID и именем"""
    log_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_id": user_info["user_id"],  # ✅ Всегда сохраняется
        "user_name": user_info["full_name"],  # ✅ Всегда сохраняется
        "first_name": user_info["first_name"],
        "last_name": user_info["last_name"],
        "username": user_info["username"],
        "language": user_info["language"],
        "type": content_type
    }
    
    # Добавляем содержимое
    if content_type == "text":
        log_data["content"] = content
    elif content_type == "photo":
        log_data["has_media"] = True
        if caption:
            log_data["caption"] = caption
    elif content_type == "video":
        log_data["has_media"] = True
        if caption:
            log_data["caption"] = caption
    elif content_type == "document":
        log_data["file_name"] = content
        if caption:
            log_data["caption"] = caption
    elif content_type == "voice":
        log_data["has_media"] = True
    elif content_type == "sticker":
        log_data["emoji"] = content
    
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


# Функция для поиска сообщений пользователя по ID или имени
def get_user_messages(user_identifier):
    """Возвращает все сообщения пользователя по ID или имени"""
    try:
        if not os.path.exists(LOG_FILE):
            return []
        
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            all_logs = json.load(f)
        
        user_messages = []
        
        # Пробуем найти по ID
        try:
            user_id = int(user_identifier)
            user_messages = [log for log in all_logs if log.get('user_id') == user_id]
            if user_messages:
                return user_messages
        except ValueError:
            pass
        
        # Поиск по имени
        for log in all_logs:
            user_name = log.get('user_name', '').lower()
            if user_identifier.lower() in user_name:
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
    user_id = user_info.get('user_id', 'Неизвестно')
    user_name = user_info.get('user_name', 'Неизвестно')
    username = user_info.get('username', 'Нет')
    
    text = (
        f"👤 **Информация о пользователе**\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🆔 **ID:** `{user_id}`\n"
        f"👤 **Имя:** {user_name}\n"
        f"📱 **Username:** {username}\n"
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


# Функция для отправки лога админу и в канал
async def send_log_to_channel(message: Message, content_type: str = "text", content: str = "", caption: str = ""):
    """Отправляет подробный лог сообщения с ОБЯЗАТЕЛЬНЫМ ID и именем"""
    user_info = get_user_info(message.from_user)
    
    # Форматируем лог
    log_text = format_log_message(user_info, content_type, content, caption)
    
    # Сохраняем в файл
    save_log_to_file(user_info, content_type, content, caption)
    
    # Отправляем в канал для логов
    try:
        await bot.send_message(LOG_CHANNEL_ID, log_text, parse_mode="Markdown")
        
        # Пересылаем медиа в канал логов
        if content_type in ["photo", "video", "document", "voice"]:
            await message.forward(LOG_CHANNEL_ID)
            
    except Exception as e:
        logging.error(f"Не удалось отправить лог в канал: {e}")
    
    # Отправляем админу личное сообщение с ID и именем
    try:
        admin_log = f"📨 Новое сообщение\n🆔 ID: {user_info['user_id']}\n👤 Имя: {user_info['full_name']}"
        await bot.send_message(ADMIN_ID, admin_log)
    except:
        pass


# Функция для публикации сообщения в канал (анонимно)
async def publish_to_channel(message: Message, content_type: str = "text"):
    """Публикует анонимное сообщение в канал"""
    try:
        if content_type == "text":
            formatted_text = f"📢 Новое сообщение!\n\n{message.text}"
            await bot.send_message(PUBLIC_CHANNEL_ID, formatted_text)
            
        elif content_type == "photo":
            caption = f"📢 Новое сообщение!\n\n{message.caption}" if message.caption else "📢 Новое сообщение!"
            await bot.send_photo(
                PUBLIC_CHANNEL_ID,
                message.photo[-1].file_id,
                caption=caption
            )
            
        elif content_type == "video":
            caption = f"📢 Новое сообщение!\n\n{message.caption}" if message.caption else "📢 Новое сообщение!"
            await bot.send_video(
                PUBLIC_CHANNEL_ID,
                message.video.file_id,
                caption=caption
            )
            
        elif content_type == "document":
            caption = f"📢 Новое сообщение!\n\n{message.caption}" if message.caption else "📢 Новое сообщение!"
            await bot.send_document(
                PUBLIC_CHANNEL_ID,
                message.document.file_id,
                caption=caption
            )
            
        elif content_type == "voice":
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
        f"⏱ Ограничение: {COOLDOWN_MINUTES} минуты между сообщениями\n\n"
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
    
    # Логируем запуск с ID и именем
    user_info = get_user_info(message.from_user)
    await send_log_to_channel(message, "start_command", f"Пользователь {user_info['full_name']} запустил бота")


# Обработчик команды /help
@dp.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "📖 Помощь\n\n"
        "Отправь мне любое сообщение, и я опубликую его анонимно\n"
        f"⏱ Между сообщениями нужно ждать {COOLDOWN_MINUTES} минуты\n\n"
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
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ Укажите ID или имя пользователя\n\n"
            "Примеры:\n"
            "/user 123456789\n"
            "/user Иван"
        )
        return
    
    user_identifier = args[1].strip()
    user_messages = get_user_messages(user_identifier)
    
    if not user_messages:
        await message.answer(f"❌ Пользователь «{user_identifier}» не найден или нет сообщений.")
        return
    
    text, page, total_pages = format_user_messages_page(user_messages, 0)
    keyboard = create_pagination_keyboard(user_identifier, page, total_pages)
    
    await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)


# Обработчик инлайн кнопок пагинации
@dp.callback_query(F.data.startswith("user_page:"))
async def handle_user_page(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ У вас нет прав", show_alert=True)
        return
    
    _, user_identifier, page_str = callback.data.split(":")
    page = int(page_str)
    
    user_messages = get_user_messages(user_identifier)
    
    if not user_messages:
        await callback.message.edit_text(f"❌ Пользователь не найден")
        await callback.answer()
        return
    
    text, current_page, total_pages = format_user_messages_page(user_messages, page)
    keyboard = create_pagination_keyboard(user_identifier, current_page, total_pages)
    
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


# Обработчик текстовых сообщений с проверкой кулдауна
@dp.message(F.text & ~F.text.startswith('/'))
async def handle_text(message: Message):
    user_id = message.from_user.id
    
    # Проверяем кулдаун
    can_send, remaining = check_cooldown(user_id)
    
    if not can_send:
        wait_time = format_cooldown_time(remaining)
        await message.answer(f"⏱ Подождите {wait_time} перед отправкой следующего сообщения.")
        return
    
    # Обновляем время последнего сообщения
    update_cooldown(user_id)
    
    # Отправляем лог и публикуем
    await send_log_to_channel(message, "text", message.text)
    await publish_to_channel(message, "text")
    await message.answer("✅ Сообщение отправлено")


# Обработчик фото с проверкой кулдауна
@dp.message(F.photo)
async def handle_photo(message: Message):
    user_id = message.from_user.id
    
    # Проверяем кулдаун
    can_send, remaining = check_cooldown(user_id)
    
    if not can_send:
        wait_time = format_cooldown_time(remaining)
        await message.answer(f"⏱ Подождите {wait_time} перед отправкой следующего сообщения.")
        return
    
    # Обновляем время последнего сообщения
    update_cooldown(user_id)
    
    caption = message.caption if message.caption else ""
    await send_log_to_channel(message, "photo", "", caption)
    await publish_to_channel(message, "photo")
    await message.answer("✅ Сообщение отправлено")


# Обработчик видео с проверкой кулдауна
@dp.message(F.video)
async def handle_video(message: Message):
    user_id = message.from_user.id
    
    # Проверяем кулдаун
    can_send, remaining = check_cooldown(user_id)
    
    if not can_send:
        wait_time = format_cooldown_time(remaining)
        await message.answer(f"⏱ Подождите {wait_time} перед отправкой следующего сообщения.")
        return
    
    # Обновляем время последнего сообщения
    update_cooldown(user_id)
    
    caption = message.caption if message.caption else ""
    await send_log_to_channel(message, "video", "", caption)
    await publish_to_channel(message, "video")
    await message.answer("✅ Сообщение отправлено")


# Обработчик документов с проверкой кулдауна
@dp.message(F.document)
async def handle_document(message: Message):
    user_id = message.from_user.id
    
    # Проверяем кулдаун
    can_send, remaining = check_cooldown(user_id)
    
    if not can_send:
        wait_time = format_cooldown_time(remaining)
        await message.answer(f"⏱ Подождите {wait_time} перед отправкой следующего сообщения.")
        return
    
    # Обновляем время последнего сообщения
    update_cooldown(user_id)
    
    file_name = message.document.file_name
    caption = message.caption if message.caption else ""
    await send_log_to_channel(message, "document", file_name, caption)
    await publish_to_channel(message, "document")
    await message.answer("✅ Сообщение отправлено")


# Обработчик голосовых сообщений с проверкой кулдауна
@dp.message(F.voice)
async def handle_voice(message: Message):
    user_id = message.from_user.id
    
    # Проверяем кулдаун
    can_send, remaining = check_cooldown(user_id)
    
    if not can_send:
        wait_time = format_cooldown_time(remaining)
        await message.answer(f"⏱ Подождите {wait_time} перед отправкой следующего сообщения.")
        return
    
    # Обновляем время последнего сообщения
    update_cooldown(user_id)
    
    await send_log_to_channel(message, "voice")
    await publish_to_channel(message, "voice")
    await message.answer("✅ Сообщение отправлено")


# Обработчик стикеров
@dp.message(F.sticker)
async def handle_sticker(message: Message):
    emoji = message.sticker.emoji
    await send_log_to_channel(message, "sticker", emoji)
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
                f"Пользователей: {unique_users}\n"
                f"⏱ Кулдаун: {COOLDOWN_MINUTES} мин"
            )
            await message.answer(stats_text)
        else:
            await message.answer("📭 Логов пока нет.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


# Команда для админа - сброс кулдауна пользователя
@dp.message(Command("reset_cooldown"))
async def cmd_reset_cooldown(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав для этой команды.")
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Укажите ID пользователя\n\nПример: /reset_cooldown 123456789")
        return
    
    try:
        user_id = int(args[1])
        if user_id in user_last_message:
            del user_last_message[user_id]
            await message.answer(f"✅ Кулдаун для пользователя {user_id} сброшен.")
        else:
            await message.answer(f"ℹ️ У пользователя {user_id} нет активного кулдауна.")
    except ValueError:
        await message.answer("❌ Неверный формат ID. Введите число.")


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
    logging.info(f"⏱ Кулдаун между сообщениями: {COOLDOWN_MINUTES} минут")
    
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