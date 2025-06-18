# sto_app/main_window.py
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                              QTabWidget, QStatusBar, QMessageBox, QFrame,
                              QLabel, QMenuBar, QMenu, QPushButton, QSizePolicy,
                              QTabBar, QSpacerItem)
from PySide6.QtCore import Qt, QSettings, Signal, QTimer
from PySide6.QtGui import QAction, QIcon, QKeySequence, QFont
from PySide6.QtCore import QSize

from datetime import datetime
import sys
import os

# Импорт вкладок
from .views.orders_view import OrdersView
from .views.new_order_view import NewOrderView
from .views.catalogs_view import CatalogsView
from .views.settings_view import SettingsView

# Импорт диалогов
from .dialogs.about_dialog import AboutDialog
from .dialogs.search_dialog import SearchDialog
from .dialogs.calendar_dialog import CalendarDialog
from .dialogs.reports_dialog import ReportsDialog

# База данных
from config.database import SessionLocal


class CompactActionButton(QPushButton):
    """Компактная кнопка действия"""
    
    def __init__(self, text, icon=None, color="#3498db"):
        super().__init__(text)
        if icon:
            self.setIcon(QIcon(icon))
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 4px;
                border: none;
                margin: 0 2px;
                min-width: 80px;
                max-height: 32px;
            }}
            QPushButton:hover {{
                background-color: {self._lighten_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(color)};
            }}
            QPushButton:disabled {{
                background-color: #95a5a6;
                color: #7f8c8d;
            }}
        """)
    
    def _lighten_color(self, color):
        """Осветлить цвет для hover эффекта"""
        color_map = {
            "#3498db": "#5dade2",
            "#e67e22": "#f39c12", 
            "#9b59b6": "#af7ac5",
            "#27ae60": "#2ecc71"
        }
        return color_map.get(color, color)
    
    def _darken_color(self, color):
        """Затемнить цвет для pressed эффекта"""
        color_map = {
            "#3498db": "#2980b9",
            "#e67e22": "#d35400",
            "#9b59b6": "#8e44ad", 
            "#27ae60": "#229954"
        }
        return color_map.get(color, color)


class CustomTabWidget(QTabWidget):
    """Кастомный виджет вкладок с кнопками справа"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setup_custom_tab_bar()
    
    def setup_custom_tab_bar(self):
        """Настройка кастомного таб-бара"""
        # Создаем контейнер для таб-бара и кнопок
        tab_container = QWidget()
        tab_layout = QHBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(5)
        
        # Получаем оригинальный таб-бар
        original_tab_bar = self.tabBar()
        
        # Добавляем растягивающийся элемент между табами и кнопками
        tab_layout.addWidget(original_tab_bar)
        tab_layout.addStretch()
        
        # Создаем кнопки действий
        self.create_action_buttons(tab_layout)
        
        # Устанавливаем кастомный таб-бар
        self.setTabBar(CustomTabBar(tab_container))
    
    def create_action_buttons(self, layout):
        """Создание кнопок действий"""
        # Поиск
        self.search_btn = CompactActionButton("🔍", color="#9b59b6")
        self.search_btn.setToolTip("Поиск (Ctrl+F)")
        self.search_btn.setMaximumWidth(40)
        layout.addWidget(self.search_btn)
        
        # Календарь
        self.calendar_btn = CompactActionButton("📅", color="#3498db")
        self.calendar_btn.setToolTip("Календарь (Ctrl+K)")
        self.calendar_btn.setMaximumWidth(40)
        layout.addWidget(self.calendar_btn)
        
        # Отчёты
        self.reports_btn = CompactActionButton("📊", color="#e67e22")
        self.reports_btn.setToolTip("Отчёты (Ctrl+R)")
        self.reports_btn.setMaximumWidth(40)
        layout.addWidget(self.reports_btn)
        
        # Зарплата
        self.salary_btn = CompactActionButton("💰", color="#f39c12")
        self.salary_btn.setToolTip("Зарплата")
        self.salary_btn.setMaximumWidth(40)
        layout.addWidget(self.salary_btn)
        
        # Все клиенты
        self.clients_btn = CompactActionButton("👥", color="#27ae60")
        self.clients_btn.setToolTip("Все клиенты")
        self.clients_btn.setMaximumWidth(40)
        layout.addWidget(self.clients_btn)


class CustomTabBar(QTabBar):
    """Кастомный таб-бар"""
    
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        
    def tabSizeHint(self, index):
        """Настройка размера вкладок"""
        size = super().tabSizeHint(index)
        # Делаем вкладки немного выше для лучшего вида
        size.setHeight(40)
        return size


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
        self.setMinimumSize(1200, 800)
        
        # Установка иконки
        try:
            self.setWindowIcon(QIcon('resources/icons/app.png'))
        except:
            pass  # Игнорируем отсутствие иконки
        
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
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Меню
        self.create_menu_bar()
        
        # Убираем верхнюю панель быстрых действий - переносим все в табы
        
        # Создаем кастомный виджет вкладок
        self.tab_widget = CustomTabWidget(self)
        
        # Создаем вкладки
        self.orders_view = OrdersView(self.db_session)
        self.new_order_view = NewOrderView(self.db_session)
        self.catalogs_view = CatalogsView(self.db_session)
        self.settings_view = SettingsView()
        
        # Добавляем ВСЕ вкладки включая "Новый заказ"
        self.tab_widget.addTab(self.orders_view, '📋 Заказы')
        self.tab_widget.addTab(self.new_order_view, '➕ Новый заказ')  # ОСТАВЛЯЕМ!
        self.tab_widget.addTab(self.catalogs_view, '📚 Справочники') 
        self.tab_widget.addTab(self.settings_view, '⚙️ Настройки')
        
        main_layout.addWidget(self.tab_widget)
        
        # Статусная строка
        self.create_status_bar()
        
        # Стилизация табов
        self.style_tabs()
        
    def style_tabs(self):
        """Стилизация вкладок"""
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                background-color: white;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border: 1px solid #bdc3c7;
                padding: 12px 20px;
                margin-right: 2px;
                font-weight: bold;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
                border-bottom: none;
            }
            QTabBar::tab:hover:!selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ecf0f1, stop:1 #d5dbdb);
            }
            QTabBar::tab:first {
                margin-left: 0;
            }
        """)
        
    def create_menu_bar(self):
        """Создание меню"""
        menubar = self.menuBar()
        
        # Меню Файл
        file_menu = QMenu('&Файл', self)
        menubar.addMenu(file_menu)
        
        file_menu.addSeparator()
        
        import_action = QAction('&Импорт данных...', self)
        import_action.setShortcut(QKeySequence('Ctrl+I'))
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)
        
        export_action = QAction('&Экспорт данных...', self)
        export_action.setShortcut(QKeySequence('Ctrl+E'))
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('&Выход', self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню Сервис
        service_menu = QMenu('&Сервис', self)
        menubar.addMenu(service_menu)
        
        # Управление зарплатой
        salary_action = QAction('Управление зарплатой', self)
        salary_action.triggered.connect(self.manage_salary)
        service_menu.addAction(salary_action)
        
        service_menu.addSeparator()
        
        # Просмотр клиентов
        clients_action = QAction('Все клиенты', self)
        clients_action.triggered.connect(self.show_all_clients)
        service_menu.addAction(clients_action)
        
        # Просмотр автомобилей
        cars_action = QAction('Все автомобили', self)
        cars_action.triggered.connect(self.show_all_cars)
        service_menu.addAction(cars_action)
        
        service_menu.addSeparator()
        
        # Импорт услуг
        import_services_action = QAction('Импорт услуг', self)
        import_services_action.triggered.connect(self.import_services)
        service_menu.addAction(import_services_action)
        
        # Меню Инструменты
        tools_menu = QMenu('&Инструменты', self)
        menubar.addMenu(tools_menu)
        
        calendar_action = QAction('&Календарь записей', self)
        calendar_action.setShortcut(QKeySequence('Ctrl+K'))
        calendar_action.triggered.connect(self.show_calendar)
        tools_menu.addAction(calendar_action)
        
        reports_action = QAction('&Отчеты', self)
        reports_action.setShortcut(QKeySequence('Ctrl+R'))
        reports_action.triggered.connect(self.show_reports)
        tools_menu.addAction(reports_action)
        
        search_action = QAction('&Поиск', self)
        search_action.setShortcut(QKeySequence('Ctrl+F'))
        search_action.triggered.connect(self.show_search)
        tools_menu.addAction(search_action)
        
        tools_menu.addSeparator()
        
        backup_action = QAction('&Резервное копирование', self)
        backup_action.triggered.connect(self.backup_database)
        tools_menu.addAction(backup_action)
        
        # Меню Справка
        help_menu = QMenu('&Справка', self)
        menubar.addMenu(help_menu)
        
        about_action = QAction('&О программе', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
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
        
        # Подключаем кнопки в кастомном таб-виджете
        if hasattr(self.tab_widget, 'search_btn'):
            self.tab_widget.search_btn.clicked.connect(self.show_search)
        if hasattr(self.tab_widget, 'calendar_btn'):
            self.tab_widget.calendar_btn.clicked.connect(self.show_calendar)
        if hasattr(self.tab_widget, 'reports_btn'):
            self.tab_widget.reports_btn.clicked.connect(self.show_reports)
        if hasattr(self.tab_widget, 'salary_btn'):
            self.tab_widget.salary_btn.clicked.connect(self.manage_salary)
        if hasattr(self.tab_widget, 'clients_btn'):
            self.tab_widget.clients_btn.clicked.connect(self.show_all_clients)
        
    def show_status_message(self, message, timeout=3000):
        """Показать сообщение в статусной строке"""
        self.status_bar.showMessage(message, timeout)
        
    def on_order_saved(self):
        """Обработка сохранения заказа"""
        self.orders_view.refresh_orders()
        self.tab_widget.setCurrentWidget(self.orders_view)
        
    def show_search(self):
        """Показать диалог поиска"""
        try:
            dialog = SearchDialog(self, self.db_session)
            dialog.exec()
        except Exception as e:
            QMessageBox.information(self, 'Поиск', f'Функция поиска в разработке\n{str(e)}')
        
    def show_calendar(self):
        """Показать календарь записей"""
        try:
            dialog = CalendarDialog(self, self.db_session)
            dialog.exec()
        except Exception as e:
            QMessageBox.information(self, 'Календарь', f'Календарь в разработке\n{str(e)}')
        
    def show_reports(self):
        """Показать окно отчетов"""
        try:
            dialog = ReportsDialog(self.db_session, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.information(self, 'Отчёты', f'Отчёты в разработке\n{str(e)}')
        
    def manage_salary(self):
        """Управление зарплатой"""
        from .dialogs.salary_dialog import SalaryDialog
        try:
            dialog = SalaryDialog(self.db_session, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.information(self, 'Зарплата', f'Управление зарплатой в разработке\n{str(e)}')
        
    def show_all_clients(self):
        """Показать всех клиентов"""
        from .dialogs.clients_list_dialog import ClientsListDialog
        try:
            dialog = ClientsListDialog(self.db_session, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.information(self, 'Клиенты', f'Просмотр клиентов в разработке\n{str(e)}')
        
    def show_all_cars(self):
        """Показать все автомобили"""
        from .dialogs.cars_list_dialog import CarsListDialog
        try:
            dialog = CarsListDialog(self.db_session, self)
            dialog.exec()
        except Exception as e:
            QMessageBox.information(self, 'Автомобили', f'Просмотр автомобилей в разработке\n{str(e)}')
        
    def import_services(self):
        """Импорт услуг"""
        from .dialogs.import_services_dialog import ImportServicesDialog
        try:
            dialog = ImportServicesDialog(self.db_session, self)
            if dialog.exec():
                self.catalogs_view.refresh_data()
                QMessageBox.information(self, 'Успех', 'Услуги импортированы успешно')
        except Exception as e:
            QMessageBox.information(self, 'Импорт услуг', f'Импорт услуг в разработке\n{str(e)}')
        
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
        except Exception as e:
            QMessageBox.information(self, 'Импорт', f'Импорт данных в разработке\n{str(e)}')
            
    def export_data(self):
        """Экспорт данных"""
        try:
            from .dialogs.import_export_dialog import ExportDialog
            dialog = ExportDialog(self, self.db_session)
            dialog.exec()
        except Exception as e:
            QMessageBox.information(self, 'Экспорт', f'Экспорт данных в разработке\n{str(e)}')
        
    def backup_database(self):
        """Резервное копирование БД"""
        try:
            from .utils.backup import BackupManager
            backup_manager = BackupManager()
            if backup_manager.create_backup():
                QMessageBox.information(self, 'Успех', 'Резервная копия создана успешно')
            else:
                QMessageBox.critical(self, 'Ошибка', 'Не удалось создать резервную копию')
        except Exception as e:
            QMessageBox.information(self, 'Резервное копирование', f'Резервное копирование в разработке\n{str(e)}')
            
    def change_theme(self, theme_name):
        """Изменить тему"""
        self.settings.setValue('theme', theme_name)
        self.theme_changed.emit(theme_name)
            
    def change_language(self, language):
        """Изменить язык"""
        self.settings.setValue('language', language)
        self.language_changed.emit(language)
        
    def show_about(self):
        """Показать информацию о программе"""
        try:
            dialog = AboutDialog(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.information(self, 'О программе', 'СТО Management System v3.0\n\nСистема управления автосервисом')
        
    def refresh_all_views(self):
        """Обновить все представления"""
        self.orders_view.refresh_orders()
        self.catalogs_view.refresh_data()
        
    def autosave(self):
        """Автосохранение"""
        # Сохраняем текущий заказ если он в процессе редактирования
        if self.tab_widget.currentWidget() == self.new_order_view:
            if hasattr(self.new_order_view, 'save_draft'):
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
        if hasattr(self.new_order_view, 'has_unsaved_changes') and self.new_order_view.has_unsaved_changes():
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
        self.db_session.close()
        
        # Останавливаем таймеры
        self.time_timer.stop()
        self.autosave_timer.stop()
        
        event.accept()