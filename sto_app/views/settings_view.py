# sto_app/views/settings_view.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QFormLayout, 
                              QComboBox, QPushButton, QLabel, QCheckBox, 
                              QSpinBox, QLineEdit, QTextEdit, QHBoxLayout)
from PySide6.QtCore import Signal, QSettings
from PySide6.QtGui import QFont


class SettingsView(QWidget):
    """Представление настроек приложения"""
    
    # Сигналы
    theme_changed = Signal(str)
    language_changed = Signal(str)
    
    def __init__(self, db_session=None, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        self.settings = QSettings('STOApp', 'Settings')
        
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Настройка интерфейса настроек"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Заголовок
        title_label = QLabel('⚙️ Настройки приложения')
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Группа интерфейса
        interface_group = QGroupBox("🎨 Интерфейс")
        interface_layout = QFormLayout(interface_group)
        
        # Тема
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(['Светлая', 'Темная'])
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        interface_layout.addRow("Тема:", self.theme_combo)
        
        # Язык
        self.language_combo = QComboBox()
        self.language_combo.addItems(['Украинский', 'Русский', 'English'])
        self.language_combo.currentTextChanged.connect(self.on_language_changed)
        interface_layout.addRow("Язык:", self.language_combo)
        
        # Размер шрифта
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(10)
        self.font_size_spin.valueChanged.connect(self.save_settings)
        interface_layout.addRow("Размер шрифта:", self.font_size_spin)
        
        layout.addWidget(interface_group)
        
        # Группа приложения
        app_group = QGroupBox("📊 Настройки приложения")
        app_layout = QFormLayout(app_group)
        
        # Автосохранение
        self.autosave_check = QCheckBox("Включить автосохранение")
        self.autosave_check.setChecked(True)
        self.autosave_check.stateChanged.connect(self.save_settings)
        app_layout.addRow(self.autosave_check)
        
        # Интервал автосохранения
        self.autosave_interval_spin = QSpinBox()
        self.autosave_interval_spin.setRange(1, 60)
        self.autosave_interval_spin.setValue(5)
        self.autosave_interval_spin.setSuffix(" мин")
        self.autosave_interval_spin.valueChanged.connect(self.save_settings)
        app_layout.addRow("Интервал автосохранения:", self.autosave_interval_spin)
        
        # Резервное копирование
        self.backup_check = QCheckBox("Автоматическое резервное копирование")
        self.backup_check.setChecked(False)
        self.backup_check.stateChanged.connect(self.save_settings)
        app_layout.addRow(self.backup_check)
        
        layout.addWidget(app_group)
        
        # Группа СТО
        sto_group = QGroupBox("🔧 Настройки СТО")
        sto_layout = QFormLayout(sto_group)
        
        # Название СТО
        self.sto_name_edit = QLineEdit()
        self.sto_name_edit.setPlaceholderText("Название вашего СТО")
        self.sto_name_edit.textChanged.connect(self.save_settings)
        sto_layout.addRow("Название СТО:", self.sto_name_edit)
        
        # Адрес
        self.sto_address_edit = QLineEdit()
        self.sto_address_edit.setPlaceholderText("Адрес СТО")
        self.sto_address_edit.textChanged.connect(self.save_settings)
        sto_layout.addRow("Адрес:", self.sto_address_edit)
        
        # Телефон
        self.sto_phone_edit = QLineEdit()
        self.sto_phone_edit.setPlaceholderText("+380...")
        self.sto_phone_edit.textChanged.connect(self.save_settings)
        sto_layout.addRow("Телефон:", self.sto_phone_edit)
        
        # НДС по умолчанию
        self.default_vat_spin = QSpinBox()
        self.default_vat_spin.setRange(0, 30)
        self.default_vat_spin.setValue(20)
        self.default_vat_spin.setSuffix(" %")
        self.default_vat_spin.valueChanged.connect(self.save_settings)
        sto_layout.addRow("НДС по умолчанию:", self.default_vat_spin)
        
        layout.addWidget(sto_group)
        
        # Группа базы данных
        db_group = QGroupBox("🗄️ База данных")
        db_layout = QVBoxLayout(db_group)
        
        # Информация о БД
        self.db_info_label = QLabel("SQLite: sto_database.db")
        self.db_info_label.setStyleSheet("color: #666; font-style: italic;")
        db_layout.addWidget(self.db_info_label)
        
        # Кнопки управления БД
        db_buttons_layout = QHBoxLayout()
        
        self.backup_db_btn = QPushButton("📋 Создать резервную копию")
        self.backup_db_btn.clicked.connect(self.backup_database)
        db_buttons_layout.addWidget(self.backup_db_btn)
        
        self.restore_db_btn = QPushButton("♻️ Восстановить из копии")
        self.restore_db_btn.clicked.connect(self.restore_database)
        db_buttons_layout.addWidget(self.restore_db_btn)
        
        self.optimize_db_btn = QPushButton("⚡ Оптимизировать")
        self.optimize_db_btn.clicked.connect(self.optimize_database)
        db_buttons_layout.addWidget(self.optimize_db_btn)
        
        db_layout.addLayout(db_buttons_layout)
        
        layout.addWidget(db_group)
        
        # Заполнитель
        layout.addStretch()
        
        # Кнопки действий
        actions_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("🔄 Сбросить настройки")
        self.reset_btn.setProperty('danger', True)
        self.reset_btn.clicked.connect(self.reset_settings)
        actions_layout.addWidget(self.reset_btn)
        
        actions_layout.addStretch()
        
        self.save_btn = QPushButton("💾 Сохранить настройки")
        self.save_btn.setProperty('accent', True)
        self.save_btn.clicked.connect(self.save_settings)
        actions_layout.addWidget(self.save_btn)
        
        layout.addLayout(actions_layout)
        
    def on_theme_changed(self, theme_text):
        """Обработка смены темы"""
        theme_map = {'Светлая': 'light', 'Темная': 'dark'}
        theme = theme_map.get(theme_text, 'light')
        self.save_settings()
        self.theme_changed.emit(theme)
        
    def on_language_changed(self, language):
        """Обработка смены языка"""
        self.save_settings()
        self.language_changed.emit(language)
        
    def load_settings(self):
        """Загрузка настроек"""
        try:
            # Тема
            theme = self.settings.value('theme', 'light')
            theme_text = 'Светлая' if theme == 'light' else 'Темная'
            index = self.theme_combo.findText(theme_text)
            if index >= 0:
                self.theme_combo.setCurrentIndex(index)
                
            # Язык
            language = self.settings.value('language', 'Украинский')
            index = self.language_combo.findText(language)
            if index >= 0:
                self.language_combo.setCurrentIndex(index)
                
            # Размер шрифта
            font_size = int(self.settings.value('font_size', 10))
            self.font_size_spin.setValue(font_size)
            
            # Автосохранение
            autosave = self.settings.value('autosave', True, type=bool)
            self.autosave_check.setChecked(autosave)
            
            # Интервал автосохранения
            interval = int(self.settings.value('autosave_interval', 5))
            self.autosave_interval_spin.setValue(interval)
            
            # Резервное копирование
            backup = self.settings.value('auto_backup', False, type=bool)
            self.backup_check.setChecked(backup)
            
            # Настройки СТО
            self.sto_name_edit.setText(self.settings.value('sto_name', ''))
            self.sto_address_edit.setText(self.settings.value('sto_address', ''))
            self.sto_phone_edit.setText(self.settings.value('sto_phone', ''))
            
            # НДС
            vat = int(self.settings.value('default_vat', 20))
            self.default_vat_spin.setValue(vat)
            
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
            
    def save_settings(self):
        """Сохранение настроек"""
        try:
            # Тема
            theme_text = self.theme_combo.currentText()
            theme = 'light' if theme_text == 'Светлая' else 'dark'
            self.settings.setValue('theme', theme)
            
            # Язык
            self.settings.setValue('language', self.language_combo.currentText())
            
            # Размер шрифта
            self.settings.setValue('font_size', self.font_size_spin.value())
            
            # Автосохранение
            self.settings.setValue('autosave', self.autosave_check.isChecked())
            self.settings.setValue('autosave_interval', self.autosave_interval_spin.value())
            
            # Резервное копирование
            self.settings.setValue('auto_backup', self.backup_check.isChecked())
            
            # Настройки СТО
            self.settings.setValue('sto_name', self.sto_name_edit.text())
            self.settings.setValue('sto_address', self.sto_address_edit.text())
            self.settings.setValue('sto_phone', self.sto_phone_edit.text())
            
            # НДС
            self.settings.setValue('default_vat', self.default_vat_spin.value())
            
            # Синхронизация настроек
            self.settings.sync()
            
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")
            
    def reset_settings(self):
        """Сброс настроек к значениям по умолчанию"""
        from PySide6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self, 'Подтверждение',
            'Сбросить все настройки к значениям по умолчанию?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )