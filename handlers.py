from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import (
    GROUP_ID, TOPIC_IDS, CHEAP_THRESHOLD, MEDIUM_THRESHOLD,
    LISTEN_CHATS, CHANNEL_USERNAME, ADMIN_ID
)
from utils import parse_price, parse_link, extract_username
from database import init_db, is_subscription_valid, set_subscription, get_subscription
import logging

init_db()

def get_subscribe_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME}")],
        [InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_subscribe")]
    ])
    return keyboard

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=['start'])
    dp.register_callback_query_handler(check_subscribe_callback, lambda c: c.data == "check_subscribe")
    dp.register_message_handler(handle_nft_post, lambda msg: msg.chat.id in LISTEN_CHATS, content_types=types.ContentTypes.TEXT)

async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        await message.answer("👋 Вы администратор, доступ предоставлен навсегда.")
        return
    try:
        member = await message.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        status = member.status
    except:
        status = "left"
    if status in ("member", "administrator", "creator"):
        set_subscription(user_id, days=7)
        expiry = get_subscription(user_id)
        await message.answer(
            f"✅ Подписка подтверждена! Доступ до {expiry}.\nТеперь вы можете отправлять объявления."
        )
    else:
        await message.answer(
            f"🔒 Для доступа подпишитесь на канал @{CHANNEL_USERNAME} и нажмите «Проверить подписку».",
            reply_markup=get_subscribe_keyboard()
        )

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
        await callback.message.edit_text(f"✅ Доступ активирован до {expiry}.")
        await callback.answer()
    else:
        await callback.answer("❌ Вы ещё не подписаны. Подпишитесь и нажмите снова.", show_alert=True)

async def handle_nft_post(message: types.Message):
    user_id = message.from_user.id

    if user_id != ADMIN_ID:
        try:
            member = await message.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
            status = member.status
        except:
            status = "left"
        if status not in ("member", "administrator", "creator"):
            await message.reply(
                f"🔒 Подпишитесь на канал @{CHANNEL_USERNAME} для отправки.",
                reply_markup=get_subscribe_keyboard()
            )
            return
        if not is_subscription_valid(user_id):
            set_subscription(user_id, days=7)

    text = message.text or message.caption or ""
    if not text:
        return
    link = parse_link(text)
    if not link:
        return
    price = parse_price(text)
    if price is None or price <= 0:
        return

    username = extract_username(message.from_user)
    is_premium = message.from_user.is_premium if hasattr(message.from_user, 'is_premium') else False
    premium_text = "✅ Premium" if is_premium else "❌ Нет Premium"

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
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")
