# 📁 Структура проекта СТО Management System v3.0

## 🗂️ Архитектура проекта

```
project/
├── shared_models/          # Общие модели для всех модулей
│   ├── __init__.py
│   ├── base.py            # Base, TimestampMixin
│   └── common_models.py   # Client, Car, Employee
│
├── sto_app/               # Модуль СТО
│   ├── __init__.py
│   ├── app.py            # STOApplication
│   ├── main_window.py    # MainWindow(QMainWindow)
│   ├── models_sto.py     # Order, OrderService, OrderPart, ServiceCatalog
│   │
│   ├── views/            # Представления (НУЖНО СОЗДАТЬ)
│   │   ├── orders_view.py      # Таблица заказов
│   │   ├── new_order_view.py   # Форма нового заказа
│   │   ├── catalogs_view.py    # Справочники
│   │   └── settings_view.py    # Настройки
│   │
│   ├── dialogs/          # Диалоговые окна (НУЖНО СОЗДАТЬ)
│   │   ├── service_dialog.py   # Добавление услуги
│   │   ├── part_dialog.py      # Добавление запчасти
│   │   └── client_dialog.py    # Клиент
│   │
│   └── styles/
│       └── themes.py     # LIGHT_THEME, DARK_THEME
│
├── sales_app/            # Модуль продаж (БУДУЩИЙ)
│   ├── __init__.py
│   ├── app.py           # SalesApplication
│   ├── main_window.py   # Окно продаж
│   ├── models_sales.py  # Product, Stock, Sale, Invoice
│   └── views/
│       ├── pos_view.py         # Точка продаж
│       ├── inventory_view.py   # Склад
│       └── reports_view.py     # Отчеты продаж
│
├── config/
│   └── database.py       # engine, SessionLocal, init_database()
│
├── main.py              # Точка входа
├── init_db.py          # Инициализация БД
└── requirements.txt    # Зависимости
```

## 🔗 Основные классы и импорты

### Модели (SQLAlchemy)
```python
# Базовые (используются в обоих модулях)
from shared_models.base import Base, TimestampMixin
from shared_models.common_models import Client, Car, Employee

# СТО
from sto_app.models_sto import (
    Order, OrderStatus, OrderService, OrderPart, 
    ServiceCatalog, CarBrand
)

# Продажи (будущие)
from sales_app.models_sales import (
    Product, Stock, Sale, SaleItem, Invoice
)
```

### UI (PySide6)
```python
from sto_app.main_window import MainWindow
from sto_app.app import STOApplication
```

### База данных
```python
from config.database import SessionLocal, get_db, init_database
```

## 📊 Связи между модулями

```
ОБЩИЕ МОДЕЛИ:
Client (1) ← → (N) Car
Client (1) ← → (N) Order (СТО)
Client (1) ← → (N) Sale (Продажи)

СТО МОДУЛЬ:
Car (1) ← → (N) Order
Order (1) ← → (N) OrderService
Order (1) ← → (N) OrderPart
Employee → Order (manager, responsible_person)

ПРОДАЖИ МОДУЛЬ:
Product (1) ← → (N) Stock
Product (1) ← → (N) SaleItem
Sale (1) ← → (N) SaleItem
Employee → Sale (seller)

МЕЖМОДУЛЬНЫЕ СВЯЗИ:
OrderPart.article ← → Product.article (по артикулу)
```

## 🎯 Статусы заказа (Enum)
- DRAFT = "Чернетка"
- IN_WORK = "В роботі"  
- WAITING_PAYMENT = "Очікує оплату"
- COMPLETED = "Завершено"
- CANCELLED = "Скасовано"

## 🔑 Ключевые методы

### Order
- `balance_due` - остаток к оплате
- `calculate_total()` - пересчет суммы

### MainWindow
- `new_order()` - новый заказ
- `show_reports()` - отчеты
- `change_theme(name)` - смена темы

## 📝 Сигналы Qt
- `MainWindow.theme_changed` → изменение темы
- `OrdersView.order_selected` → выбор заказа
- `NewOrderView.order_saved` → заказ сохранен