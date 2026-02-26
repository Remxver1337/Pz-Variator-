import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
MAIN_MENU, QUESTION_FLOW, TOUR_REQUEST = range(3)

# Данные для хранения заявок (в реальном проекте используйте БД)
user_requests = {}

# Клавиатура главного меню
def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("✍️ Создать заявку на подбор тура", callback_data="create_request")],
        [InlineKeyboardButton("❓ Ответы на вопросы", callback_data="faq")],
        [InlineKeyboardButton("📞 Остались вопросы? Связаться с менеджером", callback_data="contact")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Клавиатура для разделов заявки
def get_request_sections_keyboard():
    keyboard = [
        [InlineKeyboardButton("🌍 Направление и страна", callback_data="section_direction")],
        [InlineKeyboardButton("💰 Бюджет", callback_data="section_budget")],
        [InlineKeyboardButton("📅 Даты и продолжительность", callback_data="section_dates")],
        [InlineKeyboardButton("🏖️ Тип отдыха", callback_data="section_type")],
        [InlineKeyboardButton("🏨 Размещение", callback_data="section_accommodation")],
        [InlineKeyboardButton("✈️ Транспорт", callback_data="section_transport")],
        [InlineKeyboardButton("👨‍👩‍👧 Состав туристов", callback_data="section_tourists")],
        [InlineKeyboardButton("✨ Дополнительные пожелания", callback_data="section_additional")],
        [InlineKeyboardButton("✅ Завершить и отправить заявку", callback_data="submit_request")],
        [InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Клавиатура для FAQ
def get_faq_keyboard():
    keyboard = [
        [InlineKeyboardButton("Как подобрать тур?", callback_data="faq_how")],
        [InlineKeyboardButton("Документы для поездки", callback_data="faq_docs")],
        [InlineKeyboardButton("Оплата и возврат", callback_data="faq_payment")],
        [InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Клавиатура для возврата в разделы заявки
def get_back_to_sections_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔙 Вернуться к разделам заявки", callback_data="back_to_sections")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    welcome_message = (
        f"👋 Здравствуйте, {user.first_name}!\n\n"
        "Я помощник по подбору туров. Я помогу вам:\n"
        "• Создать заявку на подбор тура\n"
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
    query = update.callback_query
    await query.answer()
    
    if query.data == "create_request":
        # Инициализация новой заявки
        user_id = query.from_user.id
        user_requests[user_id] = {}
        
        await query.edit_message_text(
            "📝 *Создание заявки на подбор тура*\n\n"
            "Заполните информацию по разделам ниже. "
            "После заполнения всех разделов нажмите 'Завершить и отправить'.\n\n"
            "Выберите раздел для заполнения:",
            reply_markup=get_request_sections_keyboard(),
            parse_mode='Markdown'
        )
        return TOUR_REQUEST
    
    elif query.data == "faq":
        await query.edit_message_text(
            "❓ *Часто задаваемые вопросы*\n\n"
            "Выберите интересующий вас вопрос:",
            reply_markup=get_faq_keyboard(),
            parse_mode='Markdown'
        )
        return QUESTION_FLOW
    
    elif query.data == "contact":
        contact_message = (
            "📞 *Остались вопросы?*\n\n"
            "Вы можете связаться с нашим менеджером:\n"
            "• По телефону: +7 (999) 123-45-67\n"
            "• В Telegram: @tour_manager\n"
            "• По email: manager@tours.ru\n\n"
            "Мы ответим на все ваши вопросы с 10:00 до 20:00 по московскому времени."
        )
        await query.edit_message_text(
            contact_message,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        return MAIN_MENU

async def faq_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик FAQ"""
    query = update.callback_query
    await query.answer()
    
    faq_answers = {
        "faq_how": (
            "🔍 *Как подобрать тур?*\n\n"
            "Для подбора тура вам нужно:\n"
            "1. Определить направление и страну\n"
            "2. Установить бюджет\n"
            "3. Выбрать даты поездки\n"
            "4. Определить тип отдыха\n"
            "5. Выбрать категорию отеля\n"
            "6. Указать состав туристов\n\n"
            "Вы можете создать заявку через главное меню, и наш менеджер подберет для вас лучшие варианты!"
        ),
        "faq_docs": (
            "📋 *Документы для поездки*\n\n"
            "Для выезда за границу обычно требуются:\n"
            "• Загранпаспорт (срок действия не менее 6 месяцев)\n"
            "• Виза (для некоторых стран)\n"
            "• Медицинская страховка\n"
            "• Авиабилеты и ваучеры на отель\n"
            "• Доверенность на выезд детей (если едут без родителей)"
        ),
        "faq_payment": (
            "💳 *Оплата и возврат*\n\n"
            "• Предоплата для бронирования тура: 30-50%\n"
            "• Полная оплата за 7-14 дней до вылета\n"
            "• Возврат средств при отказе от тура зависит от условий отеля и авиакомпании\n"
            "• Рекомендуем оформлять страховку от невыезда"
        )
    }
    
    if query.data in faq_answers:
        await query.edit_message_text(
            faq_answers[query.data],
            reply_markup=get_faq_keyboard(),
            parse_mode='Markdown'
        )
    elif query.data == "back_to_main":
        await query.edit_message_text(
            "Главное меню:",
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU

async def tour_request_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик разделов заявки"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if query.data == "back_to_main":
        await query.edit_message_text(
            "Главное меню:",
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    
    elif query.data == "back_to_sections":
        await query.edit_message_text(
            "📝 *Создание заявки на подбор тура*\n\n"
            "Выберите раздел для заполнения:",
            reply_markup=get_request_sections_keyboard(),
            parse_mode='Markdown'
        )
        return TOUR_REQUEST
    
    elif query.data == "submit_request":
        # Проверяем, заполнены ли обязательные разделы
        required_sections = ['direction', 'budget', 'dates', 'tourists']
        missing_sections = []
        
        for section in required_sections:
            if section not in user_requests.get(user_id, {}):
                missing_sections.append(section)
        
        if missing_sections:
            await query.edit_message_text(
                "⚠️ *Не все обязательные разделы заполнены!*\n\n"
                "Пожалуйста, заполните следующие разделы:\n"
                "• Направление и страна\n"
                "• Бюджет\n"
                "• Даты и продолжительность\n"
                "• Состав туристов\n\n"
                "После заполнения всех разделов нажмите 'Завершить и отправить'.",
                reply_markup=get_request_sections_keyboard(),
                parse_mode='Markdown'
            )
            return TOUR_REQUEST
        
        # Формируем текст заявки
        request_data = user_requests[user_id]
        request_text = (
            "✅ *Новая заявка на подбор тура*\n\n"
            f"*Направление и страна:*\n{request_data.get('direction', 'Не указано')}\n\n"
            f"*Бюджет:*\n{request_data.get('budget', 'Не указано')}\n\n"
            f"*Даты и продолжительность:*\n{request_data.get('dates', 'Не указано')}\n\n"
            f"*Тип отдыха:*\n{request_data.get('type', 'Не указано')}\n\n"
            f"*Размещение:*\n{request_data.get('accommodation', 'Не указано')}\n\n"
            f"*Транспорт:*\n{request_data.get('transport', 'Не указано')}\n\n"
            f"*Состав туристов:*\n{request_data.get('tourists', 'Не указано')}\n\n"
            f"*Дополнительные пожелания:*\n{request_data.get('additional', 'Не указано')}"
        )
        
        # Отправляем заявку менеджеру (замените на ID чата менеджера)
        manager_chat_id = 123456789  # Замените на реальный ID
        try:
            await context.bot.send_message(
                chat_id=manager_chat_id,
                text=request_text,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send to manager: {e}")
        
        # Подтверждение пользователю
        await query.edit_message_text(
            "✅ *Заявка успешно отправлена!*\n\n"
            "Наш менеджер свяжется с вами в ближайшее время для подбора лучших вариантов.\n"
            "Спасибо за обращение!",
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        
        # Очищаем данные пользователя
        del user_requests[user_id]
        return MAIN_MENU
    
    # Обработка выбора конкретного раздела
    section_info = {
        "section_direction": (
            "🌍 *Направление и страна*\n\n"
            "Пожалуйста, укажите:\n"
            "• Желаемую страну или направление\n"
            "• Важны ли климатические особенности\n"
            "• Есть ли виза, нужна ли помощь с визой\n"
            "• Требования к безопасности"
        ),
        "section_budget": (
            "💰 *Бюджет*\n\n"
            "Пожалуйста, укажите:\n"
            "• Общую сумму на человека\n"
            "• Входит ли перелёт в бюджет\n"
            "• Желаемое питание (RO, BB, HB, AI)\n"
            "• Бюджет на дополнительные расходы (экскурсии, страховка, трансфер)"
        ),
        "section_dates": (
            "📅 *Даты и продолжительность*\n\n"
            "Пожалуйста, укажите:\n"
            "• Точные или гибкие даты\n"
            "• Желаемое количество ночей\n"
            "• Готовы ли рассматривать высокий сезон (выше цена)"
        ),
        "section_type": (
            "🏖️ *Тип отдыха*\n\n"
            "Выберите предпочтительный тип отдыха:\n"
            "• Пляжный\n"
            "• Экскурсионный\n"
            "• Активный (походы, спорт)\n"
            "• Семейный\n"
            "• Романтический\n"
            "• Молодёжный"
        ),
        "section_accommodation": (
            "🏨 *Размещение*\n\n"
            "Пожалуйста, укажите:\n"
            "• Желаемую категорию отеля (3*, 4*, 5*)\n"
            "• Предпочтительную локацию (центр, первая линия, тихий район)\n"
            "• Важную инфраструктуру (бассейн, SPA, анимация, детский клуб)"
        ),
        "section_transport": (
            "✈️ *Транспорт*\n\n"
            "Пожалуйста, укажите:\n"
            "• Прямой рейс или возможна пересадка\n"
            "• Удобное время вылета (особенно с детьми)\n"
            "• Предпочтительный аэропорт вылета"
        ),
        "section_tourists": (
            "👨‍👩‍👧 *Состав туристов*\n\n"
            "Пожалуйста, укажите:\n"
            "• Количество взрослых и детей\n"
            "• Возраст детей\n"
            "• Особые потребности (аллергии, диеты, инвалидность)"
        ),
        "section_additional": (
            "✨ *Дополнительные пожелания*\n\n"
            "Пожалуйста, укажите:\n"
            "• Наличие экскурсий\n"
            "• Русскоговорящий гид\n"
            "• Конкретный регион или отель\n"
            "• Медицинская страховка с расширенным покрытием"
        )
    }
    
    if query.data in section_info:
        # Сохраняем текущий раздел в контексте
        context.user_data['current_section'] = query.data
        
        await query.edit_message_text(
            section_info[query.data],
            reply_markup=get_back_to_sections_keyboard(),
            parse_mode='Markdown'
        )
        # Переходим в режим ожидания текстового ответа
        return TOUR_REQUEST

async def save_section_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранение данных из текстового ответа"""
    user_id = update.effective_user.id
    section = context.user_data.get('current_section')
    
    if section and user_id in user_requests:
        # Сохраняем ответ пользователя
        user_requests[user_id][section.replace('section_', '')] = update.message.text
        
        await update.message.reply_text(
            "✅ Информация сохранена!\n\n"
            "Выберите следующий раздел для заполнения:",
            reply_markup=get_request_sections_keyboard()
        )
        return TOUR_REQUEST
    
    # Если не в процессе заполнения заявки
    await update.message.reply_text(
        "Пожалуйста, используйте меню для навигации.",
        reply_markup=get_main_menu_keyboard()
    )
    return MAIN_MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена действия"""
    await update.message.reply_text(
        "Действие отменено. Возврат в главное меню.",
        reply_markup=get_main_menu_keyboard()
    )
    return MAIN_MENU

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка обычных сообщений"""
    await update.message.reply_text(
        "Пожалуйста, используйте кнопки меню для навигации.",
        reply_markup=get_main_menu_keyboard()
    )
    return MAIN_MENU

def main():
    """Запуск бота"""
    # Создаем приложение
    application = Application.builder().token("8598049295:AAG0vdRpvKLvakRU8QUICbFOUQs1eJM6RQg").build()
    
    # Создаем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [
                CallbackQueryHandler(main_menu_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
            ],
            QUESTION_FLOW: [
                CallbackQueryHandler(faq_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
            ],
            TOUR_REQUEST: [
                CallbackQueryHandler(tour_request_handler),
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_section_data)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(conv_handler)
    
    # Запускаем бота
    print("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()