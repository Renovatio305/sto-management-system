from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox

class ImportDialog(QDialog):
    def __init__(self, parent=None, db_session=None):
        super().__init__(parent)
        self.db_session = db_session
        self.setWindowTitle("Импорт данных")
        self.setModal(True)
        self.resize(400, 200)
        
        layout = QVBoxLayout(self)
        
        title = QLabel("📥 Импорт данных")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        
        info = QLabel("Функция импорта данных будет реализована в следующей версии.")
        info.setStyleSheet("color: #666; font-style: italic; margin: 10px 0;")
        layout.addWidget(info)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

class ExportDialog(QDialog):
    def __init__(self, parent=None, db_session=None):
        super().__init__(parent)
        self.db_session = db_session
        self.setWindowTitle("Экспорт данных")
        self.setModal(True)
        self.resize(400, 200)
        
        layout = QVBoxLayout(self)
        
        title = QLabel("📤 Экспорт данных")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        
        info = QLabel("Функция экспорта данных будет реализована в следующей версии.")
        info.setStyleSheet("color: #666; font-style: italic; margin: 10px 0;")
        layout.addWidget(info)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)