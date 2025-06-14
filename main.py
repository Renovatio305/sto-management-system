#!/usr/bin/env python
"""
СТО Management System v3.0
Модульная система управления автосервисом

Автор: AutoService Team
Лицензия: Proprietary
"""

import sys
import os
import logging
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sto_app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def check_requirements():
    """Проверка необходимых компонентов"""
    try:
        import PySide6
        logger.info(f"PySide6 версия: {PySide6.__version__}")
    except ImportError:
        logger.error("PySide6 не установлен. Установите: pip install PySide6")
        return False
    
    try:
        import sqlalchemy
        logger.info(f"SQLAlchemy версия: {sqlalchemy.__version__}")
    except ImportError:
        logger.error("SQLAlchemy не установлен. Установите: pip install sqlalchemy")
        return False
    
    # Проверка структуры директорий
    required_dirs = ['resources', 'resources/icons', 'resources/images', 'translations']
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            logger.info(f"Создание директории: {dir_name}")
            dir_path.mkdir(parents=True, exist_ok=True)
    
    return True


def main():
    """Главная функция"""
    logger.info("=== Запуск СТО Management System v3.0 ===")
    
    # Проверка требований
    if not check_requirements():
        logger.error("Не все требования выполнены. Завершение.")
        return 1
    
    try:
        # Импорт приложения
        from sto_app.app import STOApplication
        
        # Создание и запуск
        app = STOApplication(sys.argv)
        
        # Установка высокого DPI для 4K мониторов
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # Запуск
        result = app.run()
        
        logger.info("=== Завершение работы ===")
        return result
        
    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
        
        # Показываем диалог ошибки
        try:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                None,
                "Критическая ошибка",
                f"Произошла критическая ошибка:\n\n{str(e)}\n\nПодробности в файле sto_app.log"
            )
        except:
            print(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
        
        return 1


if __name__ == '__main__':
    sys.exit(main())