"""
Диалог для добавления и редактирования автомобилей в СТО Management System.

Поддерживает:
- Создание новых автомобилей для клиентов
- Редактирование существующих автомобилей
- Валидацию VIN номера (17 символов)
- Связь с клиентами через ComboBox
- Сохранение в БД с обработкой ошибок
"""

import re
import logging
from typing import Optional, List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QTextEdit, QPushButton, QMessageBox, QLabel,
    QComboBox, QSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator

from shared_models.common_models import Car, Client
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select


class CarDialog(QDialog):
    """
    Диалог для создания и редактирования автомобилей.
    
    Поддерживает два режима:
    - Создание нового автомобиля (car=None, client_id может быть указан)
    - Редактирование существующего автомобиля (car=Car объект)
    """
    
    def __init__(self, parent=None, car: Optional[Car] = None, client_id: Optional[int] = None):
        super().__init__(parent)
        self.car = car
        self.client_id = client_id
        self.db_session = parent.db_session if parent else None
        
        # ИСПРАВЛЕНИЕ: если car это int, то это ID, загружаем объект
        if isinstance(car, int):
            try:
                from sqlalchemy import select
                stmt = select(Car).where(Car.id == car)
                result = self.db_session.execute(stmt)
                self.car = result.scalar_one_or_none()
                self.is_edit_mode = self.car is not None
            except Exception as e:
                logger.error(f"Ошибка загрузки автомобиля по ID {car}: {e}")
                self.car = None
                self.is_edit_mode = False
        else:
            self.is_edit_mode = car is not None
        
        self.setWindowTitle("Редактирование автомобиля" if self.is_edit_mode else "Новый автомобиль")
        self.setModal(True)
        self.setMinimumSize(450, 500)
        self.resize(550, 600)
        
        # Логгер для отслеживания операций
        self.logger = logging.getLogger(__name__)
        
        # Список клиентов для ComboBox
        self.clients: List[Client] = []
        
        self._load_clients()
        self._setup_ui()
        self._setup_validators()
        self._connect_signals()
        
        if self.is_edit_mode:
            self._load_car_data()
        elif self.client_id:
            self._select_client_by_id(self.client_id)
        
        # Центрируем диалог относительно родительского окна
        if parent:
            self._center_on_parent(parent)

    def _load_clients(self):
        """Загрузка списка клиентов из базы данных."""
        if not self.db_session:
            return
        
        try:
            stmt = select(Client).order_by(Client.name)
            result = self.db_session.execute(stmt)
            self.clients = result.scalars().all()
            
        except SQLAlchemyError as e:
            self.logger.error(f"Ошибка при загрузке клиентов: {e}")
            QMessageBox.warning(
                self,
                "Предупреждение",
                "Не удалось загрузить список клиентов из базы данных."
            )

    def _setup_ui(self):
        """Настройка пользовательского интерфейса."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        title_label = QLabel("Информация об автомобиле")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Форма для ввода данных
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        
        # Выбор клиента
        self.client_combo = QComboBox()
        self.client_combo.setMinimumHeight(30)
        self.client_combo.addItem("-- Выберите клиента --", None)
        
        for client in self.clients:
            display_text = f"{client.name} ({client.phone})"
            self.client_combo.addItem(display_text, client.id)
        
        form_layout.addRow("Клиент*:", self.client_combo)
        
        # Марка автомобиля
        self.make_edit = QLineEdit()
        self.make_edit.setMaxLength(50)
        self.make_edit.setPlaceholderText("Toyota, BMW, Mercedes и т.д.")
        form_layout.addRow("Марка*:", self.make_edit)
        
        # Модель автомобиля
        self.model_edit = QLineEdit()
        self.model_edit.setMaxLength(50)
        self.model_edit.setPlaceholderText("Camry, X5, E-Class и т.д.")
        form_layout.addRow("Модель*:", self.model_edit)
        
        # Год выпуска
        self.year_spin = QSpinBox()
        self.year_spin.setRange(1950, 2030)
        self.year_spin.setValue(2020)
        self.year_spin.setSuffix(" г.")
        form_layout.addRow("Год выпуска*:", self.year_spin)
        
        # VIN номер
        self.vin_edit = QLineEdit()
        self.vin_edit.setMaxLength(17)
        self.vin_edit.setPlaceholderText("17 символов (буквы и цифры)")
        self.vin_edit.textChanged.connect(self._format_vin)
        form_layout.addRow("VIN номер*:", self.vin_edit)
        
        # Номерной знак
        self.license_plate_edit = QLineEdit()
        self.license_plate_edit.setMaxLength(10)
        self.license_plate_edit.setPlaceholderText("AA1234BB")
        form_layout.addRow("Номерной знак:", self.license_plate_edit)
        
        # Цвет
        self.color_edit = QLineEdit()
        self.color_edit.setMaxLength(30)
        self.color_edit.setPlaceholderText("Белый, Черный, Серебристый и т.д.")
        form_layout.addRow("Цвет:", self.color_edit)
        
        # Пробег
        self.mileage_spin = QSpinBox()
        self.mileage_spin.setRange(0, 9999999)
        self.mileage_spin.setSuffix(" км")
        self.mileage_spin.setValue(0)
        form_layout.addRow("Пробег:", self.mileage_spin)
        
        # Объем двигателя
        self.engine_volume_edit = QLineEdit()
        self.engine_volume_edit.setMaxLength(10)
        self.engine_volume_edit.setPlaceholderText("1.6, 2.0, 3.5 и т.д.")
        form_layout.addRow("Объем двигателя (л):", self.engine_volume_edit)
        
        # Тип топлива
        self.fuel_type_combo = QComboBox()
        fuel_types = ["Не указано", "Бензин", "Дизель", "Газ", "Электро", "Гибрид"]
        self.fuel_type_combo.addItems(fuel_types)
        form_layout.addRow("Тип топлива:", self.fuel_type_combo)
        
        # Активный автомобиль
        self.is_active_check = QCheckBox("Активный автомобиль")
        self.is_active_check.setChecked(True)
        self.is_active_check.setToolTip("Неактивные автомобили не отображаются в списках")
        form_layout.addRow("", self.is_active_check)
        
        # Заметки
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Дополнительная информация об автомобиле")
        form_layout.addRow("Заметки:", self.notes_edit)
        
        layout.addLayout(form_layout)
        
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

    def _setup_validators(self):
        """Настройка валидаторов для полей ввода."""
        # Валидатор для VIN номера (17 символов, латиница + цифры)
        vin_regex = QRegularExpression(r"^[A-HJ-NPR-Z0-9]{17}$")
        vin_validator = QRegularExpressionValidator(vin_regex)
        self.vin_edit.setValidator(vin_validator)
        
        # Валидатор для номерного знака (украинский формат)
        plate_regex = QRegularExpression(r"^[A-Z]{2}\d{4}[A-Z]{2}$|^[A-Z]{3}\d{3}$|^[A-Z]\d{4}[A-Z]{2}$")
        plate_validator = QRegularExpressionValidator(plate_regex)
        self.license_plate_edit.setValidator(plate_validator)
        
        # Валидатор для объема двигателя
        engine_regex = QRegularExpression(r"^\d{1,2}(\.\d{1,2})?$")
        engine_validator = QRegularExpressionValidator(engine_regex)
        self.engine_volume_edit.setValidator(engine_validator)

    def _connect_signals(self):
        """Подключение сигналов к слотам."""
        self.save_button.clicked.connect(self.save_car)
        self.cancel_button.clicked.connect(self.reject)
        
        # Валидация при изменении данных
        self.client_combo.currentIndexChanged.connect(self._validate_form)
        self.make_edit.textChanged.connect(self._validate_form)
        self.model_edit.textChanged.connect(self._validate_form)
        self.vin_edit.textChanged.connect(self._validate_form)

    def _format_vin(self, text: str):
        """Форматирование VIN номера в верхний регистр."""
        formatted_text = text.upper()
        if formatted_text != text:
            cursor_pos = self.vin_edit.cursorPosition()
            self.vin_edit.setText(formatted_text)
            self.vin_edit.setCursorPosition(cursor_pos)

    def _load_car_data(self):
        """Загрузка данных автомобиля для редактирования."""
        if not self.car:
            return
        
        # Выбор клиента
        for i in range(self.client_combo.count()):
            if self.client_combo.itemData(i) == self.car.client_id:
                self.client_combo.setCurrentIndex(i)
                break
        
        # Заполнение остальных полей
        self.make_edit.setText(self.car.make or "")
        self.model_edit.setText(self.car.model or "")
        self.year_spin.setValue(self.car.year or 2020)
        self.vin_edit.setText(self.car.vin or "")
        self.license_plate_edit.setText(self.car.license_plate or "")
        self.color_edit.setText(self.car.color or "")
        self.mileage_spin.setValue(self.car.mileage or 0)
        self.engine_volume_edit.setText(str(self.car.engine_volume) if self.car.engine_volume else "")
        
        # Тип топлива
        if self.car.fuel_type:
            index = self.fuel_type_combo.findText(self.car.fuel_type)
            if index >= 0:
                self.fuel_type_combo.setCurrentIndex(index)
        
        self.is_active_check.setChecked(self.car.is_active if self.car.is_active is not None else True)
        self.notes_edit.setPlainText(self.car.notes or "")

    def _select_client_by_id(self, client_id: int):
        """Выбор клиента по ID в ComboBox."""
        for i in range(self.client_combo.count()):
            if self.client_combo.itemData(i) == client_id:
                self.client_combo.setCurrentIndex(i)
                break

    def _validate_form(self):
        """Валидация формы и активация кнопки сохранения."""
        is_valid = True
        
        # Проверка выбора клиента
        if self.client_combo.currentData() is None:
            is_valid = False
        
        # Проверка обязательных полей
        if not self.make_edit.text().strip():
            is_valid = False
        
        if not self.model_edit.text().strip():
            is_valid = False
        
        if not self.vin_edit.text().strip():
            is_valid = False
        
        # Проверка формата VIN
        vin_text = self.vin_edit.text().strip()
        if vin_text and len(vin_text) != 17:
            is_valid = False
        
        self.save_button.setEnabled(is_valid)

    def validate_data(self) -> bool:
        """
        Валидация введенных данных.
        
        Returns:
            bool: True если данные корректны, False в противном случае
        """
        # Проверка выбора клиента
        if self.client_combo.currentData() is None:
            QMessageBox.warning(
                self,
                "Ошибка валидации",
                "Необходимо выбрать клиента для автомобиля."
            )
            self.client_combo.setFocus()
            return False
        
        # Проверка марки
        make = self.make_edit.text().strip()
        if not make:
            QMessageBox.warning(
                self,
                "Ошибка валидации",
                "Марка автомобиля является обязательным полем."
            )
            self.make_edit.setFocus()
            return False
        
        # Проверка модели
        model = self.model_edit.text().strip()
        if not model:
            QMessageBox.warning(
                self,
                "Ошибка валидации",
                "Модель автомобиля является обязательным полем."
            )
            self.model_edit.setFocus()
            return False
        
        # Проверка VIN номера
        vin = self.vin_edit.text().strip()
        if not vin:
            QMessageBox.warning(
                self,
                "Ошибка валидации",
                "VIN номер является обязательным полем."
            )
            self.vin_edit.setFocus()
            return False
        
        if len(vin) != 17:
            QMessageBox.warning(
                self,
                "Ошибка валидации",
                "VIN номер должен содержать точно 17 символов."
            )
            self.vin_edit.setFocus()
            return False
        
        # Проверка уникальности VIN
        if not self._check_vin_uniqueness(vin):
            QMessageBox.warning(
                self,
                "Ошибка валидации",
                "Автомобиль с таким VIN номером уже существует в базе данных."
            )
            self.vin_edit.setFocus()
            return False
        
        # Проверка объема двигателя
        engine_volume_text = self.engine_volume_edit.text().strip()
        if engine_volume_text:
            try:
                engine_volume = float(engine_volume_text)
                if engine_volume <= 0 or engine_volume > 20:
                    QMessageBox.warning(
                        self,
                        "Ошибка валидации",
                        "Объем двигателя должен быть от 0.1 до 20.0 литров."
                    )
                    self.engine_volume_edit.setFocus()
                    return False
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Ошибка валидации",
                    "Объем двигателя должен быть числом."
                )
                self.engine_volume_edit.setFocus()
                return False
        
        return True

    def _check_vin_uniqueness(self, vin: str) -> bool:
        """
        Проверка уникальности VIN номера.
        
        Args:
            vin: VIN номер для проверки
            
        Returns:
            bool: True если VIN уникален, False если уже существует
        """
        if not self.db_session:
            return True  # Если нет сессии, пропускаем проверку
        
        try:
            stmt = select(Car).where(Car.vin == vin)
            
            # Если редактируем существующий автомобиль, исключаем его из проверки
            if self.is_edit_mode and self.car:
                stmt = stmt.where(Car.id != self.car.id)
            
            result = self.db_session.execute(stmt)
            existing_car = result.scalar_one_or_none()
            
            return existing_car is None
            
        except SQLAlchemyError as e:
            self.logger.error(f"Ошибка при проверке уникальности VIN: {e}")
            return True  # В случае ошибки разрешаем продолжить

    def save_data(self) -> bool:
        """
        Сохранение данных автомобиля в базу данных.
        
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
            client_id = self.client_combo.currentData()
            make = self.make_edit.text().strip()
            model = self.model_edit.text().strip()
            year = self.year_spin.value()
            vin = self.vin_edit.text().strip()
            license_plate = self.license_plate_edit.text().strip() or None
            color = self.color_edit.text().strip() or None
            mileage = self.mileage_spin.value()
            
            engine_volume = None
            engine_volume_text = self.engine_volume_edit.text().strip()
            if engine_volume_text:
                engine_volume = float(engine_volume_text)
            
            fuel_type = self.fuel_type_combo.currentText()
            if fuel_type == "Не указано":
                fuel_type = None
            
            is_active = self.is_active_check.isChecked()
            notes = self.notes_edit.toPlainText().strip() or None
            
            if self.is_edit_mode:
                # Обновление существующего автомобиля
                self.car.client_id = client_id
                self.car.make = make
                self.car.model = model
                self.car.year = year
                self.car.vin = vin
                self.car.license_plate = license_plate
                self.car.color = color
                self.car.mileage = mileage
                self.car.engine_volume = engine_volume
                self.car.fuel_type = fuel_type
                self.car.is_active = is_active
                self.car.notes = notes
                
                self.logger.info(f"Обновлен автомобиль ID: {self.car.id}")
            else:
                # Создание нового автомобиля
                self.car = Car(
                    client_id=client_id,
                    make=make,
                    model=model,
                    year=year,
                    vin=vin,
                    license_plate=license_plate,
                    color=color,
                    mileage=mileage,
                    engine_volume=engine_volume,
                    fuel_type=fuel_type,
                    is_active=is_active,
                    notes=notes
                )
                self.db_session.add(self.car)
                
                self.logger.info("Создан новый автомобиль")
            
            # Сохранение в БД
            self.db_session.commit()
            
            return True
            
        except SQLAlchemyError as e:
            self.db_session.rollback()
            self.logger.error(f"Ошибка при сохранении автомобиля: {e}")
            
            QMessageBox.critical(
                self,
                "Ошибка базы данных",
                f"Не удалось сохранить автомобиль:\n{str(e)}"
            )
            return False
        
        except Exception as e:
            self.db_session.rollback()
            self.logger.error(f"Неожиданная ошибка при сохранении автомобиля: {e}")
            
            QMessageBox.critical(
                self,
                "Неожиданная ошибка",
                f"Произошла ошибка при сохранении:\n{str(e)}"
            )
            return False

    def save_car(self):
        """Обработчик кнопки сохранения."""
        if not self.validate_data():
            return
        
        if self.save_data():
            QMessageBox.information(
                self,
                "Успех",
                "Автомобиль успешно сохранен!"
            )
            self.accept()

    def get_car(self) -> Optional[Car]:
        """
        Получение объекта автомобиля после сохранения.
        
        Returns:
            Optional[Car]: Объект автомобиля или None если не сохранен
        """
        return self.car

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
    
    app = QApplication(sys.argv)
    
    # Создание тестовой БД в памяти
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Создание тестового клиента
    test_client = Client(name="Тест Клиент", phone="+380501234567")
    session.add(test_client)
    session.commit()
    
    # Создание mock родительского объекта с db_session
    class MockParent:
        def __init__(self):
            self.db_session = session
        def geometry(self):
            from PySide6.QtCore import QRect
            return QRect(100, 100, 800, 600)
    
    parent = MockParent()
    
    # Тестирование диалога создания автомобиля
    dialog = CarDialog(parent, client_id=test_client.id)
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        car = dialog.get_car()
        if car:
            print(f"Создан автомобиль: {car.make} {car.model}, VIN: {car.vin}")
    
    sys.exit(app.exec())
