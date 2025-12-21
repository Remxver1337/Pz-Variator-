import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация базы данных
DATABASE_URL = "sqlite:///clients.db"
Base = declarative_base()

# Модель клиента
class Client(Base):
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False)
    track_number = Column(String(100), nullable=False)
    days = Column(Integer, nullable=False)
    order_amount = Column(Float, nullable=False)
    product_count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    reminded = Column(Boolean, default=False)
    
    # Статусы оплат
    duty_paid = Column(Boolean, default=False)
    delivery_paid = Column(Boolean, default=False)
    insurance_paid = Column(Boolean, default=False)
    deposit_paid = Column(Boolean, default=False)
    
    def get_payment_amounts(self) -> Dict[str, float]:
        """Рассчитать суммы всех платежей"""
        return calculate_payments(self.order_amount)

# Создание базы данных
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
Session = scoped_session(sessionmaker(bind=engine))

# Состояния для ConversationHandler
USERNAME, TRACK_NUMBER, DAYS, ORDER_AMOUNT, PRODUCT_COUNT = range(5)

# Главное меню
MAIN_MENU_KEYBOARD = ReplyKeyboardMarkup(
    [["Добавить клиента", "Список клиентов"], ["Выдача оплат"]],
    resize_keyboard=True
)

# Функции расчета платежей
def calculate_duty(amount: float) -> float:
    """Расчет пошлины"""
    if 5000 <= amount < 6000:
        return 2382
    elif 6000 <= amount < 7000:
        return 2473
    elif 7000 <= amount < 8000:
        return 2789
    elif 9000 <= amount < 10000:
        return 3474
    elif 10000 <= amount < 11000:
        return 3782
    elif 11000 <= amount < 13500:
        return 3986
    elif 13500 <= amount < 15000:
        return 4387
    elif 15000 <= amount < 20000:
        return 5781  # Среднее значение из диапазона
    elif amount >= 20000:
        return 8512
    return 0

def calculate_delivery(amount: float) -> float:
    """Расчет доставки"""
    if amount <= 2000:
        return 489
    elif 2000 < amount <= 2500:
        return 1371
    elif 2500 < amount <= 3000:
        return 1481
    elif 3000 < amount <= 4000:
        return 1861
    elif 4000 < amount <= 5000:
        return 1961
    return 0

def calculate_insurance(amount: float) -> float:
    """Расчет страхового взноса"""
    if amount <= 2000:
        return 2750
    elif 2000 < amount <= 17000:
        return 4750
    elif 17000 < amount <= 25000:
        return 6750
    elif 25000 < amount <= 35000:
        return 8750
    else:
        return 9750

def calculate_deposit(amount: float) -> float:
    """Расчет залога"""
    if amount <= 2000:
        return 4750
    elif 2000 < amount <= 17000:
        return 6750
    elif 17000 < amount <= 25000:
        return 8750
    elif 25000 < amount <= 35000:
        return 10750
    else:
        return 11750

def calculate_payments(order_amount: float) -> Dict[str, float]:
    """Рассчитать все платежи для суммы заказа"""
    return {
        'duty': calculate_duty(order_amount),
        'delivery': calculate_delivery(order_amount),
        'insurance': calculate_insurance(order_amount),
        'deposit': calculate_deposit(order_amount)
    }

def format_client_info(client: Client) -> str:
    """Форматирование информации о клиенте"""
    payments = client.get_payment_amounts()
    return (
        f"👤 Клиент: @{client.username}\n"
        f"📦 Трек-номер: {client.track_number}\n"
        f"📅 Срок: {client.days} дней\n"
        f"💰 Сумма заказа: {client.order_amount:.2f}₽\n"
        f"🛍 Количество товаров: {client.product_count}\n"
        f"📅 Дата добавления: {client.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"💳 Платежи:\n"
        f"   • Пошлина: {payments['duty']}₽ {'✅' if client.duty_paid else '❌'}\n"
        f"   • Доставка: {payments['delivery']}₽ {'✅' if client.delivery_paid else '❌'}\n"
        f"   • СВ: {payments['insurance']}₽ {'✅' if client.insurance_paid else '❌'}\n"
        f"   • Залог: {payments['deposit']}₽ {'✅' if client.deposit_paid else '❌'}"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "Добро пожаловать в бот для управления клиентами!\n"
        "Выберите действие из меню:",
        reply_markup=MAIN_MENU_KEYBOARD
    )

async def add_client_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало добавления клиента"""
    await update.message.reply_text("Введите имя пользователя (например, @username):")
    return USERNAME

async def get_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение имени пользователя"""
    context.user_data['username'] = update.message.text.strip()
    await update.message.reply_text("Введите трек-номер:")
    return TRACK_NUMBER

async def get_track_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение трек-номера"""
    context.user_data['track_number'] = update.message.text.strip()
    await update.message.reply_text("Введите срок в днях:")
    return DAYS

async def get_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение срока"""
    try:
        days = int(update.message.text.strip())
        if days <= 0:
            raise ValueError
        context.user_data['days'] = days
        await update.message.reply_text("Введите сумму заказа в рублях:")
        return ORDER_AMOUNT
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число дней:")
        return DAYS

async def get_order_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение суммы заказа"""
    try:
        amount = float(update.message.text.strip())
        if amount <= 0:
            raise ValueError
        context.user_data['order_amount'] = amount
        await update.message.reply_text("Введите количество товаров:")
        return PRODUCT_COUNT
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректную сумму:")
        return ORDER_AMOUNT

async def get_product_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение количества товаров и сохранение клиента"""
    try:
        count = int(update.message.text.strip())
        if count <= 0:
            raise ValueError
        
        # Сохранение клиента в базу данных
        session = Session()
        client = Client(
            username=context.user_data['username'],
            track_number=context.user_data['track_number'],
            days=context.user_data['days'],
            order_amount=context.user_data['order_amount'],
            product_count=count
        )
        session.add(client)
        session.commit()
        
        # Получаем ID добавленного клиента
        client_id = client.id
        session.close()
        
        # Рассчитываем дату напоминания
        reminder_date = datetime.now() + timedelta(days=client.days)
        
        await update.message.reply_text(
            f"✅ Клиент успешно добавлен!\n"
            f"ID: {client_id}\n"
            f"Напоминание будет отправлено: {reminder_date.strftime('%d.%m.%Y')} в 12:00 по МСК",
            reply_markup=MAIN_MENU_KEYBOARD
        )
        
        # Планируем напоминание
        scheduler = context.application.job_queue
        reminder_time = reminder_date.replace(hour=9, minute=0, second=0)  # 12:00 МСК = 9:00 UTC
        
        scheduler.run_once(
            callback=send_reminder,
            when=reminder_time,
            data={'client_id': client_id, 'chat_id': update.effective_chat.id}
        )
        
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное количество товаров:")
        return PRODUCT_COUNT

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Отправка напоминания о клиенте"""
    job = context.job
    client_id = job.data['client_id']
    chat_id = job.data['chat_id']
    
    session = Session()
    client = session.query(Client).filter_by(id=client_id).first()
    
    if client and not client.reminded:
        client.reminded = True
        session.commit()
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"⏰ Напоминание!\n"
                 f"Срок по клиенту @{client.username} истек.\n"
                 f"Трек-номер: {client.track_number}\n"
                 f"Сумма заказа: {client.order_amount}₽"
        )
    
    session.close()

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена диалога"""
    await update.message.reply_text(
        "Действие отменено.",
        reply_markup=MAIN_MENU_KEYBOARD
    )
    return ConversationHandler.END

async def show_clients_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    """Показать список клиентов с пагинацией"""
    session = Session()
    clients = session.query(Client).order_by(Client.created_at.desc()).all()
    session.close()
    
    if not clients:
        await update.message.reply_text("Список клиентов пуст.")
        return
    
    # Пагинация
    items_per_page = 10
    total_pages = (len(clients) + items_per_page - 1) // items_per_page
    
    if page >= total_pages:
        page = total_pages - 1
    
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_clients = clients[start_idx:end_idx]
    
    keyboard = []
    for client in page_clients:
        keyboard.append([InlineKeyboardButton(
            f"@{client.username} - {client.track_number}",
            callback_data=f"client_{client.id}"
        )])
    
    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"clients_page_{page-1}"))
    
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"clients_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("Назад в меню", callback_data="back_to_menu")])
    
    await update.message.reply_text(
        f"📋 Список клиентов (стр. {page + 1}/{total_pages}):",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_client_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать информацию о конкретном клиенте"""
    query = update.callback_query
    await query.answer()
    
    client_id = int(query.data.split('_')[1])
    
    session = Session()
    client = session.query(Client).filter_by(id=client_id).first()
    session.close()
    
    if client:
        await query.edit_message_text(
            text=format_client_info(client),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Назад к списку", callback_data="clients_page_0")
            ]])
        )
    else:
        await query.edit_message_text("Клиент не найден.")

async def payments_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    """Показать список клиентов для выдачи оплат"""
    session = Session()
    clients = session.query(Client).order_by(Client.created_at.desc()).all()
    session.close()
    
    if not clients:
        await update.message.reply_text("Список клиентов пуст.")
        return
    
    # Пагинация
    items_per_page = 10
    total_pages = (len(clients) + items_per_page - 1) // items_per_page
    
    if page >= total_pages:
        page = total_pages - 1
    
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    page_clients = clients[start_idx:end_idx]
    
    keyboard = []
    for client in page_clients:
        payments = client.get_payment_amounts()
        keyboard.append([InlineKeyboardButton(
            f"@{client.username} - {client.order_amount}₽",
            callback_data=f"pay_client_{client.id}"
        )])
    
    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"payments_page_{page-1}"))
    
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"payments_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("Назад в меню", callback_data="back_to_menu")])
    
    await update.message.reply_text(
        f"💰 Выдача оплат (стр. {page + 1}/{total_pages}):",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_payment_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать варианты оплат для клиента"""
    query = update.callback_query
    await query.answer()
    
    client_id = int(query.data.split('_')[2])
    context.user_data['payment_client_id'] = client_id
    
    session = Session()
    client = session.query(Client).filter_by(id=client_id).first()
    session.close()
    
    if client:
        payments = client.get_payment_amounts()
        
        keyboard = [
            [
                InlineKeyboardButton(f"Пошлина ({payments['duty']}₽)", 
                                   callback_data=f"pay_type_duty_{client_id}"),
                InlineKeyboardButton(f"Доставка ({payments['delivery']}₽)", 
                                   callback_data=f"pay_type_delivery_{client_id}")
            ],
            [
                InlineKeyboardButton(f"СВ ({payments['insurance']}₽)", 
                                   callback_data=f"pay_type_insurance_{client_id}"),
                InlineKeyboardButton(f"Залог ({payments['deposit']}₽)", 
                                   callback_data=f"pay_type_deposit_{client_id}")
            ],
            [InlineKeyboardButton("Назад", callback_data="payments_page_0")]
        ]
        
        await query.edit_message_text(
            text=f"Выберите тип оплаты для @{client.username}:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

def get_payment_message(payment_type: str, amount: float, client: Client) -> str:
    """Получить текст сообщения для оплаты"""
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d.%m")
    
    messages = {
        'delivery': (
            f"Добрый день, Ваш заказ прибыл к нам на склад в мск. "
            f"Поставка рассортирована и готова к отправке, сумма оплаты доставки {amount}₽ "
            f"(в стоимость включён курьер до пункта отправки). "
            f"Напишите мне по оплате, выдам реквизиты"
        ),
        'duty': (
            f"Добрый день, Ваш заказ прибыл к нам на склад в мск. "
            f"Сумма оплаты за таможенную пошлину {amount}₽ "
            f"(принцип расчета ТП можете посмотреть в интернете). "
            f"Напишите мне по оплате, выдам реквизиты"
        ),
        'insurance': (
            f"Страховой взнос по заказу {amount}₽. "
            f"Сумма полностью возвратная т.е при уведомлении СДЭКа/Почты о получении товара клиентом "
            f"сумма будет возвращена в полном объеме на номер карты "
            f"(имя получателя и банк должен быть тот же, с которого была отправлена сумма)"
        ),
        'deposit': (
            f"@{client.username} Залог для отправки {amount}₽, "
            f"отправка {tomorrow} 11-12МСК, также не получили реквизиты на возврат СВ "
            f"(имя отправителя как в чеке и тот же банк)"
        )
    }
    
    return messages.get(payment_type, "")

async def send_payment_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправить сообщение с текстом оплаты"""
    query = update.callback_query
    await query.answer()
    
    data_parts = query.data.split('_')
    payment_type = data_parts[2]
    client_id = int(data_parts[3])
    
    session = Session()
    client = session.query(Client).filter_by(id=client_id).first()
    
    if client:
        payments = client.get_payment_amounts()
        amount = payments.get(payment_type, 0)
        
        # Обновляем статус оплаты
        if payment_type == 'duty':
            client.duty_paid = True
        elif payment_type == 'delivery':
            client.delivery_paid = True
        elif payment_type == 'insurance':
            client.insurance_paid = True
        elif payment_type == 'deposit':
            client.deposit_paid = True
        
        session.commit()
        
        message_text = get_payment_message(payment_type, amount, client)
        
        await query.edit_message_text(
            text=message_text,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Назад к оплатам", 
                                   callback_data=f"pay_client_{client_id}")
            ]])
        )
    
    session.close()

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback запросов"""
    query = update.callback_query
    data = query.data
    
    if data == "back_to_menu":
        await query.edit_message_text(
            "Главное меню:",
            reply_markup=MAIN_MENU_KEYBOARD
        )
    
    elif data.startswith("clients_page_"):
        page = int(data.split('_')[2])
        await show_clients_list(update, context, page)
    
    elif data.startswith("client_"):
        await show_client_info(update, context)
    
    elif data.startswith("payments_page_"):
        page = int(data.split('_')[2])
        await payments_list(update, context, page)
    
    elif data.startswith("pay_client_"):
        await show_payment_options(update, context)
    
    elif data.startswith("pay_type_"):
        await send_payment_message(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    text = update.message.text
    
    if text == "Добавить клиента":
        return await add_client_start(update, context)
    
    elif text == "Список клиентов":
        await show_clients_list(update, context)
    
    elif text == "Выдача оплат":
        await payments_list(update, context)
    
    else:
        await update.message.reply_text(
            "Используйте кнопки меню для навигации.",
            reply_markup=MAIN_MENU_KEYBOARD
        )

def main():
    """Основная функция"""
    # Токен бота - замените на свой
    TOKEN = "ВАШ_ТОКЕН_БОТА"
    
    # Создание приложения
    application = Application.builder().token(TOKEN).build()
    
    # ConversationHandler для добавления клиента
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("Добавить клиента"), add_client_start)],
        states={
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_username)],
            TRACK_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_track_number)],
            DAYS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_days)],
            ORDER_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_order_amount)],
            PRODUCT_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_product_count)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Добавление обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запуск бота
    print("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_UPDATES)

if __name__ == '__main__':
    main()