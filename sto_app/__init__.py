# sto_app/__init__.py
"""
СТО Management System
Модульная система управления автосервисом
"""

__version__ = '3.0.0'
__author__ = 'AutoService Team'
__email__ = 'support@autoservice.ua'

# Публичный API модуля
from .app import STOApplication
from .main_window import MainWindow

__all__ = ['STOApplication', 'MainWindow']