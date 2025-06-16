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
    
    # Отдельные поля для гибкости
    first_name = Column(String(100))   # Имя (может быть пустым)
    last_name = Column(String(100))    # Фамилия (может быть пустым)  
    middle_name = Column(String(100))  # Отчество (может быть пустым)
    
    role = Column(String(50))
    phone = Column(String(50))
    email = Column(String(255))
    is_active = Column(Integer, default=1)
    
    @property
    def name(self):
        """Полное ФИО"""
        parts = []
        if self.last_name:
            parts.append(self.last_name)
        if self.first_name:
            parts.append(self.first_name)
        if self.middle_name:
            parts.append(self.middle_name)
        
        if not parts:
            return f"Сотрудник {self.id}"
        
        return " ".join(parts)
    
    @property
    def short_name(self):
        """Короткое ФИО: 'Иванов И.И.' или 'Иван'"""
        if self.last_name:
            result = self.last_name
            
            if self.first_name:
                result += f" {self.first_name[0]}."
            
            if self.middle_name:
                result += f"{self.middle_name[0]}."
                
            return result
        
        elif self.first_name:
            return self.first_name
        
        elif self.middle_name:
            return self.middle_name
        
        else:
            return f"Сотрудник {self.id}"
    
    @property
    def display_name(self):
        """Имя для отображения в интерфейсе"""
        if self.last_name and self.first_name:
            return f"{self.last_name} {self.first_name}"
        elif self.last_name:
            return self.last_name
        elif self.first_name:
            return self.first_name
        else:
            return f"Сотрудник {self.id}"
    
    def has_minimal_info(self):
        """Проверка минимальной информации"""
        return bool(self.first_name or self.last_name or self.middle_name)
    
    def __repr__(self):
        return f"<Employee(id={self.id}, name='{self.display_name}', role='{self.role}')>"