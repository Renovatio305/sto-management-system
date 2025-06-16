# sto_app/styles/themes.py
"""Темы оформления для приложения"""

LIGHT_THEME = """
QMainWindow {
    background-color: #f5f5f5;
}

QTabWidget::pane {
    border: 1px solid #ddd;
    background-color: white;
}

QTabBar::tab {
    background-color: #e0e0e0;
    color: #333;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: white;
    border-bottom: 2px solid #2196F3;
}

QTabBar::tab:hover {
    background-color: #f0f0f0;
}

QPushButton {
    background-color: #2196F3;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #1976D2;
}

QPushButton:pressed {
    background-color: #0D47A1;
}

QPushButton:disabled {
    background-color: #BBBBBB;
    color: #777777;
}

/* Accent button */
QPushButton[accent="true"] {
    background-color: #4CAF50;
}

QPushButton[accent="true"]:hover {
    background-color: #45a049;
}

/* Danger button */
QPushButton[danger="true"] {
    background-color: #f44336;
}

QPushButton[danger="true"]:hover {
    background-color: #da190b;
}

QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit {
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 6px;
    color: #333;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 2px solid #2196F3;
    outline: none;
}

QComboBox {
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 6px;
    color: #333;
}

QComboBox::drop-down {
    border: none;
}

QComboBox::down-arrow {
    image: url(resources/icons/arrow_down.png);
    width: 12px;
    height: 12px;
}

QTableWidget, QTableView, QTreeWidget, QTreeView {
    background-color: white;
    border: 1px solid #ddd;
    gridline-color: #f0f0f0;
    selection-background-color: #E3F2FD;
    selection-color: #333;
}

QTableWidget::item:selected, QTreeWidget::item:selected {
    background-color: #E3F2FD;
    color: #333;
}

QHeaderView::section {
    background-color: #f5f5f5;
    color: #333;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #ddd;
    font-weight: bold;
}

QScrollBar:vertical {
    background-color: #f0f0f0;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #c0c0c0;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #a0a0a0;
}

QGroupBox {
    font-weight: bold;
    border: 2px solid #ddd;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
    background-color: white;
}

QLabel {
    color: #333;
}

QStatusBar {
    background-color: #e0e0e0;
    color: #666;
}

QMenuBar {
    background-color: #f5f5f5;
    color: #333;
}

QMenuBar::item:selected {
    background-color: #e0e0e0;
}

QMenu {
    background-color: white;
    border: 1px solid #ddd;
}

QMenu::item:selected {
    background-color: #E3F2FD;
}

QToolBar {
    background-color: #f5f5f5;
    border-bottom: 1px solid #ddd;
    spacing: 3px;
    padding: 5px;
}

QToolBar QToolButton {
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 5px;
}

QToolBar QToolButton:hover {
    background-color: #e0e0e0;
}

QToolBar QToolButton:pressed {
    background-color: #d0d0d0;
}
"""

DARK_THEME = """
QMainWindow {
    background-color: #1e1e1e;
    color: #ffffff;
}

QTabWidget::pane {
    border: 1px solid #444;
    background-color: #2d2d30;
}

QTabBar::tab {
    background-color: #252526;
    color: #cccccc;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: #2d2d30;
    color: #ffffff;
    border-bottom: 2px solid #007ACC;
}

QTabBar::tab:hover {
    background-color: #3e3e42;
}

QPushButton {
    background-color: #0e639c;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #1177bb;
}

QPushButton:pressed {
    background-color: #094771;
}

QPushButton:disabled {
    background-color: #3e3e42;
    color: #6e6e6e;
}

/* Accent button */
QPushButton[accent="true"] {
    background-color: #4daf4f;
}

QPushButton[accent="true"]:hover {
    background-color: #6fbf71;
}

/* Danger button */
QPushButton[danger="true"] {
    background-color: #f44336;
}

QPushButton[danger="true"]:hover {
    background-color: #f66356;
}

QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit {
    background-color: #3c3c3c;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 6px;
    color: #ffffff;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 2px solid #007ACC;
    outline: none;
}

QComboBox {
    background-color: #3c3c3c;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 6px;
    color: #ffffff;
}

QComboBox::drop-down {
    border: none;
}

QComboBox::down-arrow {
    image: url(resources/icons/arrow_down_white.png);
    width: 12px;
    height: 12px;
}

QTableWidget, QTableView, QTreeWidget, QTreeView {
    background-color: #252526;
    border: 1px solid #444;
    gridline-color: #3e3e42;
    selection-background-color: #094771;
    selection-color: #ffffff;
    color: #cccccc;
}

QTableWidget::item, QTreeWidget::item {
    color: #cccccc;
}

QTableWidget::item:selected, QTreeWidget::item:selected {
    background-color: #094771;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #2d2d30;
    color: #cccccc;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #444;
    font-weight: bold;
}

QScrollBar:vertical {
    background-color: #2d2d30;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #555;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #666;
}

QGroupBox {
    font-weight: bold;
    border: 2px solid #444;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 10px;
    color: #cccccc;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
    background-color: #2d2d30;
    color: #cccccc;
}

QLabel {
    color: #cccccc;
}

QStatusBar {
    background-color: #007ACC;
    color: #ffffff;
}

QMenuBar {
    background-color: #2d2d30;
    color: #cccccc;
}

QMenuBar::item:selected {
    background-color: #3e3e42;
}

QMenu {
    background-color: #252526;
    border: 1px solid #444;
    color: #cccccc;
}

QMenu::item {
    color: #cccccc;
    padding: 5px 20px;
}

QMenu::item:selected {
    background-color: #094771;
    color: #ffffff;
}

QToolBar {
    background-color: #2d2d30;
    border-bottom: 1px solid #444;
    spacing: 3px;
    padding: 5px;
}

QToolBar QToolButton {
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 5px;
    color: #cccccc;
}

QToolBar QToolButton:hover {
    background-color: #3e3e42;
}

QToolBar QToolButton:pressed {
    background-color: #094771;
}

QCheckBox, QRadioButton {
    color: #cccccc;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
}

QCheckBox::indicator:unchecked {
    background-color: #3c3c3c;
    border: 1px solid #555;
    border-radius: 3px;
}

QCheckBox::indicator:checked {
    background-color: #007ACC;
    border: 1px solid #007ACC;
    image: url(resources/icons/check_white.png);
}

QProgressBar {
    background-color: #3c3c3c;
    border: 1px solid #555;
    border-radius: 4px;
    text-align: center;
    color: #ffffff;
}

QProgressBar::chunk {
    background-color: #007ACC;
    border-radius: 3px;
}
"""

def apply_theme(app, theme_name='light'):
    """Применить тему к приложению"""
    if theme_name == 'dark':
        app.setStyleSheet(DARK_THEME)
    else:
        app.setStyleSheet(LIGHT_THEME)