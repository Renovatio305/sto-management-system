# sto_app/dialogs/calendar_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QCalendarWidget,
                              QPushButton, QLabel, QListWidget, QListWidgetItem,
                              QGroupBox, QComboBox, QDateEdit, QTimeEdit,
                              QTextEdit, QFormLayout, QMessageBox, QSplitter,
                              QWidget, QFrame)
from PySide6.QtCore import Qt, QDate, QTime, QDateTime, Signal
from PySide6.QtGui import QFont, QTextCharFormat, QColor
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from sto_app.models_sto import Order, OrderStatus


class CalendarDialog(QDialog):
    """Диалог календаря заказов"""
    
    # Сигнал для выбора заказа
    order_selected = Signal(object)
    
    def __init__(self, db_session: Session, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        
        self.setWindowTitle('📅 Календарь заказов')
        self.setMinimumSize(900, 700)
        self.resize(1100, 800)
        
        self.setup_ui()
        self.setup_connections()
        self.load_orders()
        
    def setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Заголовок
        title_label = QLabel('📅 Календарь заказов')
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Сплиттер для календаря и списка заказов
        splitter = QSplitter(Qt.Horizontal)
        
        # Левая панель - календарь
        calendar_panel = self.create_calendar_panel()
        splitter.addWidget(calendar_panel)
        
        # Правая панель - заказы выбранного дня
        orders_panel = self.create_orders_panel()
        splitter.addWidget(orders_panel)
        
        # Устанавливаем пропорции
        splitter.setSizes([400, 500])
        
        layout.addWidget(splitter)
        
        # Кнопки действий
        actions_layout = QHBoxLayout()
        
        self.new_order_btn = QPushButton('➕ Новый заказ')
        actions_layout.addWidget(self.new_order_btn)
        
        self.edit_order_btn = QPushButton('✏️ Редактировать')
        self.edit_order_btn.setEnabled(False)
        actions_layout.addWidget(self.edit_order_btn)
        
        self.view_order_btn = QPushButton('👁️ Просмотр')
        self.view_order_btn.setEnabled(False)
        actions_layout.addWidget(self.view_order_btn)
        
        actions_layout.addStretch()
        
        self.refresh_btn = QPushButton('🔄 Обновить')
        actions_layout.addWidget(self.refresh_btn)
        
        self.close_btn = QPushButton('Закрыть')
        actions_layout.addWidget(self.close_btn)
        
        layout.addLayout(actions_layout)
        
    def create_calendar_panel(self):
        """Создание панели календаря"""
        panel = QGroupBox('Календарь')
        layout = QVBoxLayout(panel)
        
        # Фильтры
        filters_layout = QFormLayout()
        
        self.status_filter = QComboBox()
        self.status_filter.addItem('Все статусы', None)
        for status in OrderStatus:
            self.status_filter.addItem(status.value, status)
        filters_layout.addRow('Статус:', self.status_filter)
        
        self.period_filter = QComboBox()
        self.period_filter.addItems([
            'Текущий месяц',
            'Следующий месяц',
            'Весь год',
            'Пользовательский период'
        ])
        filters_layout.addRow('Период:', self.period_filter)
        
        layout.addLayout(filters_layout)
        
        # Календарь
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setMinimumDate(QDate(2020, 1, 1))
        self.calendar.setMaximumDate(QDate(2030, 12, 31))
        self.calendar.setSelectedDate(QDate.currentDate())
        
        layout.addWidget(self.calendar)
        
        # Легенда
        legend_layout = QHBoxLayout()
        
        # Статусы с цветами
        statuses_info = [
            ('Черновик', '#FFA726'),
            ('В работе', '#42A5F5'),
            ('Ожидает оплату', '#FF7043'),
            ('Завершен', '#66BB6A'),
            ('Отменен', '#EF5350')
        ]
        
        for status, color in statuses_info:
            legend_item = QLabel(f'⬤ {status}')
            legend_item.setStyleSheet(f'color: {color}; font-weight: bold;')
            legend_layout.addWidget(legend_item)
            
        legend_layout.addStretch()
        layout.addLayout(legend_layout)
        
        return panel
        
    def create_orders_panel(self):
        """Создание панели заказов"""
        panel = QGroupBox('Заказы выбранного дня')
        layout = QVBoxLayout(panel)
        
        # Информация о выбранном дне
        self.selected_date_label = QLabel()
        self.update_selected_date_label()
        date_font = QFont()
        date_font.setBold(True)
        self.selected_date_label.setFont(date_font)
        layout.addWidget(self.selected_date_label)
        
        # Список заказов
        self.orders_list = QListWidget()
        self.orders_list.setAlternatingRowColors(True)
        layout.addWidget(self.orders_list)
        
        # Детали выбранного заказа
        details_group = QGroupBox('Детали заказа')
        details_layout = QVBoxLayout(details_group)
        
        self.order_details = QTextEdit()
        self.order_details.setReadOnly(True)
        self.order_details.setMaximumHeight(150)
        self.order_details.setPlaceholderText('Выберите заказ для просмотра деталей')
        details_layout.addWidget(self.order_details)
        
        layout.addWidget(details_group)
        
        return panel
        
    def setup_connections(self):
        """Настройка соединений сигналов"""
        self.calendar.selectionChanged.connect(self.on_date_selected)
        self.calendar.clicked.connect(self.on_date_clicked)
        
        self.status_filter.currentTextChanged.connect(self.on_filter_changed)
        self.period_filter.currentTextChanged.connect(self.on_period_changed)
        
        self.orders_list.itemSelectionChanged.connect(self.on_order_selected)
        self.orders_list.itemDoubleClicked.connect(self.view_order)
        
        self.new_order_btn.clicked.connect(self.new_order)
        self.edit_order_btn.clicked.connect(self.edit_order)
        self.view_order_btn.clicked.connect(self.view_order)
        self.refresh_btn.clicked.connect(self.load_orders)
        self.close_btn.clicked.connect(self.accept)
        
    def load_orders(self):
        """Загрузка заказов"""
        try:
            # Получаем все заказы
            orders = self.db_session.query(Order).all()
            
            # Группируем по датам
            self.orders_by_date = {}
            
            for order in orders:
                if order.date_received:
                    date_key = order.date_received.date()
                    if date_key not in self.orders_by_date:
                        self.orders_by_date[date_key] = []
                    self.orders_by_date[date_key].append(order)
                    
            # Обновляем календарь
            self.update_calendar_highlighting()
            
            # Обновляем список заказов для выбранной даты
            self.update_orders_list()
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка загрузки заказов: {e}')
            
    def update_calendar_highlighting(self):
        """Обновление подсветки календаря"""
        # Очищаем предыдущую подсветку
        default_format = QTextCharFormat()
        self.calendar.setDateTextFormat(QDate(), default_format)
        
        # Подсвечиваем даты с заказами
        for date, orders in self.orders_by_date.items():
            qdate = QDate(date.year, date.month, date.day)
            
            # Определяем цвет по статусам заказов
            format = QTextCharFormat()
            format.setBackground(QColor(self.get_date_color(orders)))
            format.setForeground(QColor('#ffffff'))
            format.setFontWeight(75)  # Bold
            
            self.calendar.setDateTextFormat(qdate, format)
            
    def get_date_color(self, orders):
        """Получить цвет для даты на основе статусов заказов"""
        if not orders:
            return '#ffffff'
            
        # Приоритет статусов
        status_colors = {
            OrderStatus.CANCELLED: '#EF5350',     # Красный - отменен
            OrderStatus.WAITING_PAYMENT: '#FF7043', # Оранжевый - ожидает оплату
            OrderStatus.IN_WORK: '#42A5F5',       # Синий - в работе
            OrderStatus.DRAFT: '#FFA726',         # Оранжевый - черновик
            OrderStatus.COMPLETED: '#66BB6A'      # Зеленый - завершен
        }
        
        # Находим статус с наивысшим приоритетом
        for status in [OrderStatus.CANCELLED, OrderStatus.WAITING_PAYMENT, 
                      OrderStatus.IN_WORK, OrderStatus.DRAFT, OrderStatus.COMPLETED]:
            if any(order.status == status for order in orders):
                return status_colors.get(status, '#42A5F5')
                
        return '#42A5F5'  # По умолчанию синий
        
    def on_date_selected(self):
        """Обработка выбора даты"""
        self.update_selected_date_label()
        self.update_orders_list()
        
    def on_date_clicked(self, date):
        """Обработка клика по дате"""
        self.update_orders_list()
        
    def update_selected_date_label(self):
        """Обновление метки выбранной даты"""
        selected_date = self.calendar.selectedDate()
        date_str = selected_date.toString('dd.MM.yyyy (dddd)')
        
        # Подсчитываем количество заказов
        python_date = selected_date.toPython()
        orders_count = len(self.orders_by_date.get(python_date, []))
        
        self.selected_date_label.setText(f'📅 {date_str} | Заказов: {orders_count}')
        
    def update_orders_list(self):
        """Обновление списка заказов"""
        self.orders_list.clear()
        self.order_details.clear()
        
        selected_date = self.calendar.selectedDate().toPython()
        orders = self.orders_by_date.get(selected_date, [])
        
        # Фильтрация по статусу
        status_filter = self.status_filter.currentData()
        if status_filter:
            orders = [order for order in orders if order.status == status_filter]
            
        if not orders:
            item = QListWidgetItem('Нет заказов на выбранную дату')
            item.setFlags(Qt.NoItemFlags)
            self.orders_list.addItem(item)
            return
            
        for order in orders:
            # Формируем текст элемента
            client_name = order.client.name if order.client else 'Неизвестный клиент'
            car_info = f"{order.car.brand} {order.car.model}" if order.car else 'Неизвестный автомобиль'
            status_text = order.status.value if order.status else 'Неизвестен'
            
            item_text = f"№ {order.order_number} | {client_name} | {car_info} | {status_text}"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, order)
            
            # Цвет по статусу
            if order.status == OrderStatus.COMPLETED:
                item.setBackground(QColor('#E8F5E8'))
            elif order.status == OrderStatus.IN_WORK:
                item.setBackground(QColor('#E3F2FD'))
            elif order.status == OrderStatus.WAITING_PAYMENT:
                item.setBackground(QColor('#FFF3E0'))
            elif order.status == OrderStatus.CANCELLED:
                item.setBackground(QColor('#FFEBEE'))
            elif order.status == OrderStatus.DRAFT:
                item.setBackground(QColor('#FFF8E1'))
                
            self.orders_list.addItem(item)
            
    def on_filter_changed(self):
        """Обработка изменения фильтра"""
        self.update_orders_list()
        
    def on_period_changed(self):
        """Обработка изменения периода"""
        period = self.period_filter.currentText()
        today = QDate.currentDate()
        
        if period == 'Текущий месяц':
            self.calendar.setSelectedDate(today)
        elif period == 'Следующий месяц':
            next_month = today.addMonths(1)
            self.calendar.setSelectedDate(next_month)
        elif period == 'Весь год':
            # Переход к началу года
            year_start = QDate(today.year(), 1, 1)
            self.calendar.setSelectedDate(year_start)
            
    def on_order_selected(self):
        """Обработка выбора заказа"""
        selected_items = self.orders_list.selectedItems()
        has_selection = bool(selected_items)
        
        self.edit_order_btn.setEnabled(has_selection)
        self.view_order_btn.setEnabled(has_selection)
        
        if selected_items:
            order = selected_items[0].data(Qt.UserRole)
            if order:
                self.show_order_details(order)
        else:
            self.order_details.clear()
            
    def show_order_details(self, order):
        """Показать детали заказа"""
        details = f"""
<h3>📋 Заказ № {order.order_number}</h3>

<p><b>👤 Клиент:</b> {order.client.name if order.client else 'Неизвестен'}</p>
<p><b>🚗 Автомобиль:</b> {order.car.brand} {order.car.model} ({order.car.year or ''}) если order.car else 'Неизвестен'}</p>
<p><b>📅 Дата приема:</b> {order.date_received.strftime('%d.%m.%Y %H:%M') if order.date_received else 'Не указана'}</p>
<p><b>📅 Дата выдачи:</b> {order.date_delivery.strftime('%d.%m.%Y %H:%M') if order.date_delivery else 'Не указана'}</p>
<p><b>📊 Статус:</b> {order.status.value if order.status else 'Неизвестен'}</p>
<p><b>💰 Сумма:</b> {order.total_amount or 0:.2f} ₴</p>

{f'<p><b>📝 Примечания:</b> {order.notes}</p>' if order.notes else ''}
        """
        
        self.order_details.setHtml(details)
        
    def new_order(self):
        """Создать новый заказ"""
        # Передаем выбранную дату
        selected_date = self.calendar.selectedDate().toPython()
        # Здесь будет интеграция с формой нового заказа
        QMessageBox.information(
            self, 
            'Новый заказ', 
            f'Создание нового заказа на {selected_date.strftime("%d.%m.%Y")}\n'
            'Интеграция с формой заказа будет добавлена'
        )
        
    def edit_order(self):
        """Редактировать заказ"""
        selected_items = self.orders_list.selectedItems()
        if selected_items:
            order = selected_items[0].data(Qt.UserRole)
            if order:
                self.order_selected.emit(order)
                self.accept()
                
    def view_order(self):
        """Просмотр заказа"""
        selected_items = self.orders_list.selectedItems()
        if selected_items:
            order = selected_items[0].data(Qt.UserRole)
            if order:
                # Здесь будет открытие детального просмотра заказа
                QMessageBox.information(
                    self,
                    'Просмотр заказа',
                    f'Детальный просмотр заказа № {order.order_number}\n'
                    'Функция будет реализована в следующей версии'
                )