import os

BOT_TOKEN = "8809049015:AAG6n78BagfF0AMiojQL0y1EHld3qgTylKE"

# ID группы с топиками
GROUP_ID = -1004379430999

# ID топиков (разделов)
TOPIC_IDS = {
    "cheap": 2,      # Дешёвые (до 5 TON)
    "medium": 3,     # Средние (5–30 TON)
    "expensive": 4   # Дорогие (от 30 TON)
}

# Пороги цен
CHEAP_THRESHOLD = 5
MEDIUM_THRESHOLD = 30

# Канал для подписки (без @)
CHANNEL_USERNAME = "lpdmv"

# ID администратора (бесплатный доступ)
ADMIN_ID = 8297446667

# Чаты, где бот слушает сообщения (группа с трекером)
LISTEN_CHATS = [GROUP_ID]

# Название БД
DATABASE_FILE = "subscriptions.db"
