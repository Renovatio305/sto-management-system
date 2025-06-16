# shared_models/base.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime, func

Base = declarative_base()

class TimestampMixin:
    """Миксин для добавления временных меток к моделям"""
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)