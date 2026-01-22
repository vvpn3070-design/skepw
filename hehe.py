import logging
import asyncio
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = "8231417543:AAFQ-as9mzigXJj78shMqDJJJxboSLmAbmQ"

# Каналы для подписки (формат: [название, ссылка, ID/юзернейм])
# ТОЛЬКО "СПОНСОР" и "ГЛАВНЫЙ СПОНСОР" в названиях
CHANNELS = [
    ["🔴 ГЛАВНЫЙ СПОНСОР", "https://t.me/+WNwyn_6yxOc5OGI6", "-1003265823270"],  # Главный спонсор
    ["🔵 СПОНСОР", "https://t.me/nitefree", "-1003265823270"],  # Публичный канал nitefree
    ["🟢 СПОНСОР", "https://t.me/+OmcLF8rmWL9lMTZi", "-1003339930890"],  # Новый приватный канал
    ["🟡 СПОНСОР", "https://t.me/zonixwin", "-1002544279808"],  # zonixwin
    ["🟣 СПОНСОР", "https://t.me/+HB4Y6GPYnHQzOTVi", "-1002892302639"],  # TeenBody
    ["⚪️ СПОНСОР", "https://t.me/+m_mlxM7IlFk1MGRi", "-1003082454363"],  # Новый канал
    ["🟤 СПОНСОР", "https://t.me/+s_gc1tRLvnQ4Y2Ni", "-1003080893872"],  # Новый добавленный спонсор
    ["🟦 СПОНСОР", "https://t.me/+EVQRYUSfjxM3ZjMy", "-1003190411062"],  # Новый добавленный спонсор
]

# Глобальные переменные для хранения состояния пользователей
user_states = {}
user_menu_messages = {}  # Храним ID последнего меню для каждого пользователя

# Функция проверки подписки
async def check_subscription(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        for channel_name, channel_link, channel_id in CHANNELS:
            try:
                member = await context.bot.get_chat_member(
                    chat_id=channel_id,
                    user_id=user_id
                )
                if member.status not in ['member', 'administrator', 'creator']:
                    logger.info(f"Пользователь {user_id} не подписан на {channel_name}")
                    return False
            except Exception as e:
                error_msg = str(e)
                if "USER_NOT_PARTICIPANT" in error_msg or "user not found" in error_msg.lower():
                    logger.info(f"Пользователь {user_id} не подписан на {channel_name}")
                    return False
                elif "Chat not found" in error_msg:
                    logger.error(f"Бот не имеет доступа к каналу {channel_name} (не админ)")
                    return False
                elif "Forbidden" in error_msg:
                    logger.error(f"Бот заблокирован в канале {channel_name}")
                    return False
                else:
                    logger.error(f"Ошибка проверки канала {channel_name}: {error_msg}")
                    continue
        logger.info(f"Пользователь {user_id} подписан на все каналы")
        return True
    except Exception as e:
        logger.error(f"Общая ошибка проверки подписки: {e}")
        return False

# Функция для создания клавиатуры подписки
def create_subscription_keyboard():
    keyboard = []
    for channel_name, channel_link, channel_id in CHANNELS:
        keyboard.append([InlineKeyboardButton(f"{channel_name}", url=channel_link)])
    keyboard.append([InlineKeyboardButton("✅ Проверить подписку", callback_data="check_subscription")])
    return InlineKeyboardMarkup(keyboard)

# Функция для главного меню
def create_main_menu():
    keyboard = [
        [InlineKeyboardButton("⛔️SN#S", callback_data="sns_action")],  # Большая кнопка
        [
            InlineKeyboardButton("🔐СП#М", callback_data="spam_action"),
            InlineKeyboardButton("❄️AnFreez", callback_data="anfreez_action")
        ]  # Маленькие кнопки в одном ряду
    ]
    return InlineKeyboardMarkup(keyboard)

# Функция для создания простой клавиатуры с кнопкой "Назад"
def create_back_keyboard():
    keyboard = [[InlineKeyboardButton("🔙Назад", callback_data="back_to_menu")]]
    return InlineKeyboardMarkup(keyboard)

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, что команда пришла не из канала/группы
    if update.effective_chat.type != "private":
        return
    
    user_id = update.effective_user.id
    
    # Отправка фото с меню
    caption = """
🧨 *Вы стали тестировщиком Exda Snoser (FREE VERSION)*
*Каждый день доступен один запрос, за 1 запрос можно выполнить 1 действие (сн#с , сп#м кодами)*
*Выберите действие:*
"""
    
    try:
        # Отправляем фото и меню
        message = await update.message.reply_photo(
            photo="https://t.me/ak3ic9/15",
            caption=caption,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_main_menu()
        )
        # Сохраняем ID меню сообщения
        user_menu_messages[user_id] = message.message_id
    except Exception as e:
        # Если фото не загружается, отправляем только текст
        logger.error(f"Ошибка загрузки фото: {e}")
        message = await update.message.reply_text(
            text=caption,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_main_menu()
        )
        user_menu_messages[user_id] = message.message_id

# Обработчик нажатий на кнопки
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, что callback пришел из приватного чата
    if update.effective_chat.type != "private":
        return
    
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    try:
        # Сохраняем ID текущего сообщения как меню
        user_menu_messages[user_id] = query.message.message_id
        
        # Проверяем подписку для всех действий кроме проверки подписки
        if data != "check_subscription" and data != "back_to_menu":
            is_subscribed = await check_subscription(user_id, context)
            
            if not is_subscribed:
                # Показываем сообщение о необходимости подписки
                await query.edit_message_caption(
                    caption="*📢 ПОДПИШИТЕСЬ НА ВСЕХ СПОНСОРОВ ДЛЯ ДОСТУПА*\n\n*Требуется подписка на ВСЕХ спонсоров:*",
                    parse_mode=ParseMode.MARKDOWN
                )
                await query.edit_message_reply_markup(
                    reply_markup=create_subscription_keyboard()
                )
                return
        
        # Обработка разных действий
        if data == "check_subscription":
            is_subscribed = await check_subscription(user_id, context)
            
            if is_subscribed:
                # Возвращаем в главное меню
                caption = """
🧨 *Вы стали тестировщиком Exda Snoser (FREE VERSION)*
*Каждый день доступен один запрос, за 1 запрос можно выполнить 1 действие (сн#с , сп#м кодами)*
*Выберите действие:*
"""
                try:
                    await query.edit_message_caption(
                        caption=caption,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    await query.edit_message_reply_markup(
                        reply_markup=create_main_menu()
                    )
                except Exception as e:
                    logger.error(f"Ошибка редактирования сообщения с фото: {e}")
                    await query.edit_message_text(
                        text=caption,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=create_main_menu()
                    )
            else:
                # Формируем список спонсоров для сообщения
                sponsors_list = "\n".join([f"{i+1}. {CHANNELS[i][0]}" for i in range(len(CHANNELS))])
                
                await query.edit_message_caption(
                    caption=f"*❌ Вы не подписаны на всех спонсоров!*\n\n*Требуется подписка на:*\n{sponsors_list}",
                    parse_mode=ParseMode.MARKDOWN
                )
                await query.edit_message_reply_markup(
                    reply_markup=create_subscription_keyboard()
                )
        
        elif data == "sns_action":
            user_states[user_id] = "awaiting_username_sns"
            try:
                await query.edit_message_caption(
                    caption="*🤫 Отправьте юзернейм жертвы, если его нет — айди*",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                await query.edit_message_text(
                    text="*🤫 Отправьте юзернейм жертвы, если его нет — айди*",
                    parse_mode=ParseMode.MARKDOWN
                )
            await query.edit_message_reply_markup(reply_markup=None)
        
        elif data == "spam_action":
            try:
                await query.edit_message_caption(
                    caption="_Данная функция находится в разработке..._",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                await query.edit_message_text(
                    text="_Данная функция находится в разработке..._",
                    parse_mode=ParseMode.MARKDOWN
                )
            await query.edit_message_reply_markup(
                reply_markup=create_back_keyboard()
            )
        
        elif data == "anfreez_action":
            user_states[user_id] = "awaiting_username_anfreez"
            try:
                await query.edit_message_caption(
                    caption="*Отправьте юзернейм или айди для разморозки*",
                    parse_mode=ParseMode.MARKDOWN
                )
            except:
                await query.edit_message_text(
                    text="*Отправьте юзернейм или айди для разморозки*",
                    parse_mode=ParseMode.MARKDOWN
                )
            await query.edit_message_reply_markup(reply_markup=None)
        
        elif data == "back_to_menu":
            # Очищаем состояние пользователя при возврате в меню
            if user_id in user_states:
                del user_states[user_id]
            
            caption = """
🧨 *Вы стали тестировщиком Exda Snoser (FREE VERSION)*
*Каждый день доступен один запрос, за 1 запрос можно выполнить 1 действие (сн#с , сп#м кодами)*
*Выберите действие:*
"""
            try:
                # Пробуем редактировать с фото
                await query.edit_message_caption(
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN
                )
                await query.edit_message_reply_markup(
                    reply_markup=create_main_menu()
                )
            except Exception as e:
                try:
                    # Если фото нет, редактируем текст
                    await query.edit_message_text(
                        text=caption,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=create_main_menu()
                    )
                except Exception as e2:
                    logger.error(f"Ошибка при возврате в меню: {e2}")
                    # Создаем новое меню
                    await query.message.reply_text(
                        text=caption,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=create_main_menu()
                    )
    
    except Exception as e:
        logger.error(f"Ошибка в обработчике кнопок: {e}")
        # Не отправляем сообщение об ошибке в канале

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, что сообщение пришло из приватного чата
    if update.effective_chat.type != "private":
        return
    
    user_id = update.effective_user.id
    message_text = update.message.text
    
    if user_id not in user_states:
        return
    
    state = user_states[user_id]
    
    if state == "awaiting_username_sns":
        # Удаляем состояние
        del user_states[user_id]
        
        # Показываем анимацию отправки жалоб
        processing_msg = await update.message.reply_text("*❄️ Отправляю жалобы...*", parse_mode=ParseMode.MARKDOWN)
        
        # Имитация процесса на 10-15 секунд
        await asyncio.sleep(random.uniform(10, 15))
        
        # Генерация случайных чисел
        successful = random.randint(198, 202)
        blocked = random.randint(3, 14)
        
        # Создаем клавиатуру с кнопкой назад
        keyboard = [[InlineKeyboardButton("🔙Назад", callback_data="back_to_menu")]]
        
        # Редактируем сообщение с результатами
        await processing_msg.edit_text(
            text=f"""
❄️ *ЖАЛОБЫ ДОСТАВЛЕНЫ!*
💀 *Цель:* `{message_text}`
✅ *Успешных жалоб:* `{successful}`
❌ *Заблокировано:* `{blocked}`
            """,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif state == "awaiting_username_anfreez":
        # Удаляем состояние
        del user_states[user_id]
        
        # Показываем анимацию отправки апелляций
        processing_msg = await update.message.reply_text("*❄️ Отправляю апелляции...*", parse_mode=ParseMode.MARKDOWN)
        
        # Имитация процесса
        await asyncio.sleep(5)
        
        # Генерация случайного числа
        successful = random.randint(72, 120)
        
        # Создаем клавиатуру с кнопкой назад
        keyboard = [[InlineKeyboardButton("🔙Назад", callback_data="back_to_menu")]]
        
        # Редактируем сообщение с результатами
        await processing_msg.edit_text(
            text=f"""
❄️ *АППЕЛЯЦИИ ОТПРАВЛЕНЫ ✅*
✅ *Успешно:* `{successful}`
💀 *Цель:* `{message_text}`
            """,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# Обработчик ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Логируем ошибку, но не отправляем сообщения в каналах/группах
    logger.error(f"Ошибка: {context.error}")
    
    # Отправляем сообщение об ошибке только в приватном чате
    if update and update.effective_message and update.effective_chat.type == "private":
        try:
            await update.effective_message.reply_text(
                "Произошла ошибка. Используйте /start для перезапуска."
            )
        except:
            pass

# Основная функция
def main():
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Регистрируем обработчики ТОЛЬКО для приватных чатов
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Регистрируем обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Запускаем бота
    logger.info("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
