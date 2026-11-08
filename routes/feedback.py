from flask import Blueprint, jsonify, render_template, request

import models


feedback_bp = Blueprint('feedback', name)


@feedback_bp.route('/contacts', methods=['GET', 'POST'])
def contacts():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()

        # Перевіряємо дані на сервері: браузерну перевірку можна обійти.
        if not name or not message or '@' not in email or len(email) > 254:
            return jsonify({
                'error': 'Заповніть усі поля та вкажіть коректну електронну пошту.'
            }), 400

        models.add_feedback(name, email, message)
        return jsonify({
            'status': 'success',
            'message': 'Дякуємо! Ваше повідомлення надіслано.'
        }), 200

    return render_template('contacts.html')