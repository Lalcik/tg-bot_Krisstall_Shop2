"""
database.py - Работа с базой данных
"""

import sqlite3
import time
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path='shop.db'):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        """Получить соединение с БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Инициализация базы данных"""
        conn = self.get_connection()
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

        # Создаем индексы
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_cart_user_id ON cart(user_id)')

        conn.commit()
        conn.close()
        logger.info("База данных инициализирована")

    def get_or_create_user(self, user_id, username, first_name, last_name):
        """Получить или создать пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        if not cursor.fetchone():
            cursor.execute('''
            INSERT INTO users (user_id, username, first_name, last_name) 
            VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name))
            logger.info(f"Создан новый пользователь: {user_id}")

        conn.commit()
        conn.close()
        return user_id

    def add_to_cart(self, user_id, product_id):
        """Добавить товар в корзину"""
        conn = self.get_connection()
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

    def get_cart(self, user_id, products):
        """Получить корзину пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
        SELECT product_id, quantity FROM cart 
        WHERE user_id = ?
        ''', (user_id,))

        items = []
        for row in cursor.fetchall():
            product_id = row['product_id']
            quantity = row['quantity']
            if product_id in products:
                product = products[product_id]
                items.append({
                    'product_id': product_id,
                    'title': product['title'],
                    'price': product['price'],
                    'quantity': quantity
                })

        conn.close()
        return items

    def clear_cart(self, user_id):
        """Очистить корзину"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()

    def create_order(self, user_id, product_id, amount):
        """Создать заказ"""
        order_id = f"ORD{str(int(time.time()))}{user_id}"

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
        INSERT INTO orders (order_id, user_id, product_id, amount) 
        VALUES (?, ?, ?, ?)
        ''', (order_id, user_id, product_id, amount))

        conn.commit()
        conn.close()
        return order_id

    def update_order_status(self, order_id, status, payment_id=None):
        """Обновить статус заказа"""
        conn = self.get_connection()
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

    def create_payment(self, order_id, amount):
        """Создать запись о платеже"""
        payment_id = f"PAY{str(int(time.time()))}"

        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
        INSERT INTO payments (payment_id, order_id, amount) 
        VALUES (?, ?, ?)
        ''', (payment_id, order_id, amount))

        conn.commit()
        conn.close()
        return payment_id

    def update_payment(self, payment_id, status, payment_url=None):
        """Обновить информацию о платеже"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
        UPDATE payments 
        SET status = ?, payment_url = ? 
        WHERE payment_id = ?
        ''', (status, payment_url, payment_id))

        conn.commit()
        conn.close()

    def get_user_orders(self, user_id, products):
        """Получить заказы пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
        SELECT order_id, product_id, amount, status, created_at 
        FROM orders 
        WHERE user_id = ?
        ORDER BY created_at DESC
        ''', (user_id,))

        orders = []
        for row in cursor.fetchall():
            product_id = row['product_id']
            if product_id in products:
                orders.append({
                    'order_id': row['order_id'],
                    'title': products[product_id]['title'],
                    'amount': row['amount'],
                    'status': row['status'],
                    'created_at': row['created_at']
                })

        conn.close()
        return orders

# Создаем глобальный экземпляр базы данных
db = Database()