#!/usr/bin/env python
"""
Скрипт для инициализации базы данных
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import init_database, engine
from shared_models.base import Base
from sqlalchemy import text

def reset_database():
    """Полный сброс базы данных"""
    print("⚠️  ВНИМАНИЕ: Все данные будут удалены!")
    response = input("Вы уверены? (yes/no): ")
    
    if response.lower() == 'yes':
        print("Удаление существующих таблиц...")
        Base.metadata.drop_all(bind=engine)
        print("✓ Таблицы удалены")
        
        print("Создание новых таблиц...")
        init_database()
        print("✓ База данных инициализирована")
    else:
        print("Операция отменена")

def check_database():
    """Проверка состояния базы данных"""
    with engine.connect() as conn:
        # Получаем список таблиц
        result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        ))
        tables = result.fetchall()
        
        print("Существующие таблицы:")
        for table in tables:
            print(f"  - {table[0]}")
            
            # Подсчет записей
            count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table[0]}"))
            count = count_result.scalar()
            print(f"    Записей: {count}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Управление базой данных СТО")
    parser.add_argument('--reset', action='store_true', help='Полный сброс БД')
    parser.add_argument('--check', action='store_true', help='Проверка состояния БД')
    parser.add_argument('--init', action='store_true', help='Инициализация БД (если не существует)')
    
    args = parser.parse_args()
    
    if args.reset:
        reset_database()
    elif args.check:
        check_database()
    else:
        print("Инициализация базы данных...")
        init_database()
        print("✓ База данных готова к работе")
        check_database()