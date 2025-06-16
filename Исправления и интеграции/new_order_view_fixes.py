# ИСПРАВЛЕНИЯ ДЛЯ new_order_view.py
# Эти методы нужно заменить в файле sto_app/views/new_order_view.py

# 1. ЗАМЕНИТЬ метод add_service() (строка 521):
def add_service(self):
    """Добавление услуги через диалог"""
    if not self.current_order:
        # Создаем временный заказ для передачи order_id
        reply = QMessageBox.question(
            self, 'Создание заказа',
            'Для добавления услуг необходимо сначала сохранить заказ как черновик. Продолжить?',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if not self.save_draft():
                return
        else:
            return

    dialog = ServiceDialog(self, order_id=self.current_order.id)
    dialog.service_cost_changed.connect(self.calculate_totals)
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        order_service = dialog.get_order_service()
        if order_service:
            # Обновляем таблицу услуг
            self.refresh_services_table()
            self.calculate_totals()
            self.mark_unsaved_changes()

# 2. ЗАМЕНИТЬ метод add_part() (строка 548):
def add_part(self):
    """Добавление запчасти через диалог"""
    if not self.current_order:
        reply = QMessageBox.question(
            self, 'Создание заказа',
            'Для добавления запчастей необходимо сначала сохранить заказ как черновик. Продолжить?',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if not self.save_draft():
                return
        else:
            return

    dialog = PartDialog(self, order_id=self.current_order.id)
    dialog.part_cost_changed.connect(self.calculate_totals)
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        order_part = dialog.get_order_part()
        if order_part:
            # Обновляем таблицу запчастей
            self.refresh_parts_table()
            self.calculate_totals()
            self.mark_unsaved_changes()

# 3. УДАЛИТЬ ПОЛНОСТЬЮ метод add_service_from_search() (строка 502)
# 4. УДАЛИТЬ ПОЛНОСТЬЮ метод add_part_from_search() (строка 537)

# 5. ДОБАВИТЬ новые методы в конец класса:

def refresh_services_table(self):
    """Обновление таблицы услуг из БД"""
    if not self.current_order or not self.current_order.id:
        return
        
    try:
        # Загружаем услуги из БД
        services = self.db_session.query(OrderService).filter(
            OrderService.order_id == self.current_order.id
        ).all()
        
        # Очищаем таблицу
        self.services_table.setRowCount(0)
        
        # Заполняем таблицу
        for service in services:
            self.add_service_row_from_db(service)
            
    except Exception as e:
        logger.error(f"Ошибка обновления таблицы услуг: {e}")

def refresh_parts_table(self):
    """Обновление таблицы запчастей из БД"""
    if not self.current_order or not self.current_order.id:
        return
        
    try:
        # Загружаем запчасти из БД
        parts = self.db_session.query(OrderPart).filter(
            OrderPart.order_id == self.current_order.id
        ).all()
        
        # Очищаем таблицу
        self.parts_table.setRowCount(0)
        
        # Заполняем таблицу
        for part in parts:
            self.add_part_row_from_db(part)
            
    except Exception as e:
        logger.error(f"Ошибка обновления таблицы запчастей: {e}")

def add_service_row_from_db(self, service):
    """Добавление строки услуги из объекта БД"""
    row = self.services_table.rowCount()
    self.services_table.insertRow(row)
    
    # Заполняем данные из объекта OrderService
    self.services_table.setItem(row, 0, QTableWidgetItem(service.service_catalog.name if service.service_catalog else "Услуга"))
    
    price_item = QTableWidgetItem(f'{float(service.price):.2f}')
    price_item.setTextAlignment(Qt.AlignRight)
    self.services_table.setItem(row, 1, price_item)
    
    # Цена с НДС (если есть поле)
    if hasattr(service, 'price_with_vat') and service.price_with_vat:
        vat_price = float(service.price_with_vat)
    else:
        vat_price = float(service.price) * 1.2
        
    vat_item = QTableWidgetItem(f'{vat_price:.2f}')
    vat_item.setTextAlignment(Qt.AlignRight)
    self.services_table.setItem(row, 2, vat_item)
    
    # Кнопка удаления
    delete_btn = QPushButton('🗑️')
    delete_btn.setMaximumWidth(30)
    delete_btn.clicked.connect(lambda: self.remove_service_from_db(service.id, row))
    self.services_table.setCellWidget(row, 3, delete_btn)

def add_part_row_from_db(self, part):
    """Добавление строки запчасти из объекта БД"""
    row = self.parts_table.rowCount()
    self.parts_table.insertRow(row)
    
    # Заполняем данные из объекта OrderPart
    self.parts_table.setItem(row, 0, QTableWidgetItem(part.part_number or ""))
    self.parts_table.setItem(row, 1, QTableWidgetItem(part.name))
    
    qty_item = QTableWidgetItem(str(part.quantity))
    qty_item.setTextAlignment(Qt.AlignCenter)
    self.parts_table.setItem(row, 2, qty_item)
    
    price_item = QTableWidgetItem(f'{float(part.unit_price):.2f}')
    price_item.setTextAlignment(Qt.AlignRight)
    self.parts_table.setItem(row, 3, price_item)
    
    total = float(part.unit_price) * part.quantity
    total_item = QTableWidgetItem(f'{total:.2f}')
    total_item.setTextAlignment(Qt.AlignRight)
    self.parts_table.setItem(row, 4, total_item)
    
    # Кнопка удаления
    delete_btn = QPushButton('🗑️')
    delete_btn.setMaximumWidth(30)
    delete_btn.clicked.connect(lambda: self.remove_part_from_db(part.id, row))
    self.parts_table.setCellWidget(row, 5, delete_btn)

def remove_service_from_db(self, service_id, row):
    """Удаление услуги из БД"""
    reply = QMessageBox.question(
        self, 'Подтверждение',
        'Удалить выбранную услугу?',
        QMessageBox.Yes | QMessageBox.No
    )
    
    if reply == QMessageBox.Yes:
        try:
            # Удаляем из БД
            service = self.db_session.get(OrderService, service_id)
            if service:
                self.db_session.delete(service)
                self.db_session.commit()
            
            # Удаляем из таблицы
            self.services_table.removeRow(row)
            self.calculate_totals()
            self.mark_unsaved_changes()
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Ошибка удаления услуги: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Не удалось удалить услугу: {e}')

def remove_part_from_db(self, part_id, row):
    """Удаление запчасти из БД"""
    reply = QMessageBox.question(
        self, 'Подтверждение',
        'Удалить выбранную запчасть?',
        QMessageBox.Yes | QMessageBox.No
    )
    
    if reply == QMessageBox.Yes:
        try:
            # Удаляем из БД
            part = self.db_session.get(OrderPart, part_id)
            if part:
                self.db_session.delete(part)
                self.db_session.commit()
            
            # Удаляем из таблицы
            self.parts_table.removeRow(row)
            self.calculate_totals()
            self.mark_unsaved_changes()
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Ошибка удаления запчасти: {e}")
            QMessageBox.critical(self, 'Ошибка', f'Не удалось удалить запчасть: {e}')

# ДОБАВИТЬ в импорты в начале файла:
from sto_app.models_sto import OrderService, OrderPart