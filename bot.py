import logging
import random
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

GET_CONTACT = 1

PRIZES = {
    1: "скидка 1000 рублей на любую покупку 🎁",
    2: "скидка 1500 рублей на любую покупку 🎁",
    3: "скидка 10% на любую покупку 🎁",
    4: "скидка 15% на любую покупку 🎁",
    5: "скидка 20% на изделия бренда SAINT MAEVE 🎁",
    6: "скидка 15% на любые украшения 🎁"
}

user_rolled = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"Пользователь {user_id} запустил бота")
    
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
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def roll_dice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    logger.info(f"Пользователь {user_id} бросил кубик")
    
    dice_result = random.randint(1, 6)
    prize = PRIZES[dice_result]
    
    user_rolled[user_id] = True
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

async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user = update.effective_user
    
    logger.info(f"Получен контакт от пользователя {user.id}")
    
    if contact:
        phone = contact.phone_number
        prize = context.user_data.get('prize', 'Не определен')
        
        try:
            await update.message.reply_text(
                "Спасибо! Обрабатываем...",
                reply_markup=ReplyKeyboardMarkup.remove_keyboard()
            )
            
            final_text = (
                "Спасибо за участие в розыгрыше! 🎉\n\n"
                "Вскоре наш менеджер свяжется с Вами по указанному номеру и уточнит, "
                "когда Вам было бы удобно получить подарок.\n\n"
                "А пока Вы можете подписаться на канал SAINT MAEVE Concept (@saintmaeve_concept), "
                "чтобы следить за новостями, или перейти на сайт saintmaeve.ru и выбрать свой новый образ!"
            )
            await update.message.reply_text(final_text)
            
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("📱 Канал", url="https://t.me/saintmaeve_concept")],
                [InlineKeyboardButton("🌐 Сайт", url="https://saintmaeve.ru")]
            ])
            await update.message.reply_text("Полезные ссылки:", reply_markup=buttons)
            
            admin_id = os.environ.get("ADMIN_ID")
            if admin_id:
                try:
                    await context.bot.send_message(
                        chat_id=int(admin_id),
                        text=f"📞 Новая заявка!\nИмя: {user.first_name}\nТелефон: {phone}\nПриз: {prize}"
                    )
                    logger.info(f"Уведомление отправлено админу {admin_id}")
                except Exception as e:
                    logger.error(f"Ошибка отправки админу: {e}")
            else:
                logger.warning("ADMIN_ID не задан")
                await update.message.reply_text(f"[ТЕСТ] Номер получен: {phone}")
        except Exception as e:
            logger.error(f"Ошибка в get_contact: {e}")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("До свидания!")
    return ConversationHandler.END

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        logger.error("Нет токена!")
        return
    
    app = Application.builder().token(token).build()
    
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(roll_dice_callback, pattern="^roll_dice$")],
        states={GET_CONTACT: [MessageHandler(filters.CONTACT, get_contact)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    
    print("✅ Бот запущен и готов к работе!")
    app.run_polling()

if __name__ == "__main__":
    main()
