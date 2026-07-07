from aiogram import Router, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from config import GROUP_ID, TOPIC_IDS, CHEAP_THRESHOLD, MEDIUM_THRESHOLD, LISTEN_CHATS, CHANNEL_USERNAME, ADMIN_ID
from utils import parse_price, parse_link, extract_username
from database import init_db, is_subscription_valid, set_subscription, get_subscription
import logging
import datetime

router = Router()
init_db()

def get_subscribe_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📢 Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME}")
        ],
        [
            InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_subscribe")
        ]
    ])
    return keyboard

@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        await message.answer("👋 Вы администратор, доступ предоставлен навсегда.")
        return

    try:
        member = await message.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        status = member.status
    except Exception:
        status = "left"

    if status in ("member", "administrator", "creator"):
        set_subscription(user_id, days=7)
        expiry = get_subscription(user_id)
        await message.answer(
            f"✅ Вы подписаны на канал @{CHANNEL_USERNAME}!\n"
            f"Доступ к трекеру активен до **{expiry}** (по МСК).\n"
            f"Теперь вы можете отправлять объявления о NFT-подарках в эту группу.",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            f"🔒 Для доступа к трекеру необходимо подписаться на канал @{CHANNEL_USERNAME}.\n"
            f"Нажмите кнопку ниже, подпишитесь, затем нажмите «Проверить подписку».",
            reply_markup=get_subscribe_keyboard()
        )

@router.callback_query(lambda c: c.data == "check_subscribe")
async def check_subscribe_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id == ADMIN_ID:
        await callback.message.edit_text("👋 Вы администратор, доступ уже есть.")
        await callback.answer()
        return

    try:
        member = await callback.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        status = member.status
    except Exception:
        status = "left"

    if status in ("member", "administrator", "creator"):
        set_subscription(user_id, days=7)
        expiry = get_subscription(user_id)
        await callback.message.edit_text(
            f"✅ Подписка подтверждена!\n"
            f"Доступ до **{expiry}** (по МСК).\n"
            f"Теперь вы можете отправлять объявления.",
            parse_mode="Markdown"
        )
        await callback.answer()
    else:
        await callback.answer("❌ Вы ещё не подписаны. Подпишитесь и нажмите снова.", show_alert=True)

@router.message(lambda msg: msg.chat.id in LISTEN_CHATS)
async def handle_nft_post(message: Message):
    user_id = message.from_user.id

    if user_id == ADMIN_ID:
        pass
    else:
        try:
            member = await message.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
            status = member.status
        except Exception:
            status = "left"

        if status not in ("member", "administrator", "creator"):
            await message.reply(
                f"🔒 Для отправки объявлений нужно подписаться на канал @{CHANNEL_USERNAME}.\n"
                f"Используйте /start для получения инструкций.",
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

    sender = message.from_user
    username = extract_username(sender)
    is_premium = sender.is_premium if hasattr(sender, 'is_premium') else False
    premium_text = "✅ Есть Premium" if is_premium else "❌ Нет Premium"

    if price <= CHEAP_THRESHOLD:
        category = "cheap"
        category_label = "Дешёвые (до 5 TON)"
    elif price <= MEDIUM_THRESHOLD:
        category = "medium"
        category_label = "Средние (5–30 TON)"
    else:
        category = "expensive"
        category_label = "Дорогие (от 30 TON)"

    topic_id = TOPIC_IDS.get(category)
    if not topic_id:
        return

    msg = (
        f"🎁 **Новый NFT-подарок на маркете!**\n"
        f"👤 Пользователь: {username}\n"
        f"💰 Цена: {price} TON\n"
        f"⭐ {premium_text}\n"
        f"🔗 [Ссылка на подарок]({link})\n"
        f"📂 Категория: {category_label}"
    )

    try:
        await message.bot.send_message(
            chat_id=GROUP_ID,
            message_thread_id=topic_id,
            text=msg,
            parse_mode="Markdown",
            disable_web_page_preview=False
        )
    except Exception as e:
        logging.error(f"Ошибка отправки в топик {topic_id}: {e}")
