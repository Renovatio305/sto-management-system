"""
Диалог просмотра полных деталей заказа с возможностью печати.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget, 
    QTableWidgetItem, QLabel, QPushButton, QGroupBox, QFormLayout,
    QTextEdit, QHeaderView, QAbstractItemView, QMessageBox, QWidget,
    QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sto_app.models_sto import Order, OrderService, OrderPart
from shared_models.common_models import Client, Car, Employee
from decimal import Decimal
import logging


class OrderDetailsDialog(QDialog):
    """Диалог просмотра полных деталей заказа"""
    
    def __init__(self, parent=None, order_id: int = None):
        super().__init__(parent)
        self.order_id = order_id
        self.db_session = parent.db_session if parent else None
        self.order = None
        
        self.setWindowTitle("Детали заказа")
        self.setModal(True)
        self.setMinimumSize(800, 700)
        self.resize(1000, 800)
        
        self.logger = logging.getLogger(__name__)
        
        if not self.order_id or not self.db_session:
            QMessageBox.critical(self, "Ошибка", "Не указан ID заказа или сессия БД")
            return
            
        self._load_order_data()
        if self.order:
            self._setup_ui()
            self._populate_data()
        
        if parent:
            self._center_on_parent(parent)
    
    def _load_order_data(self):
        """Загрузка данных заказа из БД"""
        try:
            # Загружаем заказ с связанными данными
            stmt = select(Order).where(Order.id == self.order_id)
            result = self.db_session.execute(stmt)
            self.order = result.scalar_one_or_none()
            
            if not self.order:
                QMessageBox.warning(self, "Предупреждение", "Заказ не найден")
                return
                
            self.logger.info(f"Загружен заказ #{self.order.id}")
            
        except SQLAlchemyError as e:
            self.logger.error(f"Ошибка загрузки заказа: {e}")
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось загрузить заказ: {e}")
    
    def _setup_ui(self):
        """Создание пользовательского интерфейса"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        header_layout = QHBoxLayout()
        
        # Информация о заказе в заголовке
        title_label = QLabel(f"Заказ №{self.order.order_number}")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Статус заказа
        status_label = QLabel(f"Статус: {self.order.status}")
        status_font = QFont()
        status_font.setPointSize(12)
        status_font.setBold(True)
        status_label.setFont(status_font)
        
        # Цвет статуса
        if self.order.status == 'completed':
            status_label.setStyleSheet("color: green;")
        elif self.order.status == 'in_progress':
            status_label.setStyleSheet("color: orange;")
        elif self.order.status == 'draft':
            status_label.setStyleSheet("color: gray;")
        else:
            status_label.setStyleSheet("color: blue;")
            
        header_layout.addWidget(status_label)
        
        layout.addLayout(header_layout)
        
        # Разделительная линия
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # Табы
        self.tab_widget = QTabWidget()
        
        # Вкладка "Общая информация"
        self._create_general_tab()
        
        # Вкладка "Услуги"
        self._create_services_tab()
        
        # Вкладка "Запчасти"
        self._create_parts_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Итоговая сумма
        self._create_totals_section(layout)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        print_btn = QPushButton("📄 Печать")
        print_btn.clicked.connect(self.print_order)
        buttons_layout.addWidget(print_btn)
        
        buttons_layout.addStretch()
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def _create_general_tab(self):
        """Создание вкладки общей информации"""
        general_tab = QWidget()
        layout = QVBoxLayout(general_tab)
        
        # Информация о заказе
        order_group = QGroupBox("Информация о заказе")
        order_layout = QFormLayout(order_group)
        
        order_layout.addRow("Номер заказа:", QLabel(str(self.order.order_number)))
        order_layout.addRow("Дата создания:", QLabel(self.order.created_at.strftime("%d.%m.%Y %H:%M") if self.order.created_at else ""))
        order_layout.addRow("Дата обновления:", QLabel(self.order.updated_at.strftime("%d.%m.%Y %H:%M") if self.order.updated_at else ""))
        order_layout.addRow("Статус:", QLabel(self.order.status or ""))
        order_layout.addRow("Приоритет:", QLabel(self.order.priority or ""))
        
        layout.addWidget(order_group)
        
        # Информация о клиенте
        if self.order.client:
            client_group = QGroupBox("Информация о клиенте")
            client_layout = QFormLayout(client_group)
            
            client_layout.addRow("ФИО:", QLabel(f"{self.order.client.last_name} {self.order.client.first_name} {self.order.client.middle_name or ''}".strip()))
            client_layout.addRow("Телефон:", QLabel(self.order.client.phone or ""))
            client_layout.addRow("Email:", QLabel(self.order.client.email or ""))
            client_layout.addRow("Адрес:", QLabel(self.order.client.address or ""))
            
            layout.addWidget(client_group)
        
        # Информация об автомобиле
        if self.order.car:
            car_group = QGroupBox("Информация об автомобиле")
            car_layout = QFormLayout(car_group)
            
            car_layout.addRow("Марка и модель:", QLabel(f"{self.order.car.make} {self.order.car.model}"))
            car_layout.addRow("Год выпуска:", QLabel(str(self.order.car.year) if self.order.car.year else ""))
            car_layout.addRow("VIN:", QLabel(self.order.car.vin or ""))
            car_layout.addRow("Гос. номер:", QLabel(self.order.car.license_plate or ""))
            car_layout.addRow("Цвет:", QLabel(self.order.car.color or ""))
            car_layout.addRow("Пробег:", QLabel(f"{self.order.car.mileage} км" if self.order.car.mileage else ""))
            
            layout.addWidget(car_group)
        
        # Описание проблемы
        if self.order.description:
            desc_group = QGroupBox("Описание проблемы")
            desc_layout = QVBoxLayout(desc_group)
            
            desc_text = QTextEdit()
            desc_text.setPlainText(self.order.description)
            desc_text.setReadOnly(True)
            desc_text.setMaximumHeight(100)
            desc_layout.addWidget(desc_text)
            
            layout.addWidget(desc_group)
        
        # Комментарии
        if self.order.notes:
            notes_group = QGroupBox("Комментарии")
            notes_layout = QVBoxLayout(notes_group)
            
            notes_text = QTextEdit()
            notes_text.setPlainText(self.order.notes)
            notes_text.setReadOnly(True)
            notes_text.setMaximumHeight(100)
            notes_layout.addWidget(notes_text)
            
            layout.addWidget(notes_group)
        
        layout.addStretch()
        self.tab_widget.addTab(general_tab, "Общая информация")
    
    def _create_services_tab(self):
        """Создание вкладки услуг"""
        services_tab = QWidget()
        layout = QVBoxLayout(services_tab)
        
        # Таблица услуг
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(6)
        self.services_table.setHorizontalHeaderLabels([
            "Услуга", "Цена", "НДС %", "Цена с НДС", "Исполнитель", "Статус"
        ])
        
        # Настройка таблицы
        self.services_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.services_table.setAlternatingRowColors(True)
        
        header = self.services_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.services_table)
        
        # Итоги по услугам
        services_totals_group = QGroupBox("Итого по услугам")
        services_totals_layout = QFormLayout(services_totals_group)
        
        self.services_subtotal_label = QLabel("0.00 грн")
        self.services_vat_label = QLabel("0.00 грн")
        self.services_total_label = QLabel("0.00 грн")
        
        services_totals_layout.addRow("Сумма без НДС:", self.services_subtotal_label)
        services_totals_layout.addRow("НДС:", self.services_vat_label)
        services_totals_layout.addRow("Итого:", self.services_total_label)
        
        layout.addWidget(services_totals_group)
        
        self.tab_widget.addTab(services_tab, "Услуги")
    
    def _create_parts_tab(self):
        """Создание вкладки запчастей"""
        parts_tab = QWidget()
        layout = QVBoxLayout(parts_tab)
        
        # Таблица запчастей
        self.parts_table = QTableWidget()
        self.parts_table.setColumnCount(6)
        self.parts_table.setHorizontalHeaderLabels([
            "Артикул", "Наименование", "Количество", "Цена за шт.", "Скидка", "Общая стоимость"
        ])
        
        # Настройка таблицы
        self.parts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.parts_table.setAlternatingRowColors(True)
        
        header = self.parts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.parts_table)
        
        # Итоги по запчастям
        parts_totals_group = QGroupBox("Итого по запчастям")
        parts_totals_layout = QFormLayout(parts_totals_group)
        
        self.parts_subtotal_label = QLabel("0.00 грн")
        self.parts_discount_label = QLabel("0.00 грн")
        self.parts_total_label = QLabel("0.00 грн")
        
        parts_totals_layout.addRow("Сумма без скидки:", self.parts_subtotal_label)
        parts_totals_layout.addRow("Скидка:", self.parts_discount_label)
        parts_totals_layout.addRow("Итого:", self.parts_total_label)
        
        layout.addWidget(parts_totals_group)
        
        self.tab_widget.addTab(parts_tab, "Запчасти")
    
    def _create_totals_section(self, layout):
        """Создание секции общих итогов"""
        totals_group = QGroupBox("ОБЩИЕ ИТОГИ")
        totals_layout = QFormLayout(totals_group)
        
        # Устанавливаем стиль для группы итогов
        totals_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        self.grand_subtotal_label = QLabel("0.00 грн")
        self.grand_vat_label = QLabel("0.00 грн")
        self.grand_discount_label = QLabel("0.00 грн")
        self.grand_total_label = QLabel("0.00 грн")
        
        # Увеличиваем шрифт для итоговых сумм
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        
        self.grand_total_label.setFont(font)
        self.grand_total_label.setStyleSheet("color: #2E8B57;")
        
        totals_layout.addRow("Услуги:", self.grand_subtotal_label)
        totals_layout.addRow("НДС:", self.grand_vat_label)
        totals_layout.addRow("Запчасти:", QLabel("см. вкладку"))
        totals_layout.addRow("Общая скидка:", self.grand_discount_label)
        totals_layout.addRow("ИТОГО К ОПЛАТЕ:", self.grand_total_label)
        
        layout.addWidget(totals_group)
    
    def _populate_data(self):
        """Заполнение данными"""
        try:
            self._populate_services()
            self._populate_parts()
            self._calculate_totals()
            
        except SQLAlchemyError as e:
            self.logger.error(f"Ошибка заполнения данных: {e}")
            QMessageBox.critical(self, "Ошибка БД", f"Ошибка заполнения данных: {e}")
    
    def _populate_services(self):
        """Заполнение таблицы услуг"""
        try:
            # Загружаем услуги заказа
            stmt = select(OrderService).where(OrderService.order_id == self.order_id)
            result = self.db_session.execute(stmt)
            services = result.scalars().all()
            
            self.services_table.setRowCount(len(services))
            
            for row, service in enumerate(services):
                # Название услуги
                service_name = service.service_catalog.name if service.service_catalog else "Услуга"
                self.services_table.setItem(row, 0, QTableWidgetItem(service_name))
                
                # Цена
                price = float(service.price) if service.price else 0.0
                price_item = QTableWidgetItem(f"{price:.2f}")
                price_item.setTextAlignment(Qt.AlignRight)
                self.services_table.setItem(row, 1, price_item)
                
                # НДС %
                vat_rate = float(service.vat_rate) if service.vat_rate else 20.0
                vat_item = QTableWidgetItem(f"{vat_rate:.0f}%")
                vat_item.setTextAlignment(Qt.AlignCenter)
                self.services_table.setItem(row, 2, vat_item)
                
                # Цена с НДС
                price_with_vat = price * (1 + vat_rate / 100)
                price_vat_item = QTableWidgetItem(f"{price_with_vat:.2f}")
                price_vat_item.setTextAlignment(Qt.AlignRight)
                self.services_table.setItem(row, 3, price_vat_item)
                
                # Исполнитель
                executor = ""
                if service.employee:
                    executor = f"{service.employee.last_name} {service.employee.first_name}"
                self.services_table.setItem(row, 4, QTableWidgetItem(executor))
                
                # Статус
                status = service.status if hasattr(service, 'status') and service.status else "Назначена"
                self.services_table.setItem(row, 5, QTableWidgetItem(status))
                
        except SQLAlchemyError as e:
            self.logger.error(f"Ошибка загрузки услуг: {e}")
    
    def _populate_parts(self):
        """Заполнение таблицы запчастей"""
        try:
            # Загружаем запчасти заказа
            stmt = select(OrderPart).where(OrderPart.order_id == self.order_id)
            result = self.db_session.execute(stmt)
            parts = result.scalars().all()
            
            self.parts_table.setRowCount(len(parts))
            
            for row, part in enumerate(parts):
                # Артикул
                self.parts_table.setItem(row, 0, QTableWidgetItem(part.part_number or ""))
                
                # Наименование
                self.parts_table.setItem(row, 1, QTableWidgetItem(part.name or ""))
                
                # Количество
                qty_item = QTableWidgetItem(str(part.quantity))
                qty_item.setTextAlignment(Qt.AlignCenter)
                self.parts_table.setItem(row, 2, qty_item)
                
                # Цена за шт.
                unit_price = float(part.unit_price) if part.unit_price else 0.0
                price_item = QTableWidgetItem(f"{unit_price:.2f}")
                price_item.setTextAlignment(Qt.AlignRight)
                self.parts_table.setItem(row, 3, price_item)
                
                # Скидка
                discount = float(part.discount) if part.discount else 0.0
                discount_item = QTableWidgetItem(f"{discount:.2f}")
                discount_item.setTextAlignment(Qt.AlignRight)
                self.parts_table.setItem(row, 4, discount_item)
                
                # Общая стоимость
                total_cost = (unit_price * part.quantity) - discount
                total_item = QTableWidgetItem(f"{total_cost:.2f}")
                total_item.setTextAlignment(Qt.AlignRight)
                self.parts_table.setItem(row, 5, total_item)
                
        except SQLAlchemyError as e:
            self.logger.error(f"Ошибка загрузки запчастей: {e}")
    
    def _calculate_totals(self):
        """Расчет итоговых сумм"""
        try:
            # Расчет по услугам
            services_subtotal = 0.0
            services_vat = 0.0
            services_total = 0.0
            
            for row in range(self.services_table.rowCount()):
                price_item = self.services_table.item(row, 1)
                vat_item = self.services_table.item(row, 3)
                
                if price_item and vat_item:
                    price = float(price_item.text())
                    price_with_vat = float(vat_item.text())
                    
                    services_subtotal += price
                    services_total += price_with_vat
            
            services_vat = services_total - services_subtotal
            
            self.services_subtotal_label.setText(f"{services_subtotal:.2f} грн")
            self.services_vat_label.setText(f"{services_vat:.2f} грн")
            self.services_total_label.setText(f"{services_total:.2f} грн")
            
            # Расчет по запчастям
            parts_subtotal = 0.0
            parts_discount = 0.0
            parts_total = 0.0
            
            for row in range(self.parts_table.rowCount()):
                price_item = self.parts_table.item(row, 3)
                qty_item = self.parts_table.item(row, 2)
                discount_item = self.parts_table.item(row, 4)
                
                if price_item and qty_item:
                    unit_price = float(price_item.text())
                    quantity = int(qty_item.text())
                    discount = float(discount_item.text()) if discount_item else 0.0
                    
                    subtotal = unit_price * quantity
                    total = subtotal - discount
                    
                    parts_subtotal += subtotal
                    parts_discount += discount
                    parts_total += total
            
            self.parts_subtotal_label.setText(f"{parts_subtotal:.2f} грн")
            self.parts_discount_label.setText(f"{parts_discount:.2f} грн")
            self.parts_total_label.setText(f"{parts_total:.2f} грн")
            
            # Общие итоги
            grand_total = services_total + parts_total
            
            self.grand_subtotal_label.setText(f"{services_subtotal:.2f} грн")
            self.grand_vat_label.setText(f"{services_vat:.2f} грн")
            self.grand_discount_label.setText(f"{parts_discount:.2f} грн")
            self.grand_total_label.setText(f"{grand_total:.2f} грн")
            
        except (ValueError, AttributeError) as e:
            self.logger.error(f"Ошибка расчета итогов: {e}")
    
    def print_order(self):
        """Печать заказа в PDF"""
        try:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(f"Заказ_{self.order.order_number}.pdf")
            
            dialog = QPrintDialog(printer, self)
            if dialog.exec() == QPrintDialog.Accepted:
                # Создаем HTML для печати
                html_content = self._generate_print_html()
                
                # Печатаем
                from PySide6.QtGui import QTextDocument
                document = QTextDocument()
                document.setHtml(html_content)
                document.print(printer)
                
                QMessageBox.information(self, "Успех", "Заказ успешно сохранен в PDF")
                
        except Exception as e:
            self.logger.error(f"Ошибка печати: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось распечатать заказ: {e}")
    
    def _generate_print_html(self):
        """Генерация HTML для печати"""
        html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; font-size: 12px; }}
                .header {{ text-align: center; margin-bottom: 20px; }}
                .section {{ margin-bottom: 15px; }}
                .section h3 {{ background-color: #f0f0f0; padding: 5px; margin: 10px 0 5px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; }}
                th, td {{ border: 1px solid #ccc; padding: 5px; text-align: left; }}
                th {{ background-color: #f0f0f0; }}
                .total {{ font-weight: bold; background-color: #e0e0e0; }}
                .right {{ text-align: right; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>ЗАКАЗ №{self.order.order_number}</h1>
                <p>Дата: {self.order.created_at.strftime('%d.%m.%Y %H:%M') if self.order.created_at else ''}</p>
                <p>Статус: {self.order.status}</p>
            </div>
        """
        
        # Информация о клиенте
        if self.order.client:
            html += f"""
            <div class="section">
                <h3>КЛИЕНТ</h3>
                <p><strong>ФИО:</strong> {self.order.client.last_name} {self.order.client.first_name} {self.order.client.middle_name or ''}</p>
                <p><strong>Телефон:</strong> {self.order.client.phone or ''}</p>
                <p><strong>Email:</strong> {self.order.client.email or ''}</p>
            </div>
            """
        
        # Информация об автомобиле
        if self.order.car:
            html += f"""
            <div class="section">
                <h3>АВТОМОБИЛЬ</h3>
                <p><strong>Марка и модель:</strong> {self.order.car.make} {self.order.car.model}</p>
                <p><strong>Год:</strong> {self.order.car.year or ''}</p>
                <p><strong>VIN:</strong> {self.order.car.vin or ''}</p>
                <p><strong>Гос. номер:</strong> {self.order.car.license_plate or ''}</p>
            </div>
            """
        
        # Услуги
        if self.services_table.rowCount() > 0:
            html += """
            <div class="section">
                <h3>УСЛУГИ</h3>
                <table>
                    <tr>
                        <th>Услуга</th>
                        <th>Цена</th>
                        <th>НДС %</th>
                        <th>Цена с НДС</th>
                        <th>Исполнитель</th>
                    </tr>
            """
            
            for row in range(self.services_table.rowCount()):
                service = self.services_table.item(row, 0).text()
                price = self.services_table.item(row, 1).text()
                vat_rate = self.services_table.item(row, 2).text()
                price_vat = self.services_table.item(row, 3).text()
                executor = self.services_table.item(row, 4).text()
                
                html += f"""
                <tr>
                    <td>{service}</td>
                    <td class="right">{price}</td>
                    <td class="right">{vat_rate}</td>
                    <td class="right">{price_vat}</td>
                    <td>{executor}</td>
                </tr>
                """
            
            html += f"""
                <tr class="total">
                    <td colspan="3">ИТОГО ПО УСЛУГАМ</td>
                    <td class="right">{self.services_total_label.text()}</td>
                    <td></td>
                </tr>
                </table>
            </div>
            """
        
        # Запчасти
        if self.parts_table.rowCount() > 0:
            html += """
            <div class="section">
                <h3>ЗАПЧАСТИ</h3>
                <table>
                    <tr>
                        <th>Артикул</th>
                        <th>Наименование</th>
                        <th>Кол-во</th>
                        <th>Цена за шт.</th>
                        <th>Скидка</th>
                        <th>Общая стоимость</th>
                    </tr>
            """
            
            for row in range(self.parts_table.rowCount()):
                part_number = self.parts_table.item(row, 0).text()
                name = self.parts_table.item(row, 1).text()
                quantity = self.parts_table.item(row, 2).text()
                unit_price = self.parts_table.item(row, 3).text()
                discount = self.parts_table.item(row, 4).text()
                total_cost = self.parts_table.item(row, 5).text()
                
                html += f"""
                <tr>
                    <td>{part_number}</td>
                    <td>{name}</td>
                    <td class="right">{quantity}</td>
                    <td class="right">{unit_price}</td>
                    <td class="right">{discount}</td>
                    <td class="right">{total_cost}</td>
                </tr>
                """
            
            html += f"""
                <tr class="total">
                    <td colspan="5">ИТОГО ПО ЗАПЧАСТЯМ</td>
                    <td class="right">{self.parts_total_label.text()}</td>
                </tr>
                </table>
            </div>
            """
        
        # Общие итоги
        html += f"""
        <div class="section">
            <h3>ОБЩИЕ ИТОГИ</h3>
            <table>
                <tr class="total">
                    <td><strong>ИТОГО К ОПЛАТЕ</strong></td>
                    <td class="right"><strong>{self.grand_total_label.text()}</strong></td>
                </tr>
            </table>
        </div>
        """
        
        # Описание и комментарии
        if self.order.description:
            html += f"""
            <div class="section">
                <h3>ОПИСАНИЕ ПРОБЛЕМЫ</h3>
                <p>{self.order.description}</p>
            </div>
            """
        
        if self.order.notes:
            html += f"""
            <div class="section">
                <h3>КОММЕНТАРИИ</h3>
                <p>{self.order.notes}</p>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html
    
    def _center_on_parent(self, parent):
        """Центрирование диалога относительно родительского окна"""
        if parent:
            parent_geometry = parent.geometry()
            dialog_geometry = self.geometry()
            
            x = parent_geometry.x() + (parent_geometry.width() - dialog_geometry.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - dialog_geometry.height()) // 2
            
            self.move(x, y)