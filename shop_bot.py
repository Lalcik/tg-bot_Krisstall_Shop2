"""
Telegram Bot для продажи цифровых товаров
С системой оплаты через NicePay
"""

import telebot
from telebot import types
import json
import os
import sqlite3
import hashlib
import uuid
import time
from datetime import datetime
import requests

# ========== КОНФИГУРАЦИЯ ==========

# Инициализация бота
bot = telebot.TeleBot("8351973351:AAHxC-400lVP9QHcyIfx-sAv_beU2ctQIcA")

# Конфигурация NicePay (замените на свои данные)
NICEPAY_CONFIG = {
    'shop_id': 'YOUR_SHOP_ID',          # Ваш ID магазина в NicePay
    'secret_key': 'YOUR_SECRET_KEY',     # Секретный ключ
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

# ========== БАЗА ДАННЫХ ==========

def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    # Таблица пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Таблица корзины
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        quantity INTEGER DEFAULT 1,
        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')

    # Таблица заказов
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        user_id INTEGER,
        product_id INTEGER,
        amount REAL,
        status TEXT DEFAULT 'pending',
        payment_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')

    # Таблица платежей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        payment_id TEXT PRIMARY KEY,
        order_id TEXT,
        amount REAL,
        currency TEXT DEFAULT 'RUB',
        status TEXT DEFAULT 'pending',
        payment_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES orders (order_id)
    )
    ''')

    conn.commit()
    conn.close()

def get_or_create_user(user_id, username, first_name, last_name):
    """Получить или создать пользователя"""
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    if not cursor.fetchone():
        cursor.execute('''
        INSERT INTO users (user_id, username, first_name, last_name) 
        VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))

    conn.commit()
    conn.close()
    return user_id

def add_to_cart(user_id, product_id):
    """Добавить товар в корзину"""
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    # Проверяем, есть ли уже товар в корзине
    cursor.execute('''
    SELECT id, quantity FROM cart 
    WHERE user_id = ? AND product_id = ?
    ''', (user_id, product_id))

    item = cursor.fetchone()
    if item:
        # Увеличиваем количество
        cursor.execute('''
        UPDATE cart SET quantity = quantity + 1 
        WHERE id = ?
        ''', (item[0],))
    else:
        # Добавляем новый товар
        cursor.execute('''
        INSERT INTO cart (user_id, product_id) 
        VALUES (?, ?)
        ''', (user_id, product_id))

    conn.commit()
    conn.close()

def get_cart(user_id):
    """Получить корзину пользователя"""
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    cursor.execute('''
    SELECT c.product_id, p.title, p.price, c.quantity
    FROM cart c
    JOIN (SELECT id as product_id, title, price FROM (SELECT * FROM PRODUCTS)) p 
    ON c.product_id = p.product_id
    WHERE c.user_id = ?
    ''', (user_id,))

    items = cursor.fetchall()
    conn.close()
    return items

def clear_cart(user_id):
    """Очистить корзину"""
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def create_order(user_id, product_id, amount):
    """Создать заказ"""
    order_id = f"ORD{str(int(time.time()))}{user_id}"

    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO orders (order_id, user_id, product_id, amount) 
    VALUES (?, ?, ?, ?)
    ''', (order_id, user_id, product_id, amount))

    conn.commit()
    conn.close()
    return order_id

def update_order_status(order_id, status, payment_id=None):
    """Обновить статус заказа"""
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    if status == 'completed':
        cursor.execute('''
        UPDATE orders 
        SET status = ?, payment_id = ?, completed_at = CURRENT_TIMESTAMP 
        WHERE order_id = ?
        ''', (status, payment_id, order_id))
    else:
        cursor.execute('''
        UPDATE orders 
        SET status = ?, payment_id = ? 
        WHERE order_id = ?
        ''', (status, payment_id, order_id))

    conn.commit()
    conn.close()

def create_payment(order_id, amount):
    """Создать запись о платеже"""
    payment_id = f"PAY{str(int(time.time()))}"

    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO payments (payment_id, order_id, amount) 
    VALUES (?, ?, ?)
    ''', (payment_id, order_id, amount))

    conn.commit()
    conn.close()
    return payment_id

def update_payment(payment_id, status, payment_url=None):
    """Обновить информацию о платеже"""
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    cursor.execute('''
    UPDATE payments 
    SET status = ?, payment_url = ? 
    WHERE payment_id = ?
    ''', (status, payment_url, payment_id))

    conn.commit()
    conn.close()

def get_user_orders(user_id):
    """Получить заказы пользователя"""
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    cursor.execute('''
    SELECT o.order_id, p.title, o.amount, o.status, o.created_at
    FROM orders o
    JOIN (SELECT id as product_id, title FROM (SELECT * FROM PRODUCTS)) p 
    ON o.product_id = p.product_id
    WHERE o.user_id = ?
    ORDER BY o.created_at DESC
    ''', (user_id,))

    orders = cursor.fetchall()
    conn.close()
    return orders

# ========== ПЛАТЕЖНАЯ СИСТЕМА NICEPAY ==========

def create_nicepay_payment(amount, order_id, description):
    """Создать платеж в NicePay"""
    try:
        # Генерация подписи
        signature_string = f"{NICEPAY_CONFIG['shop_id']}:{amount}:{order_id}:{NICEPAY_CONFIG['secret_key']}"
        signature = hashlib.sha256(signature_string.encode()).hexdigest()

        # Данные для запроса
        payload = {
            'shop_id': NICEPAY_CONFIG['shop_id'],
            'amount': amount,
            'order_id': order_id,
            'currency': 'RUB',
            'description': description,
            'signature': signature,
            'success_url': NICEPAY_CONFIG['success_url'],
            'fail_url': NICEPAY_CONFIG['fail_url'],
            'language': 'ru'
        }

        # Отправка запроса к API NicePay
        response = requests.post(
            f"{NICEPAY_CONFIG['api_url']}create",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return {
                    'success': True,
                    'payment_url': data.get('payment_url'),
                    'payment_id': data.get('payment_id')
                }

        return {'success': False, 'error': 'Не удалось создать платеж'}

    except Exception as e:
        return {'success': False, 'error': str(e)}

def check_nicepay_payment(payment_id):
    """Проверить статус платежа в NicePay"""
    try:
        payload = {
            'shop_id': NICEPAY_CONFIG['shop_id'],
            'payment_id': payment_id
        }

        response = requests.post(
            f"{NICEPAY_CONFIG['api_url']}check",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'status': data.get('status'),
                'amount': data.get('amount')
            }

        return {'success': False, 'error': 'Не удалось проверить платеж'}

    except Exception as e:
        return {'success': False, 'error': str(e)}

# ========== ГЛАВНОЕ МЕНЮ ==========

@bot.message_handler(commands=['start'])
def start_command(message):
    """Главное меню с кнопкой Каталог товаров"""
    user = message.from_user

    # Регистрируем пользователя в БД
    get_or_create_user(
        user.id,
        user.username,
        user.first_name,
        user.last_name
    )

    welcome_text = (
        f"{user.first_name}, привет!\n\n"
        "Ты в KRISTALL SHOP! У нас ты найдешь множество товаров для заработка и не только.\n\n"
        "Заглядывай в каталог и выбирай что-нибудь полезное! С любовью, KRISTALL SHOP ❤️"
    )

    # СОЗДАЕМ INLINE КНОПКУ ДЛЯ ССЫЛКИ
    inline_markup = types.InlineKeyboardMarkup()
    inline_markup.add(
        types.InlineKeyboardButton(
            '📄 Пользовательское соглашение',
            url='https://telegra.ph/Pravila-magazina-KRISSTALL-SHOP-01-23'
        )
    )

    # Отправляем ОДНО сообщение с текстом и inline-кнопкой
    bot.send_message(
        message.chat.id,
        welcome_text,
        parse_mode=None,
        reply_markup=inline_markup,
        disable_web_page_preview=True
    )

    # Ждем немного и отправляем Reply-меню отдельным сообщением
    time.sleep(0.3)

    # СОЗДАЕМ ГЛАВНОЕ МЕНЮ (Reply кнопки)
    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    # Основные кнопки
    reply_markup.add(
        types.KeyboardButton('📚 Каталог товаров'),
        types.KeyboardButton('🛒 Корзина')
    )

    reply_markup.add(
        types.KeyboardButton('📞 Поддержка'),
        types.KeyboardButton('ℹ️ О магазине')
    )

    reply_markup.add(
        types.KeyboardButton('💼 Мои заказы'),
        types.KeyboardButton('⭐️ Акции')
    )

    bot.send_message(
        message.chat.id,
        "👇 <b>Выберите действие:</b>",
        parse_mode='HTML',
        reply_markup=reply_markup
    )

# ========== КНОПКА "КАТАЛОГ ТОВАРОВ" ==========

@bot.message_handler(func=lambda m: m.text == '📚 Каталог товаров')
def catalog_button(message):
    """Показывает inline-кнопки категорий"""
    catalog_text = (
        "📚 <b>Каталог товаров</b>\n\n"
        "👇 <b>Выберите категорию:</b>"
    )

    markup = types.InlineKeyboardMarkup(row_width=2)

    markup.add(
        types.InlineKeyboardButton('🤖 СКРИПТЫ', callback_data='category_scripts'),
        types.InlineKeyboardButton('📡 ISP ДИСК', callback_data='category_isp')
    )

    markup.add(
        types.InlineKeyboardButton('🪪 УДОСТОВЕРЕНИЯ', callback_data='category_ids'),
        types.InlineKeyboardButton('📖 МАНУАЛЫ', callback_data='category_manuals')
    )

    markup.add(
        types.InlineKeyboardButton('🚀 TRAVERS SERVERA', callback_data='category_travers'),
        types.InlineKeyboardButton('💾 КАРТА ПАМЯТИ', callback_data='category_memory_cards')
    )

    markup.add(
        types.InlineKeyboardButton('📶 ТОЧКА ДОСТУПА', callback_data='category_hotspot'),
        types.InlineKeyboardButton('💽 НАКОПИТЕЛЬ', callback_data='category_storage')
    )

    markup.add(
        types.InlineKeyboardButton('⚡ ОПЕРАТИВНАЯ ПАМЯТЬ', callback_data='category_ram')
    )

    markup.add(
        types.InlineKeyboardButton('🔙 Назад в меню', callback_data='back_to_menu')
    )

    bot.send_message(message.chat.id, catalog_text,
                     parse_mode='HTML', reply_markup=markup)

# ========== КОРЗИНА ==========

@bot.message_handler(func=lambda m: m.text == '🛒 Корзина')
def show_cart(message):
    """Показать корзину"""
    user_id = message.from_user.id
    cart_items = get_cart(user_id)

    if not cart_items:
        cart_text = "🛒 <b>Ваша корзина пуста</b>\n\nДобавьте товары из каталога!"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(types.KeyboardButton('📚 Каталог товаров'))
        markup.add(types.KeyboardButton('🔙 Назад в меню'))
    else:
        total = 0
        cart_text = "🛒 <b>Ваша корзина</b>\n\n"

        for item in cart_items:
            product_id, title, price, quantity = item
            item_total = price * quantity
            total += item_total
            cart_text += f"▫️ <b>{title}</b>\n"
            cart_text += f"   Цена: {price} руб. × {quantity} = {item_total} руб.\n"
            cart_text += f"   /remove_{product_id} - Удалить\n\n"

        cart_text += f"💰 <b>Итого: {total} руб.</b>"

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(
            types.KeyboardButton('💳 Оформить заказ'),
            types.KeyboardButton('🧹 Очистить корзину')
        )
        markup.add(
            types.KeyboardButton('📚 Каталог товаров'),
            types.KeyboardButton('🔙 Назад в меню')
        )

    bot.send_message(
        message.chat.id,
        cart_text,
        parse_mode='HTML',
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == '🧹 Очистить корзину')
def clear_cart_handler(message):
    """Очистить корзину"""
    user_id = message.from_user.id
    clear_cart(user_id)

    bot.send_message(
        message.chat.id,
        "✅ Корзина очищена!",
        parse_mode='HTML'
    )

    # Возвращаемся к просмотру корзины
    show_cart(message)

@bot.message_handler(func=lambda m: m.text.startswith('/remove_'))
def remove_from_cart(message):
    """Удалить товар из корзины"""
    try:
        product_id = int(message.text.split('_')[1])
        user_id = message.from_user.id

        conn = sqlite3.connect('shop.db')
        cursor = conn.cursor()

        cursor.execute('DELETE FROM cart WHERE user_id = ? AND product_id = ?',
                      (user_id, product_id))
        conn.commit()
        conn.close()

        bot.send_message(
            message.chat.id,
            f"✅ Товар удален из корзины!",
            parse_mode='HTML'
        )

        # Показываем обновленную корзину
        show_cart(message)

    except Exception as e:
        bot.send_message(
            message.chat.id,
            "❌ Ошибка при удалении товара",
            parse_mode='HTML'
        )

# ========== ОФОРМЛЕНИЕ ЗАКАЗА ==========

@bot.message_handler(func=lambda m: m.text == '💳 Оформить заказ')
def checkout_handler(message):
    """Оформление заказа"""
    user_id = message.from_user.id
    cart_items = get_cart(user_id)

    if not cart_items:
        bot.send_message(
            message.chat.id,
            "❌ Ваша корзина пуста!",
            parse_mode='HTML'
        )
        return

    # Создаем заказ для каждого товара в корзине
    for item in cart_items:
        product_id, title, price, quantity = item
        total_amount = price * quantity

        # Создаем заказ в БД
        order_id = create_order(user_id, product_id, total_amount)

        # Создаем платеж в NicePay
        payment_result = create_nicepay_payment(
            amount=total_amount,
            order_id=order_id,
            description=f"Оплата товара: {title}"
        )

        if payment_result['success']:
            # Сохраняем информацию о платеже
            payment_id = create_payment(order_id, total_amount)
            update_payment(payment_id, 'pending', payment_result['payment_url'])
            update_order_status(order_id, 'pending', payment_id)

            # Отправляем ссылку на оплату
            payment_text = (
                f"💳 <b>Оплата заказа #{order_id}</b>\n\n"
                f"📦 Товар: {title}\n"
                f"💰 Сумма: {total_amount} руб.\n\n"
                f"Для оплаты перейдите по ссылке:\n"
                f"{payment_result['payment_url']}\n\n"
                f"После оплаты товар будет отправлен автоматически."
            )

            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "🔗 Перейти к оплате",
                    url=payment_result['payment_url']
                )
            )
            markup.add(
                types.InlineKeyboardButton(
                    "🔄 Проверить статус",
                    callback_data=f"check_payment_{payment_id}"
                )
            )

            bot.send_message(
                message.chat.id,
                payment_text,
                parse_mode='HTML',
                reply_markup=markup
            )
        else:
            bot.send_message(
                message.chat.id,
                f"❌ Ошибка при создании платежа: {payment_result.get('error')}",
                parse_mode='HTML'
            )

    # Очищаем корзину после создания заказов
    clear_cart(user_id)

# ========== МОИ ЗАКАЗЫ ==========

@bot.message_handler(func=lambda m: m.text == '💼 Мои заказы')
def my_orders_handler(message):
    """Показать заказы пользователя"""
    user_id = message.from_user.id
    orders = get_user_orders(user_id)

    if not orders:
        orders_text = "📭 <b>У вас пока нет заказов</b>\n\nПерейдите в каталог, чтобы сделать первый заказ!"
    else:
        orders_text = "📦 <b>Ваши заказы</b>\n\n"

        for order in orders:
            order_id, title, amount, status, created_at = order

            status_icons = {
                'pending': '⏳',
                'completed': '✅',
                'failed': '❌'
            }

            status_text = {
                'pending': 'Ожидает оплаты',
                'completed': 'Оплачен',
                'failed': 'Ошибка оплаты'
            }

            icon = status_icons.get(status, '📦')
            status_display = status_text.get(status, status)

            orders_text += f"{icon} <b>Заказ #{order_id}</b>\n"
            orders_text += f"Товар: {title}\n"
            orders_text += f"Сумма: {amount} руб.\n"
            orders_text += f"Статус: {status_display}\n"
            orders_text += f"Дата: {created_at}\n\n"

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton('📚 Каталог товаров'),
        types.KeyboardButton('🔙 Назад в меню')
    )

    bot.send_message(
        message.chat.id,
        orders_text,
        parse_mode='HTML',
        reply_markup=markup
    )

# ========== CALLBACK ОБРАБОТЧИКИ ==========

@bot.callback_query_handler(func=lambda call: call.data.startswith('check_payment_'))
def check_payment_status(call):
    """Проверить статус платежа"""
    payment_id = call.data.split('_')[2]

    # Проверяем статус платежа в NicePay
    result = check_nicepay_payment(payment_id)

    if result['success']:
        if result['status'] == 'success':
            # Платеж успешен
            update_payment(payment_id, 'completed')

            # Находим заказ по payment_id и обновляем его статус
            conn = sqlite3.connect('shop.db')
            cursor = conn.cursor()
            cursor.execute('SELECT order_id FROM payments WHERE payment_id = ?', (payment_id,))
            order_data = cursor.fetchone()

            if order_data:
                order_id = order_data[0]
                update_order_status(order_id, 'completed', payment_id)

                # Отправляем товар пользователю
                cursor.execute('SELECT product_id FROM orders WHERE order_id = ?', (order_id,))
                product_data = cursor.fetchone()

                if product_data:
                    product_id = product_data[0]
                    product = PRODUCTS.get(product_id)

                    if product:
                        delivery_text = (
                            f"✅ <b>Оплата подтверждена!</b>\n\n"
                            f"Заказ #{order_id} успешно оплачен.\n"
                            f"Товар: {product['title']}\n"
                            f"Сумма: {result['amount']} руб.\n\n"
                            f"Товар будет отправлен в течение 5 минут."
                        )

                        # Здесь можно добавить отправку файла или ссылки
                        bot.send_message(
                            call.message.chat.id,
                            delivery_text,
                            parse_mode='HTML'
                        )

            conn.close()

            bot.answer_callback_query(
                call.id,
                "✅ Оплата подтверждена! Товар отправляется...",
                show_alert=True
            )

        elif result['status'] == 'pending':
            bot.answer_callback_query(
                call.id,
                "⏳ Платеж еще в обработке. Попробуйте позже.",
                show_alert=True
            )

        else:
            bot.answer_callback_query(
                call.id,
                "❌ Платеж не прошел. Попробуйте оплатить снова.",
                show_alert=True
            )

    else:
        bot.answer_callback_query(
            call.id,
            f"Ошибка проверки платежа: {result.get('error')}",
            show_alert=True
        )

# ========== АДМИН ПАНЕЛЬ ==========

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    """Админ панель (для статистики)"""
    user_id = message.from_user.id

    # Здесь можно добавить проверку прав администратора
    # if user_id not in ADMIN_IDS: return

    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    # Статистика
    cursor.execute('SELECT COUNT(*) FROM users')
    users_count = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM orders WHERE status = "completed"')
    orders_count = cursor.fetchone()[0]

    cursor.execute('SELECT SUM(amount) FROM orders WHERE status = "completed"')
    revenue = cursor.fetchone()[0] or 0

    conn.close()

    admin_text = (
        "👑 <b>Админ панель</b>\n\n"
        f"👥 Пользователей: {users_count}\n"
        f"📦 Заказов: {orders_count}\n"
        f"💰 Выручка: {revenue} руб.\n\n"
        "Команды:\n"
        "/stats - Подробная статистика\n"
        "/broadcast - Рассылка\n"
        "/products - Управление товарами"
    )

    bot.send_message(
        message.chat.id,
        admin_text,
        parse_mode='HTML'
    )

# ========== ОБНОВЛЕННЫЕ CALLBACK ОБРАБОТЧИКИ ==========

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def buy_product_handler(call):
    """Обработка кнопки 'Купить сейчас'"""
    product_id = int(call.data.split('_')[1])
    product = PRODUCTS.get(product_id)
    user_id = call.from_user.id

    if product:
        # Создаем заказ
        order_id = create_order(user_id, product_id, product['price'])

        # Создаем платеж в NicePay
        payment_result = create_nicepay_payment(
            amount=product['price'],
            order_id=order_id,
            description=f"Оплата товара: {product['title']}"
        )

        if payment_result['success']:
            # Сохраняем информацию о платеже
            payment_id = create_payment(order_id, product['price'])
            update_payment(payment_id, 'pending', payment_result['payment_url'])
            update_order_status(order_id, 'pending', payment_id)

            payment_text = (
                f"💳 <b>Оплата товара</b>\n\n"
                f"📦 {product['title']}\n"
                f"💰 Сумма: {product['price']} руб.\n\n"
                f"Для оплаты перейдите по ссылке:\n"
                f"{payment_result['payment_url']}"
            )

            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "🔗 Перейти к оплате",
                    url=payment_result['payment_url']
                )
            )
            markup.add(
                types.InlineKeyboardButton(
                    "🔄 Проверить статус",
                    callback_data=f"check_payment_{payment_id}"
                )
            )

            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=payment_text,
                parse_mode='HTML',
                reply_markup=markup
            )
        else:
            bot.answer_callback_query(
                call.id,
                f"Ошибка: {payment_result.get('error')}",
                show_alert=True
            )

@bot.callback_query_handler(func=lambda call: call.data.startswith('add_'))
def add_to_cart_handler(call):
    """Добавить товар в корзину"""
    product_id = int(call.data.split('_')[1])
    product = PRODUCTS.get(product_id)

    if product:
        user_id = call.from_user.id
        add_to_cart(user_id, product_id)

        bot.answer_callback_query(
            call.id,
            f"✅ {product['title']} добавлен в корзину!"
        )

# ========== ЗАПУСК БОТА ==========

if __name__ == "__main__":
    # Инициализация базы данных
    init_db()

    print("=" * 50)
    print("🏪 KRISTALL SHOP Bot запущен!")
    print("💳 Интегрирована система оплаты через NicePay")
    print("=" * 50)
    print("📊 База данных инициализирована")
    print("⚡ Ожидаю сообщений...")

    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"❌ Ошибка: {e}")