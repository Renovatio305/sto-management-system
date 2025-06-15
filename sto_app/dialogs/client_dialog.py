"""
Диалог для добавления и редактирования клиентов в СТО Management System.

Поддерживает:
- Создание новых клиентов
- Редактирование существующих клиентов
- Валидацию данных (телефон, email)
- Сохранение в БД с обработкой ошибок
- Автоматическое применение текущей темы
"""

import re
import logging
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QTextEdit, QPushButton, QMessageBox, QLabel
)
from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator

from shared_models.common_models import Client
from sqlalchemy.exc import SQLAlchemyError


class ClientDialog(QDialog):
    """
    Диалог для создания и редактирования клиентов.
    
    Поддерживает два режима:
    - Создание нового клиента (client=None)
    - Редактирование существующего клиента (client=Client объект)
    """
    
    def __init__(self, parent=None, client: Optional[Client] = None):
        super().__init__(parent)
        self.client = client
        self.db_session = parent.db_session if parent else None
        self.is_edit_mode = client is not None
        
        self.setWindowTitle("Редактирование клиента" if self.is_edit_mode else "Новый клиент")
        self.setModal(True)
        self.setMinimumSize(400, 350)
        self.resize(500, 400)
        
        # Логгер для отслеживания операций
        self.logger = logging.getLogger(__name__)
        
        self._setup_ui()
        self._setup_validators()
        self._connect_signals()
        
        if self.is_edit_mode:
            self._load_client_data()
        
        # Центрируем диалог относительно родительского окна
        if parent:
            self._center_on_parent(parent)

    def _setup_ui(self):
        """Настройка пользовательского интерфейса."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок
        title_label = QLabel("Информация о клиенте")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Форма для ввода данных
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Поле для имени
        self.name_edit = QLineEdit()
        self.name_edit.setMaxLength(100)
        self.name_edit.setPlaceholderText("Введите полное имя клиента")
        form_layout.addRow("Имя*:", self.name_edit)
        
        # Поле для телефона
        self.phone_edit = QLineEdit()
        self.phone_edit.setMaxLength(15)
        self.phone_edit.setPlaceholderText("+380XXXXXXXXX")
        form_layout.addRow("Телефон*:", self.phone_edit)
        
        # Поле для email
        self.email_edit = QLineEdit()
        self.email_edit.setMaxLength(100)
        self.email_edit.setPlaceholderText("client@example.com")
        form_layout.addRow("Email:", self.email_edit)
        
        # Поле для адреса
        self.address_edit = QTextEdit()
        self.address_edit.setMaximumHeight(80)
        self.address_edit.setPlaceholderText("Адрес клиента (необязательно)")
        form_layout.addRow("Адрес:", self.address_edit)
        
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
        # Валидатор для украинского номера телефона
        phone_regex = QRegularExpression(r"^\+380\d{9}$")
        phone_validator = QRegularExpressionValidator(phone_regex)
        self.phone_edit.setValidator(phone_validator)
        
        # Валидатор для email
        email_regex = QRegularExpression(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        email_validator = QRegularExpressionValidator(email_regex)
        self.email_edit.setValidator(email_validator)

    def _connect_signals(self):
        """Подключение сигналов к слотам."""
        self.save_button.clicked.connect(self.save_client)
        self.cancel_button.clicked.connect(self.reject)
        
        # Валидация при изменении текста
        self.name_edit.textChanged.connect(self._validate_form)
        self.phone_edit.textChanged.connect(self._validate_form)
        self.email_edit.textChanged.connect(self._validate_form)

    def _load_client_data(self):
        """Загрузка данных клиента для редактирования."""
        if not self.client:
            return
            
        self.name_edit.setText(self.client.name or "")
        self.phone_edit.setText(self.client.phone or "")
        self.email_edit.setText(self.client.email or "")
        self.address_edit.setPlainText(self.client.address or "")

    def _validate_form(self):
        """Валидация формы и активация кнопки сохранения."""
        is_valid = True
        
        # Проверка обязательных полей
        if not self.name_edit.text().strip():
            is_valid = False
        
        if not self.phone_edit.text().strip():
            is_valid = False
        
        # Проверка формата телефона
        if self.phone_edit.text().strip():
            phone_pattern = r"^\+380\d{9}$"
            if not re.match(phone_pattern, self.phone_edit.text().strip()):
                is_valid = False
        
        # Проверка email если указан
        email_text = self.email_edit.text().strip()
        if email_text:
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, email_text):
                is_valid = False
        
        self.save_button.setEnabled(is_valid)

    def validate_data(self) -> bool:
        """
        Валидация введенных данных.
        
        Returns:
            bool: True если данные корректны, False в противном случае
        """
        # Проверка имени
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(
                self, 
                "Ошибка валидации", 
                "Имя клиента является обязательным полем."
            )
            self.name_edit.setFocus()
            return False
        
        if len(name) < 2:
            QMessageBox.warning(
                self,
                "Ошибка валидации",
                "Имя клиента должно содержать минимум 2 символа."
            )
            self.name_edit.setFocus()
            return False
        
        # Проверка телефона
        phone = self.phone_edit.text().strip()
        if not phone:
            QMessageBox.warning(
                self,
                "Ошибка валидации",
                "Номер телефона является обязательным полем."
            )
            self.phone_edit.setFocus()
            return False
        
        phone_pattern = r"^\+380\d{9}$"
        if not re.match(phone_pattern, phone):
            QMessageBox.warning(
                self,
                "Ошибка валидации",
                "Номер телефона должен быть в формате +380XXXXXXXXX"
            )
            self.phone_edit.setFocus()
            return False
        
        # Проверка email (если указан)
        email = self.email_edit.text().strip()
        if email:
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, email):
                QMessageBox.warning(
                    self,
                    "Ошибка валидации",
                    "Введите корректный email адрес."
                )
                self.email_edit.setFocus()
                return False
        
        return True

    def save_data(self) -> bool:
        """
        Сохранение данных клиента в базу данных.
        
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
            name = self.name_edit.text().strip()
            phone = self.phone_edit.text().strip()
            email = self.email_edit.text().strip() or None
            address = self.address_edit.toPlainText().strip() or None
            
            if self.is_edit_mode:
                # Обновление существующего клиента
                self.client.name = name
                self.client.phone = phone
                self.client.email = email
                self.client.address = address
                
                self.logger.info(f"Обновлен клиент ID: {self.client.id}")
            else:
                # Создание нового клиента
                self.client = Client(
                    name=name,
                    phone=phone,
                    email=email,
                    address=address
                )
                self.db_session.add(self.client)
                
                self.logger.info("Создан новый клиент")
            
            # Сохранение в БД
            self.db_session.commit()
            
            return True
            
        except SQLAlchemyError as e:
            self.db_session.rollback()
            self.logger.error(f"Ошибка при сохранении клиента: {e}")
            
            QMessageBox.critical(
                self,
                "Ошибка базы данных",
                f"Не удалось сохранить клиента:\n{str(e)}"
            )
            return False
        
        except Exception as e:
            self.db_session.rollback()
            self.logger.error(f"Неожиданная ошибка при сохранении клиента: {e}")
            
            QMessageBox.critical(
                self,
                "Неожиданная ошибка",
                f"Произошла ошибка при сохранении:\n{str(e)}"
            )
            return False

    def save_client(self):
        """Обработчик кнопки сохранения."""
        if not self.validate_data():
            return
        
        if self.save_data():
            QMessageBox.information(
                self,
                "Успех",
                "Клиент успешно сохранен!"
            )
            self.accept()

    def get_client(self) -> Optional[Client]:
        """
        Получение объекта клиента после сохранения.
        
        Returns:
            Optional[Client]: Объект клиента или None если не сохранен
        """
        return self.client

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
    
    # Создание mock родительского объекта с db_session
    class MockParent:
        def __init__(self):
            self.db_session = session
        def geometry(self):
            from PySide6.QtCore import QRect
            return QRect(100, 100, 800, 600)
    
    parent = MockParent()
    
    # Тестирование диалога создания клиента
    dialog = ClientDialog(parent)
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        client = dialog.get_client()
        if client:
            print(f"Создан клиент: {client.name}, {client.phone}")
    
    sys.exit(app.exec())
