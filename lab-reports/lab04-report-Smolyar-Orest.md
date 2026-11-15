# Лабораторна робота №4 — звіт

## Загальна інформація

- **ПІБ:** Смоляр Орест Миколайович
- **Група:** ІПЗ-22
- **Роль у команді:** QA
- **GitHub-акаунт:** [Mphizard](https://github.com/Mphizard)
- **Склад команди:**
  - Шульга Андрій Сергійович (Teamlead) — `shulgaaa294-stack`
  - Грицюк Назар Олександрович (Developer) — `SkyDreammer-exe`
  - Смоляр Орест Миколайович (QA) — `Mphizard`
- **Тема проєкту:** інтернет-магазин комп’ютерної техніки AVANGARD SHOP на Flask і SQLite
- **Репозиторій:** <https://github.com/The-Avangard/Lab-04>

## Особистий внесок у командну роботу

- створив шаблони головної адмін-панелі, керування товарами та деталей замовлення;
- реалізував і виправляв шаблони форми зворотного зв’язку та її оброблення;
- підготував стилі для вкладки зворотного зв’язку;
- перевіряв сторінки та допомагав виправляти помилки шаблонів і форм.

### Мої коміти

| Хеш | Дата | Опис |
|---|---|---|
| [`7538622`](https://github.com/The-Avangard/Lab-04/commit/75386229da8bcdf51da1bf905239b1091628d9e0) | 08.11.2026 | Додано форму товару й сторінку керування товарами |
| [`a396ac8`](https://github.com/The-Avangard/Lab-04/commit/a396ac8c2cddfffe41327aee4d052354e0977079) | 08.11.2026 | Виправлено шаблони та форму відгуків |
| [`ee4a4cf`](https://github.com/The-Avangard/Lab-04/commit/ee4a4cfb2d59d706fa1572738e36abcff850cf28) | 15.11.2026 | Оновлено стиль вкладки зворотного зв’язку |

## Реалізована функціональність

Сайт AVANGARD SHOP працює на Flask і SQLite. Користувач може переглядати каталог, додавати товари до кошика, оформлювати замовлення та надсилати відгук. В адмін-панелі є список замовлень і відгуків, деталі замовлення, керування товарами, клієнтами й промокодами. Для замовлення можна змінити статус.

## Схема бази даних

```mermaid
erDiagram
    CLIENTS ||--o{ ORDERS : places
    CLIENTS ||--o{ FEEDBACK : sends
    ORDERS ||--|{ ORDER_ITEMS : contains
    PRODUCTS ||--o{ ORDER_ITEMS : included_in

    CLIENTS {
        int id PK
        string name
        string email UK
        string phone
        string created_at
    }
    FEEDBACK {
        int id PK
        int client_id FK
        string name
        string email
        string message
        string created_at
    }
    PRODUCTS {
        int id PK
        string name
        string category
        string description
        string specifications
        float price
        string image_url
        bool is_available
        string created_at
    }
    ORDERS {
        int id PK
        int client_id FK
        string customer_name
        string email
        string address
        float total_price
        string promo_code
        float discount_amount
        string status
        string created_at
    }
    ORDER_ITEMS {
        int id PK
        int order_id FK
        int product_id FK
        int quantity
        float unit_price
    }
    PROMO_CODES {
        int id PK
        string code UK
        float discount_percent
        bool is_active
        string created_at
    }
```

Таблиці `orders` і `products` з’єднані проміжною таблицею `order_items`. Вона зберігає товар, кількість і ціну на момент оформлення. Таблиця `clients` пов’язана із замовленнями й відгуками. Дані форм перевіряються на сервері, а значення передаються до SQL-запитів як параметри.

## Скріншоти створених сторінок

### Головна сторінка

| Звичайний вигляд | Мобільний вигляд |
|---|---|
| ![Головна сторінка на комп’ютері](screenshots/main-desktop.png) | ![Головна сторінка на телефоні](screenshots/main-mobile.jpg) |

### Каталог

| Звичайний вигляд | Мобільний вигляд |
|---|---|
| ![Каталог на комп’ютері](screenshots/catalog-desktop.png) | ![Каталог на телефоні](screenshots/catalog-mobile.jpg) |

### Категорії

| Звичайний вигляд | Мобільний вигляд |
|---|---|
| ![Категорії на комп’ютері](screenshots/category-desktop.png) | ![Категорії на телефоні](screenshots/category-mobile.jpeg) |

### Про магазин

| Звичайний вигляд | Мобільний вигляд |
|---|---|
| ![Про магазин на комп’ютері](screenshots/about-desktop.png) | ![Про магазин на телефоні](screenshots/about-mobile.jpeg) |

### Зворотний зв’язок

| Звичайний вигляд | Мобільний вигляд |
|---|---|
| ![Форма зворотного зв’язку на комп’ютері](screenshots/contacts-desktop.png) | ![Форма зворотного зв’язку на телефоні](screenshots/contacts-mobile.jpeg) |

### Адмін-панель

| Звичайний вигляд | Мобільний вигляд |
|---|---|
| ![Адмін-панель на комп’ютері](screenshots/admin-desktop.png) | ![Адмін-панель на телефоні](screenshots/admin-mobile.png) |

## Труднощі та їх вирішення

Під час роботи з формами важливо було узгодити HTML-поля, серверну перевірку та назви маршрутів у шаблонах. Перевірили `url_for` і оброблення даних у Flask-маршрутах, виправили помилки шаблонів та додали серверну валідацію полів форми зворотного зв’язку.

## Висновки

Під час лабораторної роботи я створив і перевірив сторінки адмін-панелі, замовлень і зворотного зв’язку. Закріпив навички роботи з Flask-шаблонами, формами та інтеграції користувацького інтерфейсу з маршрутами застосунку.