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

## 🚀 РЕАЛЬНЫЙ СТАТУС ПРОЕКТА (уточненный)

### ✅ АРХИТЕКТУРА ГОТОВА (100%):
- **🏗️ STOApplication + MainWindow**: Полностью функциональны
- **📊 Модели данных**: Order, OrderService, OrderPart - готовы
- **🎨 Система тем**: Светлая/темная темы работают
- **🔧 Структура файлов**: Views и dialogs созданы

### ❓ ВОЗМОЖНЫЕ ЗАГЛУШКИ В СТО МОДУЛЕ:
**Файлы созданы, но содержимое может быть неполным:**
- **📱 Views**: orders_view.py, new_order_view.py, catalogs_view.py, settings_view.py
- **🔧 Dialogs**: client_dialog.py, car_dialog.py, service_dialog.py, part_dialog.py
- **🛠️ Функциональность**: CRUD операции, валидация, интеграция

### 🔄 ФАЙЛЫ ИСПРАВЛЕНИЙ УКАЗЫВАЮТ НА:
- **Проблемы интеграции** между views и dialogs
- **Недоработки в new_order_view** 
- **Проблемы с orders_view_integration**

### 📋 ЗАДАЧИ НА ЗАВТРА:

#### **ШАГ 1: Диагностика заглушек**
1. Проверить **содержимое views** - работают ли CRUD операции?
2. Протестировать **dialogs** - открываются ли и сохраняют данные?
3. Найти **заглушки типа** `pass` или `# TODO`

#### **ШАГ 2: Анализ исправлений**
1. Изучить **new_order_view_fixes.py** - что именно исправлялось
2. Понять **orders_view_integration.py** - проблемы интеграции
3. Применить исправления к основному коду

#### **ШАГ 3: Завершение функциональности**
1. **Реализовать заглушки** в views/dialogs
2. **Настроить интеграцию** между компонентами  
3. **Добавить валидацию** и обработку ошибок
4. **Протестировать полный цикл** создания заказа

### 📈 ПЛАНИРУЕТСЯ (Roadmap):
- **🛒 Sales модуль**: POS система и складской учет (файлы созданы, но содержат заглушки)
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

## 📝 ПОЛНАЯ ИНСТРУКЦИЯ ДЛЯ ЗАВТРАШНЕЙ РАБОТЫ

### 🔗 **Все файлы проекта (спарсенные ссылки):**

#### 📋 **Основные файлы:**
- **main.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/main.py
- **init_db.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/init_db.py
- **requirements.txt**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/requirements.txt
- **README.md**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/README.md

#### 📚 **Документация и инструкции:**
- **project_structure.md**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/project_structure.md
- **continuation_instructions_v5.md**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/continuation_instructions_v5.md
- **prompt_for_rebuilding_sto_app.txt**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/prompt_for_rebuilding_sto_app.txt

#### ⚙️ **Конфигурация:**
- **config/__init__.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/config/__init__.py
- **config/database.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/config/database.py

#### 📊 **Общие модели:**
- **shared_models/__init__.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/shared_models/__init__.py
- **shared_models/base.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/shared_models/base.py
- **shared_models/common_models.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/shared_models/common_models.py

#### 🔧 **СТО Модуль (основной):**
- **sto_app/__init__.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/sto_app/__init__.py
- **sto_app/app.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/sto_app/app.py
- **sto_app/main_window.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/sto_app/main_window.py
- **sto_app/models_sto.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/sto_app/models_sto.py

#### 📱 **СТО Views (интерфейсы):**
- **sto_app/views/__init__.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/sto_app/views/__init__.py
- **sto_app/views/orders_view.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/sto_app/views/orders_view.py
- **sto_app/views/new_order_view.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/sto_app/views/new_order_view.py
- **sto_app/views/catalogs_view.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/sto_app/views/catalogs_view.py
- **sto_app/views/settings_view.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/sto_app/views/settings_view.py

#### 🔧 **СТО Dialogs (диалоги):**
- **sto_app/dialogs/__init__.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/sto_app/dialogs/__init__.py
- **sto_app/dialogs/client_dialog.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/sto_app/dialogs/client_dialog.py
- **sto_app/dialogs/car_dialog.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/sto_app/dialogs/car_dialog.py
- **sto_app/dialogs/order_details_dialog.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/sto_app/dialogs/order_details_dialog.py
- **sto_app/dialogs/part_dialog.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/sto_app/dialogs/part_dialog.py
- **sto_app/dialogs/service_dialog.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/sto_app/dialogs/service_dialog.py

#### 🎨 **СТО Стили:**
- **sto_app/styles/__init__.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/sto_app/styles/__init__.py
- **sto_app/styles/themes.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/sto_app/styles/themes.py

#### 🛒 **Sales Модуль (заглушки/планируется):**
- **sales_app/app.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/sales_app/app.py
- **sales_app/main_window.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/sales_app/main_window.py
- **sales_app/models_sales.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/sales_app/models_sales.py
- **sales_app/views/pos_view.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/sales_app/views/pos_view.py
- **sales_app/views/inventory_view.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/sales_app/views/inventory_view.py
- **sales_app/views/reports_view.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/sales_app/views/reports_view.py

#### 🔧 **Исправления и интеграции:**
- **new_order_view_fixes.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/Исправления и интеграции/new_order_view_fixes.py
- **orders_view_integration.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/Исправления и интеграции/orders_view_integration.py

#### 🤖 **Утилиты:**
- **generate_raw_links.py**: https://raw.githubusercontent.com/Renovatio305/sto-management-system/main/парсер ссылок на гитхаб/generate_raw_links.py

### 🎯 **План работы на завтра:**

#### **ШАГ 1: Анализ текущего состояния**
1. Загрузить **continuation_instructions_v5.md** - там могут быть актуальные задачи
2. Изучить **prompt_for_rebuilding_sto_app.txt** - понять что нужно пересобрать
3. Проверить файлы **исправлений** - что уже исправлялось
4. Проверить **Sales модуль** - определить уровень готовности (вероятно заглушки)

#### **ШАГ 2: Тестирование основного функционала**
1. Проверить **main.py** - запуск приложения
2. Протестировать **views** - работают ли интерфейсы
3. Проверить **dialogs** - открываются ли диалоги

#### **ШАГ 3: Выявление проблем**
1. Найти **недостающие** компоненты
2. Проверить **интеграцию** между модулями
3. Выявить **ошибки** в коде

#### **ШАГ 4: Приоритетные задачи**
1. **BackupManager** (упоминается в main_window.py)
2. **SearchDialog, CalendarDialog, ReportsDialog** (условные импорты)
3. **Валидация данных** и обработка ошибок
4. **Интеграция** views с dialogs

### 🚀 **Готовность к работе:**
- ✅ **Все файлы доступны** через raw ссылки
- ✅ **Архитектура изучена** и документирована
- ✅ **Стиль кодирования** понятен
- ✅ **Технологический стек** изучен

**Можно сразу приступать к анализу и разработке!** 💪

### 📋 **Быстрый старт завтра:**
```bash
# 1. Загрузить ключевые файлы:
web_fetch("https://raw.githubusercontent.com/.../continuation_instructions_v5.md")
web_fetch("https://raw.githubusercontent.com/.../main.py") 
web_fetch("https://raw.githubusercontent.com/.../orders_view.py")

# 2. Проанализировать текущие задачи
# 3. Начать тестирование и доработку
```
