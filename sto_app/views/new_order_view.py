# sto_app/views/new_order_view.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                              QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox,
                              QPushButton, QLabel, QDateTimeEdit, QGroupBox, QTableWidget,
                              QTableWidgetItem, QHeaderView, QMessageBox, QSplitter,
                              QFrame, QCheckBox, QCompleter, QProgressBar, QDialog)
from PySide6.QtCore import Qt, Signal, QDateTime, QStringListModel, QTimer
from PySide6.QtGui import QFont, QIcon, QDoubleValidator, QIntValidator
from sto_app.models_sto import OrderService, OrderPart
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import datetime
import logging
import json

from shared_models.common_models import Client, Car, Employee
from sto_app.models_sto import Order, OrderService, OrderPart, ServiceCatalog, CarBrand, OrderStatus
from sto_app.dialogs.client_dialog import ClientDialog
from sto_app.dialogs.car_dialog import CarDialog
from sto_app.dialogs.service_dialog import ServiceDialog
from sto_app.dialogs.part_dialog import PartDialog


logger = logging.getLogger(__name__)


class NewOrderView(QWidget):
    """Представление создания/редактирования заказа"""
    
    status_message = Signal(str, int)
    order_saved = Signal()
    
    def __init__(self, db_session: Session):
        super().__init__()
        self.db_session = db_session
        self.current_order = None
        self.is_editing = False
        self.unsaved_changes = False
        
        self.setup_ui()
        self.load_initial_data()
        self.setup_connections()
        
        # Автосохранение черновика
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self.save_draft)
        self.autosave_timer.start(60000)  # Каждую минуту
        
    def setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Заголовок
        self.title_label = QLabel('📝 Новый заказ-наряд')
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        layout.addWidget(self.title_label)
        
        # Сплиттер для разделения основной информации и услуг/запчастей
        splitter = QSplitter(Qt.Vertical)
        
        # Верхняя панель с основной информацией
        top_panel = self.create_order_info_panel()
        splitter.addWidget(top_panel)
        
        # Нижняя панель с услугами и запчастями
        bottom_panel = self.create_services_parts_panel()
        splitter.addWidget(bottom_panel)
        
        # Устанавливаем пропорции: основная информация - 40%, услуги/запчасти - 60%
        splitter.setSizes([300, 450])
        
        layout.addWidget(splitter)
        
        # Панель действий
        actions_layout = self.create_actions_panel()
        layout.addLayout(actions_layout)
        
    def create_order_info_panel(self):
        """Создание панели основной информации заказа"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        panel_layout = QVBoxLayout(panel)
        
        # Горизонтальный сплиттер для левой и правой части
        h_splitter = QSplitter(Qt.Horizontal)
        
        # Левая группа - информация о заказе
        order_group = QGroupBox('📋 Информация о заказе')
        order_layout = QFormLayout(order_group)
        
        # Номер заказа
        self.order_number_edit = QLineEdit()
        self.order_number_edit.setPlaceholderText('Автоматически...')
        self.order_number_edit.setReadOnly(True)
        order_layout.addRow('№ заказа:', self.order_number_edit)
        
        # Дата приёма
        self.date_received_edit = QDateTimeEdit()
        self.date_received_edit.setDateTime(QDateTime.currentDateTime())
        self.date_received_edit.setCalendarPopup(True)
        order_layout.addRow('Дата приёма:', self.date_received_edit)
        
        # Дата выдачи
        self.date_delivery_edit = QDateTimeEdit()
        self.date_delivery_edit.setDateTime(QDateTime.currentDateTime().addDays(1))
        self.date_delivery_edit.setCalendarPopup(True)
        order_layout.addRow('Дата выдачи:', self.date_delivery_edit)
        
        # Ответственный
        self.responsible_combo = QComboBox()
        self.responsible_combo.setEditable(True)
        order_layout.addRow('Ответственный:', self.responsible_combo)
        
        # Менеджер
        self.manager_combo = QComboBox()
        self.manager_combo.setEditable(True)
        order_layout.addRow('Менеджер:', self.manager_combo)
        
        # Статус
        self.status_combo = QComboBox()
        self.status_combo.addItems([status.value for status in OrderStatus])
        order_layout.addRow('Статус:', self.status_combo)
        
        h_splitter.addWidget(order_group)
        
        # Правая группа - клиент и автомобиль
        client_car_widget = QWidget()
        client_car_layout = QVBoxLayout(client_car_widget)
        
        # Группа клиента
        client_group = QGroupBox('👤 Клиент')
        client_layout = QVBoxLayout(client_group)
        
        # Поиск клиента
        client_search_layout = QHBoxLayout()
        self.client_search_edit = QLineEdit()
        self.client_search_edit.setPlaceholderText('Введите имя клиента или телефон...')
        client_search_layout.addWidget(self.client_search_edit)
        
        self.new_client_btn = QPushButton('➕')
        self.new_client_btn.setToolTip('Новый клиент')
        self.new_client_btn.setMaximumWidth(40)
        client_search_layout.addWidget(self.new_client_btn)
        
        client_layout.addLayout(client_search_layout)
        
        # Информация о выбранном клиенте
        self.client_info_label = QLabel('Клиент не выбран')
        self.client_info_label.setStyleSheet('color: #666; font-style: italic;')
        client_layout.addWidget(self.client_info_label)
        
        client_car_layout.addWidget(client_group)
        
        # Группа автомобиля
        car_group = QGroupBox('🚗 Автомобиль')
        car_layout = QVBoxLayout(car_group)
        
        # Поиск автомобиля
        car_search_layout = QHBoxLayout()
        self.car_search_edit = QLineEdit()
        self.car_search_edit.setPlaceholderText('Введите VIN или гос. номер...')
        car_search_layout.addWidget(self.car_search_edit)
        
        self.new_car_btn = QPushButton('➕')
        self.new_car_btn.setToolTip('Новый автомобиль')
        self.new_car_btn.setMaximumWidth(40)
        car_search_layout.addWidget(self.new_car_btn)
        
        car_layout.addLayout(car_search_layout)
        
        # Быстрое добавление автомобиля
        car_quick_layout = QFormLayout()
        
        self.car_brand_combo = QComboBox()
        self.car_brand_combo.setEditable(True)
        car_quick_layout.addRow('Марка:', self.car_brand_combo)
        
        self.car_model_combo = QComboBox()
        self.car_model_combo.setEditable(True)
        car_quick_layout.addRow('Модель:', self.car_model_combo)
        
        self.car_year_spin = QSpinBox()
        self.car_year_spin.setRange(1950, 2030)
        self.car_year_spin.setValue(datetime.now().year)
        car_quick_layout.addRow('Год:', self.car_year_spin)
        
        self.car_vin_edit = QLineEdit()
        self.car_vin_edit.setPlaceholderText('17 символов')
        self.car_vin_edit.setMaxLength(17)
        car_quick_layout.addRow('VIN:', self.car_vin_edit)
        
        self.car_plate_edit = QLineEdit()
        self.car_plate_edit.setPlaceholderText('AA1234BB')
        car_quick_layout.addRow('Гос. номер:', self.car_plate_edit)
        
        car_layout.addLayout(car_quick_layout)
        
        # Информация о выбранном автомобиле
        self.car_info_label = QLabel('Автомобиль не выбран')
        self.car_info_label.setStyleSheet('color: #666; font-style: italic;')
        car_layout.addWidget(self.car_info_label)
        
        client_car_layout.addWidget(car_group)
        
        h_splitter.addWidget(client_car_widget)
        
        # Устанавливаем пропорции
        h_splitter.setSizes([400, 500])
        
        panel_layout.addWidget(h_splitter)
        
        # Группа примечаний
        notes_group = QGroupBox('📝 Примечания')
        notes_layout = QVBoxLayout(notes_group)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText('Дополнительная информация о заказе...')
        notes_layout.addWidget(self.notes_edit)
        
        panel_layout.addWidget(notes_group)
        
        return panel
        
    def create_services_parts_panel(self):
        """Создание панели услуг и запчастей"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        panel_layout = QVBoxLayout(panel)
        
        # Горизонтальный сплиттер для услуг и запчастей
        h_splitter = QSplitter(Qt.Horizontal)
        
        # Панель услуг
        services_panel = self.create_services_panel()
        h_splitter.addWidget(services_panel)
        
        # Панель запчастей
        parts_panel = self.create_parts_panel()
        h_splitter.addWidget(parts_panel)
        
        # Панель итогов
        totals_panel = self.create_totals_panel()
        
        panel_layout.addWidget(h_splitter)
        panel_layout.addWidget(totals_panel)
        
        return panel
        
    def create_services_panel(self):
        """Создание панели услуг"""
        services_group = QGroupBox('🔧 Услуги')
        services_layout = QVBoxLayout(services_group)
        
        # Панель добавления услуги
        add_service_layout = QHBoxLayout()
        
        self.service_search_edit = QLineEdit()
        self.service_search_edit.setPlaceholderText('Поиск услуги...')
        add_service_layout.addWidget(self.service_search_edit)
        
        self.add_service_btn = QPushButton('➕ Добавить')
        self.add_service_btn.clicked.connect(self.add_service)
        add_service_layout.addWidget(self.add_service_btn)
        
        services_layout.addLayout(add_service_layout)
        
        # Таблица услуг
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(4)
        self.services_table.setHorizontalHeaderLabels(['Услуга', 'Цена', 'С НДС', 'Действия'])
        
        # Настройка таблицы услуг
        services_header = self.services_table.horizontalHeader()
        services_header.setStretchLastSection(False)
        services_header.setSectionResizeMode(0, QHeaderView.Stretch)
        services_header.setSectionResizeMode(1, QHeaderView.Fixed)
        services_header.setSectionResizeMode(2, QHeaderView.Fixed)
        services_header.setSectionResizeMode(3, QHeaderView.Fixed)
        
        self.services_table.setColumnWidth(1, 100)
        self.services_table.setColumnWidth(2, 100)
        self.services_table.setColumnWidth(3, 80)
        
        self.services_table.setAlternatingRowColors(True)
        self.services_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        services_layout.addWidget(self.services_table)
        
        return services_group
        
    def create_parts_panel(self):
        """Создание панели запчастей"""
        parts_group = QGroupBox('🔩 Запчасти')
        parts_layout = QVBoxLayout(parts_group)
        
        # Панель добавления запчасти
        add_part_layout = QHBoxLayout()
        
        self.part_search_edit = QLineEdit()
        self.part_search_edit.setPlaceholderText('Поиск запчасти...')
        add_part_layout.addWidget(self.part_search_edit)
        
        self.add_part_btn = QPushButton('➕ Добавить')
        self.add_part_btn.clicked.connect(self.add_part)
        add_part_layout.addWidget(self.add_part_btn)
        
        parts_layout.addLayout(add_part_layout)
        
        # Таблица запчастей
        self.parts_table = QTableWidget()
        self.parts_table.setColumnCount(6)
        self.parts_table.setHorizontalHeaderLabels(['Артикул', 'Наименование', 'Кол-во', 'Цена', 'Сумма', 'Действия'])
        
        # Настройка таблицы запчастей
        parts_header = self.parts_table.horizontalHeader()
        parts_header.setStretchLastSection(False)
        parts_header.setSectionResizeMode(1, QHeaderView.Stretch)
        parts_header.setSectionResizeMode(0, QHeaderView.Fixed)
        parts_header.setSectionResizeMode(2, QHeaderView.Fixed)
        parts_header.setSectionResizeMode(3, QHeaderView.Fixed)
        parts_header.setSectionResizeMode(4, QHeaderView.Fixed)
        parts_header.setSectionResizeMode(5, QHeaderView.Fixed)
        
        self.parts_table.setColumnWidth(0, 100)
        self.parts_table.setColumnWidth(2, 80)
        self.parts_table.setColumnWidth(3, 100)
        self.parts_table.setColumnWidth(4, 100)
        self.parts_table.setColumnWidth(5, 80)
        
        self.parts_table.setAlternatingRowColors(True)
        self.parts_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        parts_layout.addWidget(self.parts_table)
        
        return parts_group
        
    def create_totals_panel(self):
        """Создание панели итогов"""
        totals_group = QGroupBox('💰 Расчёт стоимости')
        totals_layout = QHBoxLayout(totals_group)
        
        # Левая часть - предоплата и доплата
        payments_layout = QFormLayout()
        
        self.prepayment_edit = QDoubleSpinBox()
        self.prepayment_edit.setRange(0, 999999)
        self.prepayment_edit.setDecimals(2)
        self.prepayment_edit.setSuffix(' ₴')
        self.prepayment_edit.valueChanged.connect(self.calculate_totals)
        payments_layout.addRow('Предоплата:', self.prepayment_edit)
        
        self.additional_payment_edit = QDoubleSpinBox()
        self.additional_payment_edit.setRange(0, 999999)
        self.additional_payment_edit.setDecimals(2)
        self.additional_payment_edit.setSuffix(' ₴')
        self.additional_payment_edit.valueChanged.connect(self.calculate_totals)
        payments_layout.addRow('Доплата:', self.additional_payment_edit)
        
        totals_layout.addLayout(payments_layout)
        
        totals_layout.addStretch()
        
        # Правая часть - итоги
        summary_layout = QFormLayout()
        
        self.services_total_label = QLabel('0.00 ₴')
        self.services_total_label.setStyleSheet('font-weight: bold;')
        summary_layout.addRow('Услуги:', self.services_total_label)
        
        self.parts_total_label = QLabel('0.00 ₴')
        self.parts_total_label.setStyleSheet('font-weight: bold;')
        summary_layout.addRow('Запчасти:', self.parts_total_label)
        
        self.total_amount_label = QLabel('0.00 ₴')
        self.total_amount_label.setStyleSheet('font-weight: bold; font-size: 14px; color: #2196F3;')
        summary_layout.addRow('ИТОГО:', self.total_amount_label)
        
        self.balance_label = QLabel('0.00 ₴')
        self.balance_label.setStyleSheet('font-weight: bold; font-size: 14px; color: #f44336;')
        summary_layout.addRow('К доплате:', self.balance_label)
        
        totals_layout.addLayout(summary_layout)
        
        return totals_group
        
    def create_actions_panel(self):
        """Создание панели действий"""
        actions_layout = QHBoxLayout()
        
        # Левая сторона - основные действия
        self.save_draft_btn = QPushButton('💾 Сохранить черновик')
        self.save_draft_btn.clicked.connect(self.save_draft)
        actions_layout.addWidget(self.save_draft_btn)
        
        self.save_order_btn = QPushButton('✅ Сохранить заказ')
        self.save_order_btn.setProperty('accent', True)
        self.save_order_btn.clicked.connect(self.save_order)
        actions_layout.addWidget(self.save_order_btn)
        
        actions_layout.addStretch()
        
        # Правая сторона - дополнительные действия
        self.print_btn = QPushButton('🖨️ Печать')
        self.print_btn.clicked.connect(self.print_order)
        actions_layout.addWidget(self.print_btn)
        
        self.clear_btn = QPushButton('🗑️ Очистить')
        self.clear_btn.setProperty('danger', True)
        self.clear_btn.clicked.connect(self.clear_form)
        actions_layout.addWidget(self.clear_btn)
        
        return actions_layout
        
    def setup_connections(self):
        """Настройка соединений сигналов"""
        # Отслеживание изменений для автосохранения
        self.client_search_edit.textChanged.connect(self.on_client_search)
        self.car_search_edit.textChanged.connect(self.on_car_search)
        self.service_search_edit.returnPressed.connect(self.add_service_from_search)
        self.part_search_edit.returnPressed.connect(self.add_part_from_search)
        
        # Кнопки добавления
        self.new_client_btn.clicked.connect(self.new_client)
        self.new_car_btn.clicked.connect(self.new_car)
        
        # Изменение марки автомобиля
        self.car_brand_combo.currentTextChanged.connect(self.on_brand_changed)
        
        # Отслеживание изменений для несохранённых данных
        widgets_to_track = [
            self.date_received_edit, self.date_delivery_edit, self.notes_edit,
            self.prepayment_edit, self.additional_payment_edit, self.car_year_spin,
            self.car_vin_edit, self.car_plate_edit
        ]
        
        for widget in widgets_to_track:
            if hasattr(widget, 'textChanged'):
                widget.textChanged.connect(self.mark_unsaved_changes)
            elif hasattr(widget, 'valueChanged'):
                widget.valueChanged.connect(self.mark_unsaved_changes)
            elif hasattr(widget, 'dateTimeChanged'):
                widget.dateTimeChanged.connect(self.mark_unsaved_changes)
                
    def load_initial_data(self):
        """Загрузка начальных данных"""
        try:
            # Загружаем сотрудников
            employees = self.db_session.query(Employee).filter(Employee.is_active == 1).all()
            
            for combo in [self.responsible_combo, self.manager_combo]:
                combo.clear()
                combo.addItem('', None)
                for emp in employees:
                    combo.addItem(emp.name, emp.id)
                    
            # Загружаем марки автомобилей
            brands = self.db_session.query(CarBrand).all()
            self.car_brand_combo.clear()
            self.car_brand_combo.addItem('')
            
            for brand in brands:
                self.car_brand_combo.addItem(brand.brand, brand.id)
                
            # Настраиваем автодополнение для услуг
            services = self.db_session.query(ServiceCatalog).filter(ServiceCatalog.is_active == 1).all()
            service_names = [service.name for service in services]
            
            service_completer = QCompleter(service_names)
            service_completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.service_search_edit.setCompleter(service_completer)
            
        except Exception as e:
            logger.error(f"Ошибка загрузки начальных данных: {e}")
            
    def on_brand_changed(self, brand_name):
        """Обработка изменения марки автомобиля"""
        self.car_model_combo.clear()
        
        if not brand_name:
            return
            
        try:
            brand = self.db_session.query(CarBrand).filter(CarBrand.brand == brand_name).first()
            if brand:
                models = brand.get_models_list()
                self.car_model_combo.addItems([''] + models)
        except Exception as e:
            logger.error(f"Ошибка загрузки моделей: {e}")
            
    def on_client_search(self, text):
        """Поиск клиента"""
        if len(text) < 2:
            self.client_info_label.setText('Клиент не выбран')
            return
            
        try:
            # Поиск по имени или телефону
            clients = self.db_session.query(Client).filter(
                or_(
                    Client.name.ilike(f'%{text}%'),
                    Client.phone.ilike(f'%{text}%')
                )
            ).limit(5).all()
            
            if clients:
                client = clients[0]  # Берём первого найденного
                self.client_info_label.setText(f'📞 {client.phone}\n📍 {client.address or ""}')
                self.selected_client = client
                
                # Загружаем автомобили клиента
                self.load_client_cars(client.id)
            else:
                self.client_info_label.setText('Клиент не найден')
                self.selected_client = None
                
        except Exception as e:
            logger.error(f"Ошибка поиска клиента: {e}")
            
    def on_car_search(self, text):
        """Поиск автомобиля"""
        if len(text) < 3:
            self.car_info_label.setText('Автомобиль не выбран')
            return
            
        try:
            # Поиск по VIN или госномеру
            cars = self.db_session.query(Car).filter(
                or_(
                    Car.vin.ilike(f'%{text}%'),
                    Car.license_plate.ilike(f'%{text}%')
                )
            ).limit(5).all()
            
            if cars:
                car = cars[0]  # Берём первую найденную
                self.car_info_label.setText(f'🚗 {car.full_name}\n📋 VIN: {car.vin}')
                self.selected_car = car
                
                # Заполняем поля автомобиля
                self.fill_car_fields(car)
            else:
                self.car_info_label.setText('Автомобиль не найден')
                self.selected_car = None
                
        except Exception as e:
            logger.error(f"Ошибка поиска автомобиля: {e}")
            
    def load_client_cars(self, client_id):
        """Загрузка автомобилей клиента"""
        try:
            cars = self.db_session.query(Car).filter(Car.client_id == client_id).all()
            if cars and len(cars) == 1:
                # Если у клиента один автомобиль, автоматически выбираем его
                car = cars[0]
                self.car_search_edit.setText(car.vin or car.license_plate or '')
                self.selected_car = car
                self.fill_car_fields(car)
        except Exception as e:
            logger.error(f"Ошибка загрузки автомобилей клиента: {e}")
            
    def fill_car_fields(self, car):
        """Заполнение полей автомобиля"""
        if car.brand:
            index = self.car_brand_combo.findText(car.brand)
            if index >= 0:
                self.car_brand_combo.setCurrentIndex(index)
                
        if car.model:
            self.car_model_combo.setCurrentText(car.model)
            
        if car.year:
            self.car_year_spin.setValue(car.year)
            
        if car.vin:
            self.car_vin_edit.setText(car.vin)
            
        if car.license_plate:
            self.car_plate_edit.setText(car.license_plate)
            
    def new_client(self):
        """Создание нового клиента"""
        dialog = ClientDialog(self)
        if dialog.exec():
            # Обновляем поиск с новым клиентом
            client = dialog.get_client()
            self.client_search_edit.setText(client.name)
            self.selected_client = client
            
    def new_car(self):
        """Создание нового автомобиля"""
        if not hasattr(self, 'selected_client') or not self.selected_client:
            QMessageBox.information(self, 'Информация', 'Сначала выберите клиента')
            return
            
        dialog = CarDialog(self, self.selected_client.id)
        if dialog.exec():
            # Обновляем поиск с новым автомобилем
            car = dialog.get_car()
            self.car_search_edit.setText(car.vin or car.license_plate or '')
            self.selected_car = car
            
    def add_service(self):
        """Добавление услуги через диалог"""
        if not self.current_order:
            # Создаем временный заказ для передачи order_id
            reply = QMessageBox.question(
                self, 'Создание заказа',
                'Для добавления услуг необходимо сначала сохранить заказ как черновик. Продолжить?',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                if not self.save_draft():
                    return
            else:
                return

        dialog = ServiceDialog(self, order_id=self.current_order.id)
        dialog.service_cost_changed.connect(self.calculate_totals)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            order_service = dialog.get_order_service()
            if order_service:
                # Обновляем таблицу услуг
                self.refresh_services_table()
                self.calculate_totals()
                self.mark_unsaved_changes()
                
    def add_service_from_search(self):
        """Добавление услуги из поиска по Enter"""
        text = self.service_search_edit.text().strip()
        if text:
            self.add_service()
            
    def add_service_to_table(self, name, price):
        """Добавление услуги в таблицу"""
        row = self.services_table.rowCount()
        self.services_table.insertRow(row)
        
        # Название услуги
        name_item = QTableWidgetItem(name)
        self.services_table.setItem(row, 0, name_item)
        
        # Цена
        price_item = QTableWidgetItem(f'{price:.2f}')
        price_item.setTextAlignment(Qt.AlignRight)
        self.services_table.setItem(row, 1, price_item)
        
        # Цена с НДС
        price_with_vat = price * 1.2
        vat_item = QTableWidgetItem(f'{price_with_vat:.2f}')
        vat_item.setTextAlignment(Qt.AlignRight)
        self.services_table.setItem(row, 2, vat_item)
        
        # Кнопка удаления
        delete_btn = QPushButton('🗑️')
        delete_btn.setMaximumWidth(30)
        delete_btn.clicked.connect(lambda: self.remove_service_row(row))
        self.services_table.setCellWidget(row, 3, delete_btn)
        
        self.calculate_totals()
        self.mark_unsaved_changes()
            
    def add_part(self):
        """Добавление запчасти через диалог"""
        if not self.current_order:
            reply = QMessageBox.question(
                self, 'Создание заказа',
                'Для добавления запчастей необходимо сначала сохранить заказ как черновик. Продолжить?',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                if not self.save_draft():
                    return
            else:
                return

        dialog = PartDialog(self, order_id=self.current_order.id)
        dialog.part_cost_changed.connect(self.calculate_totals)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            order_part = dialog.get_order_part()
            if order_part:
                # Обновляем таблицу запчастей
                self.refresh_parts_table()
                self.calculate_totals()
                self.mark_unsaved_changes()
                
    def add_part_from_search(self):
        """Добавление запчасти из поиска по Enter"""
        text = self.part_search_edit.text().strip()
        if text:
            self.add_part()
            
    def add_part_to_table(self, article, name, quantity, price):
        """Добавление запчасти в таблицу"""
        row = self.parts_table.rowCount()
        self.parts_table.insertRow(row)
        
        # Артикул
        article_item = QTableWidgetItem(article or '')
        self.parts_table.setItem(row, 0, article_item)
        
        # Наименование
        name_item = QTableWidgetItem(name)
        self.parts_table.setItem(row, 1, name_item)
        
        # Количество
        qty_item = QTableWidgetItem(str(quantity))
        qty_item.setTextAlignment(Qt.AlignCenter)
        self.parts_table.setItem(row, 2, qty_item)
        
        # Цена
        price_item = QTableWidgetItem(f'{price:.2f}')
        price_item.setTextAlignment(Qt.AlignRight)
        self.parts_table.setItem(row, 3, price_item)
        
        # Сумма
        total = quantity * price
        total_item = QTableWidgetItem(f'{total:.2f}')
        total_item.setTextAlignment(Qt.AlignRight)
        self.parts_table.setItem(row, 4, total_item)
        
        # Кнопка удаления
        delete_btn = QPushButton('🗑️')
        delete_btn.setMaximumWidth(30)
        delete_btn.clicked.connect(lambda: self.remove_part_row(row))
        self.parts_table.setCellWidget(row, 5, delete_btn)
        
        self.calculate_totals()
        self.mark_unsaved_changes()
        
    def remove_service_row(self, row):
        """Удаление строки услуги"""
        reply = QMessageBox.question(
            self, 'Подтверждение',
            'Удалить выбранную услугу?',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.services_table.removeRow(row)
            self.calculate_totals()
            self.mark_unsaved_changes()
            
    def remove_part_row(self, row):
        """Удаление строки запчасти"""
        reply = QMessageBox.question(
            self, 'Подтверждение',
            'Удалить выбранную запчасть?',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.parts_table.removeRow(row)
            self.calculate_totals()
            self.mark_unsaved_changes()
            
    def calculate_totals(self):
        """Расчёт итоговых сумм"""
        try:
            # Сумма услуг
            services_total = 0.0
            for row in range(self.services_table.rowCount()):
                price_item = self.services_table.item(row, 2)  # Цена с НДС
                if price_item:
                    services_total += float(price_item.text())
                    
            # Сумма запчастей
            parts_total = 0.0
            for row in range(self.parts_table.rowCount()):
                total_item = self.parts_table.item(row, 4)  # Сумма
                if total_item:
                    parts_total += float(total_item.text())
                    
            # Общая сумма
            total_amount = services_total + parts_total
            
            # Остаток к доплате
            prepayment = self.prepayment_edit.value()
            additional_payment = self.additional_payment_edit.value()
            balance = total_amount - prepayment - additional_payment
            
            # Обновляем отображение
            self.services_total_label.setText(f'{services_total:.2f} ₴')
            self.parts_total_label.setText(f'{parts_total:.2f} ₴')
            self.total_amount_label.setText(f'{total_amount:.2f} ₴')
            
            # Цвет остатка
            if balance > 0:
                self.balance_label.setText(f'{balance:.2f} ₴')
                self.balance_label.setStyleSheet('font-weight: bold; font-size: 14px; color: #f44336;')
            elif balance < 0:
                self.balance_label.setText(f'{abs(balance):.2f} ₴ переплата')
                self.balance_label.setStyleSheet('font-weight: bold; font-size: 14px; color: #ff9800;')
            else:
                self.balance_label.setText('Оплачено полностью')
                self.balance_label.setStyleSheet('font-weight: bold; font-size: 14px; color: #4caf50;')
                
        except Exception as e:
            logger.error(f"Ошибка расчёта итогов: {e}")
            
    def mark_unsaved_changes(self):
        """Отметить наличие несохранённых изменений"""
        self.unsaved_changes = True
        title = self.title_label.text()
        if not title.endswith(' *'):
            self.title_label.setText(title + ' *')
            
    def generate_order_number(self):
        """Генерация номера заказа"""
        try:
            # Формат: СТО-YYYYMMDD-NNN
            today = datetime.now()
            date_str = today.strftime('%Y%m%d')
            
            # Ищем последний номер за сегодня
            pattern = f'СТО-{date_str}-%'
            last_order = self.db_session.query(Order).filter(
                Order.order_number.like(pattern)
            ).order_by(Order.order_number.desc()).first()
            
            if last_order:
                # Извлекаем номер и увеличиваем
                last_num = int(last_order.order_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
                
            return f'СТО-{date_str}-{new_num:03d}'
            
        except Exception as e:
            logger.error(f"Ошибка генерации номера заказа: {e}")
            return f'СТО-{datetime.now().strftime("%Y%m%d")}-001'
            
    def save_draft(self):
        """Сохранить черновик"""
        try:
            if not self.validate_minimal_data():
                return False
                
            # Если это новый заказ, создаём его
            if not self.current_order:
                self.current_order = Order()
                self.current_order.order_number = self.generate_order_number()
                self.order_number_edit.setText(self.current_order.order_number)
                
            # Заполняем основные данные
            self.fill_order_data()
            self.current_order.status = OrderStatus.DRAFT
            
            # Сохраняем в БД
            self.db_session.add(self.current_order)
            self.db_session.commit()
            
            self.unsaved_changes = False
            title = self.title_label.text().replace(' *', '')
            self.title_label.setText(title)
            
            self.status_message.emit('Черновик сохранён', 2000)
            return True
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Ошибка сохранения черновика: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить черновик: {e}')
            return False
            
    def save_order(self):
        """Сохранить заказ"""
        try:
            if not self.validate_order_data():
                return False
                
            # Если это новый заказ, создаём его
            if not self.current_order:
                self.current_order = Order()
                self.current_order.order_number = self.generate_order_number()
                self.order_number_edit.setText(self.current_order.order_number)
                
            # Заполняем данные
            self.fill_order_data()
            
            # Устанавливаем статус
            if self.status_combo.currentText():
                status_value = self.status_combo.currentText()
                for status in OrderStatus:
                    if status.value == status_value:
                        self.current_order.status = status
                        break
            else:
                self.current_order.status = OrderStatus.IN_WORK
                
            # Сохраняем в БД
            self.db_session.add(self.current_order)
            self.db_session.commit()
            
            self.unsaved_changes = False
            title = self.title_label.text().replace(' *', '')
            self.title_label.setText(title)
            
            self.status_message.emit(f'Заказ {self.current_order.order_number} сохранён', 3000)
            self.order_saved.emit()
            
            return True
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Ошибка сохранения заказа: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить заказ: {e}')
            return False
            
    def validate_minimal_data(self):
        """Минимальная валидация для черновика"""
        if not hasattr(self, 'selected_client') or not self.selected_client:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите клиента')
            return False
            
        return True
        
    def validate_order_data(self):
        """Полная валидация данных заказа"""
        if not self.validate_minimal_data():
            return False
            
        if not hasattr(self, 'selected_car') or not self.selected_car:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите автомобиль')
            return False
            
        if self.services_table.rowCount() == 0 and self.parts_table.rowCount() == 0:
            QMessageBox.warning(self, 'Предупреждение', 'Добавьте хотя бы одну услугу или запчасть')
            return False
            
        return True
        
    def fill_order_data(self):
        """Заполнение данных заказа"""
        # Основная информация
        self.current_order.date_received = self.date_received_edit.dateTime().toPython()
        self.current_order.date_delivery = self.date_delivery_edit.dateTime().toPython()
        self.current_order.notes = self.notes_edit.toPlainText()
        
        # Клиент и автомобиль
        if hasattr(self, 'selected_client'):
            self.current_order.client_id = self.selected_client.id
            
        if hasattr(self, 'selected_car'):
            self.current_order.car_id = self.selected_car.id
        else:
            # Создаём новый автомобиль из данных формы
            self.create_car_from_form()
            
        # Ответственный и менеджер
        resp_id = self.responsible_combo.currentData()
        if resp_id:
            self.current_order.responsible_person_id = resp_id
            
        mgr_id = self.manager_combo.currentData()
        if mgr_id:
            self.current_order.manager_id = mgr_id
            
        # Платежи
        self.current_order.prepayment = self.prepayment_edit.value()
        self.current_order.additional_payment = self.additional_payment_edit.value()
        
        # Рассчитываем общую сумму
        services_total = float(self.services_total_label.text().replace(' ₴', ''))
        parts_total = float(self.parts_total_label.text().replace(' ₴', ''))
        self.current_order.total_amount = services_total + parts_total
        
        # Сохраняем услуги
        self.save_order_services()
        
        # Сохраняем запчасти
        self.save_order_parts()
        
    def create_car_from_form(self):
        """Создание автомобиля из данных формы"""
        if not hasattr(self, 'selected_client'):
            return
            
        car = Car()
        car.client_id = self.selected_client.id
        car.brand = self.car_brand_combo.currentText()
        car.model = self.car_model_combo.currentText()
        car.year = self.car_year_spin.value() if self.car_year_spin.value() != datetime.now().year else None
        car.vin = self.car_vin_edit.text().strip() or None
        car.license_plate = self.car_plate_edit.text().strip() or None
        
        self.db_session.add(car)
        self.db_session.flush()  # Получаем ID
        
        self.selected_car = car
        self.current_order.car_id = car.id
        
    def save_order_services(self):
        """Сохранение услуг заказа"""
        # Удаляем старые услуги
        if self.current_order.id:
            self.db_session.query(OrderService).filter(
                OrderService.order_id == self.current_order.id
            ).delete()
            
        # Добавляем новые
        for row in range(self.services_table.rowCount()):
            service = OrderService()
            service.order_id = self.current_order.id
            service.service_name = self.services_table.item(row, 0).text()
            service.price = float(self.services_table.item(row, 1).text())
            service.price_with_vat = float(self.services_table.item(row, 2).text())
            
            self.db_session.add(service)
            
    def save_order_parts(self):
        """Сохранение запчастей заказа"""
        # Удаляем старые запчасти
        if self.current_order.id:
            self.db_session.query(OrderPart).filter(
                OrderPart.order_id == self.current_order.id
            ).delete()
            
        # Добавляем новые
        for row in range(self.parts_table.rowCount()):
            part = OrderPart()
            part.order_id = self.current_order.id
            part.article = self.parts_table.item(row, 0).text()
            part.part_name = self.parts_table.item(row, 1).text()
            part.quantity = float(self.parts_table.item(row, 2).text())
            part.price = float(self.parts_table.item(row, 3).text())
            part.total = float(self.parts_table.item(row, 4).text())
            
            self.db_session.add(part)
            
    def load_order(self, order):
        """Загрузка существующего заказа"""
        self.current_order = order
        self.is_editing = True
        
        # Основная информация
        self.order_number_edit.setText(order.order_number)
        self.date_received_edit.setDateTime(QDateTime.fromSecsSinceEpoch(int(order.date_received.timestamp())))
        
        if order.date_delivery:
            self.date_delivery_edit.setDateTime(QDateTime.fromSecsSinceEpoch(int(order.date_delivery.timestamp())))
            
        self.notes_edit.setPlainText(order.notes or '')
        
        # Статус
        if order.status:
            index = self.status_combo.findText(order.status.value)
            if index >= 0:
                self.status_combo.setCurrentIndex(index)
                
        # Платежи
        self.prepayment_edit.setValue(order.prepayment or 0)
        self.additional_payment_edit.setValue(order.additional_payment or 0)
        
        # Клиент
        if order.client:
            self.client_search_edit.setText(order.client.name)
            self.selected_client = order.client
            
        # Автомобиль
        if order.car:
            self.car_search_edit.setText(order.car.vin or order.car.license_plate or '')
            self.selected_car = order.car
            self.fill_car_fields(order.car)
            
        # Ответственный
        if order.responsible_person_id:
            for i in range(self.responsible_combo.count()):
                if self.responsible_combo.itemData(i) == order.responsible_person_id:
                    self.responsible_combo.setCurrentIndex(i)
                    break
                    
        # Менеджер
        if order.manager_id:
            for i in range(self.manager_combo.count()):
                if self.manager_combo.itemData(i) == order.manager_id:
                    self.manager_combo.setCurrentIndex(i)
                    break
                    
        # Услуги
        self.services_table.setRowCount(0)
        for service in order.services:
            self.add_service_to_table(service.service_name, service.price)
            
        # Запчасти
        self.parts_table.setRowCount(0)
        for part in order.parts:
            self.add_part_to_table(part.article, part.part_name, part.quantity, part.price)
            
        self.calculate_totals()
        self.unsaved_changes = False
        
        self.title_label.setText(f'✏️ Редактирование заказа {order.order_number}')
        
    def clear_form(self):
        """Очистка формы"""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self, 'Подтверждение',
                'Есть несохранённые изменения. Очистить форму?',
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
                
        # Сброс всех полей
        self.current_order = None
        self.is_editing = False
        self.unsaved_changes = False
        
        self.order_number_edit.clear()
        self.date_received_edit.setDateTime(QDateTime.currentDateTime())
        self.date_delivery_edit.setDateTime(QDateTime.currentDateTime().addDays(1))
        self.notes_edit.clear()
        
        self.client_search_edit.clear()
        self.car_search_edit.clear()
        
        self.car_brand_combo.setCurrentIndex(0)
        self.car_model_combo.clear()
        self.car_year_spin.setValue(datetime.now().year)
        self.car_vin_edit.clear()
        self.car_plate_edit.clear()
        
        self.responsible_combo.setCurrentIndex(0)
        self.manager_combo.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)
        
        self.prepayment_edit.setValue(0)
        self.additional_payment_edit.setValue(0)
        
        self.services_table.setRowCount(0)
        self.parts_table.setRowCount(0)
        
        self.client_info_label.setText('Клиент не выбран')
        self.car_info_label.setText('Автомобиль не выбран')
        
        self.calculate_totals()
        
        self.title_label.setText('📝 Новый заказ-наряд')
        
        self.status_message.emit('Форма очищена', 2000)
        
    def print_order(self):
        """Печать заказа"""
        if not self.current_order:
            QMessageBox.information(self, 'Информация', 'Сначала сохраните заказ')
            return
            
        # Здесь будет печать
        self.status_message.emit('Функция печати будет реализована', 2000)
        
    def has_unsaved_changes(self):
        """Проверка наличия несохранённых изменений"""
        return self.unsaved_changes
        
    def closeEvent(self, event):
        """Обработка закрытия"""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self, 'Несохранённые изменения',
                'Есть несохранённые изменения. Сохранить перед закрытием?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Save:
                if not self.save_draft():
                    event.ignore()
                    return
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
                
        self.autosave_timer.stop()
        event.accept()
      
    def refresh_services_table(self):
        """Обновление таблицы услуг из БД"""
        if not self.current_order or not self.current_order.id:
            return
            
        try:
            # Загружаем услуги из БД
            services = self.db_session.query(OrderService).filter(
                OrderService.order_id == self.current_order.id
            ).all()
            
            # Очищаем таблицу
            self.services_table.setRowCount(0)
            
            # Заполняем таблицу
            for service in services:
                self.add_service_row_from_db(service)
                
        except Exception as e:
            logger.error(f"Ошибка обновления таблицы услуг: {e}")

    def refresh_parts_table(self):
        """Обновление таблицы запчастей из БД"""
        if not self.current_order or not self.current_order.id:
            return
            
        try:
            # Загружаем запчасти из БД
            parts = self.db_session.query(OrderPart).filter(
                OrderPart.order_id == self.current_order.id
            ).all()
            
            # Очищаем таблицу
            self.parts_table.setRowCount(0)
            
            # Заполняем таблицу
            for part in parts:
                self.add_part_row_from_db(part)
                
        except Exception as e:
            logger.error(f"Ошибка обновления таблицы запчастей: {e}")

    def add_service_row_from_db(self, service):
        """Добавление строки услуги из объекта БД"""
        row = self.services_table.rowCount()
        self.services_table.insertRow(row)
        
        # Заполняем данные из объекта OrderService
        self.services_table.setItem(row, 0, QTableWidgetItem(service.service_name or "Услуга"))
        
        price_item = QTableWidgetItem(f'{float(service.price):.2f}')
        price_item.setTextAlignment(Qt.AlignRight)
        self.services_table.setItem(row, 1, price_item)
        
        # Цена с НДС
        vat_price = float(service.price_with_vat or service.price * 1.2)
        vat_item = QTableWidgetItem(f'{vat_price:.2f}')
        vat_item.setTextAlignment(Qt.AlignRight)
        self.services_table.setItem(row, 2, vat_item)
        
        # Кнопка удаления
        delete_btn = QPushButton('🗑️')
        delete_btn.setMaximumWidth(30)
        delete_btn.clicked.connect(lambda: self.remove_service_from_db(service.id, row))
        self.services_table.setCellWidget(row, 3, delete_btn)

    def add_part_row_from_db(self, part):
        """Добавление строки запчасти из объекта БД"""
        row = self.parts_table.rowCount()
        self.parts_table.insertRow(row)
        
        # Заполняем данные из объекта OrderPart
        self.parts_table.setItem(row, 0, QTableWidgetItem(part.article or ""))
        self.parts_table.setItem(row, 1, QTableWidgetItem(part.part_name))
        
        qty_item = QTableWidgetItem(str(part.quantity))
        qty_item.setTextAlignment(Qt.AlignCenter)
        self.parts_table.setItem(row, 2, qty_item)
        
        price_item = QTableWidgetItem(f'{float(part.price):.2f}')
        price_item.setTextAlignment(Qt.AlignRight)
        self.parts_table.setItem(row, 3, price_item)
        
        total = float(part.price) * part.quantity
        total_item = QTableWidgetItem(f'{total:.2f}')
        total_item.setTextAlignment(Qt.AlignRight)
        self.parts_table.setItem(row, 4, total_item)
        
        # Кнопка удаления
        delete_btn = QPushButton('🗑️')
        delete_btn.setMaximumWidth(30)
        delete_btn.clicked.connect(lambda: self.remove_part_from_db(part.id, row))
        self.parts_table.setCellWidget(row, 5, delete_btn)

    def remove_service_from_db(self, service_id, row):
        """Удаление услуги из БД"""
        reply = QMessageBox.question(
            self, 'Подтверждение',
            'Удалить выбранную услугу?',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Удаляем из БД
                service = self.db_session.get(OrderService, service_id)
                if service:
                    self.db_session.delete(service)
                    self.db_session.commit()
                
                # Удаляем из таблицы
                self.services_table.removeRow(row)
                self.calculate_totals()
                self.mark_unsaved_changes()
                
            except Exception as e:
                self.db_session.rollback()
                logger.error(f"Ошибка удаления услуги: {e}")
                QMessageBox.critical(self, 'Ошибка', f'Не удалось удалить услугу: {e}')

    def remove_part_from_db(self, part_id, row):
        """Удаление запчасти из БД"""
        reply = QMessageBox.question(
            self, 'Подтверждение',
            'Удалить выбранную запчасть?',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Удаляем из БД
                part = self.db_session.get(OrderPart, part_id)
                if part:
                    self.db_session.delete(part)
                    self.db_session.commit()
                
                # Удаляем из таблицы
                self.parts_table.removeRow(row)
                self.calculate_totals()
                self.mark_unsaved_changes()
                
            except Exception as e:
                self.db_session.rollback()
                logger.error(f"Ошибка удаления запчасти: {e}")
                QMessageBox.critical(self, 'Ошибка', f'Не удалось удалить запчасть: {e}')