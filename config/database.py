# config/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import os
from typing import Generator

# Конфигурация БД
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///sto_database.db')

# Создание движка БД с пулом соединений
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_size=5,         # Размер пула соединений
    max_overflow=10,     # Максимальное количество дополнительных соединений
    echo=False           # Логирование SQL запросов (True для отладки)
)

# Фабрика сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Получить сессию БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """Инициализация базы данных"""
    from shared_models.base import Base
    from shared_models.common_models import Client, Car, Employee
    from sto_app.models_sto import Order, OrderService, OrderPart, ServiceCatalog, CarBrand
    
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    
    # Заполняем начальными данными
    db = SessionLocal()
    try:
        # Проверяем, есть ли уже данные
        if db.query(CarBrand).count() == 0:
            # Добавляем марки автомобилей
            car_brands_data = [
                ('Toyota', 'Camry,Corolla,RAV4,Land Cruiser,Highlander,Prius,Yaris,Avalon'),
                ('Honda', 'Civic,Accord,CR-V,Pilot,Fit,HR-V,Odyssey,Ridgeline'),
                ('Volkswagen', 'Golf,Passat,Tiguan,Touareg,Polo,Jetta,Arteon,Atlas'),
                ('BMW', '3 Series,5 Series,X3,X5,X1,7 Series,X7,M3,M5'),
                ('Mercedes-Benz', 'C-Class,E-Class,GLC,GLE,A-Class,S-Class,GLA,GLB'),
                ('Audi', 'A4,A6,Q5,Q7,A3,Q3,A8,Q8,e-tron'),
                ('Mazda', 'CX-5,Mazda3,CX-9,Mazda6,MX-5,CX-30,CX-50'),
                ('Nissan', 'Rogue,Altima,Sentra,Murano,Pathfinder,Maxima,Frontier,Titan'),
                ('Hyundai', 'Elantra,Sonata,Tucson,Santa Fe,Kona,Palisade,Venue,Ioniq'),
                ('Kia', 'Optima,Sportage,Sorento,Forte,Soul,Telluride,Carnival,Stinger'),
                ('Ford', 'F-150,Escape,Explorer,Mustang,Edge,Fusion,Bronco,Ranger'),
                ('Chevrolet', 'Silverado,Equinox,Tahoe,Malibu,Traverse,Camaro,Blazer,Colorado'),
                ('Skoda', 'Octavia,Superb,Kodiaq,Karoq,Fabia,Scala,Kamiq,Enyaq'),
                ('Renault', 'Duster,Logan,Sandero,Captur,Megane,Kadjar,Arkana,Koleos'),
                ('Peugeot', '208,308,3008,5008,508,2008,408,Rifter'),
                ('Mitsubishi', 'Outlander,ASX,Pajero,Eclipse Cross,Lancer,Mirage,L200'),
                ('Subaru', 'Outback,Forester,Impreza,XV,Legacy,WRX,Ascent,BRZ'),
                ('Lexus', 'RX,NX,ES,GX,IS,LX,UX,LS'),
                ('Infiniti', 'QX50,QX60,Q50,QX80,QX30,Q60,QX55'),
                ('Volvo', 'XC60,XC90,S60,V60,XC40,S90,V90,C40')
            ]
            
            for brand, models in car_brands_data:
                car_brand = CarBrand(brand=brand, models=models)
                db.add(car_brand)
            
            db.commit()
        
        if db.query(ServiceCatalog).count() == 0:
            # Добавляем базовые услуги
            services = [
                ('Замена масла двигателя', 'Заміна масла двигуна', 500, 'Двигатель', 'масло,oil,мотор'),
                ('Замена масляного фильтра', 'Заміна масляного фільтра', 200, 'Двигатель', 'фильтр,filter'),
                ('Диагностика двигателя', 'Діагностика двигуна', 400, 'Диагностика', 'проверка,тест,scan'),
                ('Замена тормозных колодок', 'Заміна гальмівних колодок', 600, 'Тормозная система', 'колодки,тормоза,brake'),
                ('Замена тормозных дисков', 'Заміна гальмівних дисків', 800, 'Тормозная система', 'диски,тормоза,brake'),
                ('Диагностика подвески', 'Діагностика підвіски', 300, 'Подвеска', 'ходовая,suspension'),
                ('Замена амортизаторов', 'Заміна амортизаторів', 1200, 'Подвеска', 'стойки,shock'),
                ('Развал-схождение', 'Розвал-сходження', 400, 'Шиномонтаж', 'углы,alignment'),
                ('Балансировка колес', 'Балансування коліс', 300, 'Шиномонтаж', 'колеса,шины,balance'),
                ('Шиномонтаж', 'Шиномонтаж', 250, 'Шиномонтаж', 'резина,покрышки,tire'),
                ('Замена воздушного фильтра', 'Заміна повітряного фільтра', 150, 'Двигатель', 'воздух,air'),
                ('Замена свечей зажигания', 'Заміна свічок запалювання', 300, 'Двигатель', 'свечи,spark'),
                ('Диагностика электрики', 'Діагностика електрики', 350, 'Электрика', 'электро,провода,electric'),
                ('Замена аккумулятора', 'Заміна акумулятора', 200, 'Электрика', 'батарея,АКБ,battery'),
                ('Кузовной ремонт', 'Кузовний ремонт', 1500, 'Кузовной ремонт', 'кузов,вмятина,покраска'),
            ]
            
            for name, name_ua, price, category, synonyms in services:
                service = ServiceCatalog(
                    name=name,
                    name_ua=name_ua,
                    default_price=price,  # Используем правильное поле
                    description=None,
                    category=category,
                    synonyms=synonyms,
                    vat_rate=20.0,
                    duration_hours=1.0,
                    is_active=1
                )
                db.add(service)
            
    except Exception as e:
        db.rollback()
        print(f"Ошибка при инициализации БД: {e}")
    finally:
        db.close()