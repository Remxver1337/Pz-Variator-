import random
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Словарь для замены русских букв на латинские аналоги
REPLACEMENT_MAP = {
    'а': 'a', 'е': 'e', 'с': 'c', 'о': 'o',
    'р': 'p', 'х': 'x', 'у': 'y',
    'А': 'A', 'Е': 'E', 'С': 'C', 'О': 'O',
    'Р': 'P', 'Х': 'X', 'У': 'Y'
}

def replace_letters(text: str) -> str:
    """Заменяет русские буквы на латинские с шансом 50%"""
    result = []
    for char in text:
        if char in REPLACEMENT_MAP and random.random() < 0.5:
            result.append(REPLACEMENT_MAP[char])
        else:
            result.append(char)
    return ''.join(result)

async def process_text(text: str) -> str:
    """Обработка текста с ограничением времени"""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(replace_letters, text),
            timeout=2.0
        )
    except asyncio.TimeoutError:
        return "Слишком длинный текст, попробуйте покороче"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    await update.message.reply_text(
        "Отправьте текст, я заменю буквы а,е,с,о,р,х,у на латинские с шансом 50%"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений"""
    user_message = update.message.text
    
    if not user_message.strip():
        await update.message.reply_text("Отправьте текст")
        return
    
    # Отправляем сообщение о обработке
    processing_msg = await update.message.reply_text("⏳")
    
    # Обрабатываем текст
    result = await process_text(user_message)
    
    # Удаляем сообщение о обработке
    await processing_msg.delete()
    
    # Отправляем результат (только текст)
    await update.message.reply_text(result)

def main() -> None:
    """Запуск бота"""
    BOT_TOKEN = "8334892286:AAH7P7zzS6Uie3Sb8Llglg-BqiXBxais6VE"  # ← ВСТАВЬТЕ ТОКЕН ЗДЕСЬ
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Бот запущен...")
    app.run_polling()

if __name__ == '__main__':
    main()