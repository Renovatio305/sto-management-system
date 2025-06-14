from PySide6.QtWidgets import QMainWindow

class SalesMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Продажи")
