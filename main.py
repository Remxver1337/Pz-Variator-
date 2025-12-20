import logging
import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import json
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
TAG, DELIVERY_DATE, ORDER_AMOUNT, SPLIT_PAYMENT = range(4)

# Структура для хранения данных покупателя
@dataclass
class Customer:
    tag: str
    delivery_date: date
    order_amount: Optional[float] = None
    split_payment: Optional[bool] = None
    notified: bool = False

class DeliveryBot:
    def __init__(self, token: str):
        self.token = token
        self.customers: Dict[str, Customer] = {}
        self.load_data()
        
    def save_data(self):
        """Сохраняет данные в файл"""
        data = {
            tag: {
                **asdict(customer),
                'delivery_date': customer.delivery_date.isoformat()
            }
            for tag, customer in self.customers.items()
        }
        with open('customers_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_data(self):
        """Загружает данные из файла"""
        try:
            if os.path.exists('customers_data.json'):
                with open('customers_data.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for tag, customer_data in data.items():
                        customer_data['delivery_date'] = date.fromisoformat(customer_data['delivery_date'])
                        self.customers[tag] = Customer(**customer_data)
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            self.customers = {}
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        keyboard = [
            [InlineKeyboardButton("📝 Добавить покупателя", callback_data='add_customer')],
            [InlineKeyboardButton("👥 Список покупателей", callback_data='list_customers')],
            [InlineKeyboardButton("⚙️ Настройки", callback_data='settings')],
            [InlineKeyboardButton("ℹ️ Помощь", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "👋 Добро пожаловать в бот для управления доставками!\n\n"
            "Выберите действие:",
            reply_markup=reply_markup
        )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик inline кнопок"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == 'add_customer':
            await query.edit_message_text(
                "Введите тег покупателя (например: @username или номер телефона):"
            )
            return TAG
            
        elif data == 'list_customers':
            await self.show_customers_list(query)
            
        elif data == 'settings':
            await self.show_settings(query, context)
            
        elif data == 'help':
            await self.show_help(query)
            
        elif data == 'back_to_menu':
            await self.show_main_menu(query)
            
        elif data.startswith('customer_detail_'):
            tag = data.split('_', 2)[2]
            await self.show_customer_detail(query, tag)
            
        elif data.startswith('delete_customer_'):
            tag = data.split('_', 2)[2]
            await self.delete_customer(query, tag)
            
        elif data == 'toggle_order_amount':
            context.user_data['order_amount_enabled'] = not context.user_data.get('order_amount_enabled', False)
            await self.show_settings(query, context)
            
        elif data == 'toggle_split_payment':
            context.user_data['split_payment_enabled'] = not context.user_data.get('split_payment_enabled', False)
            await self.show_settings(query, context)
            
        elif data == 'set_reminder_time':
            await query.edit_message_text(
                "Введите время напоминания в формате ЧЧ:ММ (например, 10:00):"
            )
            return "REMINDER_TIME"
    
    async def get_customer_tag(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение тега покупателя"""
        tag = update.message.text.strip()
        context.user_data['current_customer'] = tag
        
        # Создаем клавиатуру для выбора даты
        keyboard = []
        today = date.today()
        
        for i in range(1, 8):
            delivery_date = today + timedelta(days=i)
            keyboard.append([
                InlineKeyboardButton(
                    f"{delivery_date.strftime('%d.%m.%Y')} ({delivery_date.strftime('%A')})",
                    callback_data=f'date_{delivery_date.isoformat()}'
                )
            ])
        
        keyboard.append([InlineKeyboardButton("📅 Ввести другую дату", callback_data='custom_date')])
        keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data='back_to_menu')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"Покупатель: {tag}\n\nВыберите дату доставки:",
            reply_markup=reply_markup
        )
        
        return DELIVERY_DATE
    
    async def get_delivery_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора даты доставки"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == 'custom_date':
            await query.edit_message_text(
                "Введите дату доставки в формате ДД.ММ.ГГГГ:"
            )
            return "CUSTOM_DATE"
        
        elif data.startswith('date_'):
            delivery_date_str = data.split('_')[1]
            delivery_date = date.fromisoformat(delivery_date_str)
            await self.process_date_selection(query, context, delivery_date)
            
        return ConversationHandler.END
    
    async def process_date_selection(self, query, context, delivery_date):
        """Обработка выбранной даты"""
        tag = context.user_data['current_customer']
        
        # Проверяем, включены ли дополнительные настройки
        order_amount_enabled = context.user_data.get('order_amount_enabled', False)
        split_payment_enabled = context.user_data.get('split_payment_enabled', False)
        
        if order_amount_enabled:
            await query.edit_message_text(
                f"Покупатель: {tag}\n"
                f"Дата доставки: {delivery_date.strftime('%d.%m.%Y')}\n\n"
                "Введите сумму заказа:"
            )
            context.user_data['delivery_date'] = delivery_date
            return ORDER_AMOUNT
        else:
            # Создаем покупателя без дополнительной информации
            self.customers[tag] = Customer(
                tag=tag,
                delivery_date=delivery_date
            )
            self.save_data()
            
            await query.edit_message_text(
                f"✅ Покупатель {tag} успешно добавлен!\n"
                f"📅 Дата доставки: {delivery_date.strftime('%d.%m.%Y')}"
            )
            await self.show_main_menu_after_action(query)
            return ConversationHandler.END
    
    async def get_order_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение суммы заказа"""
        try:
            amount = float(update.message.text.replace(',', '.'))
            context.user_data['order_amount'] = amount
            
            split_payment_enabled = context.user_data.get('split_payment_enabled', False)
            
            if split_payment_enabled:
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Да", callback_data='split_yes'),
                        InlineKeyboardButton("❌ Нет", callback_data='split_no')
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(
                    f"Сумма заказа: {amount} руб.\n\n"
                    "Оплата сплитом (раздельная оплата)?",
                    reply_markup=reply_markup
                )
                return SPLIT_PAYMENT
            else:
                await self.finalize_customer(update, context)
                return ConversationHandler.END
                
        except ValueError:
            await update.message.reply_text(
                "Пожалуйста, введите корректную сумму (например: 1500.50):"
            )
            return ORDER_AMOUNT
    
    async def get_split_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора сплит-оплаты"""
        query = update.callback_query
        await query.answer()
        
        split_payment = query.data == 'split_yes'
        context.user_data['split_payment'] = split_payment
        
        await self.finalize_customer_query(query, context)
        return ConversationHandler.END
    
    async def finalize_customer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Завершение создания покупателя без split оплаты"""
        tag = context.user_data['current_customer']
        delivery_date = context.user_data['delivery_date']
        order_amount = context.user_data.get('order_amount')
        
        self.customers[tag] = Customer(
            tag=tag,
            delivery_date=delivery_date,
            order_amount=order_amount,
            split_payment=None
        )
        self.save_data()
        
        await update.message.reply_text(
            f"✅ Покупатель {tag} успешно добавлен!\n"
            f"📅 Дата доставки: {delivery_date.strftime('%d.%m.%Y')}\n"
            f"💰 Сумма заказа: {order_amount} руб."
        )
        await self.show_main_menu_after_message(update)
    
    async def finalize_customer_query(self, query, context):
        """Завершение создания покупателя через query"""
        tag = context.user_data['current_customer']
        delivery_date = context.user_data['delivery_date']
        order_amount = context.user_data.get('order_amount')
        split_payment = context.user_data.get('split_payment')
        
        self.customers[tag] = Customer(
            tag=tag,
            delivery_date=delivery_date,
            order_amount=order_amount,
            split_payment=split_payment
        )
        self.save_data()
        
        split_text = "Да" if split_payment else "Нет" if split_payment is not None else "Не указано"
        
        await query.edit_message_text(
            f"✅ Покупатель {tag} успешно добавлен!\n"
            f"📅 Дата доставки: {delivery_date.strftime('%d.%m.%Y')}\n"
            f"💰 Сумма заказа: {order_amount} руб.\n"
            f"💳 Сплит-оплата: {split_text}"
        )
        await self.show_main_menu_after_action(query)
    
    async def show_customers_list(self, query):
        """Показать список покупателей"""
        if not self.customers:
            keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data='back_to_menu')]]
            await query.edit_message_text(
                "Список покупателей пуст.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        # Сортируем по дате доставки
        sorted_customers = sorted(
            self.customers.items(),
            key=lambda x: x[1].delivery_date
        )
        
        today = date.today()
        message_text = "👥 Список покупателей:\n\n"
        
        for i, (tag, customer) in enumerate(sorted_customers, 1):
            days_left = (customer.delivery_date - today).days
            status = "🟢" if days_left > 0 else "🟡" if days_left == 0 else "🔴"
            
            message_text += (
                f"{i}. {status} {tag}\n"
                f"   📅 {customer.delivery_date.strftime('%d.%m.%Y')} "
                f"(через {days_left} дней)\n"
            )
            
            if customer.order_amount:
                message_text += f"   💰 {customer.order_amount} руб.\n"
            
            if customer.split_payment is not None:
                split_text = "Да" if customer.split_payment else "Нет"
                message_text += f"   💳 Сплит: {split_text}\n"
            
            message_text += "\n"
        
        # Создаем клавиатуру с кнопками детализации
        keyboard = []
        for tag, _ in sorted_customers[:10]:  # Ограничиваем 10 покупателями для удобства
            keyboard.append([InlineKeyboardButton(f"🔍 {tag}", callback_data=f'customer_detail_{tag}')])
        
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data='back_to_menu')])
        
        await query.edit_message_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_customer_detail(self, query, tag):
        """Показать детали покупателя"""
        if tag not in self.customers:
            await query.answer("Покупатель не найден!")
            return
        
        customer = self.customers[tag]
        today = date.today()
        days_left = (customer.delivery_date - today).days
        
        message_text = (
            f"🔍 Детали покупателя:\n\n"
            f"🏷️ Тег: {customer.tag}\n"
            f"📅 Дата доставки: {customer.delivery_date.strftime('%d.%m.%Y')}\n"
            f"⏱️ Осталось дней: {days_left}\n"
        )
        
        if customer.order_amount:
            message_text += f"💰 Сумма заказа: {customer.order_amount} руб.\n"
        
        if customer.split_payment is not None:
            split_text = "Да" if customer.split_payment else "Нет"
            message_text += f"💳 Сплит-оплата: {split_text}\n"
        
        keyboard = [
            [InlineKeyboardButton("🗑️ Удалить", callback_data=f'delete_customer_{tag}')],
            [InlineKeyboardButton("⬅️ Назад к списку", callback_data='list_customers')]
        ]
        
        await query.edit_message_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def delete_customer(self, query, tag):
        """Удалить покупателя"""
        if tag in self.customers:
            del self.customers[tag]
            self.save_data()
            await query.answer("Покупатель удален!")
            await self.show_customers_list(query)
        else:
            await query.answer("Покупатель не найден!")
    
    async def show_settings(self, query, context):
        """Показать настройки"""
        order_amount_enabled = context.user_data.get('order_amount_enabled', False)
        split_payment_enabled = context.user_data.get('split_payment_enabled', False)
        
        order_status = "✅ ВКЛ" if order_amount_enabled else "❌ ВЫКЛ"
        split_status = "✅ ВКЛ" if split_payment_enabled else "❌ ВЫКЛ"
        
        keyboard = [
            [InlineKeyboardButton(f"💰 Ввод суммы заказа: {order_status}", callback_data='toggle_order_amount')],
            [InlineKeyboardButton(f"💳 Сплит-оплата: {split_status}", callback_data='toggle_split_payment')],
            [InlineKeyboardButton("⏰ Настройка времени напоминаний", callback_data='set_reminder_time')],
            [InlineKeyboardButton("⬅️ Назад", callback_data='back_to_menu')]
        ]
        
        await query.edit_message_text(
            "⚙️ Настройки бота:\n\n"
            "Здесь вы можете включить/выключить дополнительные функции:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_help(self, query):
        """Показать справку"""
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data='back_to_menu')]]
        
        await query.edit_message_text(
            "ℹ️ Помощь по использованию бота:\n\n"
            "📝 Добавить покупателя - добавление нового покупателя с указанием даты доставки\n"
            "👥 Список покупателей - просмотр всех покупателей и их деталей\n"
            "⚙️ Настройки - включение/выключение дополнительных функций\n\n"
            "Функции в настройках:\n"
            "• Ввод суммы заказа - запрашивать сумму заказа при добавлении\n"
            "• Сплит-оплата - спрашивать о раздельной оплате\n"
            "• Настройка времени - установить время отправки напоминаний\n\n"
            "Бот автоматически напоминает о доставке в день доставки!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_main_menu(self, query):
        """Показать главное меню"""
        keyboard = [
            [InlineKeyboardButton("📝 Добавить покупателя", callback_data='add_customer')],
            [InlineKeyboardButton("👥 Список покупателей", callback_data='list_customers')],
            [InlineKeyboardButton("⚙️ Настройки", callback_data='settings')],
            [InlineKeyboardButton("ℹ️ Помощь", callback_data='help')]
        ]
        
        await query.edit_message_text(
            "Главное меню. Выберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def show_main_menu_after_action(self, query):
        """Показать главное меню после действия"""
        await asyncio.sleep(2)
        await self.show_main_menu(query)
    
    async def show_main_menu_after_message(self, update):
        """Показать главное меню после сообщения"""
        keyboard = [
            [InlineKeyboardButton("📝 Добавить покупателя", callback_data='add_customer')],
            [InlineKeyboardButton("👥 Список покупателей", callback_data='list_customers')],
            [InlineKeyboardButton("⚙️ Настройки", callback_data='settings')],
            [InlineKeyboardButton("ℹ️ Помощь", callback_data='help')]
        ]
        
        await update.message.reply_text(
            "Выберите следующее действие:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def custom_date_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода кастомной даты"""
        query = update.callback_query
        await query.answer()
        
        try:
            date_str = update.message.text.strip()
            delivery_date = datetime.strptime(date_str, "%d.%m.%Y").date()
            
            if delivery_date < date.today():
                await update.message.reply_text(
                    "Дата не может быть в прошлом. Введите корректную дату:"
                )
                return "CUSTOM_DATE"
            
            await self.process_date_selection_message(update, context, delivery_date)
            return ConversationHandler.END
            
        except ValueError:
            await update.message.reply_text(
                "Неверный формат даты. Введите дату в формате ДД.ММ.ГГГГ:"
            )
            return "CUSTOM_DATE"
    
    async def process_date_selection_message(self, update, context, delivery_date):
        """Обработка выбранной даты из сообщения"""
        tag = context.user_data['current_customer']
        
        order_amount_enabled = context.user_data.get('order_amount_enabled', False)
        split_payment_enabled = context.user_data.get('split_payment_enabled', False)
        
        if order_amount_enabled:
            await update.message.reply_text(
                f"Покупатель: {tag}\n"
                f"Дата доставки: {delivery_date.strftime('%d.%m.%Y')}\n\n"
                "Введите сумму заказа:"
            )
            context.user_data['delivery_date'] = delivery_date
            return ORDER_AMOUNT
        else:
            self.customers[tag] = Customer(
                tag=tag,
                delivery_date=delivery_date
            )
            self.save_data()
            
            await update.message.reply_text(
                f"✅ Покупатель {tag} успешно добавлен!\n"
                f"📅 Дата доставки: {delivery_date.strftime('%d.%m.%Y')}"
            )
            await self.show_main_menu_after_message(update)
            return ConversationHandler.END
    
    async def check_deliveries(self, context: ContextTypes.DEFAULT_TYPE):
        """Проверка доставок на сегодня и отправка напоминаний"""
        today = date.today()
        
        for tag, customer in self.customers.items():
            if customer.delivery_date == today and not customer.notified:
                # Отправляем напоминание
                try:
                    await context.bot.send_message(
                        chat_id=context.job.chat_id,
                        text=f"🔔 Напоминание о доставке!\n\n"
                             f"Сегодня доставка для покупателя: {tag}\n"
                             f"Дата: {customer.delivery_date.strftime('%d.%m.%Y')}"
                    )
                    customer.notified = True
                    self.save_data()
                except Exception as e:
                    logger.error(f"Error sending reminder: {e}")
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена текущего действия"""
        await update.message.reply_text("Действие отменено.")
        await self.show_main_menu_after_message(update)
        return ConversationHandler.END

def main():
    """Основная функция запуска бота"""
    # Вставьте ваш токен бота здесь
    TOKEN = "8598049295:AAG0vdRpvKLvakRU8QUICbFOUQs1eJM6RQg"
    
    bot = DeliveryBot(TOKEN)
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Создаем ConversationHandler для добавления покупателей
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(bot.button_handler, pattern='^add_customer$')],
        states={
            TAG: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.get_customer_tag)],
            DELIVERY_DATE: [CallbackQueryHandler(bot.get_delivery_date)],
            ORDER_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.get_order_amount)],
            SPLIT_PAYMENT: [CallbackQueryHandler(bot.get_split_payment)],
            "CUSTOM_DATE": [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.custom_date_handler)],
            "REMINDER_TIME": [MessageHandler(filters.TEXT & ~filters.COMMAND, bot.set_reminder_time_handler)]
        },
        fallbacks=[
            CommandHandler('cancel', bot.cancel),
            CallbackQueryHandler(bot.button_handler, pattern='^back_to_menu$')
        ],
        allow_reentry=True
    )
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(bot.button_handler))
    
    # Добавляем обработчик для кастомной даты
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        bot.custom_date_handler
    ), group=1)
    
    # Настраиваем задачу для проверки доставок
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_daily(
            bot.check_deliveries,
            time=datetime.time(hour=9, minute=0),  # Проверка в 9:00 утра
            chat_id=None,  # Нужно будет установить при запуске
        )
    
    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()