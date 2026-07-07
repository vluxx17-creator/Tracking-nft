import os

BOT_TOKEN = "8809049015:AAG6n78BagfF0AMiojQL0y1EHld3qgTylKE"

# ID группы и топиков
GROUP_ID = -1004379430999
TOPIC_IDS = {
    "cheap": 2,      # Дешёвые
    "medium": 3,     # Средние
    "expensive": 4   # Дорогие
}

# Пороги цен
CHEAP_THRESHOLD = 5
MEDIUM_THRESHOLD = 30

# Подписка
CHANNEL_USERNAME = "lpdmv"
ADMIN_ID = 8297446667
LISTEN_CHATS = [GROUP_ID]
DATABASE_FILE = "subscriptions.db"

# Настройки веб-сервера (Render передаёт PORT)
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8080))
WEBHOOK_PATH = "/webhook"

# Внешний URL вашего сервиса (Render подставит в RENDER_EXTERNAL_URL)
# Если не задано – пропишите вручную (без слеша в конце)
WEBHOOK_HOST = os.getenv("RENDER_EXTERNAL_URL", "https://ваш-сервис.onrender.com")
