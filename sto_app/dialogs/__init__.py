"""
Диалоги для модуля СТО.
"""

from .client_dialog import ClientDialog
from .car_dialog import CarDialog
from .service_dialog import ServiceDialog
from .part_dialog import PartDialog
from .order_details_dialog import OrderDetailsDialog

__all__ = [
    'ClientDialog', 
    'CarDialog', 
    'ServiceDialog', 
    'PartDialog',
    'OrderDetailsDialog'
]