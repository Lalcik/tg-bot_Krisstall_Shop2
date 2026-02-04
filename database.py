"""
Простая база данных (для демо)
В реальном проекте используйте SQLite или PostgreSQL
"""

import json
import os


class Database:
    def __init__(self, filename='data.json'):
        self.filename = filename
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'users': {},
            'orders': {},
            'courses': {},
            'payments': {}
        }

    def save_data(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_user(self, user_id, user_data):
        self.data['users'][str(user_id)] = user_data
        self.save_data()

    def add_order(self, order_id, order_data):
        self.data['orders'][order_id] = order_data
        self.save_data()

    def get_user_courses(self, user_id):
        user_id = str(user_id)
        return self.data['users'].get(user_id, {}).get('courses', [])