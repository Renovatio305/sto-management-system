# sto_app/dialogs/search_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QLineEdit, QComboBox, QPushButton, QTableWidget,
                              QTableWidgetItem, QHeaderView, QLabel, QCheckBox,
                              QDateEdit, QGroupBox, QTabWidget, QMessageBox)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QFont
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from shared_models.common_models import Client, Car, Employee
from sto_app.models_sto import Order, OrderService, OrderPart, ServiceCatalog


class SearchDialog(QDialog):
    """Универсальный диалог поиска по всем данным"""
    
    # Сигнал для передачи выбранного элемента
    item_selected = Signal(str, object)  # (тип, объект)
    
    def __init__(self, db_session: Session, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        
        self.setWindowTitle('🔍 Универсальный поиск')
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Заголовок
        title_label = QLabel('🔍 Поиск по всем данным')
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Панель поиска
        search_group = QGroupBox('Параметры поиска')
        search_layout = QFormLayout(search_group)
        
        # Поисковая строка
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('Введите текст для поиска...')
        search_layout.addRow('Поиск:', self.search_edit)
        
        # Тип поиска
        self.search_type_combo = QComboBox()
        self.search_type_combo.addItems([
            'Все категории',
            'Клиенты',
            'Автомобили', 
            'Заказы',
            'Услуги',
            'Запчасти',
            'Сотрудники'
        ])
        search_layout.addRow('Категория:', self.search_type_combo)
        
        # Дополнительные фильтры
        filters_layout = QHBoxLayout()
        
        self.case_sensitive_cb = QCheckBox('Учитывать регистр')
        filters_layout.addWidget(self.case_sensitive_cb)
        
        self.exact_match_cb = QCheckBox('Точное совпадение')
        filters_layout.addWidget(self.exact_match_cb)
        
        filters_layout.addStretch()
        
        search_layout.addRow('Опции:', filters_layout)
        
        # Кнопки поиска
        buttons_layout = QHBoxLayout()
        
        self.search_btn = QPushButton('🔍 Найти')
        self.search_btn.setDefault(True)
        buttons_layout.addWidget(self.search_btn)
        
        self.clear_btn = QPushButton('🗑️ Очистить')
        buttons_layout.addWidget(self.clear_btn)
        
        buttons_layout.addStretch()
        
        search_layout.addRow(buttons_layout)
        
        layout.addWidget(search_group)
        
        # Результаты поиска
        results_group = QGroupBox('Результаты поиска')
        results_layout = QVBoxLayout(results_group)
        
        # Информация о результатах
        self.results_info = QLabel('Введите запрос и нажмите "Найти"')
        self.results_info.setStyleSheet('color: #666; font-style: italic;')
        results_layout.addWidget(self.results_info)
        
        # Таблица результатов
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            'Тип', 'ID', 'Основная информация', 'Дополнительно', 'Дата'
        ])
        
        # Настройка таблицы
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        
        self.results_table.setColumnWidth(0, 100)
        self.results_table.setColumnWidth(1, 80)
        self.results_table.setColumnWidth(4, 120)
        
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SingleSelection)
        
        results_layout.addWidget(self.results_table)
        
        layout.addWidget(results_group)
        
        # Кнопки действий
        actions_layout = QHBoxLayout()
        
        self.select_btn = QPushButton('✅ Выбрать')
        self.select_btn.setEnabled(False)
        actions_layout.addWidget(self.select_btn)
        
        self.view_btn = QPushButton('👁️ Просмотр')
        self.view_btn.setEnabled(False)
        actions_layout.addWidget(self.view_btn)
        
        actions_layout.addStretch()
        
        self.close_btn = QPushButton('Закрыть')
        actions_layout.addWidget(self.close_btn)
        
        layout.addLayout(actions_layout)
        
    def setup_connections(self):
        """Настройка соединений сигналов"""
        self.search_edit.returnPressed.connect(self.perform_search)
        self.search_btn.clicked.connect(self.perform_search)
        self.clear_btn.clicked.connect(self.clear_search)
        
        self.results_table.itemSelectionChanged.connect(self.on_selection_changed)
        self.results_table.itemDoubleClicked.connect(self.select_item)
        
        self.select_btn.clicked.connect(self.select_item)
        self.view_btn.clicked.connect(self.view_item)
        self.close_btn.clicked.connect(self.reject)
        
    def perform_search(self):
        """Выполнить поиск"""
        query = self.search_edit.text().strip()
        
        if not query:
            self.results_info.setText('Введите поисковый запрос')
            self.results_table.setRowCount(0)
            return
            
        search_type = self.search_type_combo.currentText()
        case_sensitive = self.case_sensitive_cb.isChecked()
        exact_match = self.exact_match_cb.isChecked()
        
        try:
            results = []
            
            # Выбираем методы поиска
            if search_type in ['Все категории', 'Клиенты']:
                results.extend(self.search_clients(query, case_sensitive, exact_match))
                
            if search_type in ['Все категории', 'Автомобили']:
                results.extend(self.search_cars(query, case_sensitive, exact_match))
                
            if search_type in ['Все категории', 'Заказы']:
                results.extend(self.search_orders(query, case_sensitive, exact_match))
                
            if search_type in ['Все категории', 'Услуги']:
                results.extend(self.search_services(query, case_sensitive, exact_match))
                
            if search_type in ['Все категории', 'Сотрудники']:
                results.extend(self.search_employees(query, case_sensitive, exact_match))
                
            # Отображаем результаты
            self.display_results(results)
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка поиска: {e}')
            
    def search_clients(self, query, case_sensitive, exact_match):
        """Поиск клиентов"""
        results = []
        
        # Формируем условия поиска
        if exact_match:
            if case_sensitive:
                conditions = [
                    Client.name == query,
                    Client.phone == query,
                    Client.email == query
                ]
            else:
                conditions = [
                    Client.name.ilike(query),
                    Client.phone.ilike(query),
                    Client.email.ilike(query)
                ]
        else:
            if case_sensitive:
                pattern = f'%{query}%'
                conditions = [
                    Client.name.like(pattern),
                    Client.phone.like(pattern),
                    Client.email.like(pattern),
                    Client.address.like(pattern)
                ]
            else:
                pattern = f'%{query}%'
                conditions = [
                    Client.name.ilike(pattern),
                    Client.phone.ilike(pattern),
                    Client.email.ilike(pattern),
                    Client.address.ilike(pattern)
                ]
        
        clients = self.db_session.query(Client).filter(or_(*conditions)).all()
        
        for client in clients:
            results.append({
                'type': 'Клиент',
                'id': client.id,
                'main_info': client.name,
                'additional': f'📞 {client.phone} | 📧 {client.email or ""}',
                'date': client.created_at.strftime('%d.%m.%Y') if hasattr(client, 'created_at') else '',
                'object': client
            })
            
        return results
        
    def search_cars(self, query, case_sensitive, exact_match):
        """Поиск автомобилей"""
        results = []
        
        # Формируем условия поиска
        if exact_match:
            if case_sensitive:
                conditions = [
                    Car.vin == query,
                    Car.license_plate == query,
                    Car.brand == query,
                    Car.model == query
                ]
            else:
                conditions = [
                    Car.vin.ilike(query),
                    Car.license_plate.ilike(query),
                    Car.brand.ilike(query),
                    Car.model.ilike(query)
                ]
        else:
            pattern = f'%{query}%'
            if case_sensitive:
                conditions = [
                    Car.vin.like(pattern),
                    Car.license_plate.like(pattern),
                    Car.brand.like(pattern),
                    Car.model.like(pattern)
                ]
            else:
                conditions = [
                    Car.vin.ilike(pattern),
                    Car.license_plate.ilike(pattern),
                    Car.brand.ilike(pattern),
                    Car.model.ilike(pattern)
                ]
        
        cars = self.db_session.query(Car).filter(or_(*conditions)).all()
        
        for car in cars:
            results.append({
                'type': 'Автомобиль',
                'id': car.id,
                'main_info': f'{car.brand} {car.model} ({car.year or ""})',
                'additional': f'🔢 {car.license_plate or ""} | VIN: {car.vin or ""}',
                'date': car.created_at.strftime('%d.%m.%Y') if hasattr(car, 'created_at') else '',
                'object': car
            })
            
        return results
        
    def search_orders(self, query, case_sensitive, exact_match):
        """Поиск заказов"""
        results = []
        
        # Формируем условия поиска
        if exact_match:
            if case_sensitive:
                conditions = [Order.order_number == query]
            else:
                conditions = [Order.order_number.ilike(query)]
        else:
            pattern = f'%{query}%'
            if case_sensitive:
                conditions = [
                    Order.order_number.like(pattern),
                    Order.notes.like(pattern)
                ]
            else:
                conditions = [
                    Order.order_number.ilike(pattern),
                    Order.notes.ilike(pattern)
                ]
        
        orders = self.db_session.query(Order).filter(or_(*conditions)).all()
        
        for order in orders:
            client_name = order.client.name if order.client else "Неизвестно"
            car_info = f"{order.car.brand} {order.car.model}" if order.car else "Неизвестно"
            
            results.append({
                'type': 'Заказ',
                'id': order.id,
                'main_info': f'№ {order.order_number} | {client_name}',
                'additional': f'🚗 {car_info} | 💰 {order.total_amount or 0:.2f} ₴',
                'date': order.date_received.strftime('%d.%m.%Y') if order.date_received else '',
                'object': order
            })
            
        return results
        
    def search_services(self, query, case_sensitive, exact_match):
        """Поиск услуг"""
        results = []
        
        # Формируем условия поиска
        if exact_match:
            if case_sensitive:
                conditions = [ServiceCatalog.name == query]
            else:
                conditions = [ServiceCatalog.name.ilike(query)]
        else:
            pattern = f'%{query}%'
            if case_sensitive:
                conditions = [
                    ServiceCatalog.name.like(pattern),
                    ServiceCatalog.description.like(pattern),
                    ServiceCatalog.synonyms.like(pattern)
                ]
            else:
                conditions = [
                    ServiceCatalog.name.ilike(pattern),
                    ServiceCatalog.description.ilike(pattern),
                    ServiceCatalog.synonyms.ilike(pattern)
                ]
        
        services = self.db_session.query(ServiceCatalog).filter(or_(*conditions)).all()
        
        for service in services:
            results.append({
                'type': 'Услуга',
                'id': service.id,
                'main_info': service.name,
                'additional': f'💰 {service.price:.2f} ₴ | {service.description or ""}',
                'date': service.created_at.strftime('%d.%m.%Y') if hasattr(service, 'created_at') else '',
                'object': service
            })
            
        return results
        
    def search_employees(self, query, case_sensitive, exact_match):
        """Поиск сотрудников"""
        results = []
        
        # Формируем условия поиска
        if exact_match:
            if case_sensitive:
                conditions = [
                    Employee.name == query,
                    Employee.phone == query,
                    Employee.email == query
                ]
            else:
                conditions = [
                    Employee.name.ilike(query),
                    Employee.phone.ilike(query),
                    Employee.email.ilike(query)
                ]
        else:
            pattern = f'%{query}%'
            if case_sensitive:
                conditions = [
                    Employee.name.like(pattern),
                    Employee.phone.like(pattern),
                    Employee.email.like(pattern),
                    Employee.position.like(pattern)
                ]
            else:
                conditions = [
                    Employee.name.ilike(pattern),
                    Employee.phone.ilike(pattern),
                    Employee.email.ilike(pattern),
                    Employee.position.ilike(pattern)
                ]
        
        employees = self.db_session.query(Employee).filter(or_(*conditions)).all()
        
        for employee in employees:
            results.append({
                'type': 'Сотрудник',
                'id': employee.id,
                'main_info': employee.name,
                'additional': f'📞 {employee.phone or ""} | 👔 {employee.position or ""}',
                'date': employee.created_at.strftime('%d.%m.%Y') if hasattr(employee, 'created_at') else '',
                'object': employee
            })
            
        return results
        
    def display_results(self, results):
        """Отображение результатов поиска"""
        self.results_table.setRowCount(len(results))
        
        if not results:
            self.results_info.setText('По вашему запросу ничего не найдено')
            return
            
        self.results_info.setText(f'Найдено результатов: {len(results)}')
        
        for row, result in enumerate(results):
            # Тип
            type_item = QTableWidgetItem(result['type'])
            self.results_table.setItem(row, 0, type_item)
            
            # ID
            id_item = QTableWidgetItem(str(result['id']))
            id_item.setTextAlignment(Qt.AlignCenter)
            self.results_table.setItem(row, 1, id_item)
            
            # Основная информация
            main_item = QTableWidgetItem(result['main_info'])
            self.results_table.setItem(row, 2, main_item)
            
            # Дополнительная информация
            additional_item = QTableWidgetItem(result['additional'])
            self.results_table.setItem(row, 3, additional_item)
            
            # Дата
            date_item = QTableWidgetItem(result['date'])
            date_item.setTextAlignment(Qt.AlignCenter)
            self.results_table.setItem(row, 4, date_item)
            
            # Сохраняем объект в первой ячейке
            type_item.setData(Qt.UserRole, result['object'])
            
    def clear_search(self):
        """Очистить поиск"""
        self.search_edit.clear()
        self.search_type_combo.setCurrentIndex(0)
        self.case_sensitive_cb.setChecked(False)
        self.exact_match_cb.setChecked(False)
        self.results_table.setRowCount(0)
        self.results_info.setText('Введите запрос и нажмите "Найти"')
        
    def on_selection_changed(self):
        """Обработка изменения выбора"""
        has_selection = bool(self.results_table.selectedItems())
        self.select_btn.setEnabled(has_selection)
        self.view_btn.setEnabled(has_selection)
        
    def select_item(self):
        """Выбрать элемент"""
        current_row = self.results_table.currentRow()
        if current_row >= 0:
            type_item = self.results_table.item(current_row, 0)
            if type_item:
                obj = type_item.data(Qt.UserRole)
                item_type = type_item.text()
                
                self.item_selected.emit(item_type, obj)
                self.accept()
                
    def view_item(self):
        """Просмотр элемента"""
        current_row = self.results_table.currentRow()
        if current_row >= 0:
            type_item = self.results_table.item(current_row, 0)
            if type_item:
                obj = type_item.data(Qt.UserRole)
                item_type = type_item.text()
                
                # Здесь можно добавить логику просмотра деталей
                QMessageBox.information(
                    self, 
                    'Просмотр', 
                    f'Просмотр деталей для {item_type} будет реализован в следующей версии'
                )
            