"""
Диалог для добавления и редактирования услуг в заказе СТО Management System.

Поддерживает:
- Выбор услуги из каталога
- Настройка цены и скидки
- Указание количества и времени выполнения
- Назначение исполнителя
- Добавление комментариев
- Расчет итоговой стоимости с учетом скидок
"""

import logging
from typing import Optional, List
from decimal import Decimal

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLineEdit, QTextEdit, QPushButton, QMessageBox, QLabel,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from shared_models.common_models import Employee
from sto_app.models_sto import ServiceCatalog, OrderService
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select


class ServiceDialog(QDialog):
    """
    Диалог для добавления или редактирования услуги в заказе.
    
    Поддерживает два режима:
    - Добавление новой услуги в заказ (order_service=None)
    - Редактирование существующей услуги в заказе (order_service=OrderService объект)
    """
    
    # Сигнал для обновления итоговой стоимости в родительском окне
    service_cost_changed = Signal()
    
    def __init__(self, parent=None, order_service: Optional[OrderService] = None, order_id: Optional[int] = None):
        super().__init__(parent)
        self.order_service = order_service
        self.order_id = order_id
        self.db_session = parent.db_session if parent else None
        self.is_edit_mode = order_service is not None
        
        self.setWindowTitle("Редактирование услуги" if self.is_edit_mode else "Добавление услуги")
        self.setModal(True)
        self.setMinimumSize(500, 600)
        self.resize(600, 700)
        
        # Логгер для отслеживания операций
        self.logger = logging.getLogger(__name__)
        
        # Списки для ComboBox
        self.services: List[ServiceCatalog] = []
        self.employees: List[Employee] = []
        
        self._load_data()
        self._setup_ui()
        self._connect_signals()
        
        if self.is_edit_mode:
            self._load_service_data()
        
        self._calculate_total()
        
        # Центрируем диалог относительно родительского окна
        if parent:
            self._center_on_parent(parent)

    def _load_data(self):
        """Загрузка данных из базы данных."""
        if not self.db_session:
            return
        
        try:
            # Загрузка каталога услуг
            stmt = select(ServiceCatalog).where(ServiceCatalog.is_active == True).order_by(ServiceCatalog.name)
            result = self.db_session.execute(stmt)
            self.services = result.scalars().all()
            
            # Загрузка сотрудников
            stmt = select(Employee).where(Employee.is_active == True).order_by(Employee.name)
            result = self.db_session.execute(stmt)
            self.employees = result.scalars().all()
            
        except SQLAlchemyError as e:
            self.logger.error(f"Ошибка при загрузке данных: {e}")
            QMessageBox.warning(
                self,
                "Предупреждение",
                "Не удалось загрузить данные из базы данных."
            )

    def _setup_ui(self):
        """Настройка пользовательского интерфейса."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        title_label = QLabel("Информация об услуге")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Основная информация об услуге
        service_group = QGroupBox("Основная информация")
        service_layout = QFormLayout(service_group)
        service_layout.setSpacing(10)
        
        # Выбор услуги из каталога
        self.service_combo = QComboBox()
        self.service_combo.setMinimumHeight(30)
        self.service_combo.addItem("-- Выберите услугу --", None)
        
        for service in self.services:
            display_text = f"{service.name} - {service.price:.2f} грн"
            self.service_combo.addItem(display_text, service.id)
        
        service_layout.addRow("Услуга*:", self.service_combo)
        
        # Описание выбранной услуги (только для чтения)
        self.service_description_label = QLabel()
        self.service_description_label.setWordWrap(True)
        self.service_description_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        service_layout.addRow("Описание:", self.service_description_label)
        
        # Исполнитель
        self.employee_combo = QComboBox()
        self.employee_combo.addItem("-- Не назначен --", None)
        
        for employee in self.employees:
            display_text = f"{employee.name} ({employee.position or 'Сотрудник'})"
            self.employee_combo.addItem(display_text, employee.id)
        
        service_layout.addRow("Исполнитель:", self.employee_combo)
        
        layout.addWidget(service_group)
        
        # Параметры выполнения
        params_group = QGroupBox("Параметры выполнения")
        params_layout = QFormLayout(params_group)
        params_layout.setSpacing(10)
        
        # Количество
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 999)
        self.quantity_spin.setValue(1)
        self.quantity_spin.setSuffix(" шт.")
        params_layout.addRow("Количество*:", self.quantity_spin)
        
        # Время выполнения (в часах)
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(0.1, 999.9)
        self.duration_spin.setValue(1.0)
        self.duration_spin.setSingleStep(0.5)
        self.duration_spin.setSuffix(" ч.")
        self.duration_spin.setDecimals(1)
        params_layout.addRow("Время выполнения:", self.duration_spin)
        
        layout.addWidget(params_group)
        
        # Ценообразование
        price_group = QGroupBox("Ценообразование")
        price_layout = QGridLayout(price_group)
        price_layout.setSpacing(10)
        
        # Базовая цена
        price_layout.addWidget(QLabel("Базовая цена*:"), 0, 0)
        self.base_price_spin = QDoubleSpinBox()
        self.base_price_spin.setRange(0.01, 999999.99)
        self.base_price_spin.setValue(100.00)
        self.base_price_spin.setSuffix(" грн")
        self.base_price_spin.setDecimals(2)
        price_layout.addWidget(self.base_price_spin, 0, 1)
        
        # Скидка
        price_layout.addWidget(QLabel("Скидка:"), 1, 0)
        discount_layout = QHBoxLayout()
        
        self.discount_spin = QDoubleSpinBox()
        self.discount_spin.setRange(0.00, 99.99)
        self.discount_spin.setValue(0.00)
        self.discount_spin.setSuffix(" %")
        self.discount_spin.setDecimals(2)
        discount_layout.addWidget(self.discount_spin)
        
        # Фиксированная скидка в гривнах
        self.fixed_discount_check = QCheckBox("Фиксированная сумма")
        discount_layout.addWidget(self.fixed_discount_check)
        
        price_layout.addLayout(discount_layout, 1, 1)
        
        # Итоговая цена (только для чтения)
        price_layout.addWidget(QLabel("Итоговая цена:"), 2, 0)
        self.total_price_label = QLabel("100.00 грн")
        self.total_price_label.setStyleSheet("font-weight: bold; color: #2E7D32; font-size: 14px;")
        price_layout.addWidget(self.total_price_label, 2, 1)
        
        layout.addWidget(price_group)
        
        # Дополнительная информация
        notes_group = QGroupBox("Дополнительная информация")
        notes_layout = QFormLayout(notes_group)
        
        # Комментарии
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Особенности выполнения услуги, замечания...")
        notes_layout.addRow("Комментарии:", self.notes_edit)
        
        # Статус завершения
        self.is_completed_check = QCheckBox("Услуга выполнена")
        self.is_completed_check.setToolTip("Отметьте когда услуга полностью выполнена")
        notes_layout.addRow("", self.is_completed_check)
        
        layout.addWidget(notes_group)
        
        # Информация об обязательных полях
        info_label = QLabel("* - обязательные поля")
        info_label.setStyleSheet("color: #666; font-size: 12px; margin-top: 5px;")
        layout.addWidget(info_label)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.save_button = QPushButton("Сохранить")
        self.save_button.setDefault(True)
        self.save_button.setMinimumWidth(100)
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.setMinimumWidth(100)
        
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)

    def _connect_signals(self):
        """Подключение сигналов к слотам."""
        self.save_button.clicked.connect(self.save_service)
        self.cancel_button.clicked.connect(self.reject)
        
        # Автоматическое заполнение при выборе услуги
        self.service_combo.currentIndexChanged.connect(self._on_service_selected)
        
        # Пересчет итоговой цены при изменении параметров
        self.quantity_spin.valueChanged.connect(self._calculate_total)
        self.base_price_spin.valueChanged.connect(self._calculate_total)
        self.discount_spin.valueChanged.connect(self._calculate_total)
        self.fixed_discount_check.toggled.connect(self._on_discount_type_changed)
        
        # Валидация формы
        self.service_combo.currentIndexChanged.connect(self._validate_form)
        self.base_price_spin.valueChanged.connect(self._validate_form)

    def _on_service_selected(self, index: int):
        """Обработчик выбора услуги из каталога."""
        service_id = self.service_combo.currentData()
        
        if service_id:
            # Найти выбранную услугу
            selected_service = None
            for service in self.services:
                if service.id == service_id:
                    selected_service = service
                    break
            
            if selected_service:
                # Автозаполнение полей
                self.base_price_spin.setValue(float(selected_service.price))
                self.duration_spin.setValue(float(selected_service.duration_hours or 1.0))
                
                # Показать описание
                description = selected_service.description or "Описание отсутствует"
                self.service_description_label.setText(description)
            else:
                self.service_description_label.setText("")
        else:
            self.service_description_label.setText("")

    def _on_discount_type_changed(self, is_fixed: bool):
        """Обработчик изменения типа скидки."""
        if is_fixed:
            self.discount_spin.setSuffix(" грн")
            self.discount_spin.setRange(0.00, 99999.99)
            self.discount_spin.setToolTip("Фиксированная скидка в гривнах")
        else:
            self.discount_spin.setSuffix(" %")
            self.discount_spin.setRange(0.00, 99.99)
            self.discount_spin.setToolTip("Процентная скидка")
        
        self._calculate_total()

    def _calculate_total(self):
        """Расчет итоговой стоимости услуги."""
        try:
            base_price = Decimal(str(self.base_price_spin.value()))
            quantity = Decimal(str(self.quantity_spin.value()))
            discount_value = Decimal(str(self.discount_spin.value()))
            
            # Расчет стоимости с учетом количества
            subtotal = base_price * quantity
            
            # Применение скидки
            if self.fixed_discount_check.isChecked():
                # Фиксированная скидка в гривнах
                total = subtotal - discount_value
            else:
                # Процентная скидка
                discount_amount = subtotal * (discount_value / Decimal('100'))
                total = subtotal - discount_amount
            
            # Итоговая сумма не может быть отрицательной
            total = max(total, Decimal('0'))
            
            self.total_price_label.setText(f"{total:.2f} грн")
            
            # Цветовая индикация
            if discount_value > 0:
                self.total_price_label.setStyleSheet("font-weight: bold; color: #FF6B35; font-size: 14px;")
            else:
                self.total_price_label.setStyleSheet("font-weight: bold; color: #2E7D32; font-size: 14px;")
            
        except Exception as e:
            self.logger.error(f"Ошибка при расчете итоговой стоимости: {e}")
            self.total_price_label.setText("Ошибка расчета")

    def _load_service_data(self):
        """Загрузка данных услуги для редактирования."""
        if not self.order_service:
            return
        
        # Выбор услуги из каталога
        if self.order_service.service_catalog_id:
            for i in range(self.service_combo.count()):
                if self.service_combo.itemData(i) == self.order_service.service_catalog_id:
                    self.service_combo.setCurrentIndex(i)
                    break
        
        # Выбор исполнителя
        if self.order_service.employee_id:
            for i in range(self.employee_combo.count()):
                if self.employee_combo.itemData(i) == self.order_service.employee_id:
                    self.employee_combo.setCurrentIndex(i)
                    break
        
        # Заполнение остальных полей
        self.quantity_spin.setValue(self.order_service.quantity or 1)
        self.duration_spin.setValue(float(self.order_service.duration_hours or 1.0))
        self.base_price_spin.setValue(float(self.order_service.price or 0))
        
        # Скидка
        discount_amount = float(self.order_service.discount_amount or 0)
        discount_percent = float(self.order_service.discount_percent or 0)
        
        if discount_amount > 0:
            self.fixed_discount_check.setChecked(True)
            self.discount_spin.setValue(discount_amount)
        elif discount_percent > 0:
            self.fixed_discount_check.setChecked(False)
            self.discount_spin.setValue(discount_percent)
        
        self.notes_edit.setPlainText(self.order_service.notes or "")
        self.is_completed_check.setChecked(self.order_service.is_completed or False)

    def _validate_form(self):
        """Валидация формы и активация кнопки сохранения."""
        is_valid = True
        
        # Проверка выбора услуги
        if self.service_combo.currentData() is None:
            is_valid = False
        
        # Проверка базовой цены
        if self.base_price_spin.value() <= 0:
            is_valid = False
        
        self.save_button.setEnabled(is_valid)

    def validate_data(self) -> bool:
        """
        Валидация введенных данных.
        
        Returns:
            bool: True если данные корректны, False в противном случае
        """
        # Проверка выбора услуги
        if self.service_combo.currentData() is None:
            QMessageBox.warning(
                self,
                "Ошибка валидации",
                "Необходимо выбрать услугу из каталога."
            )
            self.service_combo.setFocus()
            return False
        
        # Проверка базовой цены
        if self.base_price_spin.value() <= 0:
            QMessageBox.warning(
                self,
                "Ошибка валидации",
                "Базовая цена должна быть больше нуля."
            )
            self.base_price_spin.setFocus()
            return False
        
        # Проверка количества
        if self.quantity_spin.value() <= 0:
            QMessageBox.warning(
                self,
                "Ошибка валидации",
                "Количество должно быть больше нуля."
            )
            self.quantity_spin.setFocus()
            return False
        
        return True

    def save_data(self) -> bool:
        """
        Сохранение данных услуги в базу данных.
        
        Returns:
            bool: True если сохранение прошло успешно, False в противном случае
        """
        if not self.db_session:
            QMessageBox.critical(
                self,
                "Ошибка",
                "Отсутствует соединение с базой данных."
            )
            return False
        
        try:
            # Получение данных из полей
            service_catalog_id = self.service_combo.currentData()
            employee_id = self.employee_combo.currentData()
            quantity = self.quantity_spin.value()
            duration_hours = Decimal(str(self.duration_spin.value()))
            price = Decimal(str(self.base_price_spin.value()))
            
            # Скидка
            discount_amount = None
            discount_percent = None
            
            if self.discount_spin.value() > 0:
                if self.fixed_discount_check.isChecked():
                    discount_amount = Decimal(str(self.discount_spin.value()))
                else:
                    discount_percent = Decimal(str(self.discount_spin.value()))
            
            notes = self.notes_edit.toPlainText().strip() or None
            is_completed = self.is_completed_check.isChecked()
            
            if self.is_edit_mode:
                # Обновление существующей услуги
                self.order_service.service_catalog_id = service_catalog_id
                self.order_service.employee_id = employee_id
                self.order_service.quantity = quantity
                self.order_service.duration_hours = duration_hours
                self.order_service.price = price
                self.order_service.discount_amount = discount_amount
                self.order_service.discount_percent = discount_percent
                self.order_service.notes = notes
                self.order_service.is_completed = is_completed
                
                self.logger.info(f"Обновлена услуга в заказе ID: {self.order_service.id}")
            else:
                # Создание новой услуги в заказе
                self.order_service = OrderService(
                    order_id=self.order_id,
                    service_catalog_id=service_catalog_id,
                    employee_id=employee_id,
                    quantity=quantity,
                    duration_hours=duration_hours,
                    price=price,
                    discount_amount=discount_amount,
                    discount_percent=discount_percent,
                    notes=notes,
                    is_completed=is_completed
                )
                self.db_session.add(self.order_service)
                
                self.logger.info("Добавлена новая услуга в заказ")
            
            # Сохранение в БД
            self.db_session.commit()
            
            # Испустить сигнал об изменении стоимости
            self.service_cost_changed.emit()
            
            return True
            
        except SQLAlchemyError as e:
            self.db_session.rollback()
            self.logger.error(f"Ошибка при сохранении услуги: {e}")
            
            QMessageBox.critical(
                self,
                "Ошибка базы данных",
                f"Не удалось сохранить услугу:\n{str(e)}"
            )
            return False
        
        except Exception as e:
            self.db_session.rollback()
            self.logger.error(f"Неожиданная ошибка при сохранении услуги: {e}")
            
            QMessageBox.critical(
                self,
                "Неожиданная ошибка",
                f"Произошла ошибка при сохранении:\n{str(e)}"
            )
            return False

    def save_service(self):
        """Обработчик кнопки сохранения."""
        if not self.validate_data():
            return
        
        if self.save_data():
            QMessageBox.information(
                self,
                "Успех",
                "Услуга успешно сохранена!"
            )
            self.accept()

    def get_order_service(self) -> Optional[OrderService]:
        """
        Получение объекта услуги заказа после сохранения.
        
        Returns:
            Optional[OrderService]: Объект услуги или None если не сохранен
        """
        return self.order_service

    def get_total_cost(self) -> Decimal:
        """
        Получение итоговой стоимости услуги.
        
        Returns:
            Decimal: Итоговая стоимость услуги
        """
        try:
            base_price = Decimal(str(self.base_price_spin.value()))
            quantity = Decimal(str(self.quantity_spin.value()))
            discount_value = Decimal(str(self.discount_spin.value()))
            
            subtotal = base_price * quantity
            
            if self.fixed_discount_check.isChecked():
                total = subtotal - discount_value
            else:
                discount_amount = subtotal * (discount_value / Decimal('100'))
                total = subtotal - discount_amount
            
            return max(total, Decimal('0'))
            
        except Exception:
            return Decimal('0')

    def _center_on_parent(self, parent):
        """Центрирование диалога относительно родительского окна."""
        if parent:
            parent_rect = parent.geometry()
            dialog_rect = self.geometry()
            
            center_x = parent_rect.x() + (parent_rect.width() - dialog_rect.width()) // 2
            center_y = parent_rect.y() + (parent_rect.height() - dialog_rect.height()) // 2
            
            self.move(center_x, center_y)


# Пример использования диалога
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from shared_models.common_models import Base
    from sto_app.models_sto import Base as STOBase
    
    app = QApplication(sys.argv)
    
    # Создание тестовой БД в памяти
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    STOBase.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Создание тестовых данных
    test_employee = Employee(name="Иван Мастер", position="Механик")
    test_service = ServiceCatalog(
        name="Замена масла",
        description="Замена моторного масла и масляного фильтра",
        price=Decimal('500.00'),
        duration_hours=Decimal('1.5'),
        is_active=True
    )
    session.add_all([test_employee, test_service])
    session.commit()
    
    # Создание mock родительского объекта с db_session
    class MockParent:
        def __init__(self):
            self.db_session = session
        def geometry(self):
            from PySide6.QtCore import QRect
            return QRect(100, 100, 800, 600)
    
    parent = MockParent()
    
    # Тестирование диалога добавления услуги
    dialog = ServiceDialog(parent, order_id=1)
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        order_service = dialog.get_order_service()
        if order_service:
            total_cost = dialog.get_total_cost()
            print(f"Добавлена услуга. Итоговая стоимость: {total_cost} грн")
    
    sys.exit(app.exec())
