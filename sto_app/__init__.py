"""
СТО Management System - Модуль управления автосервисом.

Основные компоненты:
- STOApplication: Главное приложение
- MainWindow: Основное окно с табами
- Модели данных: Order, OrderService, OrderPart
- Views: Представления для заказов, клиентов, справочников
- Dialogs: Диалоговые окна для ввода данных
- Utils: Утилиты (резервное копирование и др.)
"""

from .app import STOApplication
from .main_window import MainWindow

# Модели данных
from .models_sto import (
    Order, 
    OrderService, 
    OrderPart, 
    ServiceCatalog, 
    CarBrand, 
    OrderStatus
)

# Views (представления)
try:
    from .views import (
        OrdersView,
        NewOrderView, 
        CatalogsView,
        SettingsView
    )
except ImportError:
    # Если views недоступны, устанавливаем None
    OrdersView = None
    NewOrderView = None
    CatalogsView = None
    SettingsView = None

# Dialogs (диалоги)
try:
    from .dialogs import (
        ClientDialog,
        CarDialog,
        ServiceDialog,
        PartDialog,
        OrderDetailsDialog,
        AboutDialog,
        SearchDialog,
        CalendarDialog,
        ReportsDialog
    )
except ImportError:
    # Базовые диалоги должны быть доступны
    from .dialogs import (
        ClientDialog,
        CarDialog, 
        ServiceDialog,
        PartDialog,
        OrderDetailsDialog
    )
    # Дополнительные диалоги могут отсутствовать
    AboutDialog = None
    SearchDialog = None
    CalendarDialog = None
    ReportsDialog = None

# Utils (утилиты)
try:
    from .utils import BackupManager
except ImportError:
    BackupManager = None

# Стили
try:
    from .styles import themes
except ImportError:
    themes = None

__version__ = '3.0'
__author__ = 'СТО Management Team'

__all__ = [
    # Основные компоненты
    'STOApplication',
    'MainWindow',
    
    # Модели
    'Order',
    'OrderService', 
    'OrderPart',
    'ServiceCatalog',
    'CarBrand',
    'OrderStatus',
    
    # Views
    'OrdersView',
    'NewOrderView',
    'CatalogsView', 
    'SettingsView',
    
    # Dialogs
    'ClientDialog',
    'CarDialog',
    'ServiceDialog',
    'PartDialog', 
    'OrderDetailsDialog',
    'AboutDialog',
    'SearchDialog',
    'CalendarDialog',
    'ReportsDialog',
    
    # Utils
    'BackupManager',
    
    # Стили
    'themes',
    
    # Метаданные
    '__version__',
    '__author__'
]