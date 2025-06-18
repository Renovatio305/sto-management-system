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

# Импорт вкладок (будут созданы далее)
from .views.orders_view import OrdersView
from .views.new_order_view import NewOrderView
from .views.catalogs_view import CatalogsView
from .views.settings_view import SettingsView

# Импорт диалогов
from .dialogs.about_dialog import AboutDialog

# База данных
from config.database import SessionLocal


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
        
        # Установка иконки
        self.setWindowIcon(QIcon('resources/icons/app.png'))
        
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
        self.settings_view = SettingsView()
        
        # Добавляем вкладки
        self.tab_widget.addTab(self.orders_view, QIcon('resources/icons/orders.png'), 'Заказы')
        self.tab_widget.addTab(self.new_order_view, QIcon('resources/icons/new_order.png'), 'Новый заказ')
        self.tab_widget.addTab(self.catalogs_view, QIcon('resources/icons/catalog.png'), 'Справочники')
        self.tab_widget.addTab(self.settings_view, QIcon('resources/icons/settings.png'), 'Настройки')
        
        main_layout.addWidget(self.tab_widget)
        
        # Статусная строка
        self.create_status_bar()
        
    def create_menu_bar(self):
        """Создание меню"""
        menubar = self.menuBar()
        
        # Меню Файл
        file_menu = QMenu('&Файл', self)
        menubar.addMenu(file_menu)
        
        new_order_action = QAction(QIcon('resources/icons/new_order.png'), '&Новый заказ', self)
        new_order_action.setShortcut(QKeySequence.New)
        new_order_action.triggered.connect(self.new_order)
        file_menu.addAction(new_order_action)
        
        file_menu.addSeparator()
        
        import_action = QAction(QIcon('resources/icons/import.png'), '&Импорт данных...', self)
        import_action.setShortcut(QKeySequence('Ctrl+I'))
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)
        
        export_action = QAction(QIcon('resources/icons/export.png'), '&Экспорт данных...', self)
        export_action.setShortcut(QKeySequence('Ctrl+E'))
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction(QIcon('resources/icons/exit.png'), '&Выход', self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню Правка
        edit_menu = QMenu('&Правка', self)
        menubar.addMenu(edit_menu)
        
        find_action = QAction(QIcon('resources/icons/search.png'), '&Поиск...', self)
        find_action.setShortcut(QKeySequence.Find)
        find_action.triggered.connect(self.show_search)
        edit_menu.addAction(find_action)
        
        # Меню Вид
        view_menu = QMenu('&Вид', self)
        menubar.addMenu(view_menu)
        
        # Подменю тем
        theme_menu = QMenu('Тема', self)
        theme_menu.setIcon(QIcon('resources/icons/theme.png'))
        view_menu.addMenu(theme_menu)
        
        light_theme_action = QAction('Светлая', self)
        light_theme_action.setCheckable(True)
        light_theme_action.triggered.connect(lambda: self.change_theme('light'))
        theme_menu.addAction(light_theme_action)
        
        dark_theme_action = QAction('Темная', self)
        dark_theme_action.setCheckable(True)
        dark_theme_action.triggered.connect(lambda: self.change_theme('dark'))
        theme_menu.addAction(dark_theme_action)
        
        # Группа для радио-кнопок
        self.theme_action_group = [light_theme_action, dark_theme_action]
        
        view_menu.addSeparator()
        
        fullscreen_action = QAction('Полноэкранный режим', self)
        fullscreen_action.setShortcut(QKeySequence.FullScreen)
        fullscreen_action.setCheckable(True)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # Меню Инструменты
        tools_menu = QMenu('&Инструменты', self)
        menubar.addMenu(tools_menu)
        
        calendar_action = QAction(QIcon('resources/icons/calendar.png'), '&Календарь записей', self)
        calendar_action.setShortcut(QKeySequence('Ctrl+K'))
        calendar_action.triggered.connect(self.show_calendar)
        tools_menu.addAction(calendar_action)
        
        reports_action = QAction(QIcon('resources/icons/reports.png'), '&Отчеты', self)
        reports_action.setShortcut(QKeySequence('Ctrl+R'))
        reports_action.triggered.connect(self.show_reports)
        tools_menu.addAction(reports_action)
        
        tools_menu.addSeparator()
        
        backup_action = QAction(QIcon('resources/icons/backup.png'), '&Резервное копирование', self)
        backup_action.triggered.connect(self.backup_database)
        tools_menu.addAction(backup_action)
        
        # Меню Справка
        help_menu = QMenu('&Справка', self)
        menubar.addMenu(help_menu)
        
        help_action = QAction(QIcon('resources/icons/help.png'), '&Руководство пользователя', self)
        help_action.setShortcut(QKeySequence.HelpContents)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        help_menu.addSeparator()
        
        about_action = QAction(QIcon('resources/icons/about.png'), '&О программе', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_toolbar(self):
        """Создание панели инструментов"""
        toolbar = QToolBar('Главная панель')
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(toolbar)
        
        # Новый заказ
        new_order_action = QAction(QIcon('resources/icons/new_order.png'), 'Новый заказ', self)
        new_order_action.triggered.connect(self.new_order)
        toolbar.addAction(new_order_action)
        
        # Поиск
        search_action = QAction(QIcon('resources/icons/search.png'), 'Поиск', self)
        search_action.triggered.connect(self.show_search)
        toolbar.addAction(search_action)
        
        toolbar.addSeparator()
        
        # Календарь
        calendar_action = QAction(QIcon('resources/icons/calendar.png'), 'Календарь', self)
        calendar_action.triggered.connect(self.show_calendar)
        toolbar.addAction(calendar_action)
        
        # Отчеты
        reports_action = QAction(QIcon('resources/icons/reports.png'), 'Отчеты', self)
        reports_action.triggered.connect(self.show_reports)
        toolbar.addAction(reports_action)
        
        toolbar.addSeparator()
        
        # Печать
        print_action = QAction(QIcon('resources/icons/print.png'), 'Печать', self)
        print_action.triggered.connect(self.print_current)
        toolbar.addAction(print_action)
        
        # PDF
        pdf_action = QAction(QIcon('resources/icons/pdf.png'), 'Экспорт в PDF', self)
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
        # Связываем сигналы из вкладок
        self.orders_view.status_message.connect(self.show_status_message)
        self.new_order_view.status_message.connect(self.show_status_message)
        self.new_order_view.order_saved.connect(self.on_order_saved)
        
        # Сигналы изменения настроек
        self.settings_view.theme_changed.connect(self.change_theme)
        self.settings_view.language_changed.connect(self.change_language)
        
    def show_status_message(self, message, timeout=3000):
        """Показать сообщение в статусной строке"""
        self.status_bar.showMessage(message, timeout)
        
    def new_order(self):
        """Переключиться на вкладку нового заказа"""
        self.tab_widget.setCurrentWidget(self.new_order_view)
        self.new_order_view.clear_form()
        
    def on_order_saved(self):
        """Обработка сохранения заказа"""
        self.orders_view.refresh_orders()
        self.tab_widget.setCurrentWidget(self.orders_view)
        
    def show_search(self):
        """Показать диалог поиска"""
        from .dialogs.search_dialog import SearchDialog
        dialog = SearchDialog(self, self.db_session)
        dialog.exec()
        
    def show_calendar(self):
        """Показать календарь записей"""
        from .dialogs.calendar_dialog import CalendarDialog
        dialog = CalendarDialog(self, self.db_session)
        dialog.exec()
        
    def show_reports(self):
        """Показать окно отчетов"""
        from .dialogs.reports_dialog import ReportsDialog
        dialog = ReportsDialog(self.db_session, self)
        dialog.exec()
        
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
        from .dialogs.import_export_dialog import ImportDialog
        dialog = ImportDialog(self, self.db_session)
        if dialog.exec():
            self.refresh_all_views()
            
    def export_data(self):
        """Экспорт данных"""
        from .dialogs.import_export_dialog import ExportDialog
        dialog = ExportDialog(self, self.db_session)
        dialog.exec()
        
    def backup_database(self):
        """Резервное копирование БД"""
        from .utils.backup import BackupManager
        backup_manager = BackupManager()
        if backup_manager.create_backup():
            QMessageBox.information(self, 'Успех', 'Резервная копия создана успешно')
        else:
            QMessageBox.critical(self, 'Ошибка', 'Не удалось создать резервную копию')
            
    def change_theme(self, theme_name):
        """Изменить тему"""
        self.settings.setValue('theme', theme_name)
        self.theme_changed.emit(theme_name)
        
        # Обновляем чекбоксы в меню
        for i, action in enumerate(self.theme_action_group):
            action.setChecked(i == 0 if theme_name == 'light' else i == 1)
            
    def change_language(self, language):
        """Изменить язык"""
        self.settings.setValue('language', language)
        self.language_changed.emit(language)
        # Здесь будет перезагрузка интерфейса
        
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
        dialog = AboutDialog(self)
        dialog.exec()
        
    def refresh_all_views(self):
        """Обновить все представления"""
        self.orders_view.refresh_orders()
        self.catalogs_view.refresh_data()
        
    def autosave(self):
        """Автосохранение"""
        # Сохраняем текущий заказ если он в процессе редактирования
        if self.tab_widget.currentWidget() == self.new_order_view:
            self.new_order_view.save_draft()
            
    def load_settings(self):
        """Загрузка настроек"""
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
        
    def save_settings(self):
        """Сохранение настроек"""
        self.settings.setValue('geometry', self.saveGeometry())
        self.settings.setValue('windowState', self.saveState())
        
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        # Проверяем несохраненные изменения
        if self.new_order_view.has_unsaved_changes():
            reply = QMessageBox.question(
                self, 'Несохраненные изменения',
                'Есть несохраненные изменения. Сохранить перед выходом?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Save:
                self.new_order_view.save_order()
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
                
        # Сохраняем настройки
        self.save_settings()
        
        # Закрываем соединение с БД
        self.db_session.close()
        
        # Останавливаем таймеры
        self.time_timer.stop()
        self.autosave_timer.stop()
        
        event.accept()