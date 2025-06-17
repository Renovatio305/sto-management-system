"""
Представление для управления справочниками (услуги, сотрудники).
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget,
    QTableWidgetItem, QPushButton, QHeaderView, QAbstractItemView,
    QMessageBox, QDialog, QFormLayout, QLineEdit, QComboBox,
    QTextEdit, QDoubleSpinBox, QGroupBox, QLabel, QCheckBox,
    QDateEdit, QSpinBox
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QFont
from sqlalchemy import select, desc
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sto_app.models_sto import ServiceCatalog
from shared_models.common_models import Employee
from decimal import Decimal
import logging


class ServiceCatalogDialog(QDialog):
    """Диалог добавления/редактирования услуги в каталоге"""
    
    def __init__(self, parent=None, service=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.db_session = parent.db_session if parent else None
        self.service = service  # Для редактирования
        self.is_editing = service is not None
        
        self.setWindowTitle("Редактирование услуги" if self.is_editing else "Новая услуга")
        self.setModal(True)
        self.setMinimumSize(400, 300)
        
        self.logger = logging.getLogger(__name__)
        
        self._setup_ui()
        if self.is_editing:
            self._populate_fields()
        
        if parent:
            self._center_on_parent(parent)
    
    def _setup_ui(self):
        """Создание интерфейса"""
        layout = QVBoxLayout(self)
        
        # Форма
        form_group = QGroupBox("Информация об услуге")
        form_layout = QFormLayout(form_group)
        
        # Название
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Введите название услуги")
        form_layout.addRow("Название*:", self.name_edit)
        
        # Описание
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Описание услуги (опционально)")
        form_layout.addRow("Описание:", self.description_edit)
        
        # Категория
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.addItems([
            "Диагностика", "Ремонт двигателя", "Ремонт трансмиссии",
            "Ремонт подвески", "Электрика", "Кузовной ремонт",
            "Шиномонтаж", "Техобслуживание", "Прочее"
        ])
        form_layout.addRow("Категория:", self.category_combo)
        
        # Цена по умолчанию
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0.0, 999999.99)
        self.price_spin.setDecimals(2)
        self.price_spin.setSuffix(" грн")
        form_layout.addRow("Цена по умолчанию:", self.price_spin)
        
        # НДС
        self.vat_rate_spin = QDoubleSpinBox()
        self.vat_rate_spin.setRange(0.0, 100.0)
        self.vat_rate_spin.setValue(20.0)
        self.vat_rate_spin.setDecimals(1)
        self.vat_rate_spin.setSuffix(" %")
        form_layout.addRow("Ставка НДС:", self.vat_rate_spin)
        
        # Продолжительность (в часах)
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(0.0, 999.0)
        self.duration_spin.setDecimals(1)
        self.duration_spin.setSuffix(" ч")
        form_layout.addRow("Продолжительность:", self.duration_spin)
        
        # Активность
        self.is_active_check = QCheckBox("Услуга активна")
        self.is_active_check.setChecked(True)
        form_layout.addRow("", self.is_active_check)
        
        layout.addWidget(form_group)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save_service)
        buttons_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def _populate_fields(self):
        """Заполнение полей при редактировании"""
        if not self.service:
            return
            
        self.name_edit.setText(self.service.name or "")
        self.description_edit.setPlainText(self.service.description or "")
        self.category_combo.setCurrentText(self.service.category or "")
        self.price_spin.setValue(float(self.service.default_price) if self.service.default_price else 0.0)
        self.vat_rate_spin.setValue(float(self.service.vat_rate) if self.service.vat_rate else 20.0)
        self.duration_spin.setValue(float(self.service.duration_hours) if self.service.duration_hours else 0.0)
        
        if hasattr(self.service, 'is_active'):
            self.is_active_check.setChecked(bool(self.service.is_active))
    
    def save_service(self):
        """Сохранение услуги"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Предупреждение", "Введите название услуги")
            self.name_edit.setFocus()
            return
        
        try:
            if self.is_editing:
                # Обновляем существующую услугу
                service = self.service
            else:
                # Создаем новую услугу
                service = ServiceCatalog()
                self.db_session.add(service)
            
            # Заполняем данные
            service.name = name
            service.description = self.description_edit.toPlainText().strip() or None
            service.category = self.category_combo.currentText().strip() or None
            service.default_price = Decimal(str(self.price_spin.value()))
            service.vat_rate = Decimal(str(self.vat_rate_spin.value()))
            service.duration_hours = Decimal(str(self.duration_spin.value())) if self.duration_spin.value() > 0 else None
            
            if hasattr(service, 'is_active'):
                service.is_active = self.is_active_check.isChecked()
            
            self.db_session.commit()
            
            action = "обновлена" if self.is_editing else "добавлена"
            QMessageBox.information(self, "Успех", f"Услуга '{name}' успешно {action}")
            self.accept()
            
        except IntegrityError as e:
            self.db_session.rollback()
            self.logger.error(f"Ошибка целостности при сохранении услуги: {e}")
            QMessageBox.critical(self, "Ошибка", "Услуга с таким названием уже существует")
            
        except SQLAlchemyError as e:
            self.db_session.rollback()
            self.logger.error(f"Ошибка БД при сохранении услуги: {e}")
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось сохранить услугу: {e}")
        
        except Exception as e:
            self.db_session.rollback()
            self.logger.error(f"Неожиданная ошибка при сохранении услуги: {e}")
            QMessageBox.critical(self, "Ошибка", f"Неожиданная ошибка: {e}")
    
    def _center_on_parent(self, parent):
        """Центрирование диалога"""
        if parent:
            parent_geometry = parent.geometry()
            dialog_geometry = self.geometry()
            
            x = parent_geometry.x() + (parent_geometry.width() - dialog_geometry.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - dialog_geometry.height()) // 2
            
            self.move(x, y)


class EmployeeDialog(QDialog):
    """Диалог добавления/редактирования сотрудника"""
    
    def __init__(self, parent=None, employee=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.db_session = parent.db_session if parent else None
        self.employee = employee
        self.is_editing = employee is not None
        
        self.setWindowTitle("Редактирование сотрудника" if self.is_editing else "Новый сотрудник")
        self.setModal(True)
        self.setMinimumSize(400, 400)
        
        self.logger = logging.getLogger(__name__)
        
        self._setup_ui()
        if self.is_editing:
            self._populate_fields()
        
        if parent:
            self._center_on_parent(parent)
    
    def _setup_ui(self):
        """Создание интерфейса"""
        layout = QVBoxLayout(self)
        
        # Персональные данные
        personal_group = QGroupBox("Персональные данные")
        personal_layout = QFormLayout(personal_group)
        
        self.last_name_edit = QLineEdit()
        self.last_name_edit.setPlaceholderText("Фамилия")
        personal_layout.addRow("Фамилия*:", self.last_name_edit)
        
        self.first_name_edit = QLineEdit()
        self.first_name_edit.setPlaceholderText("Имя")
        personal_layout.addRow("Имя*:", self.first_name_edit)
        
        self.middle_name_edit = QLineEdit()
        self.middle_name_edit.setPlaceholderText("Отчество (опционально)")
        personal_layout.addRow("Отчество:", self.middle_name_edit)
        
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("+380XXXXXXXXX")
        personal_layout.addRow("Телефон:", self.phone_edit)
        
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("email@example.com")
        personal_layout.addRow("Email:", self.email_edit)
        
        layout.addWidget(personal_group)
        
        # Рабочие данные
        work_group = QGroupBox("Рабочие данные")
        work_layout = QFormLayout(work_group)
        
        self.position_edit = QLineEdit()
        self.position_edit.setPlaceholderText("Должность")
        work_layout.addRow("Должность*:", self.position_edit)
        
        self.department_combo = QComboBox()
        self.department_combo.setEditable(True)
        self.department_combo.addItems([
            "Автосервис", "Диагностика", "Кузовной цех",
            "Электрика", "Шиномонтаж", "Администрация", "Склад"
        ])
        work_layout.addRow("Отдел:", self.department_combo)
        
        self.hire_date_edit = QDateEdit()
        self.hire_date_edit.setDate(QDate.currentDate())
        self.hire_date_edit.setCalendarPopup(True)
        work_layout.addRow("Дата приема:", self.hire_date_edit)
        
        self.hourly_rate_spin = QDoubleSpinBox()
        self.hourly_rate_spin.setRange(0.0, 9999.99)
        self.hourly_rate_spin.setDecimals(2)
        self.hourly_rate_spin.setSuffix(" грн/ч")
        work_layout.addRow("Часовая ставка:", self.hourly_rate_spin)
        
        self.is_active_check = QCheckBox("Сотрудник активен")
        self.is_active_check.setChecked(True)
        work_layout.addRow("", self.is_active_check)
        
        layout.addWidget(work_group)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save_employee)
        buttons_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def _populate_fields(self):
        """Заполнение полей при редактировании"""
        if not self.employee:
            return
            
        self.last_name_edit.setText(self.employee.last_name or "")
        self.first_name_edit.setText(self.employee.first_name or "")
        self.middle_name_edit.setText(self.employee.middle_name or "")
        self.phone_edit.setText(self.employee.phone or "")
        self.email_edit.setText(self.employee.email or "")
        self.position_edit.setText(self.employee.position or "")
        
        if hasattr(self.employee, 'department'):
            self.department_combo.setCurrentText(self.employee.department or "")
        
        if hasattr(self.employee, 'hire_date') and self.employee.hire_date:
            self.hire_date_edit.setDate(QDate(self.employee.hire_date))
        
        if hasattr(self.employee, 'hourly_rate') and self.employee.hourly_rate:
            self.hourly_rate_spin.setValue(float(self.employee.hourly_rate))
        
        if hasattr(self.employee, 'is_active'):
            self.is_active_check.setChecked(bool(self.employee.is_active))
    
    def save_employee(self):
        """Сохранение сотрудника"""
        last_name = self.last_name_edit.text().strip()
        first_name = self.first_name_edit.text().strip()
        position = self.position_edit.text().strip()
        
        if not last_name or not first_name:
            QMessageBox.warning(self, "Предупреждение", "Введите фамилию и имя сотрудника")
            return
        
        if not position:
            QMessageBox.warning(self, "Предупреждение", "Введите должность сотрудника")
            return
        
        try:
            if self.is_editing:
                employee = self.employee
            else:
                employee = Employee()
                self.db_session.add(employee)
            
            employee.last_name = last_name
            employee.first_name = first_name
            employee.middle_name = self.middle_name_edit.text().strip() or None
            employee.phone = self.phone_edit.text().strip() or None
            employee.email = self.email_edit.text().strip() or None
            employee.position = position
            
            if hasattr(employee, 'department'):
                employee.department = self.department_combo.currentText().strip() or None
            
            if hasattr(employee, 'hire_date'):
                employee.hire_date = self.hire_date_edit.date().toPython()
            
            if hasattr(employee, 'hourly_rate'):
                employee.hourly_rate = Decimal(str(self.hourly_rate_spin.value())) if self.hourly_rate_spin.value() > 0 else None
            
            if hasattr(employee, 'is_active'):
                employee.is_active = self.is_active_check.isChecked()
            
            self.db_session.commit()
            
            action = "обновлен" if self.is_editing else "добавлен"
            QMessageBox.information(self, "Успех", f"Сотрудник '{last_name} {first_name}' успешно {action}")
            self.accept()
            
        except SQLAlchemyError as e:
            self.db_session.rollback()
            self.logger.error(f"Ошибка БД при сохранении сотрудника: {e}")
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось сохранить сотрудника: {e}")
        
        except Exception as e:
            self.db_session.rollback()
            self.logger.error(f"Неожиданная ошибка при сохранении сотрудника: {e}")
            QMessageBox.critical(self, "Ошибка", f"Неожиданная ошибка: {e}")
    
    def _center_on_parent(self, parent):
        """Центрирование диалога"""
        if parent:
            parent_geometry = parent.geometry()
            dialog_geometry = self.geometry()
            
            x = parent_geometry.x() + (parent_geometry.width() - dialog_geometry.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - dialog_geometry.height()) // 2
            
            self.move(x, y)


class CatalogsView(QWidget):
    """Представление для управления справочниками"""
    
    # Сигналы
    data_changed = Signal()  # Сигнал об изменении данных
    
    def __init__(self, db_session, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        self.logger = logging.getLogger(__name__)
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Создание пользовательского интерфейса"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        title_label = QLabel("Управление справочниками")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Табы
        self.tab_widget = QTabWidget()
        
        # Вкладка услуг
        self._create_services_tab()
        
        # Вкладка сотрудников
        self._create_employees_tab()
        
        layout.addWidget(self.tab_widget)
    
    def _create_services_tab(self):
        """Создание вкладки управления услугами"""
        services_widget = QWidget()
        layout = QVBoxLayout(services_widget)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        add_service_btn = QPushButton("➕ Добавить услугу")
        add_service_btn.clicked.connect(self.add_service)
        buttons_layout.addWidget(add_service_btn)
        
        edit_service_btn = QPushButton("✏️ Редактировать")
        edit_service_btn.clicked.connect(self.edit_service)
        buttons_layout.addWidget(edit_service_btn)
        
        delete_service_btn = QPushButton("🗑️ Удалить")
        delete_service_btn.clicked.connect(self.delete_service)
        buttons_layout.addWidget(delete_service_btn)
        
        buttons_layout.addStretch()
        
        refresh_services_btn = QPushButton("🔄 Обновить")
        refresh_services_btn.clicked.connect(self.load_services)
        buttons_layout.addWidget(refresh_services_btn)
        
        layout.addLayout(buttons_layout)
        
        # Таблица услуг
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(6)
        self.services_table.setHorizontalHeaderLabels([
            "ID", "Название", "Категория", "Цена по умолчанию", "НДС %", "Статус"
        ])
        
        # Настройка таблицы
        self.services_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.services_table.setAlternatingRowColors(True)
        self.services_table.setSortingEnabled(True)
        
        header = self.services_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Название
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Категория
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Цена
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # НДС
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Статус
        
        # Скрываем колонку ID
        self.services_table.setColumnHidden(0, True)
        
        # Двойной клик для редактирования
        self.services_table.doubleClicked.connect(self.edit_service)
        
        layout.addWidget(self.services_table)
        
        self.tab_widget.addTab(services_widget, "Каталог услуг")
    
    def _create_employees_tab(self):
        """Создание вкладки управления сотрудниками"""
        employees_widget = QWidget()
        layout = QVBoxLayout(employees_widget)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        add_employee_btn = QPushButton("➕ Добавить сотрудника")
        add_employee_btn.clicked.connect(self.add_employee)
        buttons_layout.addWidget(add_employee_btn)
        
        edit_employee_btn = QPushButton("✏️ Редактировать")
        edit_employee_btn.clicked.connect(self.edit_employee)
        buttons_layout.addWidget(edit_employee_btn)
        
        delete_employee_btn = QPushButton("🗑️ Удалить")
        delete_employee_btn.clicked.connect(self.delete_employee)
        buttons_layout.addWidget(delete_employee_btn)
        
        buttons_layout.addStretch()
        
        refresh_employees_btn = QPushButton("🔄 Обновить")
        refresh_employees_btn.clicked.connect(self.load_employees)
        buttons_layout.addWidget(refresh_employees_btn)
        
        layout.addLayout(buttons_layout)
        
        # Таблица сотрудников
        self.employees_table = QTableWidget()
        self.employees_table.setColumnCount(6)
        self.employees_table.setHorizontalHeaderLabels([
            "ID", "ФИО", "Должность", "Отдел", "Телефон", "Статус"
        ])
        
        # Настройка таблицы
        self.employees_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.employees_table.setAlternatingRowColors(True)
        self.employees_table.setSortingEnabled(True)
        
        header = self.employees_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # ФИО
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Должность
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Отдел
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Телефон
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Статус
        
        # Скрываем колонку ID
        self.employees_table.setColumnHidden(0, True)
        
        # Двойной клик для редактирования
        self.employees_table.doubleClicked.connect(self.edit_employee)
        
        layout.addWidget(self.employees_table)
        
        self.tab_widget.addTab(employees_widget, "Сотрудники")
    
    def _load_data(self):
        """Загрузка всех данных"""
        self.load_services()
        self.load_employees()
    
    def load_services(self):
        """Загрузка каталога услуг"""
        try:
            stmt = select(ServiceCatalog).order_by(ServiceCatalog.name)
            result = self.db_session.execute(stmt)
            services = result.scalars().all()
            
            self.services_table.setRowCount(len(services))
            
            for row, service in enumerate(services):
                # ID (скрытая колонка)
                id_item = QTableWidgetItem(str(service.id))
                id_item.setData(Qt.UserRole, service.id)
                self.services_table.setItem(row, 0, id_item)
                
                # Название
                self.services_table.setItem(row, 1, QTableWidgetItem(service.name or ""))
                
                # Категория
                self.services_table.setItem(row, 2, QTableWidgetItem(service.category or ""))
                
                # Цена по умолчанию
                price = float(service.default_price) if service.default_price else 0.0
                price_item = QTableWidgetItem(f"{price:.2f} грн")
                price_item.setTextAlignment(Qt.AlignRight)
                self.services_table.setItem(row, 3, price_item)
                
                # НДС
                vat_rate = float(service.vat_rate) if service.vat_rate else 0.0
                vat_item = QTableWidgetItem(f"{vat_rate:.1f}%")
                vat_item.setTextAlignment(Qt.AlignCenter)
                self.services_table.setItem(row, 4, vat_item)
                
                # Статус
                status = "Активна"
                if hasattr(service, 'is_active') and not service.is_active:
                    status = "Неактивна"
                
                status_item = QTableWidgetItem(status)
                if status == "Неактивна":
                    status_item.setForeground(Qt.red)
                else:
                    status_item.setForeground(Qt.darkGreen)
                
                self.services_table.setItem(row, 5, status_item)
            
            self.logger.info(f"Загружено {len(services)} услуг")
            
        except SQLAlchemyError as e:
            self.logger.error(f"Ошибка загрузки услуг: {e}")
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось загрузить каталог услуг: {e}")
    
    def load_employees(self):
        """Загрузка списка сотрудников"""
        try:
            stmt = select(Employee).order_by(Employee.last_name, Employee.first_name)
            result = self.db_session.execute(stmt)
            employees = result.scalars().all()
            
            self.employees_table.setRowCount(len(employees))
            
            for row, employee in enumerate(employees):
                # ID (скрытая колонка)
                id_item = QTableWidgetItem(str(employee.id))
                id_item.setData(Qt.UserRole, employee.id)
                self.employees_table.setItem(row, 0, id_item)
                
                # ФИО
                full_name = f"{employee.last_name} {employee.first_name}"
                if employee.middle_name:
                    full_name += f" {employee.middle_name}"
                self.employees_table.setItem(row, 1, QTableWidgetItem(full_name))
                
                # Должность
                self.employees_table.setItem(row, 2, QTableWidgetItem(employee.role or ""))
                
                # Отдел
                department = ""
                if hasattr(employee, 'department'):
                    department = employee.department or ""
                self.employees_table.setItem(row, 3, QTableWidgetItem(department))
                
                # Телефон
                self.employees_table.setItem(row, 4, QTableWidgetItem(employee.phone or ""))
                
                # Статус
                status = "Активен"
                if hasattr(employee, 'is_active') and not employee.is_active:
                    status = "Неактивен"
                
                status_item = QTableWidgetItem(status)
                if status == "Неактивен":
                    status_item.setForeground(Qt.red)
                else:
                    status_item.setForeground(Qt.darkGreen)
                
                self.employees_table.setItem(row, 5, status_item)
            
            self.logger.info(f"Загружено {len(employees)} сотрудников")
            
        except SQLAlchemyError as e:
            self.logger.error(f"Ошибка загрузки сотрудников: {e}")
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось загрузить список сотрудников: {e}")
    
    # === МЕТОДЫ УПРАВЛЕНИЯ УСЛУГАМИ ===
    
    def add_service(self):
        """Добавление новой услуги"""
        dialog = ServiceCatalogDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_services()
            self.data_changed.emit()
    
    def edit_service(self):
        """Редактирование выбранной услуги"""
        current_row = self.services_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "Информация", "Выберите услугу для редактирования")
            return
        
        service_id = self.services_table.item(current_row, 0).data(Qt.UserRole)
        
        try:
            stmt = select(ServiceCatalog).where(ServiceCatalog.id == service_id)
            result = self.db_session.execute(stmt)
            service = result.scalar_one_or_none()
            
            if not service:
                QMessageBox.warning(self, "Предупреждение", "Услуга не найдена")
                return
            
            dialog = ServiceCatalogDialog(self, service=service)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_services()
                self.data_changed.emit()
                
        except SQLAlchemyError as e:
            self.logger.error(f"Ошибка получения услуги: {e}")
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось получить данные услуги: {e}")
    
    def delete_service(self):
        """Удаление выбранной услуги"""
        current_row = self.services_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "Информация", "Выберите услугу для удаления")
            return
        
        service_name = self.services_table.item(current_row, 1).text()
        service_id = self.services_table.item(current_row, 0).data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self, 'Подтверждение удаления',
            f'Вы уверены, что хотите удалить услугу "{service_name}"?\n\n'
            'Это действие нельзя будет отменить.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                service = self.db_session.get(ServiceCatalog, service_id)
                if service:
                    self.db_session.delete(service)
                    self.db_session.commit()
                    
                    self.load_services()
                    self.data_changed.emit()
                    
                    QMessageBox.information(self, "Успех", f'Услуга "{service_name}" удалена')
                else:
                    QMessageBox.warning(self, "Предупреждение", "Услуга не найдена")
                    
            except IntegrityError as e:
                self.db_session.rollback()
                self.logger.error(f"Ошибка целостности при удалении услуги: {e}")
                QMessageBox.critical(
                    self, "Ошибка удаления",
                    f'Не удалось удалить услугу "{service_name}".\n\n'
                    'Возможно, она используется в заказах.'
                )
            except SQLAlchemyError as e:
                self.db_session.rollback()
                self.logger.error(f"Ошибка БД при удалении услуги: {e}")
                QMessageBox.critical(self, "Ошибка БД", f"Не удалось удалить услугу: {e}")
    
    # === МЕТОДЫ УПРАВЛЕНИЯ СОТРУДНИКАМИ ===
    
    def add_employee(self):
        """Добавление нового сотрудника"""
        dialog = EmployeeDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_employees()
            self.data_changed.emit()
    
    def edit_employee(self):
        """Редактирование выбранного сотрудника"""
        current_row = self.employees_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "Информация", "Выберите сотрудника для редактирования")
            return
        
        employee_id = self.employees_table.item(current_row, 0).data(Qt.UserRole)
        
        try:
            stmt = select(Employee).where(Employee.id == employee_id)
            result = self.db_session.execute(stmt)
            employee = result.scalar_one_or_none()
            
            if not employee:
                QMessageBox.warning(self, "Предупреждение", "Сотрудник не найден")
                return
            
            dialog = EmployeeDialog(self, employee=employee)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_employees()
                self.data_changed.emit()
                
        except SQLAlchemyError as e:
            self.logger.error(f"Ошибка получения сотрудника: {e}")
            QMessageBox.critical(self, "Ошибка БД", f"Не удалось получить данные сотрудника: {e}")
    
    def delete_employee(self):
        """Удаление выбранного сотрудника"""
        current_row = self.employees_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "Информация", "Выберите сотрудника для удаления")
            return
        
        employee_name = self.employees_table.item(current_row, 1).text()
        employee_id = self.employees_table.item(current_row, 0).data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self, 'Подтверждение удаления',
            f'Вы уверены, что хотите удалить сотрудника "{employee_name}"?\n\n'
            'Это действие нельзя будет отменить.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                employee = self.db_session.get(Employee, employee_id)
                if employee:
                    self.db_session.delete(employee)
                    self.db_session.commit()
                    
                    self.load_employees()
                    self.data_changed.emit()
                    
                    QMessageBox.information(self, "Успех", f'Сотрудник "{employee_name}" удален')
                else:
                    QMessageBox.warning(self, "Предупреждение", "Сотрудник не найден")
                    
            except IntegrityError as e:
                self.db_session.rollback()
                self.logger.error(f"Ошибка целостности при удалении сотрудника: {e}")
                QMessageBox.critical(
                    self, "Ошибка удаления",
                    f'Не удалось удалить сотрудника "{employee_name}".\n\n'
                    'Возможно, он назначен исполнителем в заказах.'
                )
            except SQLAlchemyError as e:
                self.db_session.rollback()
                self.logger.error(f"Ошибка БД при удалении сотрудника: {e}")
                QMessageBox.critical(self, "Ошибка БД", f"Не удалось удалить сотрудника: {e}")
    
    def refresh_data(self):
        """Обновление всех данных"""
        self._load_data()
    
    def get_active_services(self):
        """Получение списка активных услуг для использования в других модулях"""
        try:
            stmt = select(ServiceCatalog)
            if hasattr(ServiceCatalog, 'is_active'):
                stmt = stmt.where(ServiceCatalog.is_active == True)
            stmt = stmt.order_by(ServiceCatalog.name)
            
            result = self.db_session.execute(stmt)
            return result.scalars().all()
            
        except SQLAlchemyError as e:
            self.logger.error(f"Ошибка получения активных услуг: {e}")
            return []
    
    def get_active_employees(self):
        """Получение списка активных сотрудников для использования в других модулях"""
        try:
            stmt = select(Employee)
            if hasattr(Employee, 'is_active'):
                stmt = stmt.where(Employee.is_active == True)
            stmt = stmt.order_by(Employee.last_name, Employee.first_name)
            
            result = self.db_session.execute(stmt)
            return result.scalars().all()
            
        except SQLAlchemyError as e:
            self.logger.error(f"Ошибка получения активных сотрудников: {e}")
            return []
