"""
Представление для создания нового заказа
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                               QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox, 
                               QFrame, QCheckBox, QCompleter, QProgressBar, QScrollArea,
                               QSplitter, QGroupBox, QSpacerItem, QSizePolicy, QDateEdit,
                               QDoubleSpinBox, QSpinBox, QTableWidget, QTableWidgetItem,
                               QHeaderView, QAbstractItemView, QTabWidget, QMessageBox,
                               QDateTimeEdit)
from PySide6.QtCore import Qt, QDate, Signal, QTimer, QDateTime
from PySide6.QtGui import QFont, QPalette, QColor, QPixmap, QPainter
import logging
from datetime import datetime
from decimal import Decimal

# Импорты моделей
from shared_models.common_models import Client, Car, Employee
from ..models_sto import Order, OrderService, OrderPart, ServiceCatalog, OrderStatus

# Импорты диалогов
from ..dialogs.client_dialog import ClientDialog
from ..dialogs.car_dialog import CarDialog
from ..dialogs.service_dialog import ServiceDialog
from ..dialogs.part_dialog import PartDialog


class NewOrderView(QWidget):
    """Представление для создания нового заказа"""
    
    order_created = Signal(dict)
    status_message = Signal(str, int)
    order_saved = Signal()
    
    def __init__(self, db_session, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)
        
        # Данные заказа
        self.current_order = None
        self.selected_client = None
        self.selected_car = None
        self.unsaved_changes = False
        
        self.setup_ui()
        self.setup_connections()
        self.load_data()
        
        # Автосохранение
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self.save_draft)
        self.autosave_timer.start(300000)  # 5 минут
    
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
        
        # Верхняя панель - информация о заказе и клиенте
        self.create_order_info_panel()
        
        # Нижняя панель - услуги и запчасти
        self.create_services_parts_panel()
        
        # Добавляем панели в сплиттер
        self.main_splitter.addWidget(self.order_info_widget)
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
        """)
        
        main_layout.addWidget(self.main_splitter)
        
        # Панель кнопок управления
        self.create_control_buttons()
        main_layout.addWidget(self.control_buttons_widget)
    
    def create_order_info_panel(self):
        """Создание панели информации о заказе"""
        self.order_info_widget = QWidget()
        layout = QHBoxLayout(self.order_info_widget)
        
        # Левая группа - основная информация заказа
        order_group = QGroupBox("📋 Информация о заказе")
        order_layout = QGridLayout(order_group)
        
        # Номер заказа
        order_layout.addWidget(QLabel("Номер заказа:"), 0, 0)
        self.order_number_edit = QLineEdit()
        self.order_number_edit.setPlaceholderText("Автоматически...")
        self.order_number_edit.setReadOnly(True)
        order_layout.addWidget(self.order_number_edit, 0, 1)
        
        # Дата приёма
        order_layout.addWidget(QLabel("Дата приёма:"), 1, 0)
        self.date_received_edit = QDateTimeEdit()
        self.date_received_edit.setDateTime(QDateTime.currentDateTime())
        self.date_received_edit.setCalendarPopup(True)
        order_layout.addWidget(self.date_received_edit, 1, 1)
        
        # Дата выдачи
        order_layout.addWidget(QLabel("Дата выдачи:"), 2, 0)
        self.date_delivery_edit = QDateTimeEdit()
        self.date_delivery_edit.setDateTime(QDateTime.currentDateTime().addDays(1))
        self.date_delivery_edit.setCalendarPopup(True)
        order_layout.addWidget(self.date_delivery_edit, 2, 1)
        
        # Статус
        order_layout.addWidget(QLabel("Статус:"), 3, 0)
        self.status_combo = QComboBox()
        for status in OrderStatus:
            self.status_combo.addItem(status.value, status)
        order_layout.addWidget(self.status_combo, 3, 1)
        
        layout.addWidget(order_group)
        
        # Правая группа - клиент и автомобиль
        client_car_group = QGroupBox("👤 Клиент и автомобиль")
        client_car_layout = QVBoxLayout(client_car_group)
        
        # Поиск клиента
        client_search_layout = QHBoxLayout()
        client_search_layout.addWidget(QLabel("Клиент:"))
        self.client_search_edit = QLineEdit()
        self.client_search_edit.setPlaceholderText("Введите имя или телефон...")
        client_search_layout.addWidget(self.client_search_edit)
        
        self.new_client_btn = QPushButton("+ Новый")
        self.new_client_btn.setStyleSheet("background-color: #27ae60; color: white;")
        client_search_layout.addWidget(self.new_client_btn)
        
        client_car_layout.addLayout(client_search_layout)
        
        # Информация о клиенте
        self.client_info_label = QLabel("Клиент не выбран")
        self.client_info_label.setStyleSheet("color: #666; font-style: italic; margin: 5px;")
        client_car_layout.addWidget(self.client_info_label)
        
        # Поиск автомобиля
        car_search_layout = QHBoxLayout()
        car_search_layout.addWidget(QLabel("Автомобиль:"))
        self.car_combo = QComboBox()
        self.car_combo.setEnabled(False)
        car_search_layout.addWidget(self.car_combo)
        
        self.new_car_btn = QPushButton("+ Новый")
        self.new_car_btn.setStyleSheet("background-color: #3498db; color: white;")
        self.new_car_btn.setEnabled(False)
        car_search_layout.addWidget(self.new_car_btn)
        
        client_car_layout.addLayout(car_search_layout)
        
        # Информация об автомобиле
        self.car_info_label = QLabel("Автомобиль не выбран")
        self.car_info_label.setStyleSheet("color: #666; font-style: italic; margin: 5px;")
        client_car_layout.addWidget(self.car_info_label)
        
        # Примечания
        client_car_layout.addWidget(QLabel("Примечания:"))
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Дополнительная информация...")
        client_car_layout.addWidget(self.notes_edit)
        
        layout.addWidget(client_car_group)
    
    def create_services_parts_panel(self):
        """Создание панели услуг и запчастей"""
        self.services_parts_widget = QWidget()
        layout = QHBoxLayout(self.services_parts_widget)
        
        # Создаем табы для услуг и запчастей
        tabs = QTabWidget()
        
        # Вкладка услуг
        self.create_services_tab(tabs)
        
        # Вкладка запчастей
        self.create_parts_tab(tabs)
        
        layout.addWidget(tabs)
        
        # Панель итогов
        self.create_totals_panel()
        layout.addWidget(self.totals_widget)
        
        # Пропорции: 70% табы, 30% итоги
        layout.setStretchFactor(tabs, 7)
        layout.setStretchFactor(self.totals_widget, 3)
    
    def create_services_tab(self, tabs):
        """Создание вкладки услуг"""
        services_widget = QWidget()
        services_layout = QVBoxLayout(services_widget)
        
        # Управление услугами
        services_control_layout = QHBoxLayout()
        
        self.add_service_btn = QPushButton("+ Добавить услугу")
        self.add_service_btn.setStyleSheet("background-color: #27ae60; color: white;")
        services_control_layout.addWidget(self.add_service_btn)
        
        self.remove_service_btn = QPushButton("- Удалить")
        self.remove_service_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        services_control_layout.addWidget(self.remove_service_btn)
        
        services_control_layout.addStretch()
        services_layout.addLayout(services_control_layout)
        
        # Таблица услуг
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(4)
        self.services_table.setHorizontalHeaderLabels([
            "Услуга", "Цена", "Мастер", "Статус"
        ])
        
        # Настройка таблицы
        header = self.services_table.horizontalHeader()
        header.setStretchLastSection(True)
        self.services_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.services_table.setAlternatingRowColors(True)
        
        services_layout.addWidget(self.services_table)
        
        tabs.addTab(services_widget, "🔧 Услуги")
    
    def create_parts_tab(self, tabs):
        """Создание вкладки запчастей"""
        parts_widget = QWidget()
        parts_layout = QVBoxLayout(parts_widget)
        
        # Управление запчастями
        parts_control_layout = QHBoxLayout()
        
        self.add_part_btn = QPushButton("+ Добавить запчасть")
        self.add_part_btn.setStyleSheet("background-color: #27ae60; color: white;")
        parts_control_layout.addWidget(self.add_part_btn)
        
        self.remove_part_btn = QPushButton("- Удалить")
        self.remove_part_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        parts_control_layout.addWidget(self.remove_part_btn)
        
        parts_control_layout.addStretch()
        parts_layout.addLayout(parts_control_layout)
        
        # Таблица запчастей
        self.parts_table = QTableWidget()
        self.parts_table.setColumnCount(5)
        self.parts_table.setHorizontalHeaderLabels([
            "Запчасть", "Артикул", "Количество", "Цена за ед.", "Итого"
        ])
        
        # Настройка таблицы
        header = self.parts_table.horizontalHeader()
        header.setStretchLastSection(True)
        self.parts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.parts_table.setAlternatingRowColors(True)
        
        parts_layout.addWidget(self.parts_table)
        
        tabs.addTab(parts_widget, "🔩 Запчасти")
    
    def create_totals_panel(self):
        """Создание панели итогов"""
        self.totals_widget = QWidget()
        totals_layout = QVBoxLayout(self.totals_widget)
        
        # Группа итогов
        totals_group = QGroupBox("💰 Итоги заказа")
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
        group_layout.addWidget(self.discount_input, 2, 1)
        
        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        group_layout.addWidget(line, 3, 0, 1, 2)
        
        # Общая сумма
        group_layout.addWidget(QLabel("ИТОГО:"), 4, 0)
        self.total_label = QLabel("0.00 ₽")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #e74c3c;")
        group_layout.addWidget(self.total_label, 4, 1)
        
        totals_layout.addWidget(totals_group)
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
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        
        # Кнопка сохранения черновика
        self.save_draft_btn = QPushButton("💾 Сохранить черновик")
        self.save_draft_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                font-weight: bold;
                padding: 12px 25px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
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
        layout.addWidget(self.save_draft_btn)
        layout.addWidget(self.save_btn)
    
    def setup_connections(self):
        """Настройка соединений сигналов"""
        # Поиск клиента
        self.client_search_edit.textChanged.connect(self.search_clients)
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
        self.save_draft_btn.clicked.connect(self.save_draft)
        self.clear_btn.clicked.connect(self.clear_form)
        
        # Отслеживание изменений
        self.notes_edit.textChanged.connect(self.mark_unsaved_changes)
        self.date_received_edit.dateTimeChanged.connect(self.mark_unsaved_changes)
        self.date_delivery_edit.dateTimeChanged.connect(self.mark_unsaved_changes)
    
    def load_data(self):
        """Загрузка данных"""
        try:
            # Настройка автодополнения для поиска клиентов
            clients = self.db_session.query(Client).all()
            client_names = [f"{c.name} - {c.phone}" for c in clients]
            completer = QCompleter(client_names)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.client_search_edit.setCompleter(completer)
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки данных: {e}")
    
    def search_clients(self, text):
        """Поиск клиентов"""
        if len(text) < 2:
            self.client_info_label.setText("Клиент не выбран")
            self.selected_client = None
            self.car_combo.clear()
            self.car_combo.setEnabled(False)
            self.new_car_btn.setEnabled(False)
            return
        
        try:
            clients = self.db_session.query(Client).filter(
                (Client.name.ilike(f"%{text}%")) |
                (Client.phone.ilike(f"%{text}%"))
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
        info_text = f"📞 {client.phone}"
        if client.address:
            info_text += f"\n📍 {client.address}"
        self.client_info_label.setText(info_text)
        
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
            cars = self.db_session.query(Car).filter_by(client_id=self.selected_client.id).all()
            
            self.car_combo.clear()
            self.car_combo.addItem("Выберите автомобиль", None)
            
            for car in cars:
                display_text = f"{car.make or 'Неизв.'} {car.model or ''} ({car.year or 'н/д'}) - {car.license_plate or 'без номера'}"
                self.car_combo.addItem(display_text, car)
            
            self.car_combo.setEnabled(True)
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки автомобилей: {e}")
    
    def on_car_selected(self, index):
        """Обработка выбора автомобиля"""
        if index <= 0:
            self.selected_car = None
            self.car_info_label.setText("Автомобиль не выбран")
            self.check_form_validity()
            return
        
        car = self.car_combo.itemData(index)
        if car:
            self.select_car(car)
    
    def select_car(self, car):
        """Выбор автомобиля"""
        self.selected_car = car
        
        # Обновляем информацию об автомобиле
        info_text = f"🚗 {car.make or 'Неизв.'} {car.model or ''} ({car.year or 'н/д'})"
        if car.vin:
            info_text += f"\n📋 VIN: {car.vin}"
        self.car_info_label.setText(info_text)
        
        self.check_form_validity()
    
    def create_new_client(self):
        """Создание нового клиента"""
        dialog = ClientDialog(parent=self)
        dialog.db_session = self.db_session
        if dialog.exec():
            client = dialog.get_client()
            if client:
                self.client_search_edit.setText(client.name)
                self.select_client(client)
                self.load_data()  # Обновляем автодополнение
    
    def create_new_car(self):
        """Создание нового автомобиля"""
        if not self.selected_client:
            return
        
        dialog = CarDialog(parent=self, client_id=self.selected_client.id)
        dialog.db_session = self.db_session
        if dialog.exec():
            car = dialog.get_car()
            if car:
                self.load_client_cars()
                
                # Автоматически выбираем новый автомобиль
                for i in range(self.car_combo.count()):
                    if self.car_combo.itemData(i) and self.car_combo.itemData(i).id == car.id:
                        self.car_combo.setCurrentIndex(i)
                        break
    
    def add_service(self):
        """Добавление услуги"""
        if not self.current_order:
            if not self.save_draft():
                return
        
        try:
            dialog = ServiceDialog(parent=self, order_id=self.current_order.id)
            dialog.db_session = self.db_session
            if dialog.exec():
                self.refresh_services_table()
                self.calculate_totals()
                self.mark_unsaved_changes()
        except Exception as e:
            self.logger.error(f"Ошибка добавления услуги: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить услугу: {e}")
    
    def remove_service(self):
        """Удаление услуги"""
        current_row = self.services_table.currentRow()
        if current_row >= 0:
            result = QMessageBox.question(
                self, "Подтверждение", 
                "Удалить выбранную услугу?",
                QMessageBox.Yes | QMessageBox.No
            )
            if result == QMessageBox.Yes:
                self.services_table.removeRow(current_row)
                self.calculate_totals()
                self.mark_unsaved_changes()
    
    def add_part(self):
        """Добавление запчасти"""
        if not self.current_order:
            if not self.save_draft():
                return
        
        try:
            dialog = PartDialog(parent=self, order_id=self.current_order.id)
            dialog.db_session = self.db_session
            if dialog.exec():
                self.refresh_parts_table()
                self.calculate_totals()
                self.mark_unsaved_changes()
        except Exception as e:
            self.logger.error(f"Ошибка добавления запчасти: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить запчасть: {e}")
    
    def remove_part(self):
        """Удаление запчасти"""
        current_row = self.parts_table.currentRow()
        if current_row >= 0:
            result = QMessageBox.question(
                self, "Подтверждение", 
                "Удалить выбранную запчасть?",
                QMessageBox.Yes | QMessageBox.No
            )
            if result == QMessageBox.Yes:
                self.parts_table.removeRow(current_row)
                self.calculate_totals()
                self.mark_unsaved_changes()
    
    def refresh_services_table(self):
        """Обновление таблицы услуг"""
        if not self.current_order:
            return
        
        try:
            services = self.db_session.query(OrderService).filter_by(order_id=self.current_order.id).all()
            
            self.services_table.setRowCount(len(services))
            
            for row, service in enumerate(services):
                self.services_table.setItem(row, 0, QTableWidgetItem(service.service_name or ''))
                self.services_table.setItem(row, 1, QTableWidgetItem(f"{service.price:.2f} ₽"))
                self.services_table.setItem(row, 2, QTableWidgetItem(""))  # Мастер
                self.services_table.setItem(row, 3, QTableWidgetItem("Ожидает"))  # Статус
        except Exception as e:
            self.logger.error(f"Ошибка обновления таблицы услуг: {e}")
    
    def refresh_parts_table(self):
        """Обновление таблицы запчастей"""
        if not self.current_order:
            return
        
        try:
            parts = self.db_session.query(OrderPart).filter_by(order_id=self.current_order.id).all()
            
            self.parts_table.setRowCount(len(parts))
            
            for row, part in enumerate(parts):
                self.parts_table.setItem(row, 0, QTableWidgetItem(part.part_name or ''))
                self.parts_table.setItem(row, 1, QTableWidgetItem(part.article or ''))
                self.parts_table.setItem(row, 2, QTableWidgetItem(str(part.quantity)))
                self.parts_table.setItem(row, 3, QTableWidgetItem(f"{part.price:.2f} ₽"))
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления таблицы запчастей: {e}")
    
    def calculate_totals(self):
        """Расчет итогов"""
        # Сумма услуг
        services_total = 0.0
        if self.current_order:
            try:
                services = self.db_session.query(OrderService).filter_by(order_id=self.current_order.id).all()
                services_total = sum(service.price for service in services)
            except:
                pass
        
        self.services_total_label.setText(f"{services_total:.2f} ₽")
        
        # Сумма запчастей
        parts_total = 0.0
        if self.current_order:
            try:
                parts = self.db_session.query(OrderPart).filter_by(order_id=self.current_order.id).all()
                parts_total = sum(part.quantity * part.price for part in parts)
            except:
                pass
        
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
            self.selected_car is not None
        )
        
        self.save_btn.setEnabled(is_valid)
    
    def mark_unsaved_changes(self):
        """Отметка несохраненных изменений"""
        self.unsaved_changes = True
    
    def generate_order_number(self):
        """Генерация номера заказа"""
        try:
            today = datetime.now()
            date_str = today.strftime('%Y%m%d')
            
            # Ищем последний номер за сегодня
            pattern = f'СТО-{date_str}-%'
            last_order = self.db_session.query(Order).filter(
                Order.order_number.like(pattern)
            ).order_by(Order.order_number.desc()).first()
            
            if last_order:
                last_num = int(last_order.order_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
                
            return f'СТО-{date_str}-{new_num:03d}'
            
        except Exception as e:
            self.logger.error(f"Ошибка генерации номера заказа: {e}")
            return f'СТО-{datetime.now().strftime("%Y%m%d")}-001'
    
    def save_draft(self):
        """Сохранение черновика"""
        try:
            if not self.selected_client:
                QMessageBox.warning(self, "Предупреждение", "Выберите клиента")
                return False
            
            # Создаем новый заказ если его нет
            if not self.current_order:
                self.current_order = Order()
                self.current_order.order_number = self.generate_order_number()
                self.order_number_edit.setText(self.current_order.order_number)
                self.db_session.add(self.current_order)
            
            # Заполняем данные
            self.current_order.client_id = self.selected_client.id
            if self.selected_car:
                self.current_order.car_id = self.selected_car.id
            
            self.current_order.date_received = self.date_received_edit.dateTime().toPython()
            self.current_order.date_delivery = self.date_delivery_edit.dateTime().toPython()
            self.current_order.notes = self.notes_edit.toPlainText()
            self.current_order.status = OrderStatus.DRAFT
            
            # Рассчитываем итоговую сумму
            services_total = 0.0
            parts_total = 0.0
            
            if self.current_order.id:
                services = self.db_session.query(OrderService).filter_by(order_id=self.current_order.id).all()
                services_total = sum(service.price for service in services)
                
                parts = self.db_session.query(OrderPart).filter_by(order_id=self.current_order.id).all()
                parts_total = sum(part.quantity * part.price for part in parts)
            
            self.current_order.total_amount = services_total + parts_total
            
            self.db_session.commit()
            
            self.unsaved_changes = False
            self.status_message.emit("Черновик сохранен", 2000)
            
            return True
            
        except Exception as e:
            self.db_session.rollback()
            self.logger.error(f"Ошибка сохранения черновика: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить черновик: {e}")
            return False
    
    def save_order(self):
        """Сохранение заказа"""
        if not self.selected_client or not self.selected_car:
            QMessageBox.warning(self, "Предупреждение", "Выберите клиента и автомобиль")
            return
        
        try:
            # Сначала сохраняем как черновик
            if not self.save_draft():
                return
            
            # Устанавливаем статус
            status_index = self.status_combo.currentIndex()
            if status_index >= 0:
                status_data = self.status_combo.itemData(status_index)
                if status_data:
                    self.current_order.status = status_data
                else:
                    self.current_order.status = OrderStatus.IN_WORK
            
            self.db_session.commit()
            
            # Отправляем сигнал о создании заказа
            order_data = {
                'id': self.current_order.id,
                'number': self.current_order.order_number,
                'client': self.selected_client.name,
                'car': f"{self.selected_car.make} {self.selected_car.model}",
                'total': self.current_order.total_amount
            }
            self.order_created.emit(order_data)
            self.order_saved.emit()
            
            QMessageBox.information(self, "Успех", f"Заказ {self.current_order.order_number} сохранен!")
            
            # Очищаем форму для нового заказа
            self.clear_form()
            
        except Exception as e:
            self.db_session.rollback()
            self.logger.error(f"Ошибка сохранения заказа: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить заказ: {e}")
    
    def clear_form(self):
        """Очистка формы"""
        if self.unsaved_changes:
            result = QMessageBox.question(
                self, "Подтверждение", 
                "Очистить всю форму? Все несохраненные данные будут потеряны.",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if result != QMessageBox.Yes:
                return
        
        # Очищаем данные
        self.current_order = None
        self.selected_client = None
        self.selected_car = None
        self.unsaved_changes = False
        
        # Очищаем интерфейс
        self.order_number_edit.clear()
        self.client_search_edit.clear()
        self.client_info_label.setText("Клиент не выбран")
        
        self.car_combo.clear()
        self.car_combo.setEnabled(False)
        self.new_car_btn.setEnabled(False)
        self.car_info_label.setText("Автомобиль не выбран")
        
        self.date_received_edit.setDateTime(QDateTime.currentDateTime())
        self.date_delivery_edit.setDateTime(QDateTime.currentDateTime().addDays(1))
        self.status_combo.setCurrentIndex(0)
        
        self.services_table.setRowCount(0)
        self.parts_table.setRowCount(0)
        
        self.discount_input.setValue(0)
        self.notes_edit.clear()
        
        self.calculate_totals()
        self.check_form_validity()
    
    def has_unsaved_changes(self):
        """Проверка наличия несохраненных изменений"""
        return self.unsaved_changes
    
    def closeEvent(self, event):
        """Обработка закрытия виджета"""
        if self.unsaved_changes:
            result = QMessageBox.question(
                self, "Несохраненные изменения",
                "Есть несохраненные изменения. Сохранить перед закрытием?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            
            if result == QMessageBox.Save:
                if not self.save_draft():
                    event.ignore()
                    return
            elif result == QMessageBox.Cancel:
                event.ignore()
                return
        
        self.autosave_timer.stop()
        event.accept()