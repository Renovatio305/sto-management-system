from PySide6.QtWidgets import QApplication
from sales_app.main_window import SalesMainWindow
import sys

class SalesApplication:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.main_window = SalesMainWindow()

    def run(self):
        self.main_window.show()
        sys.exit(self.app.exec())
