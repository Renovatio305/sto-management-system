# shared_models/common_models.py
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float
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
    year = Column(Integer)
    license_plate = Column(String(50))
    vin = Column(String(50), unique=True, index=True)
    mileage = Column(Integer)
    
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
    """Модель сотрудника"""
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    role = Column(String(50))  # 'manager', 'master', 'admin'
    phone = Column(String(50))
    email = Column(String(255))
    is_active = Column(Integer, default=1)
    
    def __repr__(self):
        return f"<Employee(id={self.id}, name='{self.name}', role='{self.role}')>"