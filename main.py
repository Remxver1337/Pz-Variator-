import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
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

# Данные для хранения заявок
user_requests = {}

# ID чата менеджера (замените на @WindowVadim)
MANAGER_CHAT_ID = "@WindowVadim"  # Для отправки в чат с менеджером
# Или используйте числовой ID: MANAGER_CHAT_ID = 123456789

# Клавиатура главного меню (обычные кнопки)
def get_main_menu_keyboard():
    keyboard = [
        [KeyboardButton("✍️ Создать заявку на подбор тура")],
        [KeyboardButton("❓ Ответы на вопросы")],
        [KeyboardButton("📞 Остались вопросы?")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Клавиатура для разделов заявки
def get_request_sections_keyboard():
    keyboard = [
        [KeyboardButton("🌍 Направление и страна")],
        [KeyboardButton("💰 Бюджет")],
        [KeyboardButton("📅 Даты и продолжительность")],
        [KeyboardButton("🏖️ Тип отдыха")],
        [KeyboardButton("🏨 Размещение")],
        [KeyboardButton("✈️ Транспорт")],
        [KeyboardButton("👨‍👩‍👧 Состав туристов")],
        [KeyboardButton("✨ Дополнительные пожелания")],
        [KeyboardButton("✅ Завершить и отправить заявку")],
        [KeyboardButton("🔙 В главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Клавиатура для возврата к разделам заявки
def get_back_to_sections_keyboard():
    keyboard = [
        [KeyboardButton("🔙 Вернуться к разделам заявки")]
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
    text = update.message.text
    
    if text == "✍️ Создать заявку на подбор тура":
        # Инициализация новой заявки
        user_id = update.effective_user.id
        user_requests[user_id] = {}
        
        await update.message.reply_text(
            "📝 *Создание заявки на подбор тура*\n\n"
            "Заполните информацию по разделам ниже. "
            "После заполнения всех разделов нажмите 'Завершить и отправить'.\n\n"
            "Выберите раздел для заполнения:",
            reply_markup=get_request_sections_keyboard(),
            parse_mode='Markdown'
        )
        return TOUR_REQUEST
    
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
            "Для подбора тура вам нужно:\n"
            "1. Определить направление и страну\n"
            "2. Установить бюджет\n"
            "3. Выбрать даты поездки\n"
            "4. Определить тип отдыха\n"
            "5. Выбрать категорию отеля\n"
            "6. Указать состав туристов\n\n"
            "Вы можете создать заявку через главное меню, и наш менеджер подберет для вас лучшие варианты!"
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

async def tour_request_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик разделов заявки"""
    text = update.message.text
    user_id = update.effective_user.id
    
    if text == "🔙 В главное меню":
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    
    elif text == "🔙 Вернуться к разделам заявки":
        await update.message.reply_text(
            "📝 *Создание заявки на подбор тура*\n\n"
            "Выберите раздел для заполнения:",
            reply_markup=get_request_sections_keyboard(),
            parse_mode='Markdown'
        )
        return TOUR_REQUEST
    
    elif text == "✅ Завершить и отправить заявку":
        # Проверяем, заполнены ли обязательные разделы
        required_sections = ['direction', 'budget', 'dates', 'tourists']
        missing_sections = []
        section_names = {
            'direction': 'Направление и страна',
            'budget': 'Бюджет',
            'dates': 'Даты и продолжительность',
            'tourists': 'Состав туристов'
        }
        
        for section in required_sections:
            if section not in user_requests.get(user_id, {}):
                missing_sections.append(section_names[section])
        
        if missing_sections:
            missing_text = "\n".join([f"• {s}" for s in missing_sections])
            await update.message.reply_text(
                f"⚠️ *Не все обязательные разделы заполнены!*\n\n"
                f"Пожалуйста, заполните следующие разделы:\n{missing_text}\n\n"
                "После заполнения всех разделов нажмите 'Завершить и отправить'.",
                reply_markup=get_request_sections_keyboard(),
                parse_mode='Markdown'
            )
            return TOUR_REQUEST
        
        # Формируем текст заявки
        request_data = user_requests[user_id]
        user_info = update.effective_user
        username = user_info.username or "Не указан"
        first_name = user_info.first_name or "Не указан"
        
        request_text = (
            "✅ *НОВАЯ ЗАЯВКА НА ПОДБОР ТУРА*\n\n"
            f"👤 *Клиент:* @{username} ({first_name})\n"
            f"🆔 *ID:* {user_id}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🌍 *Направление и страна:*\n{request_data.get('direction', 'Не указано')}\n\n"
            f"💰 *Бюджет:*\n{request_data.get('budget', 'Не указано')}\n\n"
            f"📅 *Даты и продолжительность:*\n{request_data.get('dates', 'Не указано')}\n\n"
            f"🏖️ *Тип отдыха:*\n{request_data.get('type', 'Не указано')}\n\n"
            f"🏨 *Размещение:*\n{request_data.get('accommodation', 'Не указано')}\n\n"
            f"✈️ *Транспорт:*\n{request_data.get('transport', 'Не указано')}\n\n"
            f"👨‍👩‍👧 *Состав туристов:*\n{request_data.get('tourists', 'Не указано')}\n\n"
            f"✨ *Дополнительные пожелания:*\n{request_data.get('additional', 'Не указано')}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📅 *Время отправки:* {update.message.date.strftime('%d.%m.%Y %H:%M')}"
        )
        
        # Отправляем заявку менеджеру @WindowVadim
        try:
            await context.bot.send_message(
                chat_id=MANAGER_CHAT_ID,
                text=request_text,
                parse_mode='Markdown'
            )
            
            # Подтверждение пользователю
            await update.message.reply_text(
                "✅ *Заявка успешно отправлена!*\n\n"
                f"Наш менеджер @WindowVadim свяжется с вами в ближайшее время для подбора лучших вариантов.\n"
                "Спасибо за обращение!",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Failed to send to manager: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при отправке заявки. Пожалуйста, попробуйте позже или свяжитесь с менеджером напрямую: @WindowVadim",
                reply_markup=get_main_menu_keyboard()
            )
        
        # Очищаем данные пользователя
        if user_id in user_requests:
            del user_requests[user_id]
        return MAIN_MENU
    
    # Обработка выбора конкретного раздела
    section_info = {
        "🌍 Направление и страна": (
            "🌍 *Направление и страна*\n\n"
            "Пожалуйста, напишите одним сообщением:\n"
            "• Желаемую страну или направление\n"
            "• Важны ли климатические особенности\n"
            "• Есть ли виза, нужна ли помощь с визой\n"
            "• Требования к безопасности"
        ),
        "💰 Бюджет": (
            "💰 *Бюджет*\n\n"
            "Пожалуйста, напишите одним сообщением:\n"
            "• Общую сумму на человека\n"
            "• Входит ли перелёт в бюджет\n"
            "• Желаемое питание (RO, BB, HB, AI)\n"
            "• Бюджет на дополнительные расходы (экскурсии, страховка, трансфер)"
        ),
        "📅 Даты и продолжительность": (
            "📅 *Даты и продолжительность*\n\n"
            "Пожалуйста, напишите одним сообщением:\n"
            "• Точные или гибкие даты\n"
            "• Желаемое количество ночей\n"
            "• Готовы ли рассматривать высокий сезон (выше цена)"
        ),
        "🏖️ Тип отдыха": (
            "🏖️ *Тип отдыха*\n\n"
            "Пожалуйста, напишите одним сообщением, какой тип отдыха предпочитаете:\n"
            "• Пляжный\n"
            "• Экскурсионный\n"
            "• Активный (походы, спорт)\n"
            "• Семейный\n"
            "• Романтический\n"
            "• Молодёжный"
        ),
        "🏨 Размещение": (
            "🏨 *Размещение*\n\n"
            "Пожалуйста, напишите одним сообщением:\n"
            "• Желаемую категорию отеля (3*, 4*, 5*)\n"
            "• Предпочтительную локацию (центр, первая линия, тихий район)\n"
            "• Важную инфраструктуру (бассейн, SPA, анимация, детский клуб)"
        ),
        "✈️ Транспорт": (
            "✈️ *Транспорт*\n\n"
            "Пожалуйста, напишите одним сообщением:\n"
            "• Прямой рейс или возможна пересадка\n"
            "• Удобное время вылета (особенно с детьми)\n"
            "• Предпочтительный аэропорт вылета"
        ),
        "👨‍👩‍👧 Состав туристов": (
            "👨‍👩‍👧 *Состав туристов*\n\n"
            "Пожалуйста, напишите одним сообщением:\n"
            "• Количество взрослых и детей\n"
            "• Возраст детей\n"
            "• Особые потребности (аллергии, диеты, инвалидность)"
        ),
        "✨ Дополнительные пожелания": (
            "✨ *Дополнительные пожелания*\n\n"
            "Пожалуйста, напишите одним сообщением:\n"
            "• Наличие экскурсий\n"
            "• Русскоговорящий гид\n"
            "• Конкретный регион или отель\n"
            "• Медицинская страховка с расширенным покрытием"
        )
    }
    
    if text in section_info:
        # Сохраняем текущий раздел в контексте
        context.user_data['current_section'] = text
        
        await update.message.reply_text(
            section_info[text],
            reply_markup=get_back_to_sections_keyboard(),
            parse_mode='Markdown'
        )
        return TOUR_REQUEST

async def save_section_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранение данных из текстового ответа"""
    user_id = update.effective_user.id
    section = context.user_data.get('current_section')
    
    if section and user_id in user_requests:
        # Преобразуем название раздела в ключ для словаря
        section_key_map = {
            "🌍 Направление и страна": "direction",
            "💰 Бюджет": "budget",
            "📅 Даты и продолжительность": "dates",
            "🏖️ Тип отдыха": "type",
            "🏨 Размещение": "accommodation",
            "✈️ Транспорт": "transport",
            "👨‍👩‍👧 Состав туристов": "tourists",
            "✨ Дополнительные пожелания": "additional"
        }
        
        key = section_key_map.get(section)
        if key:
            user_requests[user_id][key] = update.message.text
            
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
    
    # Создаем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_handler)
            ],
            QUESTION_FLOW: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, faq_handler)
            ],
            TOUR_REQUEST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tour_request_handler)
            ],
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