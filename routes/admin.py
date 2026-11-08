import math
import sqlite3

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

import models


admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

PRODUCT_CATEGORIES = ('Ноутбук', 'Стаціонарний ПК')


@admin_bp.route('/')
def admin():
    """Головна сторінка адмін-панелі: замовлення та відгуки."""
    return render_template(
        'admin.html',
        orders=models.get_orders(),
        feedback=models.get_feedback(),
    )


# ------------------------------------------------------------------ замовлення


@admin_bp.route('/orders/<int:order_id>')
def order_details(order_id):
    order, items = models.get_order_details(order_id)
    if order is None:
        abort(404)

    return render_template(
        'order_details.html',
        order=order,
        items=items,
        statuses=models.ORDER_STATUSES,
    )


@admin_bp.route('/orders/<int:order_id>/status', methods=['POST'])
def update_order_status(order_id):
    order = models.get_order(order_id)
    if order is None:
        abort(404)

    status = request.form.get('status', '')
    try:
        models.update_order_status(order_id, status)
    except ValueError:
        flash('Невідомий статус замовлення.', 'error')
    else:
        flash(f'Статус замовлення №{order_id} оновлено.', 'success')

    return redirect(url_for('admin.order_details', order_id=order_id))


@admin_bp.route('/orders/<int:order_id>/delete', methods=['POST'])
def delete_order(order_id):
    order = models.get_order(order_id)
    if order is None:
        abort(404)

    models.delete_order(order_id)
    flash(f'Замовлення №{order_id} видалено.', 'success')
    return redirect(url_for('admin.admin'))


# --------------------------------------------------------------------- відгуки


@admin_bp.route('/feedback/<int:feedback_id>/edit', methods=['GET', 'POST'])
def edit_feedback(feedback_id):
    feedback = models.get_feedback_item(feedback_id)
    if feedback is None:
        abort(404)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()

        if not name or '@' not in email or not message:
            flash('Заповніть усі поля та вкажіть коректну електронну пошту.', 'error')
            return render_template(
                'feedback_form.html',
                feedback=request.form.to_dict(),
            )

        models.update_feedback(feedback_id, name, email, message)
        flash('Відгук оновлено.', 'success')
        return redirect(url_for('admin.admin'))

    return render_template('feedback_form.html', feedback=feedback)


@admin_bp.route('/feedback/<int:feedback_id>/delete', methods=['POST'])
def delete_feedback(feedback_id):
    feedback = models.get_feedback_item(feedback_id)
    if feedback is None:
        abort(404)

    models.delete_feedback(feedback_id)
    flash('Відгук видалено.', 'success')
    return redirect(url_for('admin.admin'))


# ---------------------------------------------------------------------- товари


def read_product_form():
    """Перевіряє дані товару й повертає словник для models.add/update_product."""
    category = request.form.get('category', '').strip()
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    specifications = request.form.get('specifications', '').strip()
    image_url = request.form.get('image_url', '').strip()

    try:
        price = float(request.form.get('price', '').replace(',', '.'))
    except ValueError as error:
        raise ValueError('Ціна має бути числом.') from error

    if category not in PRODUCT_CATEGORIES:
        raise ValueError('Оберіть категорію товару.')
    if not name:
        raise ValueError('Вкажіть назву товару.')
    if not math.isfinite(price) or price < 0:
        raise ValueError('Ціна має бути невід’ємним числом.')

    return {
        'category': category,
        'name': name,
        'description': description,
        'specifications': specifications,
        'price': price,
        'image_url': image_url,
    }


@admin_bp.route('/products')
def products():
    return render_template(
        'admin_products.html',
        products=models.get_products(),
    )


@admin_bp.route('/products/new', methods=['GET', 'POST'])
def new_product():
    if request.method == 'POST':
        try:
            data = read_product_form()
        except ValueError as error:
            flash(str(error), 'error')
            return render_template(
                'product_form.html',
                product=request.form.to_dict(),
                categories=PRODUCT_CATEGORIES,
                is_new=True,
            )

        models.add_product(**data)
        flash(f'Товар «{data["name"]}» додано.', 'success')
        return redirect(url_for('admin.products'))

    return render_template(
        'product_form.html',
        product={},
        categories=PRODUCT_CATEGORIES,
        is_new=True,
    )


@admin_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
def edit_product(product_id):
    product = models.get_product(product_id)
    if product is None:
        abort(404)

    if request.method == 'POST':
        try:
            data = read_product_form()
        except ValueError as error:
            flash(str(error), 'error')
            return render_template(
                'product_form.html',
                product=request.form.to_dict(),
                categories=PRODUCT_CATEGORIES,
                is_new=False,
            )

        models.update_product(product_id, **data)
        flash(f'Товар «{data["name"]}» оновлено.', 'success')
        return redirect(url_for('admin.products'))

    return render_template(
        'product_form.html',
        product=product,
        categories=PRODUCT_CATEGORIES,
        is_new=False,
    )


@admin_bp.route('/products/<int:product_id>/delete', methods=['POST'])
def delete_product(product_id):
    product = models.get_product(product_id)
    if product is None:
        abort(404)

    try:
        models.delete_product(product_id)
    except sqlite3.IntegrityError:
        flash('Не можна видалити товар, який уже є в замовленні.', 'error')
    else:
        flash('Товар видалено.', 'success')

    return redirect(url_for('admin.products'))


# --------------------------------------------------------------------- клієнти


def read_client_form():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    phone = request.form.get('phone', '').strip()

    if not name:
        raise ValueError('Вкажіть ім’я клієнта.')
    if '@' not in email or len(email) > 254:
        raise ValueError('Вкажіть коректну електронну пошту.')

    return {'name': name, 'email': email, 'phone': phone}


@admin_bp.route('/clients')
def clients():
    return render_template('admin_clients.html', clients=models.get_clients())


@admin_bp.route('/clients/new', methods=['GET', 'POST'])
def new_client():
    if request.method == 'POST':
        try:
            data = read_client_form()
            models.add_client(**data)
        except ValueError as error:
            flash(str(error), 'error')
        except sqlite3.IntegrityError:
            flash('Клієнт із такою електронною поштою вже існує.', 'error')
        else:
            flash(f'Клієнта «{data["name"]}» додано.', 'success')
            return redirect(url_for('admin.clients'))

        return render_template(
            'client_form.html',
            client=request.form.to_dict(),
            is_new=True,
        )

    return render_template('client_form.html', client={}, is_new=True)


@admin_bp.route('/clients/<int:client_id>/edit', methods=['GET', 'POST'])
def edit_client(client_id):
    client = models.get_client(client_id)
    if client is None:
        abort(404)

    if request.method == 'POST':
        try:
            data = read_client_form()
            models.update_client(client_id, **data)
        except ValueError as error:
            flash(str(error), 'error')
        except sqlite3.IntegrityError:
            flash('Інший клієнт уже використовує цю електронну пошту.', 'error')
        else:
            flash('Дані клієнта оновлено.', 'success')
            return redirect(url_for('admin.clients'))

        return render_template(
            'client_form.html',
            client=request.form.to_dict(),
            is_new=False,
        )

    return render_template('client_form.html', client=client, is_new=False)


@admin_bp.route('/clients/<int:client_id>/delete', methods=['POST'])
def delete_client(client_id):
    client = models.get_client(client_id)
    if client is None:
        abort(404)

    models.delete_client(client_id)
    flash('Клієнта видалено.', 'success')
    return redirect(url_for('admin.clients'))


# ------------------------------------------------------------------- промокоди


def read_promo_form():
    code = request.form.get('code', '').strip()
    is_active = request.form.get('is_active') == 'on'

    try:
        discount_percent = float(
            request.form.get('discount_percent', '').replace(',', '.')
        )
    except ValueError as error:
        raise ValueError('Розмір знижки має бути числом.') from error

    if not code:
        raise ValueError('Вкажіть код промокоду.')
    if not math.isfinite(discount_percent) or not 0 < discount_percent <= 100:
        raise ValueError('Знижка має бути більшою за 0 і не перевищувати 100%.')

    return {
        'code': code,
        'discount_percent': discount_percent,
        'is_active': is_active,
    }


@admin_bp.route('/promos')
def promos():
    return render_template(
        'admin_promos.html',
        promo_codes=models.get_promo_codes(),
    )


@admin_bp.route('/promos/new', methods=['GET', 'POST'])
def new_promo():
    if request.method == 'POST':
        try:
            data = read_promo_form()
            models.add_promo_code(**data)
        except ValueError as error:
            flash(str(error), 'error')
        except sqlite3.IntegrityError:
            flash('Промокод із таким значенням уже існує.', 'error')
        else:
            flash(f'Промокод «{data["code"]}» додано.', 'success')
            return redirect(url_for('admin.promos'))

        return render_template(
            'promo_form.html',
            promo=request.form.to_dict(),
            is_new=True,
        )

    return render_template('promo_form.html', promo={}, is_new=True)


@admin_bp.route('/promos/<int:promo_id>/edit', methods=['GET', 'POST'])
def edit_promo(promo_id):
    promo = next(
        (item for item in models.get_promo_codes() if item['id'] == promo_id),
        None,
    )
    if promo is None:
        abort(404)

    if request.method == 'POST':
        try:
            data = read_promo_form()
            models.update_promo_code(promo_id, **data)
        except ValueError as error:
            flash(str(error), 'error')
        except sqlite3.IntegrityError:
            flash('Інший промокод уже має таке значення.', 'error')
        else:
            flash('Промокод оновлено.', 'success')
            return redirect(url_for('admin.promos'))

        return render_template(
            'promo_form.html',
            promo=request.form.to_dict(),
            is_new=False,
        )

    return render_template('promo_form.html', promo=promo, is_new=False)


@admin_bp.route('/promos/<int:promo_id>/delete', methods=['POST'])
def delete_promo(promo_id):
    promo = next(
        (item for item in models.get_promo_codes() if item['id'] == promo_id),
        None,
    )
    if promo is None:
        abort(404)

    models.delete_promo_code(promo_id)
    flash('Промокод видалено.', 'success')
    return redirect(url_for('admin.promos'))
