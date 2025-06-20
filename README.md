# СТО Management System v3.0

Модульная система управления автосервисом на PySide6 + SQLAlchemy

## 📁 Структура проекта

```
sto-management-system/
├── shared_models/
│   ├── __init__.py
│   ├── base.py              # Базовые классы моделей
│   └── common_models.py     # Общие модели (Client, Car, Employee)
├── config/
│   ├── __init__.py
│   └── database.py          # Конфигурация БД
├── sto_app/
│   ├── __init__.py
│   ├── app.py              # Главный класс приложения
│   ├── main_window.py      # Главное окно
│   ├── models_sto.py       # Модели СТО
│   ├── styles/
│   │   ├── __init__.py
│   │   └── themes.py       # Темы оформления
│   ├── views/              # (В РАЗРАБОТКЕ)
│   └── dialogs/            # (В РАЗРАБОТКЕ)
├── sales_app/              # (ПЛАНИРУЕТСЯ)
├── main.py                 # Точка входа
├── init_db.py             # Инициализация БД
├── requirements.txt       # Зависимости
├── project_structure.md   # Детальная структура
└── README.md             # Этот файл
```

## 🚀 Быстрый старт

```bash
# Клонирование
git clone https://github.com/yourusername/sto-management-system.git
cd sto-management-system

# Установка зависимостей
pip install -r requirements.txt

# Инициализация БД
python init_db.py

# Запуск
python main.py
```

## 🛠 Технологии

- **Python 3.10+**
- **PySide6** - современный UI
- **SQLAlchemy 2.0** - ORM
- **SQLite** - база данных (с возможностью миграции на MySQL)
- **ReportLab** - генерация PDF
- **Pandas** - работа с данными

## 📊 Модели данных

### Общие модели (shared_models)
- `Client` - клиенты
- `Car` - автомобили  
- `Employee` - сотрудники

### Модели СТО (sto_app)
- `Order` - заказы (наряд-заказ)
- `OrderService` - услуги в заказе
- `OrderPart` - запчасти в заказе
- `ServiceCatalog` - каталог услуг

## 🎯 Текущий статус

✅ **Готово:**
- Архитектура проекта
- Модели данных
- Главное окно
- Система тем

🚧 **В разработке:**
- Views (представления)
- Диалоги
- Система печати

📅 **Планируется:**
- Модуль продаж (sales_app)
- Отчеты и аналитика
- REST API

## 🤝 Для разработчиков

См. [project_structure.md](project_structure.md) для детальной информации о структуре проекта.

### Примеры использования в промптах для AI:

```
Проект: https://github.com/username/sto-management-system
Задача: Создать OrdersView согласно структуре
```

## 📝 Лицензия

Proprietary - Все права защищены#   s t o - m a n a g e m e n t - s y s t e m  
 #   s t o - m a n a g e m e n t - s y s t e m  
 #   s t o - m a n a g e m e n t - s y s t e m  
 