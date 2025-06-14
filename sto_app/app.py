# sto_app/app.py
import sys
import os
from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtCore import Qt, QTimer, QTranslator, QLocale
from PySide6.QtGui import QPixmap, QIcon

from .main_window import MainWindow
from .styles.themes import apply_theme
from config.database import init_database, engine


class STOApplication(QApplication):
    """Главный класс приложения СТО"""
    
    def __init__(self, argv):
        super().__init__(argv)
        
        # Установка основных параметров
        self.setApplicationName('СТО Management System')
        self.setOrganizationName('AutoService')
        self.setOrganizationDomain('autoservice.ua')
        
        # Установка иконки приложения
        self.setWindowIcon(QIcon('resources/icons/app.png'))
        
        # Инициализация
        self.translator = QTranslator()
        self.splash = None
        self.main_window = None
        
    def run(self):
        """Запуск приложения"""
        # Показываем заставку
        self.show_splash()
        
        # Инициализация БД
        self.splash_message("Инициализация базы данных...")
        try:
            init_database()
        except Exception as e:
            print(f"Ошибка инициализации БД: {e}")
            return 1
        
        # Загрузка переводов
        self.splash_message("Загрузка языковых файлов...")
        self.load_translations()
        
        # Применение темы
        self.splash_message("Применение темы...")
        settings = self.main_window.settings if self.main_window else None
        theme = settings.value('theme', 'light') if settings else 'light'
        apply_theme(self, theme)
        
        # Создание главного окна
        self.splash_message("Загрузка интерфейса...")
        self.main_window = MainWindow()
        
        # Подключение сигналов темы
        self.main_window.theme_changed.connect(lambda t: apply_theme(self, t))
        
        # Закрытие заставки и показ главного окна
        QTimer.singleShot(1000, self.finish_loading)
        
        return self.exec()
    
    def show_splash(self):
        """Показать заставку при загрузке"""
        splash_pixmap = QPixmap('resources/images/splash.png')
        if splash_pixmap.isNull():
            # Создаем простую заставку если изображение не найдено
            splash_pixmap = QPixmap(600, 400)
            splash_pixmap.fill(Qt.white)
        
        self.splash = QSplashScreen(splash_pixmap)
        self.splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.splash.show()
        
        # Обработка событий для отображения
        self.processEvents()
    
    def splash_message(self, message):
        """Показать сообщение на заставке"""
        if self.splash:
            self.splash.showMessage(
                message,
                Qt.AlignBottom | Qt.AlignCenter,
                Qt.black
            )
            self.processEvents()
    
    def finish_loading(self):
        """Завершение загрузки"""
        if self.splash:
            self.splash.finish(self.main_window)
        self.main_window.show()
    
    def load_translations(self):
        """Загрузка переводов"""
        locale = QLocale.system().name()
        
        # Пытаемся загрузить перевод для системной локали
        if self.translator.load(f"translations/sto_{locale}.qm"):
            self.installTranslator(self.translator)
        elif self.translator.load(f"translations/sto_uk_UA.qm"):
            # По умолчанию украинский
            self.installTranslator(self.translator)