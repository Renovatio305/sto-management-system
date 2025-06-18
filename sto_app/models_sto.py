# sto_app/models_sto.py
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float, DateTime, Enum
from sqlalchemy.orm import relationship
from shared_models.base import Base, TimestampMixin
import enum


class OrderStatus(enum.Enum):
    """Статусы заказа"""
    DRAFT = "Чернетка"
    IN_WORK = "В роботі"
    WAITING_PAYMENT = "Очікує оплату"
    COMPLETED = "Завершено"
    CANCELLED = "Скасовано"


class Order(Base, TimestampMixin):
    """Модель заказа"""
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    car_id = Column(Integer, ForeignKey('cars.id'), nullable=False)
    
    date_received = Column(DateTime, nullable=False)
    date_delivery = Column(DateTime)
    
    responsible_person_id = Column(Integer, ForeignKey('employees.id'))
    manager_id = Column(Integer, ForeignKey('employees.id'))
    
    status = Column(Enum(OrderStatus), default=OrderStatus.DRAFT, nullable=False)
    
    total_amount = Column(Float, default=0.0)
    prepayment = Column(Float, default=0.0)
    additional_payment = Column(Float, default=0.0)
    
    notes = Column(Text)
    
    # Отношения
    client = relationship("Client", back_populates="orders")
    car = relationship("Car", back_populates="orders")
    services = relationship("OrderService", back_populates="order", cascade="all, delete-orphan")
    parts = relationship("OrderPart", back_populates="order", cascade="all, delete-orphan")
    
    responsible_person = relationship("Employee", foreign_keys=[responsible_person_id])
    manager = relationship("Employee", foreign_keys=[manager_id])
    
    @property
    def balance_due(self):
        """Остаток к оплате"""
        return self.total_amount - self.prepayment - self.additional_payment
    
    def __repr__(self):
        return f"<Order(id={self.id}, number='{self.order_number}', status={self.status.value})>"


class OrderService(Base):
    """Услуги в заказе"""
    __tablename__ = 'order_services'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    
    # Основная информация об услуге
    service_name = Column(String(500), nullable=False)
    service_name_ua = Column(String(500))
    
    # Связи с каталогом и сотрудником
    service_catalog_id = Column(Integer, ForeignKey('services_catalog.id'))  
    employee_id = Column(Integer, ForeignKey('employees.id'))                
    
    # Параметры выполнения
    quantity = Column(Integer, default=1)                             
    duration_hours = Column(Float, default=1.0)                         
    
    # Ценообразование
    price = Column(Float, nullable=False)
    price_with_vat = Column(Float)
    discount_amount = Column(Float, default=0.0)                            
    discount_percent = Column(Float, default=0.0)                        
    
    # Статус и комментарии
    is_completed = Column(Integer, default=0)                              
    notes = Column(Text)                                                   
    
    # Отношения
    order = relationship("Order", back_populates="services")
    service_catalog = relationship("ServiceCatalog")                        
    employee = relationship("Employee")                                      
    
    def calculate_vat(self, vat_rate=0.2):
        """Рассчитать цену с НДС"""
        self.price_with_vat = self.price * (1 + vat_rate)
        return self.price_with_vat
    
    def calculate_total_with_discount(self):                               
        """Рассчитать итоговую стоимость с учетом скидки"""
        subtotal = self.price * self.quantity
        
        if self.discount_amount:
            total = subtotal - self.discount_amount
        elif self.discount_percent:
            discount = subtotal * (self.discount_percent / 100)
            total = subtotal - discount
        else:
            total = subtotal
            
        return max(total, 0)  # Не может быть отрицательной

class OrderPart(Base):
    """Запчасти в заказе"""
    __tablename__ = 'order_parts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    
    # Основная информация
    name = Column(String(500), nullable=False)  # part_name в диалоге
    part_number = Column(String(100))           # article в старой модели
    manufacturer = Column(String(100))          # ДОБАВЛЕНО для part_dialog.py
    supplier = Column(String(100))              # ДОБАВЛЕНО для part_dialog.py
    
    # Количество и единицы
    unit = Column(String(20), default='шт')
    quantity = Column(Integer, nullable=False)
    
    # Ценообразование  
    unit_price = Column(Float, nullable=False)  # price в старой модели
    total = Column(Float)
    discount_amount = Column(Float, default=0.0)    # ДОБАВЛЕНО для part_dialog.py
    discount_percent = Column(Float, default=0.0)   # ДОБАВЛЕНО для part_dialog.py
    
    # Дополнительная информация
    description = Column(Text)                  # ДОБАВЛЕНО для part_dialog.py
    in_stock = Column(Integer, default=1)       # ДОБАВЛЕНО для part_dialog.py
    is_received = Column(Integer, default=0)    # ДОБАВЛЕНО для part_dialog.py
    
    # Совместимость со старыми полями
    article = Column(String(100))  # алиас для part_number
    part_name = Column(String(500))  # алиас для name
    part_name_ua = Column(String(500))
    price = Column(Float)  # алиас для unit_price
    
    # Отношения
    order = relationship("Order", back_populates="parts")
    
    def calculate_total(self):
        """Рассчитать общую стоимость"""
        if self.unit_price and self.quantity:
            subtotal = self.unit_price * self.quantity
            
            # Применяем скидки
            if self.discount_amount:
                self.total = subtotal - self.discount_amount
            elif self.discount_percent:
                discount = subtotal * (self.discount_percent / 100)
                self.total = subtotal - discount
            else:
                self.total = subtotal
                
            # Обновляем совместимые поля
            self.price = self.unit_price
            self.part_name = self.name
            self.article = self.part_number
            
            return max(self.total, 0)
        return 0


class ServiceCatalog(Base, TimestampMixin):
    """Каталог услуг"""
    __tablename__ = 'services_catalog'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(500), unique=True, nullable=False, index=True)
    name_ua = Column(String(500))
    description = Column(Text)
    category = Column(String(100))
    default_price = Column(Float, nullable=False)  # БАЗОВАЯ цена
    vat_rate = Column(Float, default=20.0)
    duration_hours = Column(Float, default=1.0)
    synonyms = Column(Text)
    is_active = Column(Integer, default=1)
    
    def __repr__(self):
        return f"<ServiceCatalog(id={self.id}, name='{self.name}', default_price={self.default_price})>"


class CarBrand(Base):
    """Марки автомобилей"""
    __tablename__ = 'car_brands'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    brand = Column(String(100), unique=True, nullable=False)
    models = Column(Text)  # Список моделей через запятую
    
    def get_models_list(self):
        """Получить список моделей"""
        return [m.strip() for m in self.models.split(',')] if self.models else []
