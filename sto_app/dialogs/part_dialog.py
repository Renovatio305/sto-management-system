"""
Диалог для добавления и редактирования запчастей в заказе СТО Management System.

Поддерживает:
- Ручной ввод информации о запчасти
- Настройка цены, количества и скидки
- Указание поставщика
- Расчет итоговой стоимости
- Отметка о наличии на складе
"""

import logging
from typing import Optional
from decimal import Decimal

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLineEdit, QTextEdit, QPushButton, QMessageBox, QLabel,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox
)
from PySide6.QtCore import Qt, Signal

from sto_app.models_sto import OrderPart
from sqlalchemy.exc import SQLAlchemyError


class PartDialog(QDialog):
    """
    Диалог для добавления или редактирования запчасти в заказе.
    
    Поддерживает два режима:
    - Добавление новой запчасти в заказ (order_part=None)
    - Редактирование существующей запчасти в заказе (order_part=OrderPart объект)
    """
    
    # Сигнал для обновления итоговой стоимости в родительском окне
    part_cost_changed = Signal()
    
    def __init__(self, parent=None, order_part: Optional[OrderPart] = None, order_id: Optional[int] = None):
        super().__init__(parent)
        self.order_part = order_part
        self.order_id = order_id
        self.db_session = parent.db_session if parent else None
        self.is_edit_mode = order_part is not None
        
        self.setWindowTitle("Редактирование запчасти" if self.is_edit_mode else "Добавление запчасти")
        self.setModal(True)
        self.setMinimumSize(450, 550)
        self.resize(550, 650)
        
        # Логгер для отслеживания операций
        self.logger = logging.getLogger(__name__)
        
        self._setup_ui()
        self._connect_signals()
        
        if self.is_edit_mode:
            self._load_part_data()
        
        self._calculate_total()
        
        # Центрируем диалог относительно родительского окна
        if parent:
            self._center_on_parent(parent)

    def _setup_ui(self):
        """Настройка пользовательского интерфейса."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        title_label = QLabel("Информация о запчасти")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Основная информация о запчасти
        part_group = QGroupBox("Основная информация")
        part_layout = QFormLayout(part_group)
        part_layout.setSpacing(10)
        
        # Название запчасти
        self.name_edit = QLineEdit()
        self.name_edit.setMaxLength(200)
        self.name_edit.setPlaceholderText("Название запчасти")
        part_layout.addRow("Название*:", self.name_edit)
        
        # Артикул/номер запчасти
        self.part_number_edit = QLineEdit()
        self.part_number_edit.setMaxLength(50)
        self.part_number_edit.setPlaceholderText("Артикул или каталожный номер")
        part_layout.addRow("Артикул:", self.part_number_edit)
        
        # Производитель
        self.manufacturer_edit = QLineEdit()
        self.manufacturer_edit.setMaxLength(100)
        self.manufacturer_edit.setPlaceholderText("Производитель запчасти")
        part_layout.addRow("Производитель:", self.manufacturer_edit)
        
        # Поставщик
        self.supplier_edit = QLineEdit()
        self.supplier_edit.setMaxLength(100)
        self.supplier_edit.setPlaceholderText("Поставщик")
        part_layout.addRow("Поставщик:", self.supplier_edit)
        
        layout.addWidget(part_group)
        
        # Количество и наличие
        quantity_group = QGroupBox("Количество и наличие")
        quantity_layout = QFormLayout(quantity_group)
        quantity_layout.setSpacing(10)
        
        # Количество
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 9999)
        self.quantity_spin.setValue(1)
        self.quantity_spin.setSuffix(" шт.")
        quantity_layout.addRow("Количество*:", self.quantity_spin)
        
        # Единица измерения
        self.unit_combo = QComboBox()
        units = ["шт.", "м", "кг", "л", "упак.", "комп.", "набор"]
        self.unit_combo.addItems(units)
        quantity_layout.addRow("Единица измерения:", self.unit_combo)
        
        # Наличие на складе
        self.in_stock_check = QCheckBox("Есть на складе")
        self.in_stock_check.setChecked(True)
        quantity_layout.addRow("", self.in_stock_check)
        
        layout.addWidget(quantity_group)
        
        # Ценообразование
        price_group = QGroupBox("Ценообразование")
        price_layout = QGridLayout(price_group)
        price_layout.setSpacing(10)
        
        # Цена за единицу
        price_layout.addWidget(QLabel("Цена за единицу*:"), 0, 0)
        self.unit_price_spin = QDoubleSpinBox()
        self.unit_price_spin.setRange(0.01, 999999.99)
        self.unit_price_spin.setValue(100.00)
        self.unit_price_spin.setSuffix(" грн")
        self.unit_price_spin.setDecimals(2)
        price_layout.addWidget(self.unit_price_spin, 0, 1)
        
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
        
        # Итоговая стоимость (только для чтения)
        price_layout.addWidget(QLabel("Итоговая стоимость:"), 2, 0)
        self.total_cost_label = QLabel("100.00 грн")
        self.total_cost_label.setStyleSheet("font-weight: bold; color: #2E7D32; font-size: 14px;")
        price_layout.addWidget(self.total_cost_label, 2, 1)
        
        layout.addWidget(price_group)
        
        # Дополнительная информация
        notes_group = QGroupBox("Дополнительная информация")
        notes_layout = QFormLayout(notes_group)
        
        # Описание/комментарии
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(60)
        self.description_edit.setPlaceholderText("Описание, особенности установки...")
        notes_layout.addRow("Описание:", self.description_edit)
        
        # Статус получения
        self.is_received_check = QCheckBox("Запчасть получена")
        self.is_received_check.setToolTip("Отметьте когда запчасть получена и готова к установке")
        notes_layout.addRow("", self.is_received_check)
        
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
        self.save_button.clicked.connect(self.save_part)
        self.cancel_button.clicked.connect(self.reject)
        
        # Пересчет итоговой стоимости при изменении параметров
        self.quantity_spin.valueChanged.connect(self._calculate_total)
        self.unit_price_spin.valueChanged.connect(self._calculate_total)
        self.discount_spin.valueChanged.connect(self._calculate_total)
        self.fixed_discount_check.toggled.connect(self._on_discount_type_changed)
        
        # Валидация формы
        self.name_edit.textChanged.connect(self._validate_form)
        self.unit_price_spin.valueChanged.connect(self._validate_form)

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
        """Расчет итоговой стоимости запчасти."""
        try:
            unit_price = Decimal(str(self.unit_price_spin.value()))
            quantity = Decimal(str(self.quantity_spin.value()))
            discount_value = Decimal(str(self.discount_spin.value()))
            
            # Расчет стоимости с учетом количества
            subtotal = unit_price * quantity
            
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
            
            self.total_cost_label.setText(f"{total:.2f} грн")
            
            # Цветовая индикация
            if discount_value > 0:
                self.total_cost_label.setStyleSheet("font-weight: bold; color: #FF6B35; font-size: 14px;")
            else:
                self.total_cost_label.setStyleSheet("font-weight: bold; color: #2E7D32; font-size: 14px;")
            
        except Exception as e:
            self.logger.error(f"Ошибка при расчете итоговой стоимости: {e}")
            self.total_cost_label.setText("Ошибка расчета")

    def _load_part_data(self):
        """Загрузка данных запчасти для редактирования."""
        if not self.order_part:
            return
        
        # Заполнение полей
        self.name_edit.setText(self.order_part.name or "")
        self.part_number_edit.setText(self.order_part.part_number or "")
        self.manufacturer_edit.setText(self.order_part.manufacturer or "")
        self.supplier_edit.setText(self.order_part.supplier or "")
        self.quantity_spin.setValue(self.order_part.quantity or 1)
        
        # Единица измерения
        if self.order_part.unit:
            index = self.unit_combo.findText(self.order_part.unit)
            if index >= 0:
                self.unit_combo.setCurrentIndex(index)
        
        self.unit_price_spin.setValue(float(self.order_part.unit_price or 0))
        
        # Скидка
        discount_amount = float(self.order_part.discount_amount or 0)
        discount_percent = float(self.order_part.discount_percent or 0)
        
        if discount_amount > 0:
            self.fixed_discount_check.setChecked(True)
            self.discount_spin.setValue(discount_amount)
        elif discount_percent > 0:
            self.fixed_discount_check.setChecked(False)
            self.discount_spin.setValue(discount_percent)
        
        self.description_edit.setPlainText(self.order_part.description or "")
        self.in_stock_check.setChecked(self.order_part.in_stock if self.order_part.in_stock is not None else True)
        self.is_received_check.setChecked(self.order_part.is_received or False)

    def _validate_form(self):
        """Валидация формы и активация кнопки сохранения."""
        is_valid = True
        
        # Проверка названия запчасти
        if not self.name_edit.text().strip():
            is_valid = False
        
        # Проверка цены
        if self.unit_price_spin.value() <= 0:
            is_valid = False
        
        self.save_button.setEnabled(is_valid)

    def validate_data(self) -> bool:
        """Валидация введенных данных."""
        # Проверка названия
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(
                self,
                "Ошибка валидации",
                "Название запчасти является обязательным полем."
            )
            self.name_edit.setFocus()
            return False
        
        # Проверка цены
        if self.unit_price_spin.value() <= 0:
            QMessageBox.warning(
                self,
                "Ошибка валидации",
                "Цена за единицу должна быть больше нуля."
            )
            self.unit_price_spin.setFocus()
            return False
        
        return True

    def save_data(self) -> bool:
        """Сохранение данных запчасти в базу данных."""
        if not self.db_session:
            QMessageBox.critical(self, "Ошибка", "Отсутствует соединение с базой данных.")
            return False
        
        try:
            # Получение данных из полей
            name = self.name_edit.text().strip()
            part_number = self.part_number_edit.text().strip() or None
            manufacturer = self.manufacturer_edit.text().strip() or None
            supplier = self.supplier_edit.text().strip() or None
            quantity = self.quantity_spin.value()
            unit = self.unit_combo.currentText()
            unit_price = Decimal(str(self.unit_price_spin.value()))
            
            # Скидка
            discount_amount = None
            discount_percent = None
            
            if self.discount_spin.value() > 0:
                if self.fixed_discount_check.isChecked():
                    discount_amount = Decimal(str(self.discount_spin.value()))
                else:
                    discount_percent = Decimal(str(self.discount_spin.value()))
            
            description = self.description_edit.toPlainText().strip() or None
            in_stock = self.in_stock_check.isChecked()
            is_received = self.is_received_check.isChecked()
            
            if self.is_edit_mode:
                # Обновление существующей запчасти
                self.order_part.name = name
                self.order_part.part_number = part_number
                self.order_part.manufacturer = manufacturer
                self.order_part.supplier = supplier
                self.order_part.quantity = quantity
                self.order_part.unit = unit
                self.order_part.unit_price = unit_price
                self.order_part.discount_amount = discount_amount
                self.order_part.discount_percent = discount_percent
                self.order_part.description = description
                self.order_part.in_stock = in_stock
                self.order_part.is_received = is_received
                
                self.logger.info(f"Обновлена запчасть в заказе ID: {self.order_part.id}")
            else:
                # Создание новой запчасти в заказе
                self.order_part = OrderPart(
                    order_id=self.order_id,
                    name=name,
                    part_number=part_number,
                    manufacturer=manufacturer,
                    supplier=supplier,
                    quantity=quantity,
                    unit=unit,
                    unit_price=unit_price,
                    discount_amount=discount_amount,
                    discount_percent=discount_percent,
                    description=description,
                    in_stock=in_stock,
                    is_received=is_received
                )
                self.db_session.add(self.order_part)
                
                self.logger.info("Добавлена новая запчасть в заказ")
            
            # Сохранение в БД
            self.db_session.commit()
            
            # Испустить сигнал об изменении стоимости
            self.part_cost_changed.emit()
            
            return True
            
        except SQLAlchemyError as e:
            self.db_session.rollback()
            self.logger.error(f"Ошибка при сохранении запчасти: {e}")
            QMessageBox.critical(self, "Ошибка базы данных", f"Не удалось сохранить запчасть:\n{str(e)}")
            return False
        
        except Exception as e:
            self.db_session.rollback()
            self.logger.error(f"Неожиданная ошибка при сохранении запчасти: {e}")
            QMessageBox.critical(self, "Неожиданная ошибка", f"Произошла ошибка при сохранении:\n{str(e)}")
            return False

    def save_part(self):
        """Обработчик кнопки сохранения."""
        if not self.validate_data():
            return
        
        if self.save_data():
            QMessageBox.information(self, "Успех", "Запчасть успешно сохранена!")
            self.accept()

    def get_order_part(self) -> Optional[OrderPart]:
        """Получение объекта запчасти заказа после сохранения."""
        return self.order_part

    def get_total_cost(self) -> Decimal:
        """Получение итоговой стоимости запчасти."""
        try:
            unit_price = Decimal(str(self.unit_price_spin.value()))
            quantity = Decimal(str(self.quantity_spin.value()))
            discount_value = Decimal(str(self.discount_spin.value()))
            
            subtotal = unit_price * quantity
            
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
