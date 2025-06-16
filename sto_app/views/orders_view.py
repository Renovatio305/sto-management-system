# sto_app/views/orders_view.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableView, 
                              QToolBar, QLineEdit, QComboBox, QPushButton, QLabel,
                              QHeaderView, QMenu, QMessageBox, QSplitter, QFrame,
                              QGroupBox, QDateEdit, QCheckBox)
from PySide6.QtCore import Qt, Signal, QAbstractTableModel, QModelIndex, QSortFilterProxyModel, QDate
from PySide6.QtGui import QAction, QIcon, QFont, QColor, QPalette
from sto_app.dialogs.order_details_dialog import OrderDetailsDialog
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc
from datetime import datetime, timedelta
import logging

from shared_models.common_models import Client, Car
from sto_app.models_sto import Order, OrderStatus
from sto_app.dialogs.order_details_dialog import OrderDetailsDialog


logger = logging.getLogger(__name__)


class OrdersTableModel(QAbstractTableModel):
    """Модель данных для таблицы заказов"""
    
    def __init__(self, db_session: Session):
        super().__init__()
        self.db_session = db_session
        self.orders = []
        self.headers = [
            '№ заказа', 'Дата приёма', 'Клиент', 'Автомобиль', 
            'VIN', 'Статус', 'Сумма', 'Остаток', 'Ответственный'
        ]
        
    def rowCount(self, parent=QModelIndex()):
        return len(self.orders)
        
    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)
        
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None
        
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self.orders):
            return None
            
        order = self.orders[index.row()]
        col = index.column()
        
        if role == Qt.DisplayRole:
            if col == 0:  # № заказа
                return order.order_number
            elif col == 1:  # Дата приёма
                return order.date_received.strftime('%d.%m.%Y') if order.date_received else ''
            elif col == 2:  # Клиент
                return order.client.name if order.client else ''
            elif col == 3:  # Автомобиль
                return order.car.full_name if order.car else ''
            elif col == 4:  # VIN
                return order.car.vin if order.car else ''
            elif col == 5:  # Статус
                return order.status.value if order.status else ''
            elif col == 6:  # Сумма
                return f"{order.total_amount:.2f} ₴" if order.total_amount else '0.00 ₴'
            elif col == 7:  # Остаток
                return f"{order.balance_due:.2f} ₴" if order.balance_due else '0.00 ₴'
            elif col == 8:  # Ответственный
                return order.responsible_person.name if order.responsible_person else ''

        elif role == Qt.UserRole:
            # Сохраняем ID заказа для доступа из views
            return order.id      
                
        elif role == Qt.BackgroundRole:
            # Цветовая индикация статусов
            if col == 5:  # Колонка статуса
                if order.status == OrderStatus.DRAFT:
                    return QColor(255, 248, 220)  # Светло-жёлтый
                elif order.status == OrderStatus.IN_WORK:
                    return QColor(173, 216, 230)  # Светло-голубой
                elif order.status == OrderStatus.WAITING_PAYMENT:
                    return QColor(255, 218, 185)  # Светло-оранжевый
                elif order.status == OrderStatus.COMPLETED:
                    return QColor(144, 238, 144)  # Светло-зелёный
                elif order.status == OrderStatus.CANCELLED:
                    return QColor(255, 182, 193)  # Светло-красный
                    
        elif role == Qt.TextAlignmentRole:
            if col in [6, 7]:  # Суммы
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter
            
        elif role == Qt.FontRole:
            if col == 0:  # № заказа жирным
                font = QFont()
                font.setBold(True)
                return font
                
        return None
        
    def get_order(self, index):
        """Получить заказ по индексу"""
        if 0 <= index < len(self.orders):
            return self.orders[index]
        return None
        
    def refresh_data(self, filters=None):
        """Обновить данные с применением фильтров"""
        self.beginResetModel()
        
        try:
            query = self.db_session.query(Order).options(
                joinedload(Order.client),
                joinedload(Order.car),
                joinedload(Order.responsible_person)
            )
            
            # Применяем фильтры
            if filters:
                if filters.get('status') and filters['status'] != 'Все':
                    query = query.filter(Order.status == OrderStatus(filters['status']))
                    
                if filters.get('client_search'):
                    search_term = f"%{filters['client_search']}%"
                    query = query.join(Client).filter(Client.name.ilike(search_term))
                    
                if filters.get('vin_search'):
                    search_term = f"%{filters['vin_search']}%"
                    query = query.join(Car).filter(Car.vin.ilike(search_term))
                    
                if filters.get('date_from'):
                    query = query.filter(Order.date_received >= filters['date_from'])
                    
                if filters.get('date_to'):
                    query = query.filter(Order.date_received <= filters['date_to'])
                    
                if filters.get('only_unpaid'):
                    query = query.filter(Order.total_amount > Order.prepayment + Order.additional_payment)
            
            self.orders = query.order_by(desc(Order.date_received)).all()
            
        except Exception as e:
            logger.error(f"Ошибка загрузки заказов: {e}")
            self.orders = []
            
        self.endResetModel()


class OrdersView(QWidget):
    """Представление списка заказов"""
    
    status_message = Signal(str, int)
    order_selected = Signal(int)
    
    def __init__(self, db_session: Session):
        super().__init__()
        self.db_session = db_session
        self.setup_ui()
        self.load_orders()
        
    def setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Заголовок
        title_label = QLabel('📋 Управление заказами')
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Сплиттер для разделения фильтров и таблицы
        splitter = QSplitter(Qt.Vertical)
        
        # Панель фильтров
        filters_frame = self.create_filters_panel()
        splitter.addWidget(filters_frame)
        
        # Таблица заказов
        table_frame = self.create_table_panel()
        splitter.addWidget(table_frame)
        
        # Устанавливаем пропорции: фильтры - 25%, таблица - 75%
        splitter.setSizes([200, 600])
        
        layout.addWidget(splitter)
        
        # Панель действий
        actions_layout = self.create_actions_panel()
        layout.addLayout(actions_layout)
        
    def create_filters_panel(self):
        """Создание панели фильтров"""
        filters_frame = QFrame()
        filters_frame.setFrameStyle(QFrame.StyledPanel)
        filters_layout = QVBoxLayout(filters_frame)
        
        # Группа быстрых фильтров
        quick_filters_group = QGroupBox('🔍 Быстрые фильтры')
        quick_layout = QHBoxLayout(quick_filters_group)
        
        # Фильтр по статусу
        quick_layout.addWidget(QLabel('Статус:'))
        self.status_filter = QComboBox()
        self.status_filter.addItems(['Все', 'Чернетка', 'В роботі', 'Очікує оплату', 'Завершено', 'Скасовано'])
        self.status_filter.currentTextChanged.connect(self.apply_filters)
        quick_layout.addWidget(self.status_filter)
        
        # Только неоплаченные
        self.unpaid_only_cb = QCheckBox('Только с долгом')
        self.unpaid_only_cb.toggled.connect(self.apply_filters)
        quick_layout.addWidget(self.unpaid_only_cb)
        
        quick_layout.addStretch()
        filters_layout.addWidget(quick_filters_group)
        
        # Группа поиска
        search_group = QGroupBox('🔎 Поиск')
        search_layout = QVBoxLayout(search_group)
        
        # Поиск по клиенту
        client_layout = QHBoxLayout()
        client_layout.addWidget(QLabel('Клиент:'))
        self.client_search = QLineEdit()
        self.client_search.setPlaceholderText('Введите имя клиента...')
        self.client_search.textChanged.connect(self.apply_filters)
        client_layout.addWidget(self.client_search)
        search_layout.addLayout(client_layout)
        
        # Поиск по VIN
        vin_layout = QHBoxLayout()
        vin_layout.addWidget(QLabel('VIN/Номер:'))
        self.vin_search = QLineEdit()
        self.vin_search.setPlaceholderText('Введите VIN или гос. номер...')
        self.vin_search.textChanged.connect(self.apply_filters)
        vin_layout.addWidget(self.vin_search)
        search_layout.addLayout(vin_layout)
        
        filters_layout.addWidget(search_group)
        
        # Группа фильтра по датам
        dates_group = QGroupBox('📅 Период')
        dates_layout = QHBoxLayout(dates_group)
        
        dates_layout.addWidget(QLabel('С:'))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_from.dateChanged.connect(self.apply_filters)
        dates_layout.addWidget(self.date_from)
        
        dates_layout.addWidget(QLabel('По:'))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.dateChanged.connect(self.apply_filters)
        dates_layout.addWidget(self.date_to)
        
        # Кнопка сброса фильтров
        reset_btn = QPushButton('🗑️ Сбросить')
        reset_btn.clicked.connect(self.reset_filters)
        dates_layout.addWidget(reset_btn)
        
        filters_layout.addWidget(dates_group)
        filters_layout.addStretch()
        
        return filters_frame
        
    def create_table_panel(self):
        """Создание панели с таблицей"""
        table_frame = QFrame()
        table_layout = QVBoxLayout(table_frame)
        
        # Заголовок таблицы
        table_header = QHBoxLayout()
        table_title = QLabel('📊 Список заказов')
        table_title_font = QFont()
        table_title_font.setPointSize(12)
        table_title_font.setBold(True)
        table_title.setFont(table_title_font)
        table_header.addWidget(table_title)
        
        # Счётчик записей
        self.records_label = QLabel('Записей: 0')
        table_header.addWidget(self.records_label)
        table_header.addStretch()
        
        # Кнопка обновления
        refresh_btn = QPushButton('🔄 Обновить')
        refresh_btn.clicked.connect(self.load_orders)
        table_header.addWidget(refresh_btn)
        
        table_layout.addLayout(table_header)
        
        # Таблица заказов
        self.orders_table = QTableView()
        self.orders_model = OrdersTableModel(self.db_session)
        self.orders_table.setModel(self.orders_model)
        
        # Настройка таблицы
        self.orders_table.setSelectionBehavior(QTableView.SelectRows)
        self.orders_table.setAlternatingRowColors(True)
        self.orders_table.setSortingEnabled(True)
        self.orders_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.orders_table.customContextMenuRequested.connect(self.show_context_menu)
        self.orders_table.doubleClicked.connect(self.edit_order)
        
        # Настройка заголовков
        header = self.orders_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        
        # Установка ширины колонок
        self.orders_table.setColumnWidth(0, 100)  # № заказа
        self.orders_table.setColumnWidth(1, 100)  # Дата
        self.orders_table.setColumnWidth(2, 200)  # Клиент
        self.orders_table.setColumnWidth(3, 150)  # Автомобиль
        self.orders_table.setColumnWidth(4, 120)  # VIN
        self.orders_table.setColumnWidth(5, 120)  # Статус
        self.orders_table.setColumnWidth(6, 100)  # Сумма
        self.orders_table.setColumnWidth(7, 100)  # Остаток
        
        table_layout.addWidget(self.orders_table)
        
        return table_frame
        
    def create_actions_panel(self):
        """Создание панели действий"""
        actions_layout = QHBoxLayout()
        
        # Основные действия
        new_order_btn = QPushButton('➕ Новый заказ')
        new_order_btn.setProperty('accent', True)
        new_order_btn.clicked.connect(self.new_order)
        actions_layout.addWidget(new_order_btn)
        
        edit_order_btn = QPushButton('✏️ Редактировать')
        edit_order_btn.clicked.connect(self.edit_order)
        actions_layout.addWidget(edit_order_btn)
        
        view_order_btn = QPushButton('👁️ Просмотр')
        view_order_btn.clicked.connect(self.view_order_details)
        actions_layout.addWidget(view_order_btn)
        
        actions_layout.addStretch()
        
        # Дополнительные действия
        print_btn = QPushButton('🖨️ Печать')
        print_btn.clicked.connect(self.print_order)
        actions_layout.addWidget(print_btn)
        
        export_btn = QPushButton('📄 Экспорт')
        export_btn.clicked.connect(self.export_orders)
        actions_layout.addWidget(export_btn)
        
        return actions_layout
        
    def show_context_menu(self, position):
        """Показать контекстное меню"""
        if not self.orders_table.indexAt(position).isValid():
            return
            
        menu = QMenu(self)
        
        view_action = QAction(QIcon('resources/icons/view.png'), 'Просмотр', self)
        view_action.triggered.connect(self.view_order_details)
        menu.addAction(view_action)
        
        edit_action = QAction(QIcon('resources/icons/edit.png'), 'Редактировать', self)
        edit_action.triggered.connect(self.edit_order)
        menu.addAction(edit_action)
        
        menu.addSeparator()
        
        print_action = QAction(QIcon('resources/icons/print.png'), 'Печать наряда', self)
        print_action.triggered.connect(self.print_order)
        menu.addAction(print_action)
        
        pdf_action = QAction(QIcon('resources/icons/pdf.png'), 'Экспорт в PDF', self)
        pdf_action.triggered.connect(self.export_pdf)
        menu.addAction(pdf_action)
        
        menu.addSeparator()
        
        copy_action = QAction(QIcon('resources/icons/copy.png'), 'Копировать данные', self)
        copy_action.triggered.connect(self.copy_order_data)
        menu.addAction(copy_action)
        
        # Показать статус зависимые действия
        selected_order = self.get_selected_order()
        if selected_order:
            menu.addSeparator()
            
            if selected_order.status == OrderStatus.DRAFT:
                start_work_action = QAction('▶️ Начать работу', self)
                start_work_action.triggered.connect(self.start_work)
                menu.addAction(start_work_action)
                
            elif selected_order.status == OrderStatus.IN_WORK:
                complete_action = QAction('✅ Завершить работу', self)
                complete_action.triggered.connect(self.complete_work)
                menu.addAction(complete_action)
                
            elif selected_order.status in [OrderStatus.WAITING_PAYMENT, OrderStatus.COMPLETED]:
                payment_action = QAction('💰 Добавить оплату', self)
                payment_action.triggered.connect(self.add_payment)
                menu.addAction(payment_action)
        
        menu.exec(self.orders_table.mapToGlobal(position))
        
    def get_selected_order(self):
        """Получить выбранный заказ"""
        selection = self.orders_table.selectionModel()
        if not selection.hasSelection():
            return None
            
        row = selection.currentIndex().row()
        return self.orders_model.get_order(row)
        
    def apply_filters(self):
        """Применить фильтры"""
        filters = {
            'status': self.status_filter.currentText(),
            'client_search': self.client_search.text().strip(),
            'vin_search': self.vin_search.text().strip(),
            'date_from': self.date_from.date().toPython(),
            'date_to': self.date_to.date().toPython(),
            'only_unpaid': self.unpaid_only_cb.isChecked()
        }
        
        self.orders_model.refresh_data(filters)
        self.update_records_count()
        
    def reset_filters(self):
        """Сбросить все фильтры"""
        self.status_filter.setCurrentIndex(0)
        self.client_search.clear()
        self.vin_search.clear()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_to.setDate(QDate.currentDate())
        self.unpaid_only_cb.setChecked(False)
        self.apply_filters()
        
    def update_records_count(self):
        """Обновить счётчик записей"""
        count = self.orders_model.rowCount()
        self.records_label.setText(f'Записей: {count}')
        
    def load_orders(self):
        """Загрузить заказы"""
        self.apply_filters()
        self.status_message.emit('Заказы загружены', 2000)
        
    def refresh_orders(self):
        """Обновить список заказов"""
        self.load_orders()
        
    def new_order(self):
        """Создать новый заказ"""
        # Сигнал будет перехвачен главным окном для переключения на вкладку
        self.status_message.emit('Переход к созданию нового заказа', 1000)
        
    def view_order_details(self):
        """Просмотр полных деталей выбранного заказа"""
        current_row = self.orders_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "Информация", "Выберите заказ для просмотра")
            return
        
        try:
            order_id = self.get_order_id_from_row(current_row)
            
            if not order_id:
                QMessageBox.warning(self, "Предупреждение", "Не удалось определить ID заказа")
                return
                
            dialog = OrderDetailsDialog(self, order_id=order_id)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть детали заказа: {e}")
        
    def edit_order(self):
        """Редактирование заказа"""
        current_row = self.orders_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, 'Информация', 'Выберите заказ для редактирования')
            return
        
        try:
            order_id = self.get_order_id_from_row(current_row)
            if not order_id:
                QMessageBox.warning(self, "Предупреждение", "Не удалось определить ID заказа")
                return
                
            dialog = OrderDetailsDialog(self, order_id=order_id, read_only=False)
            
    def start_work(self):
        """Начать работу по заказу"""
        order = self.get_selected_order()
        if not order or order.status != OrderStatus.DRAFT:
            return
            
        try:
            order.status = OrderStatus.IN_WORK
            self.db_session.commit()
            self.refresh_orders()
            self.status_message.emit(f'Заказ {order.order_number} переведён в работу', 3000)
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Ошибка изменения статуса: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Не удалось изменить статус: {e}')
            
    def complete_work(self):
        """Завершить работу"""
        order = self.get_selected_order()
        if not order or order.status != OrderStatus.IN_WORK:
            return
            
        try:
            if order.balance_due > 0:
                order.status = OrderStatus.WAITING_PAYMENT
                message = f'Заказ {order.order_number} ожидает доплату'
            else:
                order.status = OrderStatus.COMPLETED
                message = f'Заказ {order.order_number} завершён'
                
            self.db_session.commit()
            self.refresh_orders()
            self.status_message.emit(message, 3000)
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Ошибка завершения работ: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Не удалось завершить работы: {e}')
            
    def add_payment(self):
        """Добавить оплату"""
        order = self.get_selected_order()
        if not order:
            return
            
        # Здесь будет диалог для добавления оплаты
        from sto_app.dialogs.payment_dialog import PaymentDialog
        dialog = PaymentDialog(self, order)
        if dialog.exec():
            self.refresh_orders()
            
    def print_order(self):
        """Печать заказа"""
        order = self.get_selected_order()
        if not order:
            QMessageBox.information(self, 'Информация', 'Выберите заказ для печати')
            return
            
        # Здесь будет система печати
        self.status_message.emit('Функция печати будет реализована', 2000)
        
    def export_pdf(self):
        """Экспорт в PDF"""
        order = self.get_selected_order()
        if not order:
            QMessageBox.information(self, 'Информация', 'Выберите заказ для экспорта')
            return
            
        # Здесь будет экспорт в PDF
        self.status_message.emit('Функция экспорта в PDF будет реализована', 2000)
        
    def export_orders(self):
        """Экспорт списка заказов"""
        # Здесь будет экспорт в Excel
        self.status_message.emit('Функция экспорта в Excel будет реализована', 2000)
        
    def copy_order_data(self):
        """Копировать данные заказа"""
        order = self.get_selected_order()
        if not order:
            return

    def get_order_id_from_row(self, row):
        """Получить ID заказа из строки таблицы"""
        try:
            # Пытаемся получить ID из UserRole
            for col in range(self.orders_table.columnCount()):
                item = self.orders_table.item(row, col)
                if item and item.data(Qt.UserRole):
                    return int(item.data(Qt.UserRole))
            
            # Если не найден, ищем по номеру заказа
            order_number_item = self.orders_table.item(row, 0)
            if order_number_item:
                order_number = order_number_item.text()
                from sqlalchemy import select
                from sto_app.models_sto import Order
                
                stmt = select(Order.id).where(Order.order_number == order_number)
                result = self.db_session.execute(stmt)
                return result.scalar_one_or_none()
                
        except Exception as e:
            logger.error(f"Ошибка получения ID заказа: {e}")
            return None
            
        # Формируем строку с данными заказа
        data = f"""Заказ: {order.order_number}
Дата: {order.date_received.strftime('%d.%m.%Y') if order.date_received else ''}
Клиент: {order.client.name if order.client else ''}
Автомобиль: {order.car.full_name if order.car else ''}
VIN: {order.car.vin if order.car else ''}
Статус: {order.status.value if order.status else ''}
Сумма: {order.total_amount:.2f} ₴
Остаток: {order.balance_due:.2f} ₴"""
        
        from PySide6.QtGui import QClipboard
        clipboard = QClipboard()
        clipboard.setText(data)
        self.status_message.emit('Данные заказа скопированы в буфер обмена', 2000)
