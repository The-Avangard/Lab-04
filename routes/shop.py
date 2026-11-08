"""Каталог, кошик і оформлення замовлення AVANGARD SHOP."""

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

import models


shop_bp = Blueprint('shop', __name__)
MAX_QUANTITY = 99


def get_cart():
    """Повертає кошик у форматі {id_товару: кількість}."""
    cart = {}

    for product_id, quantity in session.get('cart', {}).items():
        try:
            product_id = int(product_id)
            quantity = int(quantity)
        except (TypeError, ValueError):
            continue

        if product_id > 0 and quantity > 0:
            cart[product_id] = min(quantity, MAX_QUANTITY)

    return cart


def save_cart(cart):
    """Зберігає у сесії id товарів і кількість, без цін."""
    session['cart'] = {
        str(product_id): quantity
        for product_id, quantity in cart.items()
    }


def build_cart_lines():
    """Формує рядки кошика з актуальними товарами з бази."""
    cart = get_cart()
    products = models.get_products_by_ids(cart.keys())
    lines = []

    for product in products:
        if product['is_available']:
            quantity = cart[product['id']]
            lines.append({
                'product': product,
                'quantity': quantity,
                'subtotal': round(product['price'] * quantity, 2),
            })

    # Прибираємо товари, які вже недоступні або відсутні в базі.
    if len(lines) != len(cart):
        save_cart({
            line['product']['id']: line['quantity']
            for line in lines
        })

    return lines


@shop_bp.route('/catalog')
def catalog():
    """Показує каталог із пошуком і фільтром за категорією."""
    query = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()

    products = models.get_products(query=query, category=category)
    categories = sorted({
        product['category']
        for product in models.get_products()
    })

    return render_template(
        'catalog.html',
        products=products,
        categories=categories,
        search_query=query,
        selected_category=category,
    )


@shop_bp.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = models.get_product(product_id)

    if product is None or not product['is_available']:
        flash('Цей товар зараз недоступний.', 'error')
        return redirect(url_for('shop.catalog'))

    cart = get_cart()
    cart[product_id] = min(
        cart.get(product_id, 0) + 1,
        MAX_QUANTITY,
    )
    save_cart(cart)

    flash(f'«{product["name"]}» додано до кошика.', 'success')
    return redirect(url_for('shop.catalog'))


@shop_bp.route('/cart')
def cart():
    lines = build_cart_lines()
    total = round(sum(line['subtotal'] for line in lines), 2)

    return render_template(
        'cart.html',
        lines=lines,
        total=total,
        max_quantity=MAX_QUANTITY,
    )


@shop_bp.route('/cart/update/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    cart = get_cart()

    if product_id in cart:
        try:
            quantity = int(request.form.get('quantity', '1'))
        except ValueError:
            quantity = 1

        if quantity <= 0:
            cart.pop(product_id)
        else:
            cart[product_id] = min(quantity, MAX_QUANTITY)

        save_cart(cart)

    return redirect(url_for('shop.cart'))


@shop_bp.route('/cart/remove/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart = get_cart()
    cart.pop(product_id, None)
    save_cart(cart)

    return redirect(url_for('shop.cart'))


@shop_bp.route('/checkout', methods=['POST'])
def checkout():
    customer_name = request.form.get('customer_name', '').strip()
    email = request.form.get('email', '').strip()
    address = request.form.get('address', '').strip()
    promo_code = request.form.get('promo_code', '').strip()

    if not customer_name or '@' not in email or not address:
        flash(
            'Вкажіть ім’я, коректну електронну пошту та адресу доставки.',
            'error',
        )
        return redirect(url_for('shop.cart'))

    try:
        order_id = models.create_order(
            customer_name=customer_name,
            email=email,
            address=address,
            cart=get_cart(),
            promo_code=promo_code,
        )
    except ValueError as error:
        flash(str(error), 'error')
        return redirect(url_for('shop.cart'))

    save_cart({})
    flash(f'Замовлення №{order_id} оформлено. Дякуємо!', 'success')
    return redirect(url_for('shop.catalog'))
