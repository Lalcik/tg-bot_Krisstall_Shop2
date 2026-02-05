"""
Telegram Bot для продажи цифровых товаров
С отдельной кнопкой "Каталог товаров" и inline-кнопками категорий
С интеграцией CryptoBot для оплаты криптовалютой
"""

import telebot
from telebot import types
import json
import os
from datetime import datetime
import time
import hashlib
import sqlite3
import uuid
import traceback
import requests

# Инициализация бота
bot = telebot.TeleBot("8351973351:AAHxC-400lVP9QHcyIfx-sAv_beU2ctQIcA")

# ========== НАСТРОЙКИ CRYPTOBOT ==========
# Получите токен на @CryptoBot или @CryptoTestnetBot для тестов
CRYPTOBOT_API_TOKEN = ""  # Ваш API токен от CryptoBot
CRYPTOBOT_TEST_MODE = True  # Используйте True для тестового режима

# URL API CryptoBot
if CRYPTOBOT_TEST_MODE:
    CRYPTOBOT_API_URL = "https://testnet-pay.crypt.bot/api"
    print("⚠️ Используется ТЕСТОВЫЙ режим CryptoBot (Testnet)")
else:
    CRYPTOBOT_API_URL = "https://net-pay.crypt.bot/api"
    print("✅ Используется ПРОДАКШН режим CryptoBot")

# ========== БАЗА ДАННЫХ (ИСПРАВЛЕННАЯ) ==========
def init_database():
    """Инициализация базы данных с проверкой структуры"""
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()

    print("🔄 Проверяем структуру базы данных...")

    # Таблица заказов - создаем или проверяем
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE,
            user_id INTEGER,
            product_id INTEGER,
            product_title TEXT,
            amount REAL,
            status TEXT DEFAULT 'pending',
            payment_method TEXT,
            payment_url TEXT,
            cryptobot_invoice_id TEXT,
            cryptobot_asset TEXT,
            cryptobot_amount TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Проверяем наличие всех необходимых столбцов
    cursor.execute("PRAGMA table_info(orders)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    print(f"Столбцы в таблице orders: {column_names}")

    # Добавляем недостающие столбцы для CryptoBot
    required_columns = {
        'product_title': 'TEXT',
        'payment_method': 'TEXT',
        'payment_url': 'TEXT',
        'cryptobot_invoice_id': 'TEXT',
        'cryptobot_asset': 'TEXT',
        'cryptobot_amount': 'TEXT'
    }

    for col_name, col_type in required_columns.items():
        if col_name not in column_names:
            print(f"⚠️ Добавляем столбец {col_name} в таблицу orders")
            try:
                cursor.execute(f'ALTER TABLE orders ADD COLUMN {col_name} {col_type}')
                print(f"✅ Столбец {col_name} добавлен")
            except Exception as e:
                print(f"❌ Ошибка при добавлении столбца {col_name}: {e}")

    # Таблица корзины - создаем или проверяем
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            product_title TEXT,
            price REAL,
            quantity INTEGER DEFAULT 1,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Проверяем столбцы в корзине
    cursor.execute("PRAGMA table_info(cart)")
    cart_columns = cursor.fetchall()
    cart_column_names = [col[1] for col in cart_columns]

    print(f"Столбцы в таблице cart: {cart_column_names}")

    # Добавляем недостающие столбцы в корзину
    required_cart_columns = {
        'product_title': 'TEXT',
        'price': 'REAL'
    }

    for col_name, col_type in required_cart_columns.items():
        if col_name not in cart_column_names:
            print(f"⚠️ Добавляем столбец {col_name} в таблицу cart")
            try:
                cursor.execute(f'ALTER TABLE cart ADD COLUMN {col_name} {col_type}')
                print(f"✅ Стобец {col_name} добавлен")
            except Exception as e:
                print(f"❌ Ошибка при добавлении столбца {col_name}: {e}")

    conn.commit()
    conn.close()
    print("✅ База данных проверена и готова к работе")

# Инициализируем БД
init_database()

# База данных товаров (упрощенная версия)
PRODUCTS = {
    # СКРИПТЫ
    1: {'id': 1, 'category': 'СКРИПТЫ', 'title': '🤖 Script Alfa Only', 'price': 1500,
        'description': 'скрипт alfa Only'},
    2: {'id': 2, 'category': 'СКРИПТЫ', 'title': 'Script Диску', 'price': 2500,
        'description': 'Скрипт диска'},

    # ISP ДИСК
    3: {'id': 3, 'category': 'ISP ДИСК', 'title': '📡 ISP Disk|XQW', 'price': 3892, 'description': 'ISP ДИСК|XQW'},
    4: {'id': 4, 'category': 'ISP ДИСК', 'title': '🔐 ISP Disk|TUl', 'price': 3029, 'description': 'IPS ДИСК|TUl'},

    # УДОСТОВЕРЕНИЯ
    5: {'id': 5, 'category': 'УДОСТОВЕРЕНИЯ', 'title': '🪪 Удостоверение|XQW', 'price': 4313,
        'description': 'Электронное удостоверение'},
    6: {'id': 6, 'category': 'УДОСТОВЕРЕНИЯ', 'title': '🏢Удостоверение|TUl ', 'price': 2029,
        'description': 'Электронное удостоверение '},

    # МАНУАЛЫ
    7: {'id': 7, 'category': 'Мануал по использованию ISP Диска', 'title': '📖  Manual', 'price': 2455,
        'description': 'зачем нужен ISP ДИСК'},

    # TRAVERS SERVERA
    8: {'id': 8, 'category': 'TRAVERS SERVERA|XQW', 'title': '🚀 Server Traversal', 'price': 1299,
        'description': 'Инструмент обхода'},
    9: {'id': 9, 'category': 'TRAVERS SERVERA|TUl', 'title': '🚀 Server Traversal', 'price': 1029,
        'description': 'Инструмент обхода'},

    # КАРТА ПАМЯТИ
    10: {'id': 10, 'category': 'КАРТА ПАМЯТИ', 'title': '💾 Encrypted SD 128GB', 'price': 5500,
         'description': 'Зашифрованная карта'},

    # ТОЧКА ДОСТУПА
    11: {'id': 11, 'category': 'ТОЧКА ДОСТУПА', 'title': '📶 Portable WiFi', 'price': 3900,
         'description': 'Мобильная точка доступа'},

    # НАКОПИТЕЛЬ
    12: {'id': 12, 'category': 'НАКОПИТЕЛЬ', 'title': '💽 External SSD 1TB', 'price': 6500,
         'description': 'Внешний SSD'},

    # ОПЕРАТИВНАЯ ПАМЯТЬ
    13: {'id': 13, 'category': 'ОПЕРАТИВНАЯ ПАМЯТЬ', 'title': '⚡ DDR4 RAM 16GB', 'price': 2800,
         'description': 'Комплект памяти'},
}

# ========== ПЛАТЕЖНЫЕ СИСТЕМЫ ==========
class PaymentSystem:
    @staticmethod
    def create_payment(order_data, payment_method):
        """Создание платежа в зависимости от выбранного метода"""
        try:
            if payment_method == 'card':
                return PaymentSystem._create_card_payment(order_data)
            elif payment_method == 'yoomoney':
                return PaymentSystem._create_yoomoney_payment(order_data)
            elif payment_method == 'cryptobot':
                return PaymentSystem._create_cryptobot_payment(order_data)
            else:
                return {'success': False, 'error': 'Неизвестный метод оплаты'}
        except Exception as e:
            print(f"❌ Ошибка создания платежа: {e}")
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _create_card_payment(order_data):
        """Создание платежа банковской картой (тестовый)"""
        order_id = order_data['order_id']
        amount = order_data['amount']

        # Тестовый платежный URL
        payment_url = f"https://test-payment.example.com/pay?order_id={order_id}&amount={amount}"

        # Сохраняем платеж в БД
        conn = sqlite3.connect('shop.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE orders 
            SET payment_url = ?, payment_method = 'card', status = 'waiting_payment'
            WHERE order_id = ?
        ''', (payment_url, order_id))
        conn.commit()
        conn.close()

        return {
            'success': True,
            'payment_url': payment_url,
            'order_id': order_id,
            'method': 'card'
        }

    @staticmethod
    def _create_yoomoney_payment(order_data):
        """Создание платежа через ЮMoney (тестовый)"""
        order_id = order_data['order_id']
        amount = order_data['amount']

        # Тестовый платежный URL для ЮMoney
        payment_url = f"https://yoomoney.ru/pay?order_id={order_id}&amount={amount}"

        # Сохраняем платеж в БД
        conn = sqlite3.connect('shop.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE orders 
            SET payment_url = ?, payment_method = 'yoomoney', status = 'waiting_payment'
            WHERE order_id = ?
        ''', (payment_url, order_id))
        conn.commit()
        conn.close()

        return {
            'success': True,
            'payment_url': payment_url,
            'order_id': order_id,
            'method': 'yoomoney'
        }

    @staticmethod
    def _create_cryptobot_payment(order_data):
        """Создание платежа через CryptoBot (криптовалюта)"""
        try:
            order_id = order_data['order_id']
            amount_rub = order_data['amount']
            description = order_data.get('description', f"Оплата заказа {order_id}")

            # Конвертируем рубли в USDT (примерный курс)
            # В реальном проекте используйте актуальный курс обмена
            exchange_rate = 90  # 1 USDT ≈ 90 RUB (примерно)
            amount_usdt = round(float(amount_rub) / exchange_rate, 2)

            # Минимальная сумма для CryptoBot
            if amount_usdt < 1.0:
                amount_usdt = 1.0  # Минимум 1 USDT

            # Создаем инвойс в CryptoBot
            headers = {
                "Crypto-Pay-API-Token": CRYPTOBOT_API_TOKEN,
                "Content-Type": "application/json"
            }

            payload = {
                "asset": "USDT",  # Можно изменить на BTC, ETH, TON и т.д.
                "amount": str(amount_usdt),
                "description": description,
                "hidden_message": f"Заказ {order_id}",
                "paid_btn_name": "viewItem",  # Кнопка после оплаты
                "paid_btn_url": f"https://t.me/{bot.get_me().username}?start=order_{order_id}",
                "payload": order_id,  # Передаем ID заказа для вебхука
                "allow_comments": True,
                "allow_anonymous": False,
                "expires_in": 3600  # Инвойс действителен 1 час
            }

            if CRYPTOBOT_API_TOKEN:
                try:
                    response = requests.post(
                        f"{CRYPTOBOT_API_URL}/createInvoice",
                        headers=headers,
                        json=payload,
                        timeout=30
                    )

                    if response.status_code == 200:
                        result = response.json()
                        if result.get('ok'):
                            invoice = result['result']

                            # Сохраняем информацию о платеже в БД
                            conn = sqlite3.connect('shop.db')
                            cursor = conn.cursor()
                            cursor.execute('''
                                UPDATE orders 
                                SET payment_url = ?, payment_method = 'cryptobot', 
                                    status = 'waiting_payment', cryptobot_invoice_id = ?,
                                    cryptobot_asset = ?, cryptobot_amount = ?
                                WHERE order_id = ?
                            ''', (
                                invoice.get('pay_url'),
                                invoice.get('invoice_id'),
                                invoice.get('asset'),
                                invoice.get('amount'),
                                order_id
                            ))
                            conn.commit()
                            conn.close()

                            return {
                                'success': True,
                                'payment_url': invoice.get('pay_url'),
                                'order_id': order_id,
                                'method': 'cryptobot',
                                'invoice_id': invoice.get('invoice_id'),
                                'asset': invoice.get('asset'),
                                'amount': invoice.get('amount'),
                                'real_mode': not CRYPTOBOT_TEST_MODE
                            }
                        else:
                            return {
                                'success': False,
                                'error': f"CryptoBot error: {result.get('error', 'Unknown error')}"
                            }
                    else:
                        return {
                            'success': False,
                            'error': f"HTTP error: {response.status_code}"
                        }
                except Exception as e:
                    return {
                        'success': False,
                        'error': f"CryptoBot API error: {str(e)}"
                    }
            else:
                # Если токен не настроен, создаем тестовую ссылку
                print("⚠️ CryptoBot токен не настроен, используем тестовую ссылку")
                payment_url = f"https://t.me/CryptoTestnetBot?start=invoice_{order_id}"

                conn = sqlite3.connect('shop.db')
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE orders 
                    SET payment_url = ?, payment_method = 'cryptobot', status = 'waiting_payment'
                    WHERE order_id = ?
                ''', (payment_url, order_id))
                conn.commit()
                conn.close()

                return {
                    'success': True,
                    'payment_url': payment_url,
                    'order_id': order_id,
                    'method': 'cryptobot',
                    'test_mode': True
                }

        except Exception as e:
            print(f"❌ Ошибка создания платежа CryptoBot: {e}")
            return {'success': False, 'error': str(e)}

    @staticmethod
    def check_cryptobot_payment(invoice_id):
        """Проверка статуса оплаты в CryptoBot"""
        try:
            if not CRYPTOBOT_API_TOKEN:
                return {'success': False, 'error': 'CryptoBot не настроен'}

            headers = {
                "Crypto-Pay-API-Token": CRYPTOBOT_API_TOKEN
            }

            response = requests.get(
                f"{CRYPTOBOT_API_URL}/getInvoices?invoice_ids={invoice_id}",
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('ok') and result.get('result', {}).get('items'):
                    invoice = result['result']['items'][0]
                    return {
                        'success': True,
                        'status': invoice.get('status'),
                        'amount': invoice.get('amount'),
                        'asset': invoice.get('asset'),
                        'paid_at': invoice.get('paid_at')
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('error', 'Invoice not found')
                    }
            else:
                return {
                    'success': False,
                    'error': f"HTTP error: {response.status_code}"
                }

        except Exception as e:
            return {
                'success': False,
                'error': f"API error: {str(e)}"
            }

    @staticmethod
    def simulate_payment(order_id):
        """Симуляция успешной оплаты (для тестирования)"""
        try:
            conn = sqlite3.connect('shop.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE orders 
                SET status = 'paid'
                WHERE order_id = ?
            ''', (order_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Ошибка симуляции платежа: {e}")
            return False

# ========== ГЛАВНОЕ МЕНЮ ==========

@bot.message_handler(commands=['start'])
def start_command(message):
    try:
        file = open('I:\\javanik\\тг шоп\\аваjpg.jpg', 'rb')
        bot.send_photo(message.chat.id, file, reply_markup=None)
    except:
        pass

    user = message.from_user

    welcome_text = (
        f"{user.first_name}, привет!\n\n"
        "Ты в KRISTALL SHOP! У нас ты найдешь множество товаров для заработка и не только.\n\n"
        "Заглядывай в каталог и выбирай что-нибудь полезное! С любовью, KRISTALL SHOP ❤️"
    )

    inline_markup = types.InlineKeyboardMarkup()
    inline_markup.add(
        types.InlineKeyboardButton(
            '📄 Пользовательское соглашение',
            url='https://telegra.ph/Pravila-magazina-KRISSTALL-SHOP-01-23'
        )
    )

    bot.send_message(
        message.chat.id,
        welcome_text,
        parse_mode=None,
        reply_markup=inline_markup,
        disable_web_page_preview=True
    )

    time.sleep(0.3)

    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    reply_markup.add(
        types.KeyboardButton('📚 Каталог товаров'),
        types.KeyboardButton('🛒 Корзина')
    )
    reply_markup.add(
        types.KeyboardButton('📞 Поддержка'),
        types.KeyboardButton('ℹ️ О магазине')
    )
    reply_markup.add(
        types.KeyboardButton('💳 Оплата'),
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
    """Показывает inline-кнопки категорий при нажатии на 'Каталог товаров'"""

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


# ========== ОБРАБОТКА КАТЕГОРИЙ (INLINE) ==========

@bot.callback_query_handler(func=lambda call: call.data.startswith('category_'))
def show_category_products_inline(call):
    """Показать товары выбранной категории (через inline-кнопки)"""
    try:
        category_map = {
            'category_scripts': 'СКРИПТЫ',
            'category_isp': 'ISP ДИСК',
            'category_ids': 'УДОСТОВЕРЕНИЯ',
            'category_manuals': 'Мануал по использованию ISP Диска',
            'category_travers': 'TRAVERS SERVERA',
            'category_memory_cards': 'КАРТА ПАМЯТИ',
            'category_hotspot': 'ТОЧКА ДОСТУПА',
            'category_storage': 'НАКОПИТЕЛЬ',
            'category_ram': 'ОПЕРАТИВНАЯ ПАМЯТЬ'
        }

        category_data = call.data
        category_name = category_map.get(category_data)

        if not category_name:
            bot.answer_callback_query(call.id, "Категория не найдена")
            return

        category_products = [p for p in PRODUCTS.values() if p['category'] == category_name]

        if not category_products:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"⚠️ Товары в категории '{category_name}' временно отсутствуют.\n\nНажмите /start для возврата в меню.",
                parse_mode='HTML'
            )
            bot.answer_callback_query(call.id)
            return

        products_text = f"<b>📂 Категория: {category_name}</b>\n\n"

        for product in category_products:
            products_text += (
                f"<b>{product['title']}</b>\n"
                f"💰 Цена: <code>{product['price']} руб.</code>\n"
                f"📝 {product['description']}\n"
                f"🆔 ID: <code>#{product['id']:03d}</code>\n"
                f"👇 /product_{product['id']} - Подробнее\n\n"
            )

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton('📚 Назад к каталогу', callback_data='back_to_catalog'),
            types.InlineKeyboardButton('🏠 В главное меню', callback_data='back_to_menu')
        )

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=products_text,
            parse_mode='HTML',
            reply_markup=markup
        )

    except Exception as e:
        print(f"Ошибка в show_category_products_inline: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка загрузки категории")

    bot.answer_callback_query(call.id)


# ========== КОМАНДЫ ДЛЯ ТОВАРОВ ==========

@bot.message_handler(commands=['product_1', 'product_2', 'product_3', 'product_4',
                               'product_5', 'product_6', 'product_7', 'product_8',
                               'product_9', 'product_10', 'product_11', 'product_12',
                               'product_13'])
def show_product_detail(message):
    """Показать детальную информацию о товаре"""
    try:
        product_id = int(message.text.split('_')[1])
        product = PRODUCTS.get(product_id)

        if not product:
            bot.send_message(message.chat.id, "❌ Товар не найден")
            return

        detail_text = (
            f"<b>{product['title']}</b>\n\n"
            f"📂 <b>Категория:</b> {product['category']}\n"
            f"💰 <b>Цена:</b> <code>{product['price']} руб.</code>\n\n"
            f"📝 <b>Описание:</b>\n{product['description']}\n\n"
            f"🚚 <b>Получение:</b> Мгновенно после оплаты\n"
            f"🆔 <b>ID товара:</b> <code>#{product_id:03d}</code>"
        )

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton(
                "🛒 Добавить в корзину",
                callback_data=f"add_{product_id}"
            ),
            types.InlineKeyboardButton(
                "💳 Купить сейчас",
                callback_data=f"buy_now_{product_id}"
            )
        )

        markup.add(
            types.InlineKeyboardButton(
                "🔙 Назад к категории",
                callback_data=f"back_to_{product['category'].replace(' ', '_')}"
            )
        )

        bot.send_message(
            message.chat.id,
            detail_text,
            parse_mode='HTML',
            reply_markup=markup
        )
    except Exception as e:
        print(f"Ошибка в show_product_detail: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка загрузки товара")


# ========== ОБРАБОТКА ДОБАВЛЕНИЯ В КОРЗИНУ ==========

@bot.callback_query_handler(func=lambda call: call.data.startswith('add_'))
def add_to_cart(call):
    """Добавление товара в корзину"""
    try:
        product_id = int(call.data.split('_')[1])
        product = PRODUCTS.get(product_id)

        if not product:
            bot.answer_callback_query(call.id, "❌ Товар не найден")
            return

        user_id = call.from_user.id

        conn = sqlite3.connect('shop.db')
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, quantity FROM cart 
            WHERE user_id = ? AND product_id = ?
        ''', (user_id, product_id))

        existing = cursor.fetchone()

        if existing:
            cursor.execute('''
                UPDATE cart SET quantity = quantity + 1 
                WHERE id = ?
            ''', (existing[0],))
        else:
            cursor.execute('''
                INSERT INTO cart (user_id, product_id, product_title, price)
                VALUES (?, ?, ?, ?)
            ''', (user_id, product_id, product['title'], product['price']))

        conn.commit()
        conn.close()

        bot.answer_callback_query(
            call.id,
            f"✅ {product['title']} добавлен в корзину!"
        )
    except Exception as e:
        print(f"Ошибка в add_to_cart: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка добавления в корзину")


# ========== КОРЗИНА ==========

@bot.message_handler(func=lambda m: m.text == '🛒 Корзина')
def show_cart(message):
    """Показать корзину с товарами"""
    try:
        user_id = message.from_user.id

        conn = sqlite3.connect('shop.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT product_id, product_title, price, quantity 
            FROM cart WHERE user_id = ?
        ''', (user_id,))

        cart_items = cursor.fetchall()
        conn.close()

        if not cart_items:
            cart_text = "🛒 <b>Ваша корзина пуста</b>"

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
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
            return

        cart_text = "🛒 <b>Ваша корзина</b>\n\n"
        total = 0

        for item in cart_items:
            product_id, title, price, quantity = item
            item_total = price * quantity
            total += item_total

            cart_text += (
                f"• {title}\n"
                f"  Цена: {price} руб. × {quantity} = {item_total} руб.\n"
                f"  ID: <code>#{product_id:03d}</code>\n\n"
            )

        cart_text += f"<b>💰 Итого: {total} руб.</b>"

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
    except Exception as e:
        print(f"Ошибка в show_cart: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка загрузки корзины")


# ========== ПРЯМАЯ ПОКУПКА ==========

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_now_'))
def buy_now(call):
    """Прямая покупка без корзины"""
    try:
        print(f"🛒 Нажата кнопка 'Купить сейчас': {call.data}")

        product_id = int(call.data.replace('buy_now_', ''))
        product = PRODUCTS.get(product_id)

        if not product:
            bot.answer_callback_query(call.id, "❌ Товар не найден")
            return

        user_id = call.from_user.id

        order_id = f"DIRECT_{user_id}_{product_id}_{int(time.time())}"

        conn = sqlite3.connect('shop.db')
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO orders (order_id, user_id, product_id, product_title, amount, status)
                VALUES (?, ?, ?, ?, ?, 'pending')
            ''', (order_id, user_id, product_id, product['title'], product['price']))

            conn.commit()
            print(f"✅ Заказ {order_id} создан в БД")

        except Exception as db_error:
            print(f"❌ Ошибка БД при создании заказа: {db_error}")
            try:
                cursor.execute('''
                    INSERT INTO orders (order_id, user_id, product_id, amount, status)
                    VALUES (?, ?, ?, ?, 'pending')
                ''', (order_id, user_id, product_id, product['price']))
                conn.commit()
                print("✅ Заказ создан без product_title")
            except Exception as alt_error:
                print(f"❌ Альтернативный запрос тоже не сработал: {alt_error}")
                bot.answer_callback_query(call.id, "❌ Ошибка базы данных")
                conn.close()
                return
        finally:
            conn.close()

        show_payment_options(call, {
            'order_id': order_id,
            'product': product['title'],
            'amount': product['price']
        })

        bot.answer_callback_query(call.id)

    except Exception as e:
        print(f"❌ Критическая ошибка в buy_now: {e}")
        traceback.print_exc()
        bot.answer_callback_query(call.id, "❌ Ошибка при создании заказа")


# ========== ОПЦИИ ОПЛАТЫ (С ДОБАВЛЕННЫМ CRYPTOBOT) ==========

def show_payment_options(message_or_call, order_info):
    """Показать варианты оплаты с CryptoBot"""
    try:
        payment_text = (
            f"💳 <b>Оплата заказа</b>\n\n"
            f"📦 Товар: {order_info['product']}\n"
            f"💰 Сумма: <b>{order_info['amount']} руб.</b>\n"
            f"🆔 Номер заказа: <code>{order_info['order_id']}</code>\n\n"
            f"👇 Выберите способ оплаты:"
        )

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton(
                "💳 Банковская карта",
                callback_data=f"pay_card_{order_info['order_id']}"
            ),
            types.InlineKeyboardButton(
                "🤝 ЮMoney",
                callback_data=f"pay_yoomoney_{order_info['order_id']}"
            )
        )
        markup.add(
            types.InlineKeyboardButton(
                "₿ Криптовалюта (CryptoBot)",
                callback_data=f"pay_cryptobot_{order_info['order_id']}"
            )
        )
        markup.add(
            types.InlineKeyboardButton(
                "🔙 Назад к каталогу",
                callback_data="back_to_catalog"
            )
        )

        if isinstance(message_or_call, types.CallbackQuery):
            chat_id = message_or_call.message.chat.id
            message_id = message_or_call.message.message_id

            try:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=payment_text,
                    parse_mode='HTML',
                    reply_markup=markup
                )
            except:
                bot.send_message(
                    chat_id,
                    payment_text,
                    parse_mode='HTML',
                    reply_markup=markup
                )
        else:
            bot.send_message(
                message_or_call.chat.id,
                payment_text,
                parse_mode='HTML',
                reply_markup=markup
            )

    except Exception as e:
        print(f"❌ Ошибка в show_payment_options: {e}")
        if isinstance(message_or_call, types.CallbackQuery):
            bot.send_message(
                message_or_call.message.chat.id,
                "❌ Ошибка при создании платежа"
            )


# ========== ОБРАБОТКА ВЫБОРА СПОСОБА ОПЛАТЫ ==========

@bot.callback_query_handler(func=lambda call: call.data.startswith(('pay_card_', 'pay_yoomoney_', 'pay_cryptobot_')))
def handle_payment_method(call):
    """Обработка выбора способа оплаты"""
    try:
        print(f"DEBUG: Получен payment callback: {call.data}")

        if call.data.startswith('pay_card_'):
            order_id = call.data.replace('pay_card_', '')
            payment_method = 'card'
            method_name = "💳 Банковской картой"
        elif call.data.startswith('pay_yoomoney_'):
            order_id = call.data.replace('pay_yoomoney_', '')
            payment_method = 'yoomoney'
            method_name = "🤝 ЮMoney"
        else:
            order_id = call.data.replace('pay_cryptobot_', '')
            payment_method = 'cryptobot'
            method_name = "₿ Криптовалютой (CryptoBot)"

        print(f"DEBUG: Order ID для оплаты: {order_id}")

        # Находим заказ
        conn = sqlite3.connect('shop.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT product_title, amount FROM orders WHERE order_id = ?
        ''', (order_id,))

        order = cursor.fetchone()

        if not order:
            bot.answer_callback_query(call.id, "❌ Заказ не найден")
            return

        product_title, amount = order
        print(f"DEBUG: Найден заказ: {product_title}, {amount} руб.")

        # Создаем платеж
        payment_data = {
            'order_id': order_id,
            'amount': amount,
            'description': f"Оплата: {product_title}"
        }

        payment_result = PaymentSystem.create_payment(payment_data, payment_method)

        if payment_result['success']:
            payment_url = payment_result['payment_url']

            # Формируем сообщение в зависимости от метода оплаты
            if payment_method == 'cryptobot':
                if payment_result.get('test_mode'):
                    payment_info = (
                        f"✅ <b>Тестовый платеж CryptoBot создан</b>\n\n"
                        f"📦 Товар: {product_title}\n"
                        f"💰 Сумма: ~{amount} руб. (в USDT)\n"
                        f"₿ Способ: {method_name}\n"
                        f"🆔 Заказ: <code>{order_id}</code>\n"
                        f"⚠️ <i>Тестовый режим (Testnet)</i>\n\n"
                        f"👇 Нажмите кнопку для оплаты:"
                    )
                else:
                    asset = payment_result.get('asset', 'USDT')
                    crypto_amount = payment_result.get('amount', '?')
                    payment_info = (
                        f"✅ <b>Платеж CryptoBot создан</b>\n\n"
                        f"📦 Товар: {product_title}\n"
                        f"💰 Сумма: {crypto_amount} {asset} (~{amount} руб.)\n"
                        f"₿ Способ: {method_name}\n"
                        f"🆔 Заказ: <code>{order_id}</code>\n"
                        f"🕒 Счет действителен: 1 час\n\n"
                        f"👇 Нажмите кнопку для оплаты:"
                    )
            else:
                payment_info = (
                    f"✅ <b>Платеж создан</b>\n\n"
                    f"📦 Товар: {product_title}\n"
                    f"💰 Сумма: {amount} руб.\n"
                    f"💳 Способ: {method_name}\n"
                    f"🆔 Заказ: <code>{order_id}</code>\n\n"
                    f"👇 Нажмите кнопку для оплаты:"
                )

            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    "💳 Перейти к оплате",
                    url=payment_url
                )
            )

            # Для CryptoBot добавляем дополнительную информацию
            if payment_method == 'cryptobot':
                markup.add(
                    types.InlineKeyboardButton(
                        "ℹ️ Инструкция по оплате",
                        callback_data=f"cryptobot_help_{order_id}"
                    )
                )

            markup.add(
                types.InlineKeyboardButton(
                    "🔄 Проверить статус",
                    callback_data=f"check_status_{order_id}"
                ),
                types.InlineKeyboardButton(
                    "✅ Тестовая оплата",
                    callback_data=f"test_pay_{order_id}"
                )
            )

            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=payment_info,
                parse_mode='HTML',
                reply_markup=markup
            )
        else:
            error_msg = payment_result.get('error', 'Неизвестная ошибка')
            bot.answer_callback_query(
                call.id,
                f"❌ Ошибка: {error_msg}",
                show_alert=True
            )

        bot.answer_callback_query(call.id)

    except Exception as e:
        print(f"Ошибка в handle_payment_method: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка обработки платежа")


# ========== ИНСТРУКЦИЯ ПО CRYPTOBOT ==========

@bot.callback_query_handler(func=lambda call: call.data.startswith('cryptobot_help_'))
def show_cryptobot_help(call):
    """Показать инструкцию по оплате через CryptoBot"""
    order_id = call.data.replace('cryptobot_help_', '')

    help_text = (
        "📖 <b>Инструкция по оплате через CryptoBot</b>\n\n"
        "1. <b>Нажмите кнопку 'Перейти к оплате'</b>\n"
        "   Откроется диалог с @CryptoBot или @CryptoTestnetBot\n\n"
        "2. <b>Выберите криптовалюту</b>\n"
        "   • USDT (рекомендуется)\n"
        "   • BTC (Bitcoin)\n"
        "   • ETH (Ethereum)\n"
        "   • TON (Toncoin)\n\n"
        "3. <b>Оплатите счет</b>\n"
        "   • Отправьте указанную сумму\n"
        "   • Дождитесь подтверждения сети (1-15 минут)\n\n"
        "4. <b>Проверьте статус оплаты</b>\n"
        "   • Нажмите 'Проверить статус' в этом сообщении\n"
        "   • Или подождите автоматического уведомления\n\n"
        "⚠️ <b>Важно:</b>\n"
        "• Счет действителен 1 час\n"
        "• Комиссия сети оплачивается отправителем\n"
        "• При проблемах пишите в поддержку\n\n"
        f"🆔 Ваш заказ: <code>{order_id}</code>"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            "🔙 Назад к оплате",
            callback_data=f"back_to_payment_{order_id}"
        )
    )

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=help_text,
        parse_mode='HTML',
        reply_markup=markup
    )


# ========== ВОЗВРАТ К ОПЛАТЕ ==========

@bot.callback_query_handler(func=lambda call: call.data.startswith('back_to_payment_'))
def back_to_payment(call):
    """Вернуться к оплате"""
    order_id = call.data.replace('back_to_payment_', '')

    # Находим заказ
    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT product_title, amount, payment_method FROM orders WHERE order_id = ?
    ''', (order_id,))

    order = cursor.fetchone()
    conn.close()

    if order:
        product_title, amount, payment_method = order

        if payment_method == 'cryptobot':
            # Получаем дополнительную информацию о CryptoBot платеже
            cursor.execute('''
                SELECT cryptobot_asset, cryptobot_amount FROM orders WHERE order_id = ?
            ''', (order_id,))

            crypto_info = cursor.fetchone()
            if crypto_info:
                asset, crypto_amount = crypto_info
                payment_info = (
                    f"✅ <b>Платеж CryptoBot создан</b>\n\n"
                    f"📦 Товар: {product_title}\n"
                    f"💰 Сумма: {crypto_amount} {asset} (~{amount} руб.)\n"
                    f"₿ Способ: Криптовалютой (CryptoBot)\n"
                    f"🆔 Заказ: <code>{order_id}</code>\n\n"
                    f"👇 Нажмите кнопку для оплаты:"
                )
            else:
                payment_info = (
                    f"✅ <b>Платеж CryptoBot создан</b>\n\n"
                    f"📦 Товар: {product_title}\n"
                    f"💰 Сумма: ~{amount} руб. (в USDT)\n"
                    f"₿ Способ: Криптовалютой (CryptoBot)\n"
                    f"🆔 Заказ: <code>{order_id}</code>\n\n"
                    f"👇 Нажмите кнопку для оплаты:"
                )
        else:
            payment_info = (
                f"✅ <b>Платеж создан</b>\n\n"
                f"📦 Товар: {product_title}\n"
                f"💰 Сумма: {amount} руб.\n"
                f"💳 Способ: {'Банковской картой' if payment_method == 'card' else 'ЮMoney'}\n"
                f"🆔 Заказ: <code>{order_id}</code>\n\n"
                f"👇 Нажмите кнопку для оплаты:"
            )

        # Получаем ссылку на оплату
        cursor.execute('SELECT payment_url FROM orders WHERE order_id = ?', (order_id,))
        payment_url = cursor.fetchone()[0]

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                "💳 Перейти к оплате",
                url=payment_url
            )
        )

        if payment_method == 'cryptobot':
            markup.add(
                types.InlineKeyboardButton(
                    "ℹ️ Инструкция по оплате",
                    callback_data=f"cryptobot_help_{order_id}"
                )
            )

        markup.add(
            types.InlineKeyboardButton(
                "🔄 Проверить статус",
                callback_data=f"check_status_{order_id}"
            ),
            types.InlineKeyboardButton(
                "✅ Тестовая оплата",
                callback_data=f"test_pay_{order_id}"
            )
        )

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=payment_info,
            parse_mode='HTML',
            reply_markup=markup
        )


# ========== ПРОВЕРКА СТАТУСА ОПЛАТЫ (С CRYPTOBOT) ==========

@bot.callback_query_handler(func=lambda call: call.data.startswith('check_status_'))
def check_payment_status(call):
    """Проверка статуса оплаты"""
    order_id = call.data.replace('check_status_', '')

    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute('SELECT status, payment_method, cryptobot_invoice_id FROM orders WHERE order_id = ?', (order_id,))

    result = cursor.fetchone()

    if result:
        status, payment_method, invoice_id = result

        # Если это CryptoBot и статус waiting_payment, проверяем через API
        if payment_method == 'cryptobot' and status == 'waiting_payment' and invoice_id:
            crypto_status = PaymentSystem.check_cryptobot_payment(invoice_id)
            if crypto_status['success'] and crypto_status['status'] == 'paid':
                # Обновляем статус в БД
                cursor.execute('UPDATE orders SET status = "paid" WHERE order_id = ?', (order_id,))
                conn.commit()
                status = 'paid'

        if status == 'paid':
            bot.answer_callback_query(
                call.id,
                "✅ Заказ оплачен! Товар отправлен.",
                show_alert=True
            )
        elif status == 'waiting_payment':
            bot.answer_callback_query(
                call.id,
                "⏳ Ожидается оплата...",
                show_alert=True
            )
        else:
            bot.answer_callback_query(
                call.id,
                f"📊 Статус: {status}",
                show_alert=True
            )
    else:
        bot.answer_callback_query(call.id, "❌ Заказ не найден")

    conn.close()


# ========== ОСТАЛЬНЫЕ ФУНКЦИИ ==========

# [Добавьте остальные функции из предыдущего кода:
# - checkout_order, payment_menu, pay_order_command
# - test_payment, clear_cart, handle_navigation_buttons
# - support_command, about_command, promotions
# - test_payment_command, rules_command, back_button
# - fix_database_command]

# ========== КОМАНДА ДЛЯ НАСТРОЙКИ CRYPTOBOT ==========

@bot.message_handler(commands=['setup_cryptobot'])
def setup_cryptobot_command(message):
    """Команда для настройки CryptoBot"""
    setup_text = (
        "⚙️ <b>Настройка CryptoBot</b>\n\n"
        "Для приема криптоплатежей:\n\n"
        "1. <b>Получите API токен:</b>\n"
        "   • Перейдите в @CryptoBot\n"
        "   • Нажмите 'Начать' → 'Настройки'\n"
        "   • Выберите 'Для разработчиков'\n"
        "   • Создайте новый API ключ\n\n"
        "2. <b>Для тестирования:</b>\n"
        "   • Используйте @CryptoTestnetBot\n"
        "   • Получите тестовый токен\n"
        "   • Используйте тестовую криптовалюту\n\n"
        "3. <b>Добавьте токен в код:</b>\n"
        "   • Откройте файл бота\n"
        "   • Найдите строку: <code>CRYPTOBOT_API_TOKEN = \"\"</code>\n"
        "   • Вставьте ваш токен между кавычками\n\n"
        "4. <b>Переключите режим:</b>\n"
        "   • <code>CRYPTOBOT_TEST_MODE = False</code> для продакшна\n\n"
        "✅ <b>Текущий статус:</b>\n"
        f"• Токен: {'Установлен' if CRYPTOBOT_API_TOKEN else 'Не установлен'}\n"
        f"• Режим: {'ТЕСТОВЫЙ' if CRYPTOBOT_TEST_MODE else 'ПРОДАКШН'}\n"
        f"• URL API: {CRYPTOBOT_API_URL}"
    )

    bot.send_message(
        message.chat.id,
        setup_text,
        parse_mode='HTML'
    )


# ========== КОМАНДА ДЛЯ ТЕСТА CRYPTOBOT ==========

@bot.message_handler(commands=['test_cryptobot'])
def test_cryptobot_command(message):
    """Тестирование CryptoBot"""
    if not CRYPTOBOT_API_TOKEN:
        bot.send_message(
            message.chat.id,
            "❌ CryptoBot не настроен. Используйте /setup_cryptobot"
        )
        return

    # Создаем тестовый заказ
    order_id = f"CRYPTO_TEST_{message.from_user.id}_{int(time.time())}"

    conn = sqlite3.connect('shop.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (order_id, user_id, product_title, amount, status)
        VALUES (?, ?, ?, ?, 'pending')
    ''', (order_id, message.from_user.id, "Тестовый товар (CryptoBot)", 100))
    conn.commit()
    conn.close()

    test_text = (
        f"🧪 <b>Тест CryptoBot</b>\n\n"
        f"Создан тестовый заказ:\n"
        f"🆔 <code>{order_id}</code>\n"
        f"💰 Сумма: 100 руб.\n\n"
        f"Используйте /pay_order_{order_id} для оплаты через CryptoBot"
    )

    bot.send_message(
        message.chat.id,
        test_text,
        parse_mode='HTML'
    )


# ========== ЗАПУСК БОТА ==========

if __name__ == "__main__":
    print("=" * 60)
    print("🏪 KRISTALL SHOP Bot запущен!")
    print("₿ Добавлена оплата через CryptoBot (криптовалюта)")
    print("=" * 60)
    print("🔧 Настройки CryptoBot:")
    print(f"   • Токен: {'Установлен' if CRYPTOBOT_API_TOKEN else 'НЕ установлен'}")
    print(f"   • Режим: {'ТЕСТОВЫЙ' if CRYPTOBOT_TEST_MODE else 'ПРОДАКШН'}")
    print(f"   • API URL: {CRYPTOBOT_API_URL}")
    print("=" * 60)
    print("📱 Команды для CryptoBot:")
    print("   • /setup_cryptobot - инструкция по настройке")
    print("   • /test_cryptobot - тестирование оплаты")
    print("=" * 60)
    print("⚡ Ожидаю сообщений...")

    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        traceback.print_exc()