"""
Представление для создания нового заказа
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                               QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox, 
                               QFrame, QCheckBox, QCompleter, QProgressBar, QScrollArea,
                               QSplitter, QGroupBox, QSpacerItem, QSizePolicy, QDateEdit,
                               QDoubleSpinBox, QSpinBox, QTableWidget, QTableWidgetItem,
                               QHeaderView, QAbstractItemView, QTabWidget, QMessageBox)
from PySide6.QtCore import Qt, QDate, Signal, QTimer
from PySide6.QtGui import QFont, QPalette, QColor, QPixmap, QPainter
import logging
from datetime import datetime
from decimal import Decimal
from ..models_sto import Client, Car, Service, Part, Order, OrderService, OrderPart
from ..dialogs.client_dialog import ClientDialog
from ..dialogs.car_dialog import CarDialog
from ..dialogs.service_dialog import ServiceDialog
from ..dialogs.part_dialog import PartDialog


class DragHandle(QWidget):
    """Виджет-ручка для изменения размера панелей"""
    
    def __init__(self, orientation=Qt.Horizontal):
        super().__init__()
        self.orientation = orientation
        self.setFixedSize(20, 20)
        self.setStyleSheet("""
            QWidget {
                background-color: #3498db;
                border-radius: 10px;
                border: 2px solid #2980b9;
            }
            QWidget:hover {
                background-color: #5dade2;
                border: 2px solid #3498db;
                cursor: pointer;
            }
        """)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Рисуем стрелки для обозначения возможности изменения размера
        painter.setPen(QColor("#2c3e50"))
        painter.setBrush(QColor("#2c3e50"))
        
        rect = self.rect()
        center_x = rect.width() // 2
        center_y = rect.height() // 2
        
        if self.orientation == Qt.Horizontal:
            # Горизонтальные стрелки ↔
            points1 = [
                (center_x - 4, center_y),
                (center_x - 1, center_y - 3),
                (center_x - 1, center_y + 3)
            ]
            points2 = [
                (center_x + 4, center_y),
                (center_x + 1, center_y - 3),
                (center_x + 1, center_y + 3)
            ]
            painter.drawPolygon(points1)
            painter.drawPolygon(points2)
        else:
            # Вертикальные стрелки ↕
            points1 = [
                (center_x, center_y - 4),
                (center_x - 3, center_y - 1),
                (center_x + 3, center_y - 1)
            ]
            points2 = [
                (center_x, center_y + 4),
                (center_x - 3, center_y + 1),
                (center_x + 3, center_y + 1)
            ]
            painter.drawPolygon(points1)
            painter.drawPolygon(points2)


class ScrollableGroupBox(QGroupBox):
    """Группа с прокруткой"""
    
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2c3e50;
            }
        """)
        
        # Создаем скролл область
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Контейнер для содержимого
        self.content_widget = QWidget()
        self.scroll_area.setWidget(self.content_widget)
        
        # Основной layout для группы
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.scroll_area)
        self.setLayout(main_layout)
    
    def setContentLayout(self, layout):
        """Устанавливает layout для содержимого"""
        self.content_widget.setLayout(layout)


class NewOrderView(QWidget):
    order_created = Signal(dict)
    
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.logger = logging.getLogger(__name__)
        
        # Данные заказа
        self.selected_client = None
        self.selected_car = None
        self.services = []
        self.parts = []
        
        self.setup_ui()
        self.setup_connections()
        self.load_data()
    
    def setup_ui(self):
        """Настройка интерфейса"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Заголовок
        title_label = QLabel("Создание нового заказа")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        main_layout.addWidget(title_label)
        
        # Создаем сплиттер для разделения на панели
        self.main_splitter = QSplitter(Qt.Vertical)
        self.main_splitter.setChildrenCollapsible(False)
        
        # Добавляем визуальную ручку для перетаскивания
        drag_handle = DragHandle(Qt.Horizontal)
        
        # Верхняя панель - информация о клиенте и автомобиле
        self.create_client_car_panel()
        
        # Нижняя панель - услуги и запчасти
        self.create_services_parts_panel()
        
        # Добавляем панели в сплиттер
        self.main_splitter.addWidget(self.client_car_widget)
        self.main_splitter.addWidget(self.services_parts_widget)
        
        # Устанавливаем пропорции (40% верх, 60% низ)
        self.main_splitter.setSizes([400, 600])
        
        # Стилизуем сплиттер
        self.main_splitter.setStyleSheet("""
            QSplitter::handle {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                border: 1px solid #2980b9;
                height: 8px;
                border-radius: 4px;
            }
            QSplitter::handle:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5dade2, stop:1 #3498db);
            }
            QSplitter::handle:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2980b9, stop:1 #21618c);
            }
        """)
        
        main_layout.addWidget(self.main_splitter)
        
        # Панель кнопок управления
        self.create_control_buttons()
        main_layout.addWidget(self.control_buttons_widget)
    
    def create_client_car_panel(self):
        """Создание панели клиента и автомобиля"""
        self.client_car_widget = QWidget()
        layout = QHBoxLayout(self.client_car_widget)
        
        # Группа клиента
        client_group = ScrollableGroupBox("Информация о клиенте")
        client_layout = QGridLayout()
        
        # Поиск клиента
        client_layout.addWidget(QLabel("Поиск клиента:"), 0, 0)
        self.client_search = QLineEdit()
        self.client_search.setPlaceholderText("Введите имя, телефон или email...")
        client_layout.addWidget(self.client_search, 0, 1)
        
        self.new_client_btn = QPushButton("+ Новый клиент")
        self.new_client_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; 
                color: white;
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        client_layout.addWidget(self.new_client_btn, 0, 2)
        
        # Информация о выбранном клиенте
        client_layout.addWidget(QLabel("Имя:"), 1, 0)
        self.client_name_label = QLabel("-")
        self.client_name_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        client_layout.addWidget(self.client_name_label, 1, 1, 1, 2)
        
        client_layout.addWidget(QLabel("Телефон:"), 2, 0)
        self.client_phone_label = QLabel("-")
        client_layout.addWidget(self.client_phone_label, 2, 1, 1, 2)
        
        client_layout.addWidget(QLabel("Email:"), 3, 0)
        self.client_email_label = QLabel("-")
        client_layout.addWidget(self.client_email_label, 3, 1, 1, 2)
        
        client_group.setContentLayout(client_layout)
        layout.addWidget(client_group)
        
        # Группа автомобиля
        car_group = ScrollableGroupBox("Информация об автомобиле")
        car_layout = QGridLayout()
        
        # Выбор автомобиля
        car_layout.addWidget(QLabel("Автомобиль:"), 0, 0)
        self.car_combo = QComboBox()
        self.car_combo.setEnabled(False)
        car_layout.addWidget(self.car_combo, 0, 1)
        
        self.new_car_btn = QPushButton("+ Новый автомобиль")
        self.new_car_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db; 
                color: white;
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #5dade2;
            }
        """)
        self.new_car_btn.setEnabled(False)
        car_layout.addWidget(self.new_car_btn, 0, 2)
        
        # Информация о выбранном автомобиле
        car_layout.addWidget(QLabel("Марка:"), 1, 0)
        self.car_brand_label = QLabel("-")
        self.car_brand_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        car_layout.addWidget(self.car_brand_label, 1, 1)
        
        car_layout.addWidget(QLabel("Модель:"), 1, 2)
        self.car_model_label = QLabel("-")
        self.car_model_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        car_layout.addWidget(self.car_model_label, 1, 3)
        
        car_layout.addWidget(QLabel("Год:"), 2, 0)
        self.car_year_label = QLabel("-")
        car_layout.addWidget(self.car_year_label, 2, 1)
        
        car_layout.addWidget(QLabel("Гос. номер:"), 2, 2)
        self.car_license_label = QLabel("-")
        car_layout.addWidget(self.car_license_label, 2, 3)
        
        car_layout.addWidget(QLabel("VIN:"), 3, 0)
        self.car_vin_label = QLabel("-")
        car_layout.addWidget(self.car_vin_label, 3, 1, 1, 3)
        
        car_layout.addWidget(QLabel("Пробег:"), 4, 0)
        self.car_mileage_input = QSpinBox()
        self.car_mileage_input.setRange(0, 1000000)
        self.car_mileage_input.setSuffix(" км")
        car_layout.addWidget(self.car_mileage_input, 4, 1)
        
        car_group.setContentLayout(car_layout)
        layout.addWidget(car_group)
    
    def create_services_parts_panel(self):
        """Создание панели услуг и запчастей"""
        self.services_parts_widget = QWidget()
        main_layout = QHBoxLayout(self.services_parts_widget)
        
        # Левая часть - услуги и запчасти в табах
        tabs_widget = QWidget()
        tabs_layout = QVBoxLayout(tabs_widget)
        
        # Создаем табы для услуг и запчастей
        self.tabs = QTabWidget()
        
        # Вкладка услуг
        self.create_services_tab()
        
        # Вкладка запчастей
        self.create_parts_tab()
        
        tabs_layout.addWidget(self.tabs)
        main_layout.addWidget(tabs_widget)
        
        # Правая часть - итоги и управление
        self.create_totals_panel()
        main_layout.addWidget(self.totals_widget)
        
        # Пропорции: 70% табы, 30% итоги
        main_layout.setStretchFactor(tabs_widget, 7)
        main_layout.setStretchFactor(self.totals_widget, 3)
    
    def create_services_tab(self):
        """Создание вкладки услуг"""
        services_widget = QWidget()
        services_layout = QVBoxLayout(services_widget)
        
        # Управление услугами
        services_control_layout = QHBoxLayout()
        
        self.add_service_btn = QPushButton("+ Добавить услугу")
        self.add_service_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; 
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        services_control_layout.addWidget(self.add_service_btn)
        
        self.remove_service_btn = QPushButton("- Удалить")
        self.remove_service_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c; 
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        services_control_layout.addWidget(self.remove_service_btn)
        
        services_control_layout.addStretch()
        services_layout.addLayout(services_control_layout)
        
        # Таблица услуг с прокруткой
        services_scroll = QScrollArea()
        services_scroll.setWidgetResizable(True)
        
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(5)
        self.services_table.setHorizontalHeaderLabels([
            "Услуга", "Описание", "Цена", "Мастер", "Статус"
        ])
        
        # Настройка таблицы
        header = self.services_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.resizeSection(0, 200)  # Услуга
        header.resizeSection(1, 250)  # Описание
        header.resizeSection(2, 100)  # Цена
        header.resizeSection(3, 150)  # Мастер
        
        self.services_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.services_table.setAlternatingRowColors(True)
        
        services_scroll.setWidget(self.services_table)
        services_layout.addWidget(services_scroll)
        
        self.tabs.addTab(services_widget, "🔧 Услуги")
    
    def create_parts_tab(self):
        """Создание вкладки запчастей"""
        parts_widget = QWidget()
        parts_layout = QVBoxLayout(parts_widget)
        
        # Управление запчастями
        parts_control_layout = QHBoxLayout()
        
        self.add_part_btn = QPushButton("+ Добавить запчасть")
        self.add_part_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; 
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        parts_control_layout.addWidget(self.add_part_btn)
        
        self.remove_part_btn = QPushButton("- Удалить")
        self.remove_part_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c; 
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        parts_control_layout.addWidget(self.remove_part_btn)
        
        parts_control_layout.addStretch()
        parts_layout.addLayout(parts_control_layout)
        
        # Таблица запчастей с прокруткой
        parts_scroll = QScrollArea()
        parts_scroll.setWidgetResizable(True)
        
        self.parts_table = QTableWidget()
        self.parts_table.setColumnCount(5)
        self.parts_table.setHorizontalHeaderLabels([
            "Запчасть", "Артикул", "Количество", "Цена за ед.", "Итого"
        ])
        
        # Настройка таблицы
        header = self.parts_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.resizeSection(0, 200)  # Запчасть
        header.resizeSection(1, 150)  # Артикул
        header.resizeSection(2, 80)   # Количество
        header.resizeSection(3, 100)  # Цена за ед.
        
        self.parts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.parts_table.setAlternatingRowColors(True)
        
        parts_scroll.setWidget(self.parts_table)
        parts_layout.addWidget(parts_scroll)
        
        self.tabs.addTab(parts_widget, "🔩 Запчасти")
    
    def create_totals_panel(self):
        """Создание панели итогов"""
        self.totals_widget = QWidget()
        totals_layout = QVBoxLayout(self.totals_widget)
        
        # Группа итогов
        totals_group = QGroupBox("💰 Итоги заказа")
        totals_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2c3e50;
            }
        """)
        
        group_layout = QGridLayout(totals_group)
        
        # Стоимость услуг
        group_layout.addWidget(QLabel("Услуги:"), 0, 0)
        self.services_total_label = QLabel("0.00 ₽")
        self.services_total_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        group_layout.addWidget(self.services_total_label, 0, 1)
        
        # Стоимость запчастей
        group_layout.addWidget(QLabel("Запчасти:"), 1, 0)
        self.parts_total_label = QLabel("0.00 ₽")
        self.parts_total_label.setStyleSheet("font-weight: bold; color: #3498db;")
        group_layout.addWidget(self.parts_total_label, 1, 1)
        
        # Скидка
        group_layout.addWidget(QLabel("Скидка:"), 2, 0)
        self.discount_input = QDoubleSpinBox()
        self.discount_input.setRange(0, 100)
        self.discount_input.setSuffix(" %")
        self.discount_input.setStyleSheet("padding: 5px;")
        group_layout.addWidget(self.discount_input, 2, 1)
        
        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("color: #bdc3c7;")
        group_layout.addWidget(line, 3, 0, 1, 2)
        
        # Общая сумма
        total_label = QLabel("ИТОГО:")
        total_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #2c3e50;")
        group_layout.addWidget(total_label, 4, 0)
        
        self.total_label = QLabel("0.00 ₽")
        self.total_label.setStyleSheet("""
            font-weight: bold; 
            font-size: 16px; 
            color: #e74c3c;
            background-color: #fef9e7;
            padding: 5px;
            border: 2px solid #f39c12;
            border-radius: 5px;
        """)
        group_layout.addWidget(self.total_label, 4, 1)
        
        totals_layout.addWidget(totals_group)
        
        # Примечания
        notes_group = QGroupBox("📝 Примечания")
        notes_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #95a5a6;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2c3e50;
            }
        """)
        
        notes_layout = QVBoxLayout(notes_group)
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Дополнительная информация о заказе...")
        self.notes_edit.setMaximumHeight(120)
        self.notes_edit.setStyleSheet("padding: 5px; border: 1px solid #bdc3c7; border-radius: 3px;")
        notes_layout.addWidget(self.notes_edit)
        
        totals_layout.addWidget(notes_group)
        totals_layout.addStretch()
    
    def create_control_buttons(self):
        """Создание панели управляющих кнопок"""
        self.control_buttons_widget = QWidget()
        layout = QHBoxLayout(self.control_buttons_widget)
        layout.setContentsMargins(0, 10, 0, 0)
        
        # Кнопка очистки
        self.clear_btn = QPushButton("🗑️ Очистить форму")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                font-weight: bold;
                padding: 12px 25px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        
        # Кнопка сохранения
        self.save_btn = QPushButton("💾 Сохранить заказ")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 12px 25px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.save_btn.setEnabled(False)
        
        layout.addStretch()
        layout.addWidget(self.clear_btn)
        layout.addWidget(self.save_btn)
    
    def setup_connections(self):
        """Настройка соединений сигналов"""
        # Поиск клиента
        self.client_search.textChanged.connect(self.search_clients)
        self.new_client_btn.clicked.connect(self.create_new_client)
        
        # Автомобиль
        self.car_combo.currentIndexChanged.connect(self.on_car_selected)
        self.new_car_btn.clicked.connect(self.create_new_car)
        
        # Услуги и запчасти
        self.add_service_btn.clicked.connect(self.add_service)
        self.remove_service_btn.clicked.connect(self.remove_service)
        self.add_part_btn.clicked.connect(self.add_part)
        self.remove_part_btn.clicked.connect(self.remove_part)
        
        # Расчеты
        self.discount_input.valueChanged.connect(self.calculate_totals)
        
        # Управляющие кнопки
        self.save_btn.clicked.connect(self.save_order)
        self.clear_btn.clicked.connect(self.clear_form)
    
    def load_data(self):
        """Загрузка данных"""
        try:
            # Настройка автодополнения для поиска клиентов
            clients = self.session.query(Client).all()
            client_names = [f"{c.first_name} {c.last_name} - {c.phone}" for c in clients]
            completer = QCompleter(client_names)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.client_search.setCompleter(completer)
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки данных: {e}")
    
    def search_clients(self, text):
        """Поиск клиентов"""
        if len(text) < 2:
            return
        
        try:
            clients = self.session.query(Client).filter(
                (Client.first_name.ilike(f"%{text}%")) |
                (Client.last_name.ilike(f"%{text}%")) |
                (Client.phone.ilike(f"%{text}%")) |
                (Client.email.ilike(f"%{text}%"))
            ).limit(10).all()
            
            if clients:
                # Автоматически выбираем первого найденного клиента
                self.select_client(clients[0])
                
        except Exception as e:
            self.logger.error(f"Ошибка поиска клиентов: {e}")
    
    def select_client(self, client):
        """Выбор клиента"""
        self.selected_client = client
        
        # Обновляем информацию о клиенте
        self.client_name_label.setText(f"{client.first_name} {client.last_name}")
        self.client_phone_label.setText(client.phone)
        self.client_email_label.setText(client.email or "-")
        
        # Загружаем автомобили клиента
        self.load_client_cars()
        
        # Включаем возможность добавления нового автомобиля
        self.new_car_btn.setEnabled(True)
        
        self.check_form_validity()
    
    def load_client_cars(self):
        """Загрузка автомобилей клиента"""
        if not self.selected_client:
            return
        
        try:
            cars = self.session.query(Car).filter_by(client_id=self.selected_client.id).all()
            
            self.car_combo.clear()
            self.car_combo.addItem("Выберите автомобиль", None)
            
            for car in cars:
                display_text = f"{car.brand} {car.model} ({car.year}) - {car.license_plate}"
                self.car_combo.addItem(display_text, car)
            
            self.car_combo.setEnabled(True)
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки автомобилей: {e}")
    
    def on_car_selected(self, index):
        """Обработка выбора автомобиля"""
        if index <= 0:
            self.selected_car = None
            self.clear_car_info()
            return
        
        car = self.car_combo.itemData(index)
        if car:
            self.select_car(car)
    
    def select_car(self, car):
        """Выбор автомобиля"""
        self.selected_car = car
        
        # Обновляем информацию об автомобиле
        self.car_brand_label.setText(car.brand)
        self.car_model_label.setText(car.model)
        self.car_year_label.setText(str(car.year))
        self.car_license_label.setText(car.license_plate or "-")
        self.car_vin_label.setText(car.vin or "-")
        self.car_mileage_input.setValue(car.mileage or 0)
        
        self.check_form_validity()
    
    def clear_car_info(self):
        """Очистка информации об автомобиле"""
        self.car_brand_label.setText("-")
        self.car_model_label.setText("-")
        self.car_year_label.setText("-")
        self.car_license_label.setText("-")
        self.car_vin_label.setText("-")
        self.car_mileage_input.setValue(0)
        
        self.check_form_validity()
    
    def create_new_client(self):
        """Создание нового клиента"""
        dialog = ClientDialog(self.session, parent=self)
        if dialog.exec():
            client_data = dialog.get_client_data()
            try:
                client = Client(**client_data)
                self.session.add(client)
                self.session.commit()
                
                self.select_client(client)
                self.load_data()  # Обновляем автодополнение
                
            except Exception as e:
                self.session.rollback()
                self.logger.error(f"Ошибка создания клиента: {e}")
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать клиента: {e}")
    
    def create_new_car(self):
        """Создание нового автомобиля"""
        if not self.selected_client:
            return
        
        dialog = CarDialog(self.session, self.selected_client.id, parent=self)
        if dialog.exec():
            car_data = dialog.get_car_data()
            try:
                car = Car(**car_data)
                self.session.add(car)
                self.session.commit()
                
                self.load_client_cars()
                
                # Автоматически выбираем новый автомобиль
                for i in range(self.car_combo.count()):
                    if self.car_combo.itemData(i) and self.car_combo.itemData(i).id == car.id:
                        self.car_combo.setCurrentIndex(i)
                        break
                
            except Exception as e:
                self.session.rollback()
                self.logger.error(f"Ошибка создания автомобиля: {e}")
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать автомобиль: {e}")
    
    def add_service(self):
        """Добавление услуги"""
        dialog = ServiceDialog(self.session, parent=self)
        if dialog.exec():
            service_data = dialog.get_service_data()
            self.services.append(service_data)
            self.update_services_table()
            self.calculate_totals()
    
    def remove_service(self):
        """Удаление услуги"""
        current_row = self.services_table.currentRow()
        if current_row >= 0 and current_row < len(self.services):
            result = QMessageBox.question(
                self, 
                "Подтверждение", 
                "Удалить выбранную услугу?",
                QMessageBox.Yes | QMessageBox.No
            )
            if result == QMessageBox.Yes:
                self.services.pop(current_row)
                self.update_services_table()
                self.calculate_totals()
    
    def add_part(self):
        """Добавление запчасти"""
        dialog = PartDialog(self.session, parent=self)
        if dialog.exec():
            part_data = dialog.get_part_data()
            self.parts.append(part_data)
            self.update_parts_table()
            self.calculate_totals()
    
    def remove_part(self):
        """Удаление запчасти"""
        current_row = self.parts_table.currentRow()
        if current_row >= 0 and current_row < len(self.parts):
            result = QMessageBox.question(
                self, 
                "Подтверждение", 
                "Удалить выбранную запчасть?",
                QMessageBox.Yes | QMessageBox.No
            )
            if result == QMessageBox.Yes:
                self.parts.pop(current_row)
                self.update_parts_table()
                self.calculate_totals()
    
    def update_services_table(self):
        """Обновление таблицы услуг"""
        self.services_table.setRowCount(len(self.services))
        
        for row, service in enumerate(self.services):
            self.services_table.setItem(row, 0, QTableWidgetItem(service.get('name', '')))
            self.services_table.setItem(row, 1, QTableWidgetItem(service.get('description', '')))
            self.services_table.setItem(row, 2, QTableWidgetItem(f"{service.get('price', 0):.2f} ₽"))
            self.services_table.setItem(row, 3, QTableWidgetItem(service.get('master', '')))
            self.services_table.setItem(row, 4, QTableWidgetItem(service.get('status', 'Ожидает')))
    
    def update_parts_table(self):
        """Обновление таблицы запчастей"""
        self.parts_table.setRowCount(len(self.parts))
        
        for row, part in enumerate(self.parts):
            quantity = part.get('quantity', 0)
            price = part.get('price', 0)
            total = quantity * price
            
            self.parts_table.setItem(row, 0, QTableWidgetItem(part.get('name', '')))
            self.parts_table.setItem(row, 1, QTableWidgetItem(part.get('article', '')))
            self.parts_table.setItem(row, 2, QTableWidgetItem(str(quantity)))
            self.parts_table.setItem(row, 3, QTableWidgetItem(f"{price:.2f} ₽"))
            self.parts_table.setItem(row, 4, QTableWidgetItem(f"{total:.2f} ₽"))
    
    def calculate_totals(self):
        """Расчет итогов"""
        # Сумма услуг
        services_total = sum(service.get('price', 0) for service in self.services)
        self.services_total_label.setText(f"{services_total:.2f} ₽")
        
        # Сумма запчастей
        parts_total = sum(
            part.get('quantity', 0) * part.get('price', 0) 
            for part in self.parts
        )
        self.parts_total_label.setText(f"{parts_total:.2f} ₽")
        
        # Общая сумма до скидки
        subtotal = services_total + parts_total
        
        # Применяем скидку
        discount_percent = self.discount_input.value()
        discount_amount = subtotal * (discount_percent / 100)
        total = subtotal - discount_amount
        
        self.total_label.setText(f"{total:.2f} ₽")
        
        # Проверяем валидность формы
        self.check_form_validity()
    
    def check_form_validity(self):
        """Проверка валидности формы"""
        is_valid = (
            self.selected_client is not None and
            self.selected_car is not None and
            (len(self.services) > 0 or len(self.parts) > 0)
        )
        
        self.save_btn.setEnabled(is_valid)
    
    def save_order(self):
        """Сохранение заказа"""
        if not self.selected_client or not self.selected_car:
            QMessageBox.warning(self, "Предупреждение", "Выберите клиента и автомобиль")
            return
        
        if not self.services and not self.parts:
            QMessageBox.warning(self, "Предупреждение", "Добавьте хотя бы одну услугу или запчасть")
            return
        
        try:
            # Создаем заказ
            order = Order(
                client_id=self.selected_client.id,
                car_id=self.selected_car.id,
                status='new',
                created_date=datetime.now(),
                notes=self.notes_edit.toPlainText(),
                total_amount=float(self.total_label.text().replace(' ₽', '').replace(',', '.')),
                discount_percent=self.discount_input.value()
            )
            
            self.session.add(order)
            self.session.flush()  # Получаем ID заказа
            
            # Добавляем услуги
            for service_data in self.services:
                order_service = OrderService(
                    order_id=order.id,
                    service_name=service_data.get('name', ''),
                    service_description=service_data.get('description', ''),
                    price=service_data.get('price', 0),
                    master=service_data.get('master', ''),
                    status=service_data.get('status', 'pending')
                )
                self.session.add(order_service)
            
            # Добавляем запчасти
            for part_data in self.parts:
                order_part = OrderPart(
                    order_id=order.id,
                    part_name=part_data.get('name', ''),
                    part_article=part_data.get('article', ''),
                    quantity=part_data.get('quantity', 0),
                    price=part_data.get('price', 0)
                )
                self.session.add(order_part)
            
            # Обновляем пробег автомобиля
            if self.car_mileage_input.value() > 0:
                self.selected_car.mileage = self.car_mileage_input.value()
            
            self.session.commit()
            
            # Отправляем сигнал о создании заказа
            order_data = {
                'id': order.id,
                'client': f"{self.selected_client.first_name} {self.selected_client.last_name}",
                'car': f"{self.selected_car.brand} {self.selected_car.model}",
                'total': order.total_amount
            }
            self.order_created.emit(order_data)
            
            QMessageBox.information(self, "Успех", f"Заказ №{order.id} создан успешно!")
            self.clear_form()
            
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Ошибка создания заказа: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать заказ: {e}")
    
    def clear_form(self):
        """Очистка формы"""
        result = QMessageBox.question(
            self, 
            "Подтверждение", 
            "Очистить всю форму? Все несохраненные данные будут потеряны.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if result == QMessageBox.Yes:
            # Очищаем данные
            self.selected_client = None
            self.selected_car = None
            self.services.clear()
            self.parts.clear()
            
            # Очищаем интерфейс
            self.client_search.clear()
            self.client_name_label.setText("-")
            self.client_phone_label.setText("-")
            self.client_email_label.setText("-")
            
            self.car_combo.clear()
            self.car_combo.setEnabled(False)
            self.new_car_btn.setEnabled(False)
            self.clear_car_info()
            
            self.update_services_table()
            self.update_parts_table()
            
            self.discount_input.setValue(0)
            self.notes_edit.clear()
            
            self.calculate_totals()
            self.check_form_validity()