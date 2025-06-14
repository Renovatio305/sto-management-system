from PySide6.QtWidgets import QDialog

class ServiceDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Добавление услуги")
