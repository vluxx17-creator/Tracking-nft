import logging
from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import (
    GROUP_ID, TOPIC_IDS, CHEAP_THRESHOLD, MEDIUM_THRESHOLD,
    LISTEN_CHATS, CHANNEL_USERNAME, ADMIN_ID, PRICE_STARS
)
from utils import parse_price, parse_link, extract_username
from database import init_db, is_subscription_valid, set_subscription, get_subscription
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

init_db()

# Клавиатура с кнопками подписки и покупки
def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME}")],
        [InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_subscribe")],
        [InlineKeyboardButton(text="⭐ Купить подписку (1 звезда / 7 дней)", callback_data="buy_subscription")]
    ])
    return keyboard

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=['start'])
    dp.register_message_handler(cmd_parse, commands=['parse'])  # для админа
    dp.register_callback_query_handler(check_subscribe_callback, lambda c: c.data == "check_subscribe")
    dp.register_callback_query_handler(buy_subscription_callback, lambda c: c.data == "buy_subscription")
    dp.register_callback_query_handler(pre_checkout_callback, lambda c: c.data.startswith("buy_confirm_"))
    dp.register_message_handler(handle_nft_post, lambda msg: msg.chat.id in LISTEN_CHATS, content_types=types.ContentTypes.ANY)

# ---- Команда /start ----
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    ref = message.get_args()  # реферальный код (если перешли по ссылке)

    # Если есть реферальный параметр, даём бонус рефереру
    if ref and ref.isdigit():
        referrer_id = int(ref)
        if referrer_id != user_id:
            # Добавляем 1 день рефереру
            ref_expiry = get_subscription(referrer_id)
            if ref_expiry:
                try:
                    new_date = datetime.datetime.fromisoformat(ref_expiry) + datetime.timedelta(days=1)
                    set_subscription(referrer_id, days=0, custom_date=new_date)
                except:
                    pass
            else:
                set_subscription(referrer_id, days=1)

    if user_id == ADMIN_ID:
        await message.answer("👋 Вы администратор, доступ предоставлен навсегда.")
        return

    # Проверяем подписку на канал
    try:
        member = await message.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        status = member.status
    except:
        status = "left"

    if status in ("member", "administrator", "creator"):
        set_subscription(user_id, days=7)
        expiry = get_subscription(user_id)
        await message.answer(
            f"✅ Подписка подтверждена! Доступ до {expiry}.\n"
            f"Теперь вы можете отправлять объявления в группу.\n\n"
            f"👥 Реферальная ссылка: https://t.me/{message.bot.username}?start={user_id}\n"
            f"За каждого приглашённого вы получаете +1 день.",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            f"🔒 Для доступа подпишитесь на канал @{CHANNEL_USERNAME} или купите подписку.\n"
            f"👥 Ваша реферальная ссылка: https://t.me/{message.bot.username}?start={user_id}",
            reply_markup=get_main_keyboard()
        )

# ---- Команда /parse (для админа) ----
async def cmd_parse(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Только для администратора.")
        return
    # Пытаемся получить последние 10 сообщений из группы и обработать их
    try:
        history = await message.bot.get_chat_history(GROUP_ID, limit=10)
        count = 0
        for msg in history:
            if msg.text and msg.from_user:
                # Имитируем вызов обработчика
                await handle_nft_post(msg)
                count += 1
        await message.answer(f"Обработано {count} сообщений.")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

# ---- Покупка подписки ----
async def buy_subscription_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id == ADMIN_ID:
        await callback.answer("Вы администратор, подписка не нужна.")
        return

    # Создаём инвойс для Telegram Stars
    # Для простоты используем предустановленную цену
    try:
        # Отправляем запрос на оплату через Telegram Stars
        # Используем метод send_invoice
        await callback.bot.send_invoice(
            chat_id=user_id,
            title="Подписка на трекер NFT (7 дней)",
            description="Доступ к трекеру NFT-подарков на 7 дней.",
            payload="subscription_7days",
            provider_token="",  # для Stars оставляем пустым
            currency="XTR",  # валюта Telegram Stars
            prices=[types.LabeledPrice(label="7 дней", amount=PRICE_STARS)],
            start_parameter="buy_sub",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Оплатить", pay=True)]
            ])
        )
        await callback.answer()
    except Exception as e:
        await callback.message.answer(f"Ошибка создания платежа: {e}")
        await callback.answer()

# ---- Обработка успешного платежа ----
async def pre_checkout_callback(callback: types.CallbackQuery):
    # Здесь можно обработать подтверждение оплаты (необязательно)
    await callback.answer()

# ---- Проверка подписки ----
async def check_subscribe_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id == ADMIN_ID:
        await callback.message.edit_text("Вы администратор, доступ уже есть.")
        await callback.answer()
        return
    try:
        member = await callback.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        status = member.status
    except:
        status = "left"
    if status in ("member", "administrator", "creator"):
        set_subscription(user_id, days=7)
        expiry = get_subscription(user_id)
        await callback.message.edit_text(
            f"✅ Подписка подтверждена! Доступ до {expiry}.\n"
            f"👥 Реферальная ссылка: https://t.me/{callback.bot.username}?start={user_id}"
        )
        await callback.answer()
    else:
        await callback.answer("❌ Вы ещё не подписаны. Подпишитесь или купите подписку.", show_alert=True)

# ---- Обработка сообщений из группы ----
async def handle_nft_post(message: types.Message):
    logger.info(f"Получено сообщение от {message.from_user.id} в чате {message.chat.id}")

    # Проверяем, что это текст или подпись к медиа
    text = message.text or message.caption
    if not text:
        logger.info("Сообщение без текста, пропускаем.")
        return

    user_id = message.from_user.id

    # Проверка подписки (кроме админа)
    if user_id != ADMIN_ID:
        try:
            member = await message.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
            status = member.status
        except:
            status = "left"
        if status not in ("member", "administrator", "creator"):
            logger.info(f"Пользователь {user_id} не подписан на канал.")
            await message.reply(
                f"🔒 Для отправки объявлений подпишитесь на канал @{CHANNEL_USERNAME} или купите подписку.",
                reply_markup=get_main_keyboard()
            )
            return
        if not is_subscription_valid(user_id):
            logger.info(f"У пользователя {user_id} истекла подписка, продлеваем на 7 дней.")
            set_subscription(user_id, days=7)

    # Парсинг
    link = parse_link(text)
    if not link:
        logger.info("Ссылка не найдена, пропускаем.")
        return

    price = parse_price(text)
    if price is None or price <= 0:
        logger.info("Цена не найдена или <=0, пропускаем.")
        return

    username = extract_username(message.from_user)
    is_premium = message.from_user.is_premium if hasattr(message.from_user, 'is_premium') else False
    premium_text = "✅ Premium" if is_premium else "❌ Нет Premium"

    # Категория
    if price <= CHEAP_THRESHOLD:
        category = "cheap"
        cat_label = "Дешёвые (до 5 TON)"
    elif price <= MEDIUM_THRESHOLD:
        category = "medium"
        cat_label = "Средние (5–30 TON)"
    else:
        category = "expensive"
        cat_label = "Дорогие (от 30 TON)"

    topic_id = TOPIC_IDS.get(category)
    if not topic_id:
        logger.error(f"Неизвестная категория {category}")
        return

    msg = (
        f"🎁 **Новый NFT-подарок!**\n"
        f"👤 {username}\n"
        f"💰 {price} TON\n"
        f"⭐ {premium_text}\n"
        f"🔗 [Ссылка]({link})\n"
        f"📂 {cat_label}"
    )

    try:
        await message.bot.send_message(
            chat_id=GROUP_ID,
            text=msg,
            message_thread_id=topic_id,
            parse_mode="Markdown",
            disable_web_page_preview=False
        )
        logger.info(f"Сообщение отправлено в топик {topic_id}.")
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")
