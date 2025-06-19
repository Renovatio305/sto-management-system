# sto_app/main_window.py
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                              QTabWidget, QToolBar, QStatusBar, QMessageBox,
                              QSplitter, QLabel, QMenuBar, QMenu)
from PySide6.QtCore import Qt, QSettings, Signal, QTimer
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtCore import QSize

from datetime import datetime
import sys
import os
import logging

# Импорт вкладок
from .views.orders_view import OrdersView
from .views.new_order_view import NewOrderView
from .views.catalogs_view import CatalogsView
from .views.settings_view import SettingsView

# Импорт диалогов
from .dialogs.about_dialog import AboutDialog

# База данных
from config.database import SessionLocal

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Главное окно приложения СТО"""
    
    # Сигналы
    theme_changed = Signal(str)
    language_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.db_session = SessionLocal()
        self.settings = QSettings('STOApp', 'MainWindow')
        
        self.setWindowTitle('СТО Management System v3.0')
        self.setGeometry(100, 100, 1400, 900)
        
        # Установка иконки (с проверкой существования)
        try:
            if os.path.exists('resources/icons/app.png'):
                self.setWindowIcon(QIcon('resources/icons/app.png'))
        except Exception as e:
            logger.warning(f"Не удалось загрузить иконку приложения: {e}")
        
        self.setup_ui()
        self.load_settings()
        self.setup_connections()
        
        # Таймер для автосохранения
        self.autosave_timer = QTimer()
        self.autosave_timer.timeout.connect(self.autosave)
        self.autosave_timer.start(300000)  # Каждые 5 минут
        
    def setup_ui(self):
        """Настройка интерфейса"""
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Меню
        self.create_menu_bar()
        
        # Панель инструментов
        self.create_toolbar()
        
        # Вкладки
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setMovable(True)
        
        # Создаем вкладки
        self.orders_view = OrdersView(self.db_session)
        self.new_order_view = NewOrderView(self.db_session)
        self.catalogs_view = CatalogsView(self.db_session)
        self.settings_view = SettingsView(self.db_session)
        
        # Добавляем вкладки
        self.tab_widget.addTab(self.orders_view, self._get_icon('orders'), 'Заказы')
        self.tab_widget.addTab(self.new_order_view, self._get_icon('new_order'), 'Новый заказ')
        self.tab_widget.addTab(self.catalogs_view, self._get_icon('catalog'), 'Справочники')
        self.tab_widget.addTab(self.settings_view, self._get_icon('settings'), 'Настройки')
        
        main_layout.addWidget(self.tab_widget)
        
        # Статусная строка
        self.create_status_bar()
        
    def _get_icon(self, icon_name):
        """Безопасное получение иконки"""
        icon_path = f'resources/icons/{icon_name}.png'
        try:
            if os.path.exists(icon_path):
                return QIcon(icon_path)
        except Exception as e:
            logger.warning(f"Не удалось загрузить иконку {icon_name}: {e}")
        return QIcon()  # Пустая иконка
        
    def create_menu_bar(self):
        """Создание меню"""
        menubar = self.menuBar()
        
        # Меню Файл
        file_menu = QMenu('&Файл', self)
        menubar.addMenu(file_menu)
        
        new_order_action = QAction(self._get_icon('new_order'), '&Новый заказ', self)
        new_order_action.setShortcut(QKeySequence.New)
        new_order_action.triggered.connect(self.new_order)
        file_menu.addAction(new_order_action)
        
        file_menu.addSeparator()
        
        import_action = QAction(self._get_icon('import'), '&Импорт данных...', self)
        import_action.setShortcut(QKeySequence('Ctrl+I'))
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)
        
        export_action = QAction(self._get_icon('export'), '&Экспорт данных...', self)
        export_action.setShortcut(QKeySequence('Ctrl+E'))
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction(self._get_icon('exit'), '&Выход', self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню Правка
        edit_menu = QMenu('&Правка', self)
        menubar.addMenu(edit_menu)
        
        find_action = QAction(self._get_icon('search'), '&Поиск...', self)
        find_action.setShortcut(QKeySequence.Find)
        find_action.triggered.connect(self.show_search)
        edit_menu.addAction(find_action)
        
        # Меню Вид
        view_menu = QMenu('&Вид', self)
        menubar.addMenu(view_menu)
        
        # Подменю тем
        theme_menu = QMenu('Тема', self)
        theme_menu.setIcon(self._get_icon('theme'))
        view_menu.addMenu(theme_menu)
        
        self.light_theme_action = QAction('Светлая', self)
        self.light_theme_action.setCheckable(True)
        self.light_theme_action.triggered.connect(lambda: self.change_theme('light'))
        theme_menu.addAction(self.light_theme_action)
        
        self.dark_theme_action = QAction('Темная', self)
        self.dark_theme_action.setCheckable(True)
        self.dark_theme_action.triggered.connect(lambda: self.change_theme('dark'))
        theme_menu.addAction(self.dark_theme_action)
        
        view_menu.addSeparator()
        
        fullscreen_action = QAction('Полноэкранный режим', self)
        fullscreen_action.setShortcut(QKeySequence.FullScreen)
        fullscreen_action.setCheckable(True)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # Меню Инструменты
        tools_menu = QMenu('&Инструменты', self)
        menubar.addMenu(tools_menu)
        
        calendar_action = QAction(self._get_icon('calendar'), '&Календарь записей', self)
        calendar_action.setShortcut(QKeySequence('Ctrl+K'))
        calendar_action.triggered.connect(self.show_calendar)
        tools_menu.addAction(calendar_action)
        
        reports_action = QAction(self._get_icon('reports'), '&Отчеты', self)
        reports_action.setShortcut(QKeySequence('Ctrl+R'))
        reports_action.triggered.connect(self.show_reports)
        tools_menu.addAction(reports_action)
        
        tools_menu.addSeparator()
        
        backup_action = QAction(self._get_icon('backup'), '&Резервное копирование', self)
        backup_action.triggered.connect(self.backup_database)
        tools_menu.addAction(backup_action)
        
        # Меню Справка
        help_menu = QMenu('&Справка', self)
        menubar.addMenu(help_menu)
        
        help_action = QAction(self._get_icon('help'), '&Руководство пользователя', self)
        help_action.setShortcut(QKeySequence.HelpContents)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        help_menu.addSeparator()
        
        about_action = QAction(self._get_icon('about'), '&О программе', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_toolbar(self):
        """Создание панели инструментов"""
        toolbar = QToolBar('Главная панель')
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(toolbar)
        
        # Новый заказ
        new_order_action = QAction(self._get_icon('new_order'), 'Новый заказ', self)
        new_order_action.triggered.connect(self.new_order)
        toolbar.addAction(new_order_action)
        
        # Поиск
        search_action = QAction(self._get_icon('search'), 'Поиск', self)
        search_action.triggered.connect(self.show_search)
        toolbar.addAction(search_action)
        
        toolbar.addSeparator()
        
        # Календарь
        calendar_action = QAction(self._get_icon('calendar'), 'Календарь', self)
        calendar_action.triggered.connect(self.show_calendar)
        toolbar.addAction(calendar_action)
        
        # Отчеты
        reports_action = QAction(self._get_icon('reports'), 'Отчеты', self)
        reports_action.triggered.connect(self.show_reports)
        toolbar.addAction(reports_action)
        
        toolbar.addSeparator()
        
        # Печать
        print_action = QAction(self._get_icon('print'), 'Печать', self)
        print_action.triggered.connect(self.print_current)
        toolbar.addAction(print_action)
        
        # PDF
        pdf_action = QAction(self._get_icon('pdf'), 'Экспорт в PDF', self)
        pdf_action.triggered.connect(self.export_pdf)
        toolbar.addAction(pdf_action)
        
    def create_status_bar(self):
        """Создание статусной строки"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Левая часть - общая информация
        self.status_label = QLabel('Готов')
        self.status_bar.addWidget(self.status_label)
        
        # Правая часть - постоянные виджеты
        self.user_label = QLabel('Пользователь: Администратор')
        self.status_bar.addPermanentWidget(self.user_label)
        
        self.status_bar.addPermanentWidget(QLabel(' | '))
        
        self.time_label = QLabel()
        self.update_time()
        self.status_bar.addPermanentWidget(self.time_label)
        
        # Таймер для обновления времени
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)
        
    def update_time(self):
        """Обновление времени в статусной строке"""
        current_time = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        self.time_label.setText(current_time)
        
    def setup_connections(self):
        """Настройка соединений сигналов"""
        try:
            # Связываем сигналы из вкладок
            if hasattr(self.orders_view, 'status_message'):
                self.orders_view.status_message.connect(self.show_status_message)
                
            if hasattr(self.new_order_view, 'status_message'):
                self.new_order_view.status_message.connect(self.show_status_message)
                
            if hasattr(self.new_order_view, 'order_saved'):
                self.new_order_view.order_saved.connect(self.on_order_saved)
            
            # Сигналы изменения настроек
            if hasattr(self.settings_view, 'theme_changed'):
                self.settings_view.theme_changed.connect(self.change_theme)
                
            if hasattr(self.settings_view, 'language_changed'):
                self.settings_view.language_changed.connect(self.change_language)
                
        except Exception as e:
            logger.error(f"Ошибка настройки соединений: {e}")
        
    def show_status_message(self, message, timeout=3000):
        """Показать сообщение в статусной строке"""
        self.status_bar.showMessage(message, timeout)
        
    def new_order(self):
        """Переключиться на вкладку нового заказа"""
        self.tab_widget.setCurrentWidget(self.new_order_view)
        if hasattr(self.new_order_view, 'clear_form'):
            self.new_order_view.clear_form()
        
    def on_order_saved(self):
        """Обработка сохранения заказа"""
        if hasattr(self.orders_view, 'refresh_orders'):
            self.orders_view.refresh_orders()
        self.tab_widget.setCurrentWidget(self.orders_view)
        
    def show_search(self):
        """Показать диалог поиска"""
        try:
            from .dialogs.search_dialog import SearchDialog
            dialog = SearchDialog(self, self.db_session)
            dialog.exec()
        except ImportError:
            QMessageBox.information(
                self, 'Информация', 
                'Диалог поиска ещё не реализован'
            )
        except Exception as e:
            logger.error(f"Ошибка открытия диалога поиска: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Не удалось открыть поиск: {e}')
        
    def show_calendar(self):
        """Показать календарь записей"""
        try:
            from .dialogs.calendar_dialog import CalendarDialog
            dialog = CalendarDialog(self, self.db_session)
            dialog.exec()
        except ImportError:
            QMessageBox.information(
                self, 'Информация', 
                'Календарь записей ещё не реализован'
            )
        except Exception as e:
            logger.error(f"Ошибка открытия календаря: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Не удалось открыть календарь: {e}')
        
    def show_reports(self):
        """Показать окно отчетов"""
        try:
            from .dialogs.reports_dialog import ReportsDialog
            dialog = ReportsDialog(self.db_session, self)
            dialog.exec()
        except ImportError:
            QMessageBox.information(
                self, 'Информация', 
                'Система отчётов ещё не реализована'
            )
        except Exception as e:
            logger.error(f"Ошибка открытия отчётов: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Не удалось открыть отчёты: {e}')
        
    def print_current(self):
        """Печать текущего документа"""
        current_widget = self.tab_widget.currentWidget()
        if hasattr(current_widget, 'print_document'):
            current_widget.print_document()
        else:
            QMessageBox.information(self, 'Печать', 'Печать недоступна для текущей вкладки')
            
    def export_pdf(self):
        """Экспорт в PDF"""
        current_widget = self.tab_widget.currentWidget()
        if hasattr(current_widget, 'export_pdf'):
            current_widget.export_pdf()
        else:
            QMessageBox.information(self, 'Экспорт PDF', 'Экспорт в PDF недоступен для текущей вкладки')
            
    def import_data(self):
        """Импорт данных"""
        try:
            from .dialogs.import_export_dialog import ImportDialog
            dialog = ImportDialog(self, self.db_session)
            if dialog.exec():
                self.refresh_all_views()
        except ImportError:
            QMessageBox.information(
                self, 'Информация', 
                'Функция импорта ещё не реализована'
            )
        except Exception as e:
            logger.error(f"Ошибка импорта данных: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Не удалось выполнить импорт: {e}')
            
    def export_data(self):
        """Экспорт данных"""
        try:
            from .dialogs.import_export_dialog import ExportDialog
            dialog = ExportDialog(self, self.db_session)
            dialog.exec()
        except ImportError:
            QMessageBox.information(
                self, 'Информация', 
                'Функция экспорта ещё не реализована'
            )
        except Exception as e:
            logger.error(f"Ошибка экспорта данных: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Не удалось выполнить экспорт: {e}')
            
    def backup_database(self):
        """Резервное копирование БД"""
        try:
            from .utils.backup_manager import BackupManager
            backup_manager = BackupManager()
            if backup_manager.create_backup():
                QMessageBox.information(self, 'Успех', 'Резервная копия создана успешно')
            else:
                QMessageBox.critical(self, 'Ошибка', 'Не удалось создать резервную копию')
        except ImportError:
            QMessageBox.information(
                self, 'Информация', 
                'Система резервного копирования ещё не реализована'
            )
        except Exception as e:
            logger.error(f"Ошибка резервного копирования: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Не удалось создать резервную копию: {e}')
            
    def change_theme(self, theme_name):
        """Изменить тему"""
        try:
            self.settings.setValue('theme', theme_name)
            self.theme_changed.emit(theme_name)
            
            # Обновляем чекбоксы в меню
            self.light_theme_action.setChecked(theme_name == 'light')
            self.dark_theme_action.setChecked(theme_name == 'dark')
            
            self.show_status_message(f'Тема изменена на {theme_name}', 2000)
        except Exception as e:
            logger.error(f"Ошибка изменения темы: {e}")
            
    def change_language(self, language):
        """Изменить язык"""
        try:
            self.settings.setValue('language', language)
            self.language_changed.emit(language)
            self.show_status_message(f'Язык изменён на {language}', 2000)
            # Здесь будет перезагрузка интерфейса
        except Exception as e:
            logger.error(f"Ошибка изменения языка: {e}")
            
    def toggle_fullscreen(self):
        """Переключить полноэкранный режим"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
            
    def show_help(self):
        """Показать справку"""
        QMessageBox.information(self, 'Справка', 'Руководство пользователя будет доступно в следующей версии')
        
    def show_about(self):
        """Показать информацию о программе"""
        try:
            dialog = AboutDialog(self)
            dialog.exec()
        except Exception as e:
            logger.error(f"Ошибка открытия диалога 'О программе': {e}")
            QMessageBox.critical(self, 'Ошибка', f'Не удалось открыть информацию о программе: {e}')
        
    def refresh_all_views(self):
        """Обновить все представления"""
        try:
            if hasattr(self.orders_view, 'refresh_orders'):
                self.orders_view.refresh_orders()
            if hasattr(self.catalogs_view, 'refresh_data'):
                self.catalogs_view.refresh_data()
        except Exception as e:
            logger.error(f"Ошибка обновления представлений: {e}")
            
    def autosave(self):
        """Автосохранение"""
        try:
            # Сохраняем текущий заказ если он в процессе редактирования
            if (self.tab_widget.currentWidget() == self.new_order_view and 
                hasattr(self.new_order_view, 'save_draft')):
                self.new_order_view.save_draft()
        except Exception as e:
            logger.error(f"Ошибка автосохранения: {e}")
            
    def load_settings(self):
        """Загрузка настроек"""
        try:
            # Размер и позиция окна
            geometry = self.settings.value('geometry')
            if geometry:
                self.restoreGeometry(geometry)
            
            # Состояние окна
            state = self.settings.value('windowState')
            if state:
                self.restoreState(state)
                
            # Тема
            theme = self.settings.value('theme', 'light')
            self.change_theme(theme)
        except Exception as e:
            logger.error(f"Ошибка загрузки настроек: {e}")
        
    def save_settings(self):
        """Сохранение настроек"""
        try:
            self.settings.setValue('geometry', self.saveGeometry())
            self.settings.setValue('windowState', self.saveState())
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек: {e}")
        
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        try:
            # Проверяем несохраненные изменения
            if (hasattr(self.new_order_view, 'has_unsaved_changes') and 
                self.new_order_view.has_unsaved_changes()):
                reply = QMessageBox.question(
                    self, 'Несохраненные изменения',
                    'Есть несохраненные изменения. Сохранить перед выходом?',
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
                )
                
                if reply == QMessageBox.Save:
                    if hasattr(self.new_order_view, 'save_order'):
                        self.new_order_view.save_order()
                elif reply == QMessageBox.Cancel:
                    event.ignore()
                    return
                    
            # Сохраняем настройки
            self.save_settings()
            
            # Закрываем соединение с БД
            if self.db_session:
                self.db_session.close()
            
            # Останавливаем таймеры
            if hasattr(self, 'time_timer'):
                self.time_timer.stop()
            if hasattr(self, 'autosave_timer'):
                self.autosave_timer.stop()
            
            event.accept()
            
        except Exception as e:
            logger.error(f"Ошибка при закрытии приложения: {e}")
            event.accept()  # Всё равно закрываем приложение