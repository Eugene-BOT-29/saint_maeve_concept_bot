import logging
import random
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# Включаем логирование
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния для диалога
GET_CONTACT = 1

# Словарь с призами
PRIZES = {
    1: "🍫 Сладкий подарок (шоколадка к услуге)",
    2: "💅 Скидка 15% на маникюр",
    3: "💰 500 рублей на любую услугу",
    4: "💇‍♀️ Скидка 30% на стрижку",
    5: "🎁 Маска для волос в подарок",
    6: "🏆 ДЖЕКПОТ! 10.000 ₽ на услуги салона!"
}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🌟 Добро пожаловать в розыгрыш от салона красоты!\n\n"
        "Мы дарим подарки просто так! 🎁\n"
        "Правила просты:\n"
        "1. Нажми кнопку «Бросить кубик».\n"
        "2. Узнай свой подарок.\n"
        "3. Оставь номер телефона, чтобы мы знали, кому вручать приз.\n\n"
        "Готов? Лови удачу! 👇"
    )
    keyboard = [[InlineKeyboardButton("🎲 Бросить кубик", callback_data="roll_dice")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

# Бросок кубика
async def roll_dice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    dice_result = random.randint(1, 6)
    prize = PRIZES[dice_result]
    
    context.user_data['dice_result'] = dice_result
    context.user_data['prize'] = prize
    
    result_text = (
        f"🎲 Тебе выпало число: {dice_result}\n\n"
        f"Твой подарок: {prize}\n\n"
        f"👇 Чтобы получить приз, нажми кнопку «Поделиться номером»"
    )
    
    contact_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📞 Поделиться номером телефона", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await query.message.reply_text(result_text, reply_markup=contact_keyboard)
    return GET_CONTACT

# Получение контакта
async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user = update.effective_user
    
    if contact:
        phone_number = contact.phone_number
        prize = context.user_data.get('prize', 'Не определен')
        dice = context.user_data.get('dice_result', '?')
        
        await update.message.reply_text(
            f"✅ Спасибо! Твой номер {phone_number} получен.\n"
            f"Скоро администратор свяжется с тобой, чтобы договориться о визите и вручить приз: {prize}\n\n"
            f"А пока можешь сразу перейти к записи 👇",
            reply_markup=ReplyKeyboardMarkup.remove_keyboard()
        )
        
        # Кнопка для записи (ссылку потом заменишь)
        booking_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📅 Записаться онлайн", url="https://t.me/your_username")]  # ПОТОМ ЗАМЕНИШЬ
        ])
        await update.message.reply_text("Выбери удобное время:", reply_markup=booking_keyboard)
        
        # Отправляем админу
        admin_id = int(os.environ.get("ADMIN_ID", "0"))
        admin_message = (
            f"📞 Новая заявка!\n"
            f"Имя: {user.first_name}\n"
            f"Username: @{user.username if user.username else 'нет'}\n"
            f"Телефон: {phone_number}\n"
            f"Результат кубика: {dice}\n"
            f"Приз: {prize}"
        )
        try:
            await context.bot.send_message(chat_id=admin_id, text=admin_message)
        except Exception as e:
            logger.error(f"Не удалось отправить админу: {e}")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Очень жаль! Если передумаешь, просто напиши /start")
    return ConversationHandler.END

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and update.message.text != "/start":
        await update.message.reply_text("Используй команду /start для участия в розыгрыше.")

def main():
    # Получаем токен из переменных окружения (так безопаснее)
    token = os.environ.get("BOT_TOKEN")
    if not token:
        logger.error("Нет токена! Укажи BOT_TOKEN в переменных окружения.")
        return
    
    application = Application.builder().token(token).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(roll_dice_callback, pattern="^roll_dice$")],
        states={
            GET_CONTACT: [MessageHandler(filters.CONTACT, get_contact)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    print("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
