from PySide6.QtWidgets import QDialog

class ClientDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Клиент")
