# ИНТЕГРАЦИЯ OrderDetailsDialog В OrdersView
# Добавить эти изменения в файл sto_app/views/orders_view.py

# 1. ДОБАВИТЬ в импорты (в начале файла):
from sto_app.dialogs import OrderDetailsDialog

# 2. ДОБАВИТЬ метод в класс OrdersView:
def view_order_details(self):
    """Просмотр полных деталей выбранного заказа"""
    current_row = self.orders_table.currentRow()
    if current_row < 0:
        QMessageBox.information(self, "Информация", "Выберите заказ для просмотра")
        return
    
    # Получаем ID заказа из скрытой колонки или данных строки
    order_id_item = self.orders_table.item(current_row, 0)  # Предполагаем, что ID в первой колонке
    if not order_id_item:
        QMessageBox.warning(self, "Предупреждение", "Не удалось определить ID заказа")
        return
    
    try:
        # Извлекаем ID заказа (может быть в тексте или в данных ячейки)
        order_id = int(order_id_item.text()) if order_id_item.text().isdigit() else None
        if not order_id:
            # Попробуем получить из пользовательских данных ячейки
            order_id = order_id_item.data(Qt.UserRole)
        
        if not order_id:
            QMessageBox.warning(self, "Предупреждение", "Не удалось определить ID заказа")
            return
            
        # Открываем диалог деталей заказа
        dialog = OrderDetailsDialog(self, order_id=order_id)
        dialog.exec()
        
    except (ValueError, TypeError) as e:
        QMessageBox.critical(self, "Ошибка", f"Некорректный ID заказа: {e}")
    except Exception as e:
        QMessageBox.critical(self, "Ошибка", f"Не удалось открыть детали заказа: {e}")

# 3. ДОБАВИТЬ кнопку в UI (метод setup_ui или аналогичный):
def add_details_button_to_ui(self):
    """Добавление кнопки просмотра деталей в интерфейс"""
    # Найти layout с кнопками (обычно это кнопки "Создать", "Редактировать", "Удалить")
    # и добавить новую кнопку
    
    details_btn = QPushButton("📋 Детали")
    details_btn.setToolTip("Просмотр полных деталей заказа")
    details_btn.clicked.connect(self.view_order_details)
    
    # Добавить кнопку в layout кнопок (нужно найти конкретное место в коде OrdersView)
    # Например, если есть buttons_layout:
    # buttons_layout.addWidget(details_btn)
    
    return details_btn

# 4. АЛЬТЕРНАТИВНЫЙ ВАРИАНТ - добавить в контекстное меню:
def add_to_context_menu(self):
    """Добавление пункта в контекстное меню таблицы заказов"""
    # Если в OrdersView есть контекстное меню для таблицы заказов
    
    details_action = QAction("📋 Просмотр деталей", self)
    details_action.triggered.connect(self.view_order_details)
    
    # Добавить в существующее контекстное меню
    # context_menu.addAction(details_action)
    
    return details_action

# 5. ДОБАВИТЬ обработчик двойного клика:
def setup_table_double_click(self):
    """Настройка двойного клика по таблице для открытия деталей"""
    self.orders_table.doubleClicked.connect(self.view_order_details)

# 6. УЛУЧШЕННАЯ ВЕРСИЯ с проверкой структуры таблицы:
def view_order_details_enhanced(self):
    """Улучшенная версия просмотра деталей заказа"""
    current_row = self.orders_table.currentRow()
    if current_row < 0:
        QMessageBox.information(self, "Информация", "Выберите заказ для просмотра")
        return
    
    try:
        # Определяем колонку с ID заказа
        order_id = None
        
        # Вариант 1: ID в первой колонке
        if self.orders_table.columnCount() > 0:
            id_item = self.orders_table.item(current_row, 0)
            if id_item and id_item.text().isdigit():
                order_id = int(id_item.text())
        
        # Вариант 2: ID сохранен в UserRole любой ячейки строки
        if not order_id:
            for col in range(self.orders_table.columnCount()):
                item = self.orders_table.item(current_row, col)
                if item and item.data(Qt.UserRole):
                    try:
                        order_id = int(item.data(Qt.UserRole))
                        break
                    except (ValueError, TypeError):
                        continue
        
        # Вариант 3: Поиск по номеру заказа
        if not order_id:
            # Попробуем найти колонку с номером заказа
            for col in range(self.orders_table.columnCount()):
                header_item = self.orders_table.horizontalHeaderItem(col)
                if header_item and "номер" in header_item.text().lower():
                    number_item = self.orders_table.item(current_row, col)
                    if number_item:
                        order_number = number_item.text()
                        # Поиск заказа по номеру в БД
                        try:
                            from sqlalchemy import select
                            from sto_app.models_sto import Order
                            
                            stmt = select(Order.id).where(Order.order_number == order_number)
                            result = self.db_session.execute(stmt)
                            order_id = result.scalar_one_or_none()
                            break
                        except Exception as e:
                            self.logger.error(f"Ошибка поиска заказа по номеру: {e}")
        
        if not order_id:
            QMessageBox.warning(self, "Предупреждение", 
                              "Не удалось определить ID заказа.\n"
                              "Убедитесь, что заказ выбран корректно.")
            return
        
        # Открываем диалог деталей заказа
        dialog = OrderDetailsDialog(self, order_id=order_id)
        dialog.exec()
        
    except Exception as e:
        self.logger.error(f"Ошибка открытия деталей заказа: {e}")
        QMessageBox.critical(self, "Ошибка", f"Не удалось открыть детали заказа: {e}")

# ИНСТРУКЦИЯ ПО ИНТЕГРАЦИИ:
"""
1. Найти в orders_view.py место, где создаются кнопки управления заказами
2. Добавить кнопку "Детали" рядом с существующими кнопками
3. Подключить метод view_order_details_enhanced к кнопке
4. Опционально: добавить двойной клик для быстрого доступа
5. Убедиться, что в таблице заказов сохраняется ID заказа (в UserRole или отдельной колонке)
"""