"""
Представления (Views) для модуля СТО.
"""

# Основные представления
try:
    from .orders_view import OrdersView
except ImportError:
    OrdersView = None

try:
    from .new_order_view import NewOrderView
except ImportError:
    NewOrderView = None

try:
    from .catalogs_view import CatalogsView
except ImportError:
    CatalogsView = None

try:
    from .settings_view import SettingsView
except ImportError:
    SettingsView = None

__all__ = [
    'OrdersView',
    'NewOrderView', 
    'CatalogsView',
    'SettingsView'
]