"""SQLite data layer for AVANGARD SHOP.

Connections are scoped to one Flask application context and closed by
``close_db`` registered in app.py. All user-provided SQL values are passed
as parameters rather than interpolated into query strings.
"""

import sqlite3
from datetime import datetime

from flask import current_app, g


ORDER_STATUSES = ("Нове", "В обробці", "Відправлено", "Доставлено", "Скасовано")

SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    email      TEXT NOT NULL UNIQUE,
    phone      TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id  INTEGER,
    name       TEXT NOT NULL,
    email      TEXT NOT NULL,
    message    TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS products (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT NOT NULL,
    category       TEXT NOT NULL,
    description    TEXT NOT NULL DEFAULT '',
    specifications TEXT NOT NULL DEFAULT '',
    price          REAL NOT NULL CHECK (price >= 0),
    image_url      TEXT NOT NULL DEFAULT '',
    is_available   INTEGER NOT NULL DEFAULT 1 CHECK (is_available IN (0, 1)),
    created_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id   INTEGER,
    customer_name TEXT NOT NULL,
    email       TEXT NOT NULL,
    address     TEXT NOT NULL,
    total_price REAL NOT NULL CHECK (total_price >= 0),
    status      TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE SET NULL
);

-- Junction table for the many-to-many relationship between orders and products.
-- unit_price preserves the price that applied when the order was placed.
CREATE TABLE IF NOT EXISTS order_items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id   INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity   INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products (category);
CREATE INDEX IF NOT EXISTS idx_orders_client ON orders (client_id);
CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback (created_at);
"""


INITIAL_PRODUCTS = (
    (
        'Ноутбук',
        'Apple MacBook Pro 14″ M5 16/1TB (MDE54UA/A), Silver',
        'Ноутбук для роботи, навчання та творчих завдань.',
        'Apple M5 · 16 ГБ пам’яті · SSD 1 ТБ · Liquid Retina XDR 14,2″',
        120999,
        'https://content2.rozetka.com.ua/goods/images/big/609305696.jpg',
    ),
    (
        'Ноутбук',
        'Acer Predator Helios Neo 16S AI (NH.U0KAA.001)',
        'Потужний ігровий ноутбук із дисплеєм OLED.',
        'Intel Core Ultra 9 275HX · 32 ГБ RAM · SSD 1 ТБ · RTX 5070 Ti 12 ГБ · OLED 16″, 240 Гц',
        133949,
        'https://content1.rozetka.com.ua/goods/images/big/559712768.jpg',
    ),
    (
        'Ноутбук',
        'Lenovo LOQ 17IRX10',
        'Ігровий ноутбук із великим екраном 17,3 дюйма.',
        'Intel Core i7-14700HX · 32 ГБ RAM · SSD 1 ТБ · RTX 5070 · 17,3″ FHD IPS, 165 Гц · Windows 11',
        101800,
        'https://content2.rozetka.com.ua/goods/images/big/649077820.jpg',
    ),
    (
        'Ноутбук',
        'LG Gram Book 17 (17Z90TL-H.AUB7U1), Black',
        'Легкий ноутбук із великим сенсорним екраном для роботи.',
        'Intel Core Ultra 7 258V · 32 ГБ RAM · SSD 2 ТБ · 17″ WQXGA IPS touchscreen · Intel Arc',
        127911,
        'https://content.rozetka.com.ua/goods/images/big/686416713.jpg',
    ),
    (
        'Ноутбук',
        'Dream Machines RG5060-17 (RG5060-17UA32)',
        'Ігровий ноутбук із дисплеєм QHD 165 Гц.',
        'Intel Core i7-14700HX · 32 ГБ DDR5 · SSD 1 ТБ · RTX 5060 8 ГБ, 115 Вт · 17,3″ QHD, 165 Гц',
        105999,
        'https://content1.rozetka.com.ua/goods/images/big/669216832.jpg',
    ),
    (
        'Ноутбук',
        'ASUS ROG Zephyrus G14 (GA403UM-G14.R9HX4)',
        'Компактний ігровий ноутбук із OLED-екраном.',
        'AMD Ryzen 9 270 · 16 ГБ LPDDR5X · SSD 1 ТБ · RTX 5060 8 ГБ · 14″ OLED 2880×1800, 120 Гц · Windows 11 Home',
        108876,
        'https://content.rozetka.com.ua/goods/images/big/654743053.jpg',
    ),
    (
        'Стаціонарний ПК',
        'ARTLINE Gaming PBG (PBGv01)',
        'Ігровий настільний комп’ютер у чорному корпусі.',
        'AMD Ryzen 5 7500F · 32 ГБ DDR5-6000 · SSD 1 ТБ · RTX 5060 Ti 8 ГБ · Wi-Fi 6E · без ОС',
        82999,
        'https://content1.rozetka.com.ua/goods/images/big/662975888.jpg',
    ),
    (
        'Стаціонарний ПК',
        'Ігровий ПК Lumen',
        'Комп’ютер для ігор і стримінгу.',
        'AMD Ryzen 7 7700 · 32 ГБ DDR5 · SSD 512 ГБ · RTX 5070 12 ГБ · плата B650 · блок живлення 750 Вт · Windows 11',
        102699,
        'https://content1.rozetka.com.ua/goods/images/big/680623171.png',
    ),
    (
        'Стаціонарний ПК',
        'ARTLINE Gaming PBGWHITE (PBGWHITEv07)',
        'Потужна ігрова система у білому корпусі.',
        'AMD Ryzen 7 7700 · 32 ГБ DDR5-6000 · SSD 1 ТБ · RTX 5070 12 ГБ · білий корпус · без ОС',
        114300,
        'https://content1.rozetka.com.ua/goods/images/big/666775842.webp',
    ),
)


def now():
    """Return a readable local timestamp for records in the demo database."""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def get_db():
    """Return one SQLite connection for the current Flask request/context."""
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(exception=None):
    """Close the request-scoped database connection, if one was opened."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Create tables and add the catalog's initial products once."""
    db = get_db()
    db.executescript(SCHEMA)
    product_count = db.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    if product_count == 0:
        with db:
            db.executemany(
                '''INSERT INTO products
                   (category, name, description, specifications, price, image_url, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                [(*product, now()) for product in INITIAL_PRODUCTS],
            )


# ------------------------------------------------------------------- clients

def get_clients():
    return get_db().execute('SELECT * FROM clients ORDER BY id DESC').fetchall()


def get_client(client_id):
    return get_db().execute('SELECT * FROM clients WHERE id = ?', (client_id,)).fetchone()


def add_client(name, email, phone=''):
    db = get_db()
    with db:
        cursor = db.execute(
            'INSERT INTO clients (name, email, phone, created_at) VALUES (?, ?, ?, ?)',
            (name.strip(), email.strip().lower(), phone.strip(), now()),
        )
    return cursor.lastrowid


def update_client(client_id, name, email, phone=''):
    db = get_db()
    with db:
        db.execute(
            'UPDATE clients SET name = ?, email = ?, phone = ? WHERE id = ?',
            (name.strip(), email.strip().lower(), phone.strip(), client_id),
        )


def delete_client(client_id):
    db = get_db()
    with db:
        db.execute('DELETE FROM clients WHERE id = ?', (client_id,))


# ------------------------------------------------------------------ feedback

def add_feedback(name, email, message, client_id=None):
    db = get_db()
    with db:
        cursor = db.execute(
            '''INSERT INTO feedback (client_id, name, email, message, created_at)
               VALUES (?, ?, ?, ?, ?)''',
            (client_id, name.strip(), email.strip().lower(), message.strip(), now()),
        )
    return cursor.lastrowid


def get_feedback():
    return get_db().execute('SELECT * FROM feedback ORDER BY id DESC').fetchall()


def get_feedback_item(feedback_id):
    return get_db().execute('SELECT * FROM feedback WHERE id = ?', (feedback_id,)).fetchone()


def update_feedback(feedback_id, name, email, message):
    db = get_db()
    with db:
        db.execute(
            'UPDATE feedback SET name = ?, email = ?, message = ? WHERE id = ?',
            (name.strip(), email.strip().lower(), message.strip(), feedback_id),
        )


def delete_feedback(feedback_id):
    db = get_db()
    with db:
        db.execute('DELETE FROM feedback WHERE id = ?', (feedback_id,))


# ------------------------------------------------------------------- products

def get_products(query='', category=''):
    """List products, optionally filtering by text and category."""
    sql = 'SELECT * FROM products WHERE is_available = 1'
    params = []
    if query.strip():
        pattern = f"%{query.strip()}%"
        sql += ' AND (name LIKE ? OR description LIKE ? OR specifications LIKE ?)'
        params.extend((pattern, pattern, pattern))
    if category.strip():
        sql += ' AND category = ?'
        params.append(category.strip())
    sql += ' ORDER BY id'
    return get_db().execute(sql, params).fetchall()


def get_product(product_id):
    return get_db().execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()


def get_products_by_ids(ids):
    ids = list(ids)
    if not ids:
        return []
    placeholders = ','.join('?' for _ in ids)
    return get_db().execute(
        f'SELECT * FROM products WHERE id IN ({placeholders})', ids
    ).fetchall()


def add_product(category, name, description, specifications, price, image_url):
    db = get_db()
    with db:
        cursor = db.execute(
            '''INSERT INTO products
               (category, name, description, specifications, price, image_url, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (category, name, description, specifications, price, image_url, now()),
        )
    return cursor.lastrowid


def update_product(product_id, category, name, description, specifications, price, image_url):
    db = get_db()
    with db:
        db.execute(
            '''UPDATE products
               SET category = ?, name = ?, description = ?, specifications = ?,
                   price = ?, image_url = ?
               WHERE id = ?''',
            (category, name, description, specifications, price, image_url, product_id),
        )


def delete_product(product_id):
    """Delete an unused product; referenced products are protected by SQLite."""
    db = get_db()
    with db:
        db.execute('DELETE FROM products WHERE id = ?', (product_id,))


# -------------------------------------------------------------------- orders

def create_order(customer_name, email, address, cart, client_id=None):
    """Create an order and its items atomically from ``{product_id: quantity}``."""
    normalized_cart = {}
    for raw_product_id, raw_quantity in cart.items():
        try:
            product_id = int(raw_product_id)
            quantity = int(raw_quantity)
        except (TypeError, ValueError) as error:
            raise ValueError('Некоректний товар або кількість у кошику') from error
        if product_id <= 0 or quantity <= 0:
            raise ValueError('Кількість товару має бути більшою за нуль')
        normalized_cart[product_id] = quantity

    products = get_products_by_ids(normalized_cart.keys())
    if not products:
        raise ValueError('Кошик порожній')
    if len(products) != len(normalized_cart):
        raise ValueError('Один або кілька товарів більше недоступні')

    total = round(sum(product['price'] * normalized_cart[product['id']] for product in products), 2)
    db = get_db()
    with db:
        cursor = db.execute(
            '''INSERT INTO orders
               (client_id, customer_name, email, address, total_price, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (client_id, customer_name.strip(), email.strip().lower(), address.strip(),
             total, ORDER_STATUSES[0], now()),
        )
        order_id = cursor.lastrowid
        db.executemany(
            '''INSERT INTO order_items (order_id, product_id, quantity, unit_price)
               VALUES (?, ?, ?, ?)''',
            [(order_id, product['id'], normalized_cart[product['id']], product['price'])
             for product in products],
        )
    return order_id


def get_orders():
    return get_db().execute('SELECT * FROM orders ORDER BY id DESC').fetchall()


def get_order(order_id):
    return get_db().execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()


def get_order_details(order_id):
    db = get_db()
    order = db.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    items = db.execute(
        '''SELECT p.name, oi.quantity, oi.unit_price,
                  (oi.quantity * oi.unit_price) AS subtotal
           FROM order_items AS oi
           JOIN products AS p ON p.id = oi.product_id
           WHERE oi.order_id = ? ORDER BY oi.id''',
        (order_id,),
    ).fetchall()
    return order, items


def update_order_status(order_id, status):
    if status not in ORDER_STATUSES:
        raise ValueError(f'Невідомий статус замовлення: {status}')
    db = get_db()
    with db:
        db.execute('UPDATE orders SET status = ? WHERE id = ?', (status, order_id))


def delete_order(order_id):
    """The database removes related order_items through ON DELETE CASCADE."""
    db = get_db()
    with db:
        db.execute('DELETE FROM orders WHERE id = ?', (order_id,))