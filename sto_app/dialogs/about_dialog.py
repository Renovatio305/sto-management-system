# sto_app/dialogs/about_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QTextEdit, QFrame, QApplication)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap
import sys
import platform


class AboutDialog(QDialog):
    """Диалог 'О программе'"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('О программе')
        self.setFixedSize(500, 600)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Заголовок с иконкой
        header_layout = QHBoxLayout()
        
        # Иконка программы (если есть)
        try:
            icon_label = QLabel()
            pixmap = QPixmap('resources/icons/app.png')
            if not pixmap.isNull():
                icon_label.setPixmap(pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                icon_label.setText('🔧')
                icon_label.setStyleSheet('font-size: 48px;')
            icon_label.setAlignment(Qt.AlignCenter)
            header_layout.addWidget(icon_label)
        except:
            icon_label = QLabel('🔧')
            icon_label.setStyleSheet('font-size: 48px;')
            icon_label.setAlignment(Qt.AlignCenter)
            header_layout.addWidget(icon_label)
        
        # Информация о программе
        info_layout = QVBoxLayout()
        
        # Название программы
        app_name = QLabel('СТО Management System')
        app_name_font = QFont()
        app_name_font.setPointSize(18)
        app_name_font.setBold(True)
        app_name.setFont(app_name_font)
        app_name.setAlignment(Qt.AlignLeft)
        info_layout.addWidget(app_name)
        
        # Версия
        version_label = QLabel('Версия 3.0')
        version_font = QFont()
        version_font.setPointSize(12)
        version_label.setFont(version_font)
        version_label.setStyleSheet('color: #666;')
        info_layout.addWidget(version_label)
        
        # Описание
        description_label = QLabel('Система управления автосервисом')
        description_label.setStyleSheet('color: #888;')
        info_layout.addWidget(description_label)
        
        header_layout.addLayout(info_layout)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # Подробная информация
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(200)
        
        info_content = f"""
<h3>📋 Описание</h3>
<p>СТО Management System - это комплексная система управления автосервисом, 
разработанная для автоматизации всех основных процессов станции технического обслуживания.</p>

<h3>🎯 Основные возможности:</h3>
<ul>
<li>🔧 Управление заказами-нарядами</li>
<li>👥 База клиентов и автомобилей</li>
<li>💰 Расчёт стоимости услуг и запчастей</li>
<li>📊 Справочники услуг и материалов</li>
<li>🎨 Настраиваемые темы интерфейса</li>
<li>💾 Автосохранение и резервное копирование</li>
</ul>

<h3>🛠️ Технологии:</h3>
<p>Python 3.11+, PySide6, SQLAlchemy 2.0, SQLite</p>
        """
        
        info_text.setHtml(info_content)
        layout.addWidget(info_text)
        
        # Системная информация
        system_info = QTextEdit()
        system_info.setReadOnly(True)
        system_info.setMaximumHeight(150)
        
        system_content = f"""
<h3>💻 Системная информация:</h3>
<p><b>Операционная система:</b> {platform.system()} {platform.release()}</p>
<p><b>Архитектура:</b> {platform.machine()}</p>
<p><b>Python:</b> {sys.version.split()[0]}</p>
<p><b>PySide6:</b> {self.get_pyside_version()}</p>
<p><b>SQLAlchemy:</b> {self.get_sqlalchemy_version()}</p>
        """
        
        system_info.setHtml(system_content)
        layout.addWidget(system_info)
        
        # Кнопка закрытия
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton('Закрыть')
        close_btn.clicked.connect(self.accept)
        close_btn.setMinimumWidth(100)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
    def get_pyside_version(self):
        """Получить версию PySide6"""
        try:
            import PySide6
            return PySide6.__version__
        except:
            return 'Неизвестно'
    
    def get_sqlalchemy_version(self):
        """Получить версию SQLAlchemy"""
        try:
            import sqlalchemy
            return sqlalchemy.__version__
        except:
            return 'Неизвестно'


if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialog = AboutDialog()
    dialog.exec()
    sys.exit(app.exec())
