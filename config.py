import os

BOT_TOKEN = "8809049015:AAG6n78BagfF0AMiojQL0y1EHld3qgTylKE"

GROUP_ID = -1004379430999
TOPIC_IDS = {
    "cheap": 2,
    "medium": 3,
    "expensive": 4
}
CHEAP_THRESHOLD = 5
MEDIUM_THRESHOLD = 30

CHANNEL_USERNAME = "lpdmv"
ADMIN_ID = 8297446667
LISTEN_CHATS = [GROUP_ID]
DATABASE_FILE = "subscriptions.db"

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8080))
WEBHOOK_PATH = "/webhook"
WEBHOOK_HOST = os.getenv("RENDER_EXTERNAL_URL", "https://ваш-сервис.onrender.com")

# Цена подписки в звёздах (Telegram Stars)
PRICE_STARS = 10  # 1 звезда за 7 дней (можно изменить)
