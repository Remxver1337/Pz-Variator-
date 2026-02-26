import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

# Настройка логирования
logging.basicConfig(
    format='%(asime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler (все шаги анкеты)
(
    MAIN_MENU,
    QUESTION_FLOW,
    DIRECTION,
    BUDGET,
    DATES,
    TYPE,
    ACCOMMODATION,
    TRANSPORT,
    TOURISTS,
    ADDITIONAL,
    CONFIRMATION
) = range(11)

# ID чата менеджера
MANAGER_CHAT_ID = "@WindowVadim"  # или числовой ID: 123456789

# Клавиатура главного меню
def get_main_menu_keyboard():
    keyboard = [
        [KeyboardButton("✍️ Создать заявку на подбор тура")],
        [KeyboardButton("❓ Ответы на вопросы")],
        [KeyboardButton("📞 Остались вопросы?")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Клавиатура для FAQ
def get_faq_keyboard():
    keyboard = [
        [KeyboardButton("Как подобрать тур?")],
        [KeyboardButton("Документы для поездки")],
        [KeyboardButton("Оплата и возврат")],
        [KeyboardButton("🔙 В главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Клавиатура для подтверждения
def get_confirmation_keyboard():
    keyboard = [
        [KeyboardButton("✅ Отправить заявку")],
        [KeyboardButton("🔄 Заполнить заново")],
        [KeyboardButton("🔙 В главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    welcome_message = (
        f"👋 Здравствуйте, {user.first_name}!\n\n"
        "Я помощник по подбору туров. Я помогу вам:\n"
        "• Создать заявку на подбор тура (последовательный опрос)\n"
        "• Ответить на популярные вопросы\n"
        "• Связаться с менеджером\n\n"
        "Выберите интересующий вас раздел:"
    )
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=get_main_menu_keyboard()
    )
    return MAIN_MENU

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик главного меню"""
    text = update.message.text
    
    if text == "✍️ Создать заявку на подбор тура":
        # Инициализация новой заявки
        context.user_data.clear()
        context.user_data['request'] = {}
        
        await update.message.reply_text(
            "📝 *Начинаем создание заявки на подбор тура*\n\n"
            "Я буду задавать вам вопросы по очереди. Отвечайте на них одним сообщением.\n\n"
            "**Вопрос 1/9:**\n"
            "🌍 *Куда хотите поехать?*\n"
            "(Страна, город, направление)",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode='Markdown'
        )
        return DIRECTION
    
    elif text == "❓ Ответы на вопросы":
        await update.message.reply_text(
            "❓ *Часто задаваемые вопросы*\n\n"
            "Выберите интересующий вас вопрос:",
            reply_markup=get_faq_keyboard(),
            parse_mode='Markdown'
        )
        return QUESTION_FLOW
    
    elif text == "📞 Остались вопросы?":
        contact_message = (
            "📞 *Остались вопросы?*\n\n"
            "Вы можете связаться с нашим менеджером:\n"
            "• В Telegram: @WindowVadim\n"
            "• По телефону: +7 (999) 123-45-67\n"
            "• По email: manager@tours.ru\n\n"
            "Мы ответим на все ваши вопросы с 10:00 до 20:00 по московскому времени."
        )
        await update.message.reply_text(
            contact_message,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return MAIN_MENU

async def faq_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик FAQ"""
    text = update.message.text
    
    faq_answers = {
        "Как подобрать тур?": (
            "🔍 *Как подобрать тур?*\n\n"
            "Для подбора тура я задам вам несколько вопросов:\n"
            "1. Направление и страна\n"
            "2. Бюджет\n"
            "3. Даты поездки\n"
            "4. Тип отдыха\n"
            "5. Категория отеля\n"
            "6. Состав туристов\n\n"
            "Просто нажмите 'Создать заявку' в главном меню, и я помогу вам!"
        ),
        "Документы для поездки": (
            "📋 *Документы для поездки*\n\n"
            "Для выезда за границу обычно требуются:\n"
            "• Загранпаспорт (срок действия не менее 6 месяцев)\n"
            "• Виза (для некоторых стран)\n"
            "• Медицинская страховка\n"
            "• Авиабилеты и ваучеры на отель\n"
            "• Доверенность на выезд детей (если едут без родителей)"
        ),
        "Оплата и возврат": (
            "💳 *Оплата и возврат*\n\n"
            "• Предоплата для бронирования тура: 30-50%\n"
            "• Полная оплата за 7-14 дней до вылета\n"
            "• Возврат средств при отказе от тура зависит от условий отеля и авиакомпании\n"
            "• Рекомендуем оформлять страховку от невыезда"
        )
    }
    
    if text in faq_answers:
        await update.message.reply_text(
            faq_answers[text],
            reply_markup=get_faq_keyboard(),
            parse_mode='Markdown'
        )
    elif text == "🔙 В главное меню":
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    return QUESTION_FLOW

async def get_direction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение направления"""
    context.user_data['request']['direction'] = update.message.text
    
    await update.message.reply_text(
        "✅ Информация сохранена!\n\n"
        "**Вопрос 2/9:**\n"
        "💰 *Какой у вас бюджет?*\n"
        "(Общая сумма на человека, включен ли перелёт, питание и т.д.)",
        parse_mode='Markdown'
    )
    return BUDGET

async def get_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение бюджета"""
    context.user_data['request']['budget'] = update.message.text
    
    await update.message.reply_text(
        "✅ Информация сохранена!\n\n"
        "**Вопрос 3/9:**\n"
        "📅 *Когда планируете поездку и на сколько дней?*\n"
        "(Точные или гибкие даты, количество ночей)",
        parse_mode='Markdown'
    )
    return DATES

async def get_dates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение дат"""
    context.user_data['request']['dates'] = update.message.text
    
    await update.message.reply_text(
        "✅ Информация сохранена!\n\n"
        "**Вопрос 4/9:**\n"
        "🏖️ *Какой тип отдыха предпочитаете?*\n"
        "(Пляжный, экскурсионный, активный, семейный, романтический, молодёжный)",
        parse_mode='Markdown'
    )
    return TYPE

async def get_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение типа отдыха"""
    context.user_data['request']['type'] = update.message.text
    
    await update.message.reply_text(
        "✅ Информация сохранена!\n\n"
        "**Вопрос 5/9:**\n"
        "🏨 *Какие требования к размещению?*\n"
        "(Категория отеля, локация, инфраструктура)",
        parse_mode='Markdown'
    )
    return ACCOMMODATION

async def get_accommodation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение требований к размещению"""
    context.user_data['request']['accommodation'] = update.message.text
    
    await update.message.reply_text(
        "✅ Информация сохранена!\n\n"
        "**Вопрос 6/9:**\n"
        "✈️ *Какой транспорт предпочитаете?*\n"
        "(Прямой рейс или с пересадкой, время вылета, аэропорт)",
        parse_mode='Markdown'
    )
    return TRANSPORT

async def get_transport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение требований к транспорту"""
    context.user_data['request']['transport'] = update.message.text
    
    await update.message.reply_text(
        "✅ Информация сохранена!\n\n"
        "**Вопрос 7/9:**\n"
        "👨‍👩‍👧 *Кто едет?*\n"
        "(Количество взрослых и детей, возраст детей, особые потребности)",
        parse_mode='Markdown'
    )
    return TOURISTS

async def get_tourists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение состава туристов"""
    context.user_data['request']['tourists'] = update.message.text
    
    await update.message.reply_text(
        "✅ Информация сохранена!\n\n"
        "**Вопрос 8/9:**\n"
        "✨ *Дополнительные пожелания?*\n"
        "(Экскурсии, русскоговорящий гид, конкретный отель, страховка и т.д.)",
        parse_mode='Markdown'
    )
    return ADDITIONAL

async def get_additional(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение дополнительных пожеланий"""
    context.user_data['request']['additional'] = update.message.text
    
    # Формируем предварительный просмотр заявки
    request = context.user_data['request']
    preview = (
        "📋 *Предварительный просмотр заявки*\n\n"
        f"🌍 *Направление:* {request.get('direction', 'Не указано')}\n"
        f"💰 *Бюджет:* {request.get('budget', 'Не указано')}\n"
        f"📅 *Даты:* {request.get('dates', 'Не указано')}\n"
        f"🏖️ *Тип отдыха:* {request.get('type', 'Не указано')}\n"
        f"🏨 *Размещение:* {request.get('accommodation', 'Не указано')}\n"
        f"✈️ *Транспорт:* {request.get('transport', 'Не указано')}\n"
        f"👨‍👩‍👧 *Состав:* {request.get('tourists', 'Не указано')}\n"
        f"✨ *Дополнительно:* {request.get('additional', 'Не указано')}\n\n"
        "Все ли верно? Вы можете отправить заявку или заполнить заново."
    )
    
    await update.message.reply_text(
        preview,
        reply_markup=get_confirmation_keyboard(),
        parse_mode='Markdown'
    )
    return CONFIRMATION

async def confirmation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик подтверждения заявки"""
    text = update.message.text
    user = update.effective_user
    
    if text == "✅ Отправить заявку":
        # Формируем финальную заявку
        request = context.user_data['request']
        username = user.username or "Не указан"
        first_name = user.first_name or "Не указан"
        
        final_request = (
            "✅ *НОВАЯ ЗАЯВКА НА ПОДБОР ТУРА*\n\n"
            f"👤 *Клиент:* @{username} ({first_name})\n"
            f"🆔 *ID:* {user.id}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🌍 *Направление:*\n{request.get('direction', 'Не указано')}\n\n"
            f"💰 *Бюджет:*\n{request.get('budget', 'Не указано')}\n\n"
            f"📅 *Даты:*\n{request.get('dates', 'Не указано')}\n\n"
            f"🏖️ *Тип отдыха:*\n{request.get('type', 'Не указано')}\n\n"
            f"🏨 *Размещение:*\n{request.get('accommodation', 'Не указано')}\n\n"
            f"✈️ *Транспорт:*\n{request.get('transport', 'Не указано')}\n\n"
            f"👨‍👩‍👧 *Состав туристов:*\n{request.get('tourists', 'Не указано')}\n\n"
            f"✨ *Дополнительно:*\n{request.get('additional', 'Не указано')}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📅 *Время отправки:* {update.message.date.strftime('%d.%m.%Y %H:%M')}"
        )
        
        # Отправляем менеджеру
        try:
            await context.bot.send_message(
                chat_id=MANAGER_CHAT_ID,
                text=final_request,
                parse_mode='Markdown'
            )
            
            await update.message.reply_text(
                "✅ *Заявка успешно отправлена!*\n\n"
                f"Менеджер @WindowVadim свяжется с вами в ближайшее время.\n"
                "Спасибо за обращение!",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Failed to send to manager: {e}")
            await update.message.reply_text(
                "❌ Ошибка при отправке. Пожалуйста, свяжитесь с менеджером напрямую: @WindowVadim",
                reply_markup=get_main_menu_keyboard()
            )
        
        # Очищаем данные
        context.user_data.clear()
        return MAIN_MENU
    
    elif text == "🔄 Заполнить заново":
        context.user_data['request'] = {}
        await update.message.reply_text(
            "📝 *Начинаем заново*\n\n"
            "**Вопрос 1/9:**\n"
            "🌍 *Куда хотите поехать?*",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode='Markdown'
        )
        return DIRECTION
    
    elif text == "🔙 В главное меню":
        context.user_data.clear()
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена действия"""
    context.user_data.clear()
    await update.message.reply_text(
        "Создание заявки отменено. Возврат в главное меню.",
        reply_markup=get_main_menu_keyboard()
    )
    return MAIN_MENU

async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка неизвестных сообщений"""
    await update.message.reply_text(
        "Извините, я не понимаю эту команду. Пожалуйста, используйте кнопки меню.",
        reply_markup=get_main_menu_keyboard()
    )
    return MAIN_MENU

def main():
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token("8598049295:AAG0vdRpvKLvakRU8QUICbFOUQs1eJM6RQg").build()
    
    # Создаем ConversationHandler с последовательными шагами
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_handler)],
            QUESTION_FLOW: [MessageHandler(filters.TEXT & ~filters.COMMAND, faq_handler)],
            DIRECTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_direction)],
            BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_budget)],
            DATES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dates)],
            TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_type)],
            ACCOMMODATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_accommodation)],
            TRANSPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_transport)],
            TOURISTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tourists)],
            ADDITIONAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_additional)],
            CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirmation_handler)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.COMMAND, handle_unknown))
    
    # Запускаем бота
    print("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()