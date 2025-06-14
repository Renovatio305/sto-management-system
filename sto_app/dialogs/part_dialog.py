from PySide6.QtWidgets import QDialog

class PartDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Добавление запчасти")
