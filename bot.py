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

# Словарь с призами (ОБНОВЛЕНО)
PRIZES = {
    1: "скидка 1000 рублей на любую покупку 🎁",
    2: "скидка 1500 рублей на любую покупку 🎁",
    3: "скидка 10% на любую покупку 🎁",
    4: "скидка 15% на любую покупку 🎁",
    5: "скидка 20% на изделия бренда SAINT MAEVE 🎁",
    6: "скидка 15% на любые украшения 🎁"
}

# Словарь для отслеживания, кто уже бросил кубик
# (хранится в памяти, при перезапуске бота сбрасывается)
user_rolled = {}

# Команда /start (ТЕКСТ ОБНОВЛЕН)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Проверяем, бросал ли уже пользователь кубик
    if user_id in user_rolled and user_rolled[user_id]:
        # Если уже бросал, показываем только кнопку с номером (без кубика)
        await update.message.reply_text(
            "Вы уже участвовали в розыгрыше! 🎲\n\n"
            "Если Вы ещё не оставили номер телефона, нажмите кнопку ниже, чтобы получить Ваш подарок 👇"
        )
        contact_keyboard = ReplyKeyboardMarkup(
            [[KeyboardButton("📞 Поделиться номером телефона", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await update.message.reply_text("Нажмите кнопку:", reply_markup=contact_keyboard)
        return GET_CONTACT
    
    # Новый пользователь — показываем полное приветствие
    welcome_text = (
        "Добро пожаловать в розыгрыш от концепт-стора российских дизайнеров SAINT MAEVE Concept!\n\n"
        "Мы рады, что Вас заинтересовал наш флаер, и поэтому мы предлагаем Вам сыграть в игру 🎲, "
        "в конце которой Вы обязательно получите подарок! 🎁\n\n"
        "Правила игры предельно просты:\n"
        "1. Нажмите кнопку «Бросить кубик».\n"
        "2. Узнайте Ваш подарок.\n"
        "3. Оставьте номер телефона, чтобы наша команда знала, кому вручать приз.\n\n"
        "Готовы к игре? Поймайте удачу! 👇"
    )
    keyboard = [[InlineKeyboardButton("🎲 Бросить кубик", callback_data="roll_dice")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

# Бросок кубика (ТЕКСТ ПОДАРКОВ ОБНОВЛЕН + ЗАЩИТА ОТ ПОВТОРА)
async def roll_dice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Проверяем, не бросал ли уже пользователь кубик
    if user_id in user_rolled and user_rolled[user_id]:
        await query.message.reply_text("Вы уже бросали кубик! Используйте кнопку ниже, чтобы получить подарок.")
        return
    
    # Бросаем кубик (генерируем число от 1 до 6)
    dice_result = random.randint(1, 6)
    prize = PRIZES[dice_result]
    
    # Запоминаем, что пользователь бросил кубик
    user_rolled[user_id] = True
    
    # Сохраняем результат и приз в данные пользователя
    context.user_data['dice_result'] = dice_result
    context.user_data['prize'] = prize
    
    # Формируем текст с подарком
    result_text = (
        f"🎲 Тебе выпало число: {dice_result}\n\n"
        f"Твой подарок: {prize}\n\n"
        f"👇 Чтобы получить приз, нажми кнопку «Поделиться номером»"
    )
    
    # Кнопка для отправки контакта
    contact_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📞 Поделиться номером телефона", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await query.message.reply_text(result_text, reply_markup=contact_keyboard)
    return GET_CONTACT

# Получение контакта (ФИНАЛЬНЫЙ ТЕКСТ ОБНОВЛЕН)
async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user = update.effective_user
    user_id = user.id
    
    if contact:
        phone_number = contact.phone_number
        prize = context.user_data.get('prize', 'Не определен')
        dice = context.user_data.get('dice_result', '?')
        
        # Финальное сообщение (ОБНОВЛЕНО)
        final_text = (
            "Спасибо за участие в розыгрыше! \n\n"
            "Вскоре наш менеджер свяжется с Вами по указанному номеру и уточнит, "
            "когда Вам было бы удобно получить подарок. \n\n"
            "А пока Вы можете подписаться на канал SAINT MAEVE Concept @saintmaeve_concept, "
            "чтобы следить за новостями, или перейти на сайт saintmaeve.ru и выбрать свой новый образ!"
        )
        
        # Убираем клавиатуру с кнопкой номера
        await update.message.reply_text(
            final_text,
            reply_markup=ReplyKeyboardMarkup.remove_keyboard()
        )
        
        # Кнопки для перехода на канал и сайт
        channel_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📱 Канал SAINT MAEVE", url="https://t.me/saintmaeve_concept")],
            [InlineKeyboardButton("🌐 Перейти на сайт", url="https://saintmaeve.ru")]
        ])
        await update.message.reply_text("Полезные ссылки:", reply_markup=channel_keyboard)
        
        # Отправляем уведомление админу
        admin_id = int(os.environ.get("ADMIN_ID", "0"))
        admin_message = (
            f"📞 Новая заявка с розыгрыша!\n"
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
    await update.message.reply_text("Очень жаль! Если передумаете, просто напишите /start")
    return ConversationHandler.END

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and update.message.text != "/start":
        await update.message.reply_text("Используйте команду /start для участия в розыгрыше.")

def main():
    # Получаем токен из переменных окружения
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
    
    print("Бот SAINT MAEVE запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
