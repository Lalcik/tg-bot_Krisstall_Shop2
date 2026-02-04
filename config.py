"""
Конфигурация бота
"""

# Настройки бота
BOT_TOKEN = "8351973351:AAHxC-400lVP9QHcyIfx-sAv_beU2ctQIcA"  # Получите у @BotFather
ADMIN_IDS = [1766557182]  # ID администраторов

# Настройки платежей
PAYMENT_PROVIDER = "yookassa"  # или "stripe", "paypal"
YOOKASSA_SHOP_ID = "your_shop_id"
YOOKASSA_SECRET_KEY = "your_secret_key"

# Настройки курсов
DEFAULT_CURRENCY = "RUB"
COURSE_ACCESS_DAYS = 365  # Доступ к курсу на 1 год

# URL-адреса
PLATFORM_URL = "https://academy.example.com"
SUPPORT_CHAT = "@academy_support"