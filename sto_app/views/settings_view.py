# sto_app/views/settings_view.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QGroupBox, QComboBox, QCheckBox, QPushButton,
                              QLabel, QSpinBox, QLineEdit, QTextEdit, QSlider,
                              QFileDialog, QMessageBox, QTabWidget)
from PySide6.QtCore import Qt, Signal, QSettings
from PySide6.QtGui import QFont
import logging


class SettingsView(QWidget):
    """Представление настроек приложения"""
    
    # ✅ ДОБАВЛЕНЫ недостающие сигналы
    theme_changed = Signal(str)     # Сигнал смены темы
    language_changed = Signal(str)  # Сигнал смены языка
    settings_changed = Signal()     # Сигнал изменения настроек
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.settings = QSettings('STOApp', 'Settings')
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Заголовок
        title_label = QLabel('⚙️ Настройки приложения')
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Табы настроек
        self.tab_widget = QTabWidget()
        
        # Вкладка интерфейса
        interface_tab = self.create_interface_tab()
        self.tab_widget.addTab(interface_tab, '🎨 Интерфейс')
        
        # Вкладка системы
        system_tab = self.create_system_tab()
        self.tab_widget.addTab(system_tab, '💻 Система')
        
        # Вкладка резервного копирования
        backup_tab = self.create_backup_tab()
        self.tab_widget.addTab(backup_tab, '💾 Резервные копии')
        
        layout.addWidget(self.tab_widget)
        
        # Кнопки действий
        actions_layout = QHBoxLayout()
        
        self.save_btn = QPushButton('💾 Сохранить')
        self.save_btn.clicked.connect(self.save_settings)
        actions_layout.addWidget(self.save_btn)
        
        self.reset_btn = QPushButton('🔄 Сбросить')
        self.reset_btn.clicked.connect(self.reset_settings)
        actions_layout.addWidget(self.reset_btn)
        
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)
    
    def create_interface_tab(self):
        """Создание вкладки настроек интерфейса"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Группа темы
        theme_group = QGroupBox('Тема оформления')
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(['Светлая', 'Темная', 'Системная'])
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        theme_layout.addRow('Тема:', self.theme_combo)
        
        layout.addWidget(theme_group)
        
        # Группа языка
        language_group = QGroupBox('Язык интерфейса')
        language_layout = QFormLayout(language_group)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(['Українська', 'English', 'Русский'])
        self.language_combo.currentTextChanged.connect(self.on_language_changed)
        language_layout.addRow('Язык:', self.language_combo)
        
        layout.addWidget(language_group)
        
        # Группа отображения
        display_group = QGroupBox('Отображение')
        display_layout = QFormLayout(display_group)
        
        self.show_splash_cb = QCheckBox('Показывать заставку при запуске')
        self.show_splash_cb.setChecked(True)
        display_layout.addRow('', self.show_splash_cb)
        
        self.show_tips_cb = QCheckBox('Показывать подсказки')
        self.show_tips_cb.setChecked(True)
        display_layout.addRow('', self.show_tips_cb)
        
        self.animations_cb = QCheckBox('Включить анимации')
        self.animations_cb.setChecked(True)
        display_layout.addRow('', self.animations_cb)
        
        layout.addWidget(display_group)
        
        layout.addStretch()
        return widget
    
    def create_system_tab(self):
        """Создание вкладки системных настроек"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Группа автосохранения
        autosave_group = QGroupBox('Автосохранение')
        autosave_layout = QFormLayout(autosave_group)
        
        self.autosave_enabled_cb = QCheckBox('Включить автосохранение')
        self.autosave_enabled_cb.setChecked(True)
        autosave_layout.addRow('', self.autosave_enabled_cb)
        
        self.autosave_interval_spin = QSpinBox()
        self.autosave_interval_spin.setRange(1, 60)
        self.autosave_interval_spin.setValue(5)
        self.autosave_interval_spin.setSuffix(' мин')
        autosave_layout.addRow('Интервал:', self.autosave_interval_spin)
        
        layout.addWidget(autosave_group)
        
        # Группа логирования
        logging_group = QGroupBox('Логирование')
        logging_layout = QFormLayout(logging_group)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(['DEBUG', 'INFO', 'WARNING', 'ERROR'])
        self.log_level_combo.setCurrentText('INFO')
        logging_layout.addRow('Уровень логов:', self.log_level_combo)
        
        self.log_to_file_cb = QCheckBox('Сохранять логи в файл')
        self.log_to_file_cb.setChecked(True)
        logging_layout.addRow('', self.log_to_file_cb)
        
        layout.addWidget(logging_group)
        
        # Группа производительности
        performance_group = QGroupBox('Производительность')
        performance_layout = QFormLayout(performance_group)
        
        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(10, 1000)
        self.cache_size_spin.setValue(100)
        self.cache_size_spin.setSuffix(' МБ')
        performance_layout.addRow('Размер кэша:', self.cache_size_spin)
        
        self.preload_data_cb = QCheckBox('Предзагрузка данных')
        self.preload_data_cb.setChecked(True)
        performance_layout.addRow('', self.preload_data_cb)
        
        layout.addWidget(performance_group)
        
        layout.addStretch()
        return widget
    
    def create_backup_tab(self):
        """Создание вкладки настроек резервного копирования"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Группа автобэкапа
        autobackup_group = QGroupBox('Автоматическое резервное копирование')
        autobackup_layout = QFormLayout(autobackup_group)
        
        self.autobackup_enabled_cb = QCheckBox('Включить автобэкап')
        self.autobackup_enabled_cb.setChecked(True)
        autobackup_layout.addRow('', self.autobackup_enabled_cb)
        
        self.backup_interval_spin = QSpinBox()
        self.backup_interval_spin.setRange(1, 168)
        self.backup_interval_spin.setValue(24)
        self.backup_interval_spin.setSuffix(' ч')
        autobackup_layout.addRow('Интервал:', self.backup_interval_spin)
        
        self.backup_path_edit = QLineEdit()
        self.backup_path_edit.setPlaceholderText('Путь для сохранения резервных копий')
        backup_path_button = QPushButton('📁 Выбрать')
        backup_path_button.clicked.connect(self.select_backup_path)
        
        backup_path_layout = QHBoxLayout()
        backup_path_layout.addWidget(self.backup_path_edit)
        backup_path_layout.addWidget(backup_path_button)
        autobackup_layout.addRow('Папка:', backup_path_layout)
        
        self.max_backups_spin = QSpinBox()
        self.max_backups_spin.setRange(1, 100)
        self.max_backups_spin.setValue(30)
        autobackup_layout.addRow('Макс. копий:', self.max_backups_spin)
        
        layout.addWidget(autobackup_group)
        
        # Группа ручного управления
        manual_group = QGroupBox('Ручное управление')
        manual_layout = QVBoxLayout(manual_group)
        
        buttons_layout = QHBoxLayout()
        
        create_backup_btn = QPushButton('💾 Создать резервную копию')
        create_backup_btn.clicked.connect(self.create_backup)
        buttons_layout.addWidget(create_backup_btn)
        
        restore_backup_btn = QPushButton('📥 Восстановить из копии')
        restore_backup_btn.clicked.connect(self.restore_backup)
        buttons_layout.addWidget(restore_backup_btn)
        
        manual_layout.addLayout(buttons_layout)
        
        layout.addWidget(manual_group)
        
        layout.addStretch()
        return widget
    
    def on_theme_changed(self, theme_name):
        """Обработка изменения темы"""
        theme_map = {
            'Светлая': 'light',
            'Темная': 'dark', 
            'Системная': 'system'
        }
        
        theme_key = theme_map.get(theme_name, 'light')
        self.theme_changed.emit(theme_key)
        self.logger.info(f"Тема изменена на: {theme_name}")
    
    def on_language_changed(self, language_name):
        """Обработка изменения языка"""
        language_map = {
            'Українська': 'uk_UA',
            'English': 'en_US',
            'Русский': 'ru_RU'
        }
        
        language_key = language_map.get(language_name, 'uk_UA')
        self.language_changed.emit(language_key)
        self.logger.info(f"Язык изменен на: {language_name}")
    
    def select_backup_path(self):
        """Выбор папки для резервных копий"""
        path = QFileDialog.getExistingDirectory(
            self, 
            'Выберите папку для резервных копий',
            self.backup_path_edit.text()
        )
        
        if path:
            self.backup_path_edit.setText(path)
    
    def create_backup(self):
        """Создание резервной копии"""
        QMessageBox.information(
            self,
            'Резервная копия',
            'Функция создания резервной копии будет реализована'
        )
    
    def restore_backup(self):
        """Восстановление из резервной копии"""
        QMessageBox.information(
            self,
            'Восстановление',
            'Функция восстановления будет реализована'
        )
    
    def load_settings(self):
        """Загрузка настроек"""
        try:
            # Интерфейс
            theme = self.settings.value('theme', 'light')
            theme_names = {'light': 'Светлая', 'dark': 'Темная', 'system': 'Системная'}
            self.theme_combo.setCurrentText(theme_names.get(theme, 'Светлая'))
            
            language = self.settings.value('language', 'uk_UA')
            language_names = {'uk_UA': 'Українська', 'en_US': 'English', 'ru_RU': 'Русский'}
            self.language_combo.setCurrentText(language_names.get(language, 'Українська'))
            
            # Отображение
            self.show_splash_cb.setChecked(self.settings.value('show_splash', True, bool))
            self.show_tips_cb.setChecked(self.settings.value('show_tips', True, bool))
            self.animations_cb.setChecked(self.settings.value('animations', True, bool))
            
            # Система
            self.autosave_enabled_cb.setChecked(self.settings.value('autosave_enabled', True, bool))
            self.autosave_interval_spin.setValue(self.settings.value('autosave_interval', 5, int))
            self.log_level_combo.setCurrentText(self.settings.value('log_level', 'INFO'))
            self.log_to_file_cb.setChecked(self.settings.value('log_to_file', True, bool))
            self.cache_size_spin.setValue(self.settings.value('cache_size', 100, int))
            self.preload_data_cb.setChecked(self.settings.value('preload_data', True, bool))
            
            # Резервное копирование
            self.autobackup_enabled_cb.setChecked(self.settings.value('autobackup_enabled', True, bool))
            self.backup_interval_spin.setValue(self.settings.value('backup_interval', 24, int))
            self.backup_path_edit.setText(self.settings.value('backup_path', ''))
            self.max_backups_spin.setValue(self.settings.value('max_backups', 30, int))
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки настроек: {e}")
    
    def save_settings(self):
        """Сохранение настроек"""
        try:
            # Интерфейс
            theme_map = {'Светлая': 'light', 'Темная': 'dark', 'Системная': 'system'}
            self.settings.setValue('theme', theme_map.get(self.theme_combo.currentText(), 'light'))
            
            language_map = {'Українська': 'uk_UA', 'English': 'en_US', 'Русский': 'ru_RU'}
            self.settings.setValue('language', language_map.get(self.language_combo.currentText(), 'uk_UA'))
            
            # Отображение
            self.settings.setValue('show_splash', self.show_splash_cb.isChecked())
            self.settings.setValue('show_tips', self.show_tips_cb.isChecked())
            self.settings.setValue('animations', self.animations_cb.isChecked())
            
            # Система
            self.settings.setValue('autosave_enabled', self.autosave_enabled_cb.isChecked())
            self.settings.setValue('autosave_interval', self.autosave_interval_spin.value())
            self.settings.setValue('log_level', self.log_level_combo.currentText())
            self.settings.setValue('log_to_file', self.log_to_file_cb.isChecked())
            self.settings.setValue('cache_size', self.cache_size_spin.value())
            self.settings.setValue('preload_data', self.preload_data_cb.isChecked())
            
            # Резервное копирование
            self.settings.setValue('autobackup_enabled', self.autobackup_enabled_cb.isChecked())
            self.settings.setValue('backup_interval', self.backup_interval_spin.value())
            self.settings.setValue('backup_path', self.backup_path_edit.text())
            self.settings.setValue('max_backups', self.max_backups_spin.value())
            
            self.settings_changed.emit()
            
            QMessageBox.information(self, 'Настройки', 'Настройки сохранены успешно')
            self.logger.info("Настройки сохранены")
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения настроек: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить настройки: {e}')
    
    def reset_settings(self):
        """Сброс настроек к значениям по умолчанию"""
        reply = QMessageBox.question(
            self,
            'Сброс настроек',
            'Вы уверены, что хотите сбросить все настройки к значениям по умолчанию?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.settings.clear()
            self.load_settings()
            QMessageBox.information(self, 'Настройки', 'Настройки сброшены к значениям по умолчанию')
            self.logger.info("Настройки сброшены")