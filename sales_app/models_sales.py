from config.database import Base
from sqlalchemy import Column, Integer, String

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String)

class Stock(Base):
    __tablename__ = "stock"
    id = Column(Integer, primary_key=True)

class Sale(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True)

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True)
