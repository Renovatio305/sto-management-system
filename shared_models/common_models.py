# shared_models/common_models.py
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float, Date, Numeric
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class Client(Base, TimestampMixin):
    """Модель клиента"""
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), index=True)
    address = Column(Text)
    email = Column(String(255))
    
    # Отношения
    cars = relationship("Car", back_populates="client", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="client")
    
    def __repr__(self):
        return f"<Client(id={self.id}, name='{self.name}', phone='{self.phone}')>"


class Car(Base, TimestampMixin):
    """Модель автомобиля"""
    __tablename__ = 'cars'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    brand = Column(String(100))
    model = Column(String(100))
    make = Column(String(100))  # Дублирует brand для совместимости с CarDialog
    year = Column(Integer)
    license_plate = Column(String(50))
    vin = Column(String(50), unique=True, index=True)
    mileage = Column(Integer)
    color = Column(String(50))           # Добавлено для CarDialog
    engine_volume = Column(Float)        # Добавлено для CarDialog
    fuel_type = Column(String(50))       # Добавлено для CarDialog
    is_active = Column(Integer, default=1)  # Добавлено для CarDialog
    notes = Column(Text)                 # Добавлено для CarDialog
    
    # Отношения
    client = relationship("Client", back_populates="cars")
    orders = relationship("Order", back_populates="car")
    
    @property
    def full_name(self):
        """Полное название автомобиля"""
        parts = []
        if self.brand:
            parts.append(self.brand)
        if self.model:
            parts.append(self.model)
        if self.year:
            parts.append(f"({self.year})")
        return " ".join(parts) if parts else "Не указан"
    
    def __repr__(self):
        return f"<Car(id={self.id}, brand='{self.brand}', model='{self.model}', vin='{self.vin}')>"


class Employee(Base, TimestampMixin):
    """Расширенная модель сотрудника"""
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Основная информация (для обратной совместимости)
    name = Column(String(255), nullable=False)
    role = Column(String(50))  # 'manager', 'master', 'admin'
    phone = Column(String(50))
    email = Column(String(255))
    is_active = Column(Integer, default=1)
    
    # Расширенные поля для полноценного управления персоналом
    first_name = Column(String(100))
    last_name = Column(String(100))
    middle_name = Column(String(100))
    position = Column(String(100))  # Дублирует role для совместимости с диалогами
    department = Column(String(100))
    hire_date = Column(Date)
    hourly_rate = Column(Numeric(10, 2))
    
    @property
    def full_name(self):
        """Полное имя сотрудника"""
        if self.last_name and self.first_name:
            parts = [self.last_name, self.first_name]
            if self.middle_name:
                parts.append(self.middle_name)
            return " ".join(parts)
        return self.name or "Не указано"
    
    def __repr__(self):
        return f"<Employee(id={self.id}, name='{self.name}', role='{self.role}')>"