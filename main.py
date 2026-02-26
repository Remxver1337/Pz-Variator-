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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
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
        [KeyboardButton("📚 Ответы на вопросы")],
        [KeyboardButton("❓ Остались вопросы?")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Клавиатура для FAQ
def get_faq_keyboard():
    keyboard = [
        [KeyboardButton("🔍 Как подобрать тур?")],
        [KeyboardButton("📋 Документы для поездки")],
        [KeyboardButton("💳 Оплата и возврат")],
        [KeyboardButton("🖼️ Вернуться в главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Клавиатура для этапов заполнения анкеты (с кнопками назад)
def get_question_keyboard():
    keyboard = [
        [KeyboardButton("🔙 Вернуться назад")],
        [KeyboardButton("🖼️ Вернуться в главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_message = (
        "😉 *Добро пожаловать в бот канала Window Tour!*\n\n"
        "🗣️ Бот предназначен для просмотра актуальных туров. Оформление проходит через менеджера @WindowVadim\n\n"
        "🗣️ Также в бот добавлены и другие функции, которые помогут вам лучше ориентироваться по нашему каналу\n\n"
        "🗣️ Бот принадлежит группе: https://t.me/WindowTour\n\n"
        "🗣️ Просмотр туров производится только в боте либо через менеджера @WindowVadim\n\n"
        "Выберите интересующий вас раздел:"
    )
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )
    return MAIN_MENU

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик главного меню"""
    text = update.message.text
    
    if text == "✍️ Создать заявку на подбор тура":
        # Инициализация новой заявки
        context.user_data.clear()
        context.user_data['request'] = {}
        context.user_data['question_index'] = 1  # Для отслеживания текущего вопроса
        
        await update.message.reply_text(
            "📝 *Начинаем создание заявки на подбор тура*\n\n"
            "Я буду задавать вам вопросы по очереди. Отвечайте на них подробно, чтобы менеджер мог точнее подобрать тур.\n\n"
            "➖➖➖➖➖➖➖➖➖➖\n"
            "❓ *Вопрос 1/8:*\n"
            "🌍 *Куда хотите поехать?*\n"
            "(Страна, город, направление)",
            reply_markup=get_question_keyboard(),
            parse_mode='Markdown'
        )
        return DIRECTION
    
    elif text == "📚 Ответы на вопросы":
        await update.message.reply_text(
            "📚 *Ответы на вопросы*\n\n"
            "Выберите интересующий вас вопрос:",
            reply_markup=get_faq_keyboard(),
            parse_mode='Markdown'
        )
        return QUESTION_FLOW
    
    elif text == "❓ Остались вопросы?":
        contact_message = (
            "❓ *Остались вопросы? Пиши!*\n\n"
            "В порядке очереди мы тебе обязательно ответим 👨‍💻\n\n"
            "Напиши нам: @WindowVadim"
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
        "🔍 Как подобрать тур?": (
            "🔍 *Как подобрать тур?*\n\n"
            "Для подбора тура Вы можете заполнить анкету, которая включает в себя следующие вопросы:\n\n"
            "🌍 *Куда хотите поехать?*\n\n"
            "💰 *Какой у вас бюджет?*\n\n"
            "📅 *Когда планируете поездку и на сколько дней?*\n\n"
            "🏖️ *Какой тип отдыха предпочитаете?*\n\n"
            "🏨 *Какие требования к размещению?*\n\n"
            "✈️ *Какой транспорт предпочитаете?*\n\n"
            "👨‍👩‍👧 *Кто едет?*\n\n"
            "✨ *Дополнительные пожелания?*\n\n"
            "После заполнения анкеты отправьте её менеджеру @WindowVadim и он подберет для Вас лучшие варианты и рассчитает стоимость!"
        ),
        "📋 Документы для поездки": (
            "📋 *Документы для поездки*\n\n"
            "Для выезда за границу обычно требуются:\n"
            "• Загранпаспорт (срок действия не менее 6 месяцев)\n"
            "• Виза (для некоторых стран)\n"
            "• Медицинская страховка\n"
            "• Авиабилеты и ваучеры на отель\n"
            "• Доверенность на выезд детей (если едут без родителей)\n\n"
            "Менеджер @WindowVadim подскажет точный список документов для вашего направления!"
        ),
        "💳 Оплата и возврат": (
            "💳 *Оплата и возврат*\n\n"
            "• Предоплата для бронирования тура: 30-50%\n"
            "• Полная оплата за 7-14 дней до вылета\n"
            "• Возврат средств при отказе от тура зависит от условий отеля и авиакомпании\n"
            "• Рекомендуем оформлять страховку от невыезда\n\n"
            "Точные условия вам расскажет менеджер @WindowVadim при подборе тура."
        )
    }
    
    if text in faq_answers:
        await update.message.reply_text(
            faq_answers[text],
            reply_markup=get_faq_keyboard(),
            parse_mode='Markdown'
        )
    elif text == "🖼️ Вернуться в главное меню":
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    return QUESTION_FLOW

async def handle_back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик навигации во время заполнения анкеты"""
    text = update.message.text
    current_state = context.user_data.get('current_state')
    
    if text == "🖼️ Вернуться в главное меню":
        context.user_data.clear()
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    
    elif text == "🔙 Вернуться назад":
        # Возвращаемся к предыдущему вопросу
        question_index = context.user_data.get('question_index', 1)
        if question_index > 1:
            question_index -= 1
            context.user_data['question_index'] = question_index
            
            # Определяем, на какой вопрос вернуться
            if question_index == 1:
                await update.message.reply_text(
                    "➖➖➖➖➖➖➖➖➖➖\n"
                    "❓ *Вопрос 1/8:*\n"
                    "🌍 *Куда хотите поехать?*\n"
                    "(Страна, город, направление)",
                    reply_markup=get_question_keyboard(),
                    parse_mode='Markdown'
                )
                return DIRECTION
            elif question_index == 2:
                await update.message.reply_text(
                    "➖➖➖➖➖➖➖➖➖➖\n"
                    "❓ *Вопрос 2/8:*\n"
                    "💰 *Какой у вас бюджет?*\n"
                    "(Общая сумма на человека, включен ли перелёт, питание и т.д.)",
                    reply_markup=get_question_keyboard(),
                    parse_mode='Markdown'
                )
                return BUDGET
            elif question_index == 3:
                await update.message.reply_text(
                    "➖➖➖➖➖➖➖➖➖➖\n"
                    "❓ *Вопрос 3/8:*\n"
                    "📅 *Когда планируете поездку и на сколько дней?*\n"
                    "(Точные или гибкие даты, количество ночей)",
                    reply_markup=get_question_keyboard(),
                    parse_mode='Markdown'
                )
                return DATES
            elif question_index == 4:
                await update.message.reply_text(
                    "➖➖➖➖➖➖➖➖➖➖\n"
                    "❓ *Вопрос 4/8:*\n"
                    "🏖️ *Какой тип отдыха предпочитаете?*\n"
                    "(Пляжный, экскурсионный, активный, семейный, романтический, молодёжный или комбинированный)",
                    reply_markup=get_question_keyboard(),
                    parse_mode='Markdown'
                )
                return TYPE
            elif question_index == 5:
                await update.message.reply_text(
                    "➖➖➖➖➖➖➖➖➖➖\n"
                    "❓ *Вопрос 5/8:*\n"
                    "🏨 *Какие требования к размещению?*\n"
                    "(Категория отеля, локация, инфраструктура: бассейн, SPA, анимация и т.д.)",
                    reply_markup=get_question_keyboard(),
                    parse_mode='Markdown'
                )
                return ACCOMMODATION
            elif question_index == 6:
                await update.message.reply_text(
                    "➖➖➖➖➖➖➖➖➖➖\n"
                    "❓ *Вопрос 6/8:*\n"
                    "✈️ *Какой транспорт предпочитаете?*\n"
                    "(Прямой рейс или с пересадкой, удобное время вылета, аэропорт вылета)",
                    reply_markup=get_question_keyboard(),
                    parse_mode='Markdown'
                )
                return TRANSPORT
            elif question_index == 7:
                await update.message.reply_text(
                    "➖➖➖➖➖➖➖➖➖➖\n"
                    "❓ *Вопрос 7/8:*\n"
                    "👨‍👩‍👧 *Кто едет?*\n"
                    "(Количество взрослых и детей, возраст детей, особые потребности)",
                    reply_markup=get_question_keyboard(),
                    parse_mode='Markdown'
                )
                return TOURISTS
    
    # Если нажата какая-то другая кнопка, но мы не обработали
    return current_state

async def get_direction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение направления"""
    text = update.message.text
    
    # Проверяем, не нажата ли кнопка навигации
    if text in ["🔙 Вернуться назад", "🖼️ Вернуться в главное меню"]:
        return await handle_back_navigation(update, context)
    
    context.user_data['request']['direction'] = text
    context.user_data['question_index'] = 2
    
    await update.message.reply_text(
        "✅ Информация сохранена!\n\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
        "❓ *Вопрос 2/8:*\n"
        "💰 *Какой у вас бюджет?*\n"
        "(Общая сумма на человека, включен ли перелёт, питание и т.д.)",
        reply_markup=get_question_keyboard(),
        parse_mode='Markdown'
    )
    return BUDGET

async def get_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение бюджета"""
    text = update.message.text
    
    # Проверяем, не нажата ли кнопка навигации
    if text in ["🔙 Вернуться назад", "🖼️ Вернуться в главное меню"]:
        return await handle_back_navigation(update, context)
    
    context.user_data['request']['budget'] = text
    context.user_data['question_index'] = 3
    
    await update.message.reply_text(
        "✅ Информация сохранена!\n\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
        "❓ *Вопрос 3/8:*\n"
        "📅 *Когда планируете поездку и на сколько дней?*\n"
        "(Точные или гибкие даты, количество ночей)",
        reply_markup=get_question_keyboard(),
        parse_mode='Markdown'
    )
    return DATES

async def get_dates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение дат"""
    text = update.message.text
    
    # Проверяем, не нажата ли кнопка навигации
    if text in ["🔙 Вернуться назад", "🖼️ Вернуться в главное меню"]:
        return await handle_back_navigation(update, context)
    
    context.user_data['request']['dates'] = text
    context.user_data['question_index'] = 4
    
    await update.message.reply_text(
        "✅ Информация сохранена!\n\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
        "❓ *Вопрос 4/8:*\n"
        "🏖️ *Какой тип отдыха предпочитаете?*\n"
        "(Пляжный, экскурсионный, активный, семейный, романтический, молодёжный или комбинированный)",
        reply_markup=get_question_keyboard(),
        parse_mode='Markdown'
    )
    return TYPE

async def get_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение типа отдыха"""
    text = update.message.text
    
    # Проверяем, не нажата ли кнопка навигации
    if text in ["🔙 Вернуться назад", "🖼️ Вернуться в главное меню"]:
        return await handle_back_navigation(update, context)
    
    context.user_data['request']['type'] = text
    context.user_data['question_index'] = 5
    
    await update.message.reply_text(
        "✅ Информация сохранена!\n\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
        "❓ *Вопрос 5/8:*\n"
        "🏨 *Какие требования к размещению?*\n"
        "(Категория отеля, локация, инфраструктура: бассейн, SPA, анимация и т.д.)",
        reply_markup=get_question_keyboard(),
        parse_mode='Markdown'
    )
    return ACCOMMODATION

async def get_accommodation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение требований к размещению"""
    text = update.message.text
    
    # Проверяем, не нажата ли кнопка навигации
    if text in ["🔙 Вернуться назад", "🖼️ Вернуться в главное меню"]:
        return await handle_back_navigation(update, context)
    
    context.user_data['request']['accommodation'] = text
    context.user_data['question_index'] = 6
    
    await update.message.reply_text(
        "✅ Информация сохранена!\n\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
        "❓ *Вопрос 6/8:*\n"
        "✈️ *Какой транспорт предпочитаете?*\n"
        "(Прямой рейс или с пересадкой, удобное время вылета, аэропорт вылета)",
        reply_markup=get_question_keyboard(),
        parse_mode='Markdown'
    )
    return TRANSPORT

async def get_transport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение требований к транспорту"""
    text = update.message.text
    
    # Проверяем, не нажата ли кнопка навигации
    if text in ["🔙 Вернуться назад", "🖼️ Вернуться в главное меню"]:
        return await handle_back_navigation(update, context)
    
    context.user_data['request']['transport'] = text
    context.user_data['question_index'] = 7
    
    await update.message.reply_text(
        "✅ Информация сохранена!\n\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
        "❓ *Вопрос 7/8:*\n"
        "👨‍👩‍👧 *Кто едет?*\n"
        "(Количество взрослых и детей, возраст детей, особые потребности)",
        reply_markup=get_question_keyboard(),
        parse_mode='Markdown'
    )
    return TOURISTS

async def get_tourists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение состава туристов"""
    text = update.message.text
    
    # Проверяем, не нажата ли кнопка навигации
    if text in ["🔙 Вернуться назад", "🖼️ Вернуться в главное меню"]:
        return await handle_back_navigation(update, context)
    
    context.user_data['request']['tourists'] = text
    context.user_data['question_index'] = 8
    
    await update.message.reply_text(
        "✅ Информация сохранена!\n\n"
        "➖➖➖➖➖➖➖➖➖➖\n"
        "❓ *Вопрос 8/8:*\n"
        "✨ *Дополнительные пожелания?*\n"
        "(Экскурсии, русскоговорящий гид, конкретный отель, расширенная страховка и т.д.)",
        reply_markup=get_question_keyboard(),
        parse_mode='Markdown'
    )
    return ADDITIONAL

async def get_additional(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение дополнительных пожеланий"""
    text = update.message.text
    
    # Проверяем, не нажата ли кнопка навигации
    if text in ["🔙 Вернуться назад", "🖼️ Вернуться в главное меню"]:
        return await handle_back_navigation(update, context)
    
    context.user_data['request']['additional'] = text
    
    # Формируем предварительный просмотр заявки
    request = context.user_data['request']
    
    # Создаем сообщение с заполненными данными
    filled_form = (
        "✅ *ВЫ УСПЕШНО ЗАПОЛНИЛИ ЗАЯВКУ*\n"
        "➖➖➖➖➖➖➖➖➖➖\n\n"
        f"🌍 *Направление:*\n{request.get('direction', 'Не указано')}\n\n"
        f"💰 *Бюджет:*\n{request.get('budget', 'Не указано')}\n\n"
        f"📅 *Даты:*\n{request.get('dates', 'Не указано')}\n\n"
        f"🏖️ *Тип отдыха:*\n{request.get('type', 'Не указано')}\n\n"
        f"🏨 *Размещение:*\n{request.get('accommodation', 'Не указано')}\n\n"
        f"✈️ *Транспорт:*\n{request.get('transport', 'Не указано')}\n\n"
        f"👨‍👩‍👧 *Состав туристов:*\n{request.get('tourists', 'Не указано')}\n\n"
        f"✨ *Дополнительно:*\n{request.get('additional', 'Не указано')}\n\n"
        "➖➖➖➖➖➖➖➖➖➖\n\n"
        "📤 *Перешлите это сообщение менеджеру @WindowVadim,*\n"
        "он подберет Вам тур и отправит расчет стоимости"
    )
    
    # Отправляем пользователю готовую форму для пересылки
    await update.message.reply_text(
        filled_form,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )
    
    # Очищаем данные
    context.user_data.clear()
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
    # Создаем приложение с вашим токеном
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
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.COMMAND, handle_unknown))
    
    # Запускаем бота
    print("✅ Бот успешно запущен!")
    print("📱 Токен: 8598049295:AAG0vdRpvKLvakRU8QUICbFOUQs1eJM6RQg")
    print("👤 Менеджер: @WindowVadim")
    print("📢 Канал: Window Tour")
    print("➖➖➖➖➖➖➖➖➖➖")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()