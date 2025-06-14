from PySide6.QtWidgets import QWidget

class SettingsView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Настройки")
