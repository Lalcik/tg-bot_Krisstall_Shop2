"""
config.py - Конфигурация бота
"""

# Токен бота - ЗАМЕНИТЕ НА СВОЙ РЕАЛЬНЫЙ ТОКЕН!
BOT_TOKEN = "8351973351:AAHxC-400lVP9QHcyIfx-sAv_beU2ctQIcA"

# Конфигурация NicePay (замените на свои данные)
NICEPAY_CONFIG = {
    'shop_id': 'YOUR_SHOP_ID',          # Ваш ID магазина в NicePay
    '9r1l6-ohyM5-27AO4-G6GsL-ddcI9': 'YOUR_SECRET_KEY',     # Секретный ключ
    'api_url': 'https://api.nicepay.ru/', # API URL NicePay
    'success_url': 'https://yourdomain.com/success',
    'fail_url': 'https://yourdomain.com/fail',
}

# База данных товаров
PRODUCTS = {
    1: {'id': 1, 'category': 'СКРИПТЫ', 'title': '🤖 Script Alfa Only', 'price': 1500,
        'description': 'скрипт alfa Only', 'file_id': None},
    2: {'id': 2, 'category': 'СКРИПТЫ', 'title': 'Script Диску', 'price': 2500,
        'description': 'Скрипт диска', 'file_id': None},
    3: {'id': 3, 'category': 'ISP ДИСК', 'title': '📡 ISP Disk|XQW', 'price': 3892,
        'description': 'ISP ДИСК|XQW', 'file_id': None},
    4: {'id': 4, 'category': 'ISP ДИСК', 'title': '🔐 ISP Disk|TUl', 'price': 3029,
        'description': 'IPS ДИСК|TUl', 'file_id': None},
    5: {'id': 5, 'category': 'УДОСТОВЕРЕНИЯ', 'title': '🪪 Удостоверение|XQW', 'price': 4313,
        'description': 'Электронное удостоверение', 'file_id': None},
    6: {'id': 6, 'category': 'УДОСТОВЕРЕНИЯ', 'title': '🏢Удостоверение|TUl ', 'price': 2029,
        'description': 'Электронное удостоверение ', 'file_id': None},
    7: {'id': 7, 'category': 'Мануал по использованию ISP Диска', 'title': '📖  Manual', 'price': 2455,
        'description': 'зачем нужен ISP ДИСК', 'file_id': None},
    8: {'id': 8, 'category': 'TRAVERS SERVERA|XQW', 'title': '🚀 Server Traversal', 'price': 1299,
        'description': 'Инструмент обхода', 'file_id': None},
    9: {'id': 9, 'category': 'TRAVERS SERVERA|TUl', 'title': '🚀 Server Traversal', 'price': 1029,
        'description': 'Инструмент обхода', 'file_id': None},
    10: {'id': 10, 'category': 'КАРТА ПАМЯТИ', 'title': '💾 Encrypted SD 128GB', 'price': 5500,
         'description': 'Зашифрованная карта', 'file_id': None},
    11: {'id': 11, 'category': 'ТОЧКА ДОСТУПА', 'title': '📶 Portable WiFi', 'price': 3900,
         'description': 'Мобильная точка доступа', 'file_id': None},
    12: {'id': 12, 'category': 'НАКОПИТЕЛЬ', 'title': '💽 External SSD 1TB', 'price': 6500,
         'description': 'Внешний SSD', 'file_id': None},
    13: {'id': 13, 'category': 'ОПЕРАТИВНАЯ ПАМЯТЬ', 'title': '⚡ DDR4 RAM 16GB', 'price': 2800,
         'description': 'Комплект памяти', 'file_id': None},
}