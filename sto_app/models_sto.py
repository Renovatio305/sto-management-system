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
    article = Column(String(100))
    part_name = Column(String(500), nullable=False)
    part_name_ua = Column(String(500))
    unit = Column(String(20), default='шт')
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    total = Column(Float)
    
    # Отношения
    order = relationship("Order", back_populates="parts")
    
    def calculate_total(self):
        """Рассчитать общую стоимость"""
        self.total = self.price * self.quantity
        return self.total


class ServiceCatalog(Base, TimestampMixin):
    """Каталог услуг"""
    __tablename__ = 'services_catalog'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(500), unique=True, nullable=False, index=True)
    name_ua = Column(String(500))
    price = Column(Float, nullable=False)
    category = Column(String(100))
    synonyms = Column(Text)  # Для поиска похожих услуг
    is_active = Column(Integer, default=1)
    
    def __repr__(self):
        return f"<ServiceCatalog(id={self.id}, name='{self.name}', price={self.price})>"


class CarBrand(Base):
    """Марки автомобилей"""
    __tablename__ = 'car_brands'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    brand = Column(String(100), unique=True, nullable=False)
    models = Column(Text)  # Список моделей через запятую
    
    def get_models_list(self):
        """Получить список моделей"""
        return [m.strip() for m in self.models.split(',')] if self.models else []
