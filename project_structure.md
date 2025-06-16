# 📁 СТО Management System v3.0 - Финальная структура проекта

## 🗂️ Полная архитектура проекта (актуальная)

```
project/
├── shared_models/          # ✅ Общие модели для всех модулей
│   ├── __init__.py
│   ├── base.py            # Base, TimestampMixin
│   └── common_models.py   # Client, Car, Employee
│
├── sto_app/               # ✅ Основной модуль СТО - ГОТОВ
│   ├── __init__.py
│   ├── app.py            # ✅ STOApplication с splash screen
│   ├── main_window.py    # ✅ MainWindow с табами, меню, тулбар
│   ├── models_sto.py     # ✅ Order, OrderService, OrderPart, ServiceCatalog
│   │
│   ├── views/            # ✅ Представления - основные вкладки ГОТОВЫ
│   │   ├── __init__.py
│   │   ├── orders_view.py      # ✅ Таблица заказов
│   │   ├── new_order_view.py   # ✅ Форма нового заказа
│   │   ├── catalogs_view.py    # ✅ Справочники услуг/запчастей
│   │   └── settings_view.py    # ✅ Настройки приложения
│   │
│   ├── dialogs/          # ✅ Диалоговые окна ГОТОВЫ
│   │   ├── __init__.py
│   │   ├── client_dialog.py    # ✅ Создание/редактирование клиента
│   │   ├── car_dialog.py       # ✅ Добавление автомобиля
│   │   ├── order_details_dialog.py # ✅ Детали заказа
│   │   ├── part_dialog.py      # ✅ Добавление/редактирование запчасти
│   │   ├── service_dialog.py   # ✅ Добавление/редактирование услуги
│   │   │
│   │   └── [УСЛОВНЫЕ ИМПОРТЫ - возможно нужно создать]:
│   │       ├── about_dialog.py     # ✅ О программе (готов)
│   │       ├── search_dialog.py    # ❓ Поиск по всем данным
│   │       ├── calendar_dialog.py  # ❓ Календарь записей
│   │       ├── reports_dialog.py   # ❓ Генерация отчетов
│   │       └── import_export_dialog.py # ❓ Импорт/экспорт данных
│   │
│   ├── utils/            # ❓ Утилиты (частично используются в коде)
│   │   ├── __init__.py
│   │   └── backup.py     # ❓ BackupManager (упоминается в main_window.py)
│   │
│   └── styles/           # ✅ Стили ГОТОВЫ
│       ├── __init__.py
│       └── themes.py     # ✅ LIGHT_THEME, DARK_THEME, apply_theme()
│
├── sales_app/            # 📅 Модуль продаж (ПЛАНИРУЕТСЯ)
│   ├── __init__.py
│   ├── app.py           # SalesApplication  
│   ├── main_window.py   # Окно продаж
│   ├── models_sales.py  # Product, Stock, Sale, Invoice
│   ├── views/
│   │   ├── pos_view.py         # Точка продаж
│   │   ├── inventory_view.py   # Склад
│   │   └── reports_view.py     # Отчеты продаж
│   └── dialogs/
│       ├── product_dialog.py   # Товары
│       └── sale_dialog.py      # Продажи
│
├── config/               # ✅ Конфигурация
│   ├── __init__.py
│   ├── database.py       # ✅ engine, SessionLocal, init_database()
│   └── settings.py       # Конфигурация приложения
│
├── resources/            # ✅ Ресурсы приложения (используются в коде)
│   ├── icons/           # app.png, orders.png, new_order.png, etc.
│   ├── images/          # splash.png для заставки
│   └── translations/    # sto_uk_UA.qm, sto_en_US.qm
│
├── main.py              # ✅ Точка входа в приложение
├── init_db.py          # ✅ Инициализация БД
├── requirements.txt    # ✅ Зависимости Python
├── project_structure.md # ✅ Документация структуры
└── README.md           # ✅ Описание проекта
```

## 🏗️ Реальная архитектура (основано на коде)

### 🎯 STOApplication - Главное приложение
```python
# sto_app/app.py
class STOApplication(QApplication):
    def __init__(self, argv):
        # Настройка приложения
        self.setApplicationName('СТО Management System')
        self.setOrganizationName('AutoService')
        
    def run(self):
        # 1. Splash screen с сообщениями
        # 2. Инициализация БД
        # 3. Загрузка переводов (украинский по умолчанию)
        # 4. Применение темы
        # 5. Создание MainWindow
        # 6. Подключение сигналов тем
```

### 🪟 MainWindow - Табированный интерфейс
```python
# sto_app/main_window.py  
class MainWindow(QMainWindow):
    # Сигналы
    theme_changed = Signal(str)
    language_changed = Signal(str)
    
    def __init__(self):
        self.db_session = SessionLocal()  # БД сессия
        self.settings = QSettings('STOApp', 'MainWindow')  # Настройки
        
        # UI компоненты:
        self.tab_widget = QTabWidget()  # Основные табы
        # - orders_view (Заказы)
        # - new_order_view (Новый заказ) 
        # - catalogs_view (Справочники)
        # - settings_view (Настройки)
        
        # Автосохранение каждые 5 минут
        self.autosave_timer.start(300000)
        
    # Полное меню: Файл, Правка, Вид, Инструменты, Справка
    # Тулбар с основными действиями
    # Статус-бар с временем и пользователем
```

### 📊 Модели данных - СТО бизнес-логика
```python
# sto_app/models_sto.py
class OrderStatus(enum.Enum):
    DRAFT = "Чернетка"          # Черновик
    IN_WORK = "В роботі"        # В работе
    WAITING_PAYMENT = "Очікує оплату"  # Ожидает оплаты
    COMPLETED = "Завершено"     # Завершен
    CANCELLED = "Скасовано"     # Отменен

class Order(Base, TimestampMixin):
    # Основные поля: номер, клиент, машина, даты, статус
    # Финансы: общая_сумма, предоплата, доплата
    # Связи: услуги, запчасти, сотрудники
    
    @property
    def balance_due(self):
        """Остаток к оплате"""
        return self.total_amount - self.prepayment - self.additional_payment

class OrderService(Base):
    # Услуги в заказе с НДС
    def calculate_vat(self, vat_rate=0.2):
        self.price_with_vat = self.price * (1 + vat_rate)

class OrderPart(Base):  
    # Запчасти с количеством и суммой
    def calculate_total(self):
        self.total = self.price * self.quantity

class ServiceCatalog(Base, TimestampMixin):
    # Каталог услуг с синонимами для поиска
    synonyms = Column(Text)  # Для поиска похожих услуг
```

### 🎨 Система тем - VS Code стиль
```python
# sto_app/styles/themes.py
LIGHT_THEME = """
    # Светлая тема с синими акцентами (#2196F3)
    # Специальные кнопки: accent="true", danger="true"
"""

DARK_THEME = """
    # Темная тема в стиле VS Code (#1e1e1e, #007ACC)
    # Профессиональная цветовая гамма
"""

def apply_theme(app, theme_name='light'):
    # Применение CSS стилей к приложению
```

## 📋 Views - Основные вкладки (готовы)

### 🔧 Структура Views
```python
# Все views наследуются от QWidget и интегрируются как табы
class OrdersView(QWidget):
    status_message = Signal(str)  # Для статус-бара
    
class NewOrderView(QWidget):
    order_saved = Signal()        # Уведомление о сохранении
    status_message = Signal(str)
    
    def has_unsaved_changes(self) -> bool:
        """Проверка несохраненных изменений"""
    
    def save_draft(self):
        """Автосохранение черновика"""
```

## 🔧 Dialogs - Диалоговые окна (готовы)

### ✅ Готовые диалоги:
- **client_dialog.py** - Управление клиентами
- **car_dialog.py** - Добавление автомобилей
- **order_details_dialog.py** - Подробности заказа
- **part_dialog.py** - Управление запчастями  
- **service_dialog.py** - Управление услугами

### ❓ Возможно нужно создать (условные импорты):
```python
# В main_window.py есть условные импорты:
def show_search(self):
    from .dialogs.search_dialog import SearchDialog
    
def show_calendar(self):
    from .dialogs.calendar_dialog import CalendarDialog
    
def show_reports(self):
    from .dialogs.reports_dialog import ReportsDialog
```

## 🔗 Система связей и сигналов

### 📡 Основные сигналы
```python
# MainWindow
theme_changed = Signal(str)      # Смена темы
language_changed = Signal(str)   # Смена языка

# Views  
status_message = Signal(str)     # Сообщения для статус-бара
order_saved = Signal()          # Сохранение заказа

# Connections в main_window.py
self.orders_view.status_message.connect(self.show_status_message)
self.new_order_view.order_saved.connect(self.on_order_saved)
self.settings_view.theme_changed.connect(self.change_theme)
```

### 🔄 Навигация между табами
```python
def new_order(self):
    """Переключение на таб нового заказа"""
    self.tab_widget.setCurrentWidget(self.new_order_view)
    self.new_order_view.clear_form()
    
def on_order_saved(self):
    """После сохранения заказа"""
    self.orders_view.refresh_orders()
    self.tab_widget.setCurrentWidget(self.orders_view)
```

## 🎯 Ключевые особенности архитектуры

### 💾 Управление данными
```python
# Каждый компонент получает db_session из MainWindow
def __init__(self, db_session):
    self.db_session = db_session

# Закрытие сессии при выходе
def closeEvent(self, event):
    self.db_session.close()
```

### ⚙️ Настройки приложения
```python
# QSettings для сохранения состояния
self.settings = QSettings('STOApp', 'MainWindow')

# Сохранение геометрии и темы
self.settings.setValue('theme', theme_name)
self.settings.setValue('geometry', self.saveGeometry())
```

### 🚀 Автосохранение
```python
# Каждые 5 минут
self.autosave_timer.start(300000)

def autosave(self):
    if self.tab_widget.currentWidget() == self.new_order_view:
        self.new_order_view.save_draft()
```

### 🌍 Интернационализация
```python
# Поддержка украинского языка
def load_translations(self):
    locale = QLocale.system().name()
    if self.translator.load(f"translations/sto_{locale}.qm"):
        self.installTranslator(self.translator)
    elif self.translator.load(f"translations/sto_uk_UA.qm"):
        self.installTranslator(self.translator)
```

## 🎨 UI/UX Standards

### 🎭 Цветовая схема
```css
/* Светлая тема */
Primary: #2196F3    /* Синий - основные кнопки */
Success: #4CAF50    /* Зеленый - accent="true" */
Danger:  #f44336    /* Красный - danger="true" */
Background: #f5f5f5 /* Светло-серый фон */

/* Темная тема */
Primary: #007ACC    /* Синий VS Code */
Background: #1e1e1e /* Темный фон */
Surface: #2d2d30    /* Поверхности */
Text: #cccccc       /* Основной текст */
```

### 📐 Размеры и отступы
```python
# Главное окно
self.setGeometry(100, 100, 1400, 900)  

# Иконки тулбара
toolbar.setIconSize(Qt.SizeHint(32, 32))

# Кнопки с отступами
padding: 8px 16px;
border-radius: 4px;
```

### 🔤 Ресурсы и иконки
```
resources/
├── icons/
│   ├── app.png          # Иконка приложения
│   ├── orders.png       # Заказы
│   ├── new_order.png    # Новый заказ
│   ├── catalog.png      # Справочники
│   ├── settings.png     # Настройки
│   ├── search.png       # Поиск
│   ├── calendar.png     # Календарь
│   ├── reports.png      # Отчеты
│   ├── print.png        # Печать
│   └── pdf.png          # PDF
├── images/
│   └── splash.png       # Заставка
└── translations/
    ├── sto_uk_UA.qm     # Украинский (основной)
    └── sto_en_US.qm     # Английский
```

## 🚀 Текущий статус проекта

### ✅ ПОЛНОСТЬЮ ГОТОВО (100%):
- **🏗️ Архитектура**: STOApplication + MainWindow с табами
- **📊 Модели**: Order, OrderService, OrderPart, ServiceCatalog с бизнес-логикой
- **🎨 Темы**: Светлая и темная темы в стиле VS Code  
- **📱 Views**: orders_view, new_order_view, catalogs_view, settings_view
- **🔧 Dialogs**: client_dialog, car_dialog, order_details_dialog, part_dialog, service_dialog
- **🎛️ UI**: Полное меню, тулбар, статус-бар с временем
- **💾 Автосохранение**: Каждые 5 минут + проверка изменений
- **⚙️ Настройки**: QSettings с сохранением геометрии и темы
- **🚀 Splash screen**: Красивая загрузка с прогрессом
- **🌍 i18n**: Поддержка украинского языка

### ❓ ВОЗМОЖНО НУЖНО ДОРАБОТАТЬ:
**Диалоги (условные импорты из main_window.py):**
- [ ] **SearchDialog** - поиск по всем данным  
- [ ] **CalendarDialog** - календарь записей
- [ ] **ReportsDialog** - генерация отчетов
- [ ] **ImportExportDialog** - импорт/экспорт данных

**Утилиты:**
- [ ] **BackupManager** - резервное копирование (упоминается в коде)
- [ ] **Validators** - валидация данных форм
- [ ] **Export utilities** - печать и экспорт в PDF

**Функциональность:**
- [ ] **Интеграция** между views и dialogs
- [ ] **Обновление данных** после изменений
- [ ] **Обработка ошибок** и валидация

### 📈 ПЛАНИРУЕТСЯ (Roadmap):
- **🛒 Sales модуль**: POS система и складской учет
- **🌐 REST API**: Для мобильного приложения  
- **📊 Расширенная аналитика**: Графики и отчеты
- **📱 Мобильное приложение**: Для мастеров СТО

## 🔧 Технический стек

### 🐍 Python Зависимости
```txt
PySide6          # Современный Qt UI фреймворк
SQLAlchemy 2.0   # ORM для работы с БД
ReportLab        # Генерация PDF отчетов
Pandas           # Анализ данных
```

### 🗄️ База данных
```python
# SQLite по умолчанию, с возможностью миграции на MySQL
# Все модели наследуются от Base + TimestampMixin
# Автоматическое создание таблиц при первом запуске
```

### 🎯 Архитектурные паттерны
- **📋 MVV (Model-View-ViewModel)** для UI компонентов
- **🔗 Signal-Slot** для связи между компонентами  
- **💉 Dependency Injection** через конструкторы
- **🗂️ Repository Pattern** для работы с данными
- **⚙️ Settings Pattern** для конфигурации

---

## 📝 Инструкция для завтрашней работы

### 🔗 Ссылки на ключевые файлы:
1. **app.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/refs/heads/main/sto_app/app.py
2. **main_window.py**: https://github.com/Renovatio305/sto-management-system/raw/refs/heads/main/sto_app/main_window.py  
3. **models_sto.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/refs/heads/main/sto_app/models_sto.py
4. **themes.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/refs/heads/main/sto_app/styles/themes.py

### 📂 GitHub структура:
- **Dialogs**: https://github.com/Renovatio305/sto-management-system/tree/main/sto_app/dialogs
- **Views**: https://github.com/Renovatio305/sto-management-system/tree/main/sto_app/views
- **Основной репозиторий**: https://github.com/Renovatio305/sto-management-system

### 🎯 Приоритеты для работы:
1. **Проверить функциональность** готовых компонентов
2. **Создать недостающие утилиты** (BackupManager, validators)  
3. **Доработать условные диалоги** (SearchDialog, ReportsDialog)
4. **Настроить интеграцию** между компонентами
5. **Добавить обработку ошибок** и валидацию

*Документация обновлена на основе реального кода. Проект находится в высокой стадии готовности! 🚀*
