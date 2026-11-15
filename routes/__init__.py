"""Blueprints for the AVANGARD SHOP Flask application."""

from .admin import admin_bp
from .feedback import feedback_bp
from .shop import shop_bp

__all__ = ('admin_bp', 'feedback_bp', 'shop_bp')
