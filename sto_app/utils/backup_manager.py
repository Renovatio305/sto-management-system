# sto_app/utils/backup.py
import os
import shutil
import zipfile
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import List, Dict, Optional

from PySide6.QtCore import QObject, Signal, QThread, QTimer
from PySide6.QtWidgets import QMessageBox, QProgressDialog, QApplication


logger = logging.getLogger(__name__)


class BackupWorker(QThread):
    """Рабочий поток для создания резервной копии"""
    
    progress_updated = Signal(int)
    status_updated = Signal(str)
    backup_completed = Signal(bool, str)  # success, message
    
    def __init__(self, backup_path: str, database_path: str, include_files: bool = True):
        super().__init__()
        self.backup_path = backup_path
        self.database_path = database_path
        self.include_files = include_files
        
    def run(self):
        """Выполнение резервного копирования"""
        try:
            self.status_updated.emit('Подготовка к созданию резервной копии...')
            self.progress_updated.emit(0)
            
            # Создаем временную директорию
            temp_dir = Path(self.backup_path).parent / 'temp_backup'
            temp_dir.mkdir(exist_ok=True)
            
            try:
                # Копируем базу данных
                self.status_updated.emit('Копирование базы данных...')
                self.progress_updated.emit(20)
                
                db_backup_path = temp_dir / 'database.db'
                shutil.copy2(self.database_path, db_backup_path)
                
                # Создаем метаданные
                self.status_updated.emit('Создание метаданных...')
                self.progress_updated.emit(40)
                
                metadata = {
                    'created_at': datetime.now().isoformat(),
                    'database_size': os.path.getsize(self.database_path),
                    'app_version': '3.0',
                    'backup_type': 'full' if self.include_files else 'database_only',
                    'files_included': self.include_files
                }
                
                with open(temp_dir / 'metadata.json', 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                
                # Копируем файлы ресурсов (если нужно)
                if self.include_files:
                    self.status_updated.emit('Копирование файлов ресурсов...')
                    self.progress_updated.emit(60)
                    
                    resources_dir = Path('resources')
                    if resources_dir.exists():
                        shutil.copytree(resources_dir, temp_dir / 'resources')
                
                # Создаем архив
                self.status_updated.emit('Создание архива...')
                self.progress_updated.emit(80)
                
                with zipfile.ZipFile(self.backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in temp_dir.rglob('*'):
                        if file_path.is_file():
                            arcname = file_path.relative_to(temp_dir)
                            zipf.write(file_path, arcname)
                
                self.progress_updated.emit(100)
                self.status_updated.emit('Резервная копия создана успешно')
                self.backup_completed.emit(True, f'Резервная копия сохранена: {self.backup_path}')
                
            finally:
                # Очищаем временную директорию
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}")
            self.backup_completed.emit(False, f'Ошибка: {str(e)}')


class RestoreWorker(QThread):
    """Рабочий поток для восстановления из резервной копии"""
    
    progress_updated = Signal(int)
    status_updated = Signal(str)
    restore_completed = Signal(bool, str)  # success, message
    
    def __init__(self, backup_path: str, restore_to: str):
        super().__init__()
        self.backup_path = backup_path
        self.restore_to = restore_to
        
    def run(self):
        """Выполнение восстановления"""
        try:
            self.status_updated.emit('Проверка архива...')
            self.progress_updated.emit(0)
            
            # Проверяем архив
            if not zipfile.is_zipfile(self.backup_path):
                self.restore_completed.emit(False, 'Неверный формат архива')
                return
                
            # Создаем временную директорию
            temp_dir = Path(self.restore_to) / 'temp_restore'
            temp_dir.mkdir(exist_ok=True)
            
            try:
                # Извлекаем архив
                self.status_updated.emit('Извлечение архива...')
                self.progress_updated.emit(20)
                
                with zipfile.ZipFile(self.backup_path, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # Проверяем метаданные
                metadata_path = temp_dir / 'metadata.json'
                if metadata_path.exists():
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    self.status_updated.emit(f'Восстановление из резервной копии от {metadata.get("created_at", "неизвестно")}')
                
                # Восстанавливаем базу данных
                self.status_updated.emit('Восстановление базы данных...')
                self.progress_updated.emit(60)
                
                db_source = temp_dir / 'database.db'
                if db_source.exists():
                    db_target = Path(self.restore_to) / 'sto_management.db'
                    
                    # Создаем резервную копию текущей БД
                    if db_target.exists():
                        backup_current = db_target.with_suffix('.db.backup')
                        shutil.copy2(db_target, backup_current)
                    
                    shutil.copy2(db_source, db_target)
                else:
                    self.restore_completed.emit(False, 'База данных не найдена в архиве')
                    return
                
                # Восстанавливаем файлы ресурсов
                resources_source = temp_dir / 'resources'
                if resources_source.exists():
                    self.status_updated.emit('Восстановление файлов ресурсов...')
                    self.progress_updated.emit(80)
                    
                    resources_target = Path(self.restore_to) / 'resources'
                    if resources_target.exists():
                        shutil.rmtree(resources_target)
                    shutil.copytree(resources_source, resources_target)
                
                self.progress_updated.emit(100)
                self.status_updated.emit('Восстановление завершено')
                self.restore_completed.emit(True, 'Данные восстановлены успешно')
                
            finally:
                # Очищаем временную директорию
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    
        except Exception as e:
            logger.error(f"Ошибка восстановления: {e}")
            self.restore_completed.emit(False, f'Ошибка: {str(e)}')


class BackupManager(QObject):
    """Менеджер резервного копирования"""
    
    backup_created = Signal(str)
    backup_failed = Signal(str)
    auto_backup_status = Signal(str)
    
    def __init__(self, database_path: str, backup_dir: str = None):
        super().__init__()
        self.database_path = database_path
        self.backup_dir = backup_dir or str(Path.home() / 'STO_Backups')
        
        # Создаем директорию для резервных копий
        Path(self.backup_dir).mkdir(exist_ok=True)
        
        # Настройки автобэкапа
        self.auto_backup_enabled = True
        self.auto_backup_interval = 24  # часов
        self.max_backups = 30  # максимальное количество резервных копий
        
        # Таймер для автоматического резервного копирования
        self.auto_backup_timer = QTimer()
        self.auto_backup_timer.timeout.connect(self.create_auto_backup)
        
        # Загружаем настройки
        self.load_settings()
        
        # Запускаем автобэкап если включен
        if self.auto_backup_enabled:
            self.start_auto_backup()
    
    def load_settings(self):
        """Загрузка настроек из файла"""
        settings_path = Path(self.backup_dir) / 'backup_settings.json'
        
        if settings_path.exists():
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                self.auto_backup_enabled = settings.get('auto_backup_enabled', True)
                self.auto_backup_interval = settings.get('auto_backup_interval', 24)
                self.max_backups = settings.get('max_backups', 30)
                
            except Exception as e:
                logger.error(f"Ошибка загрузки настроек резервного копирования: {e}")
    
    def save_settings(self):
        """Сохранение настроек в файл"""
        settings_path = Path(self.backup_dir) / 'backup_settings.json'
        
        settings = {
            'auto_backup_enabled': self.auto_backup_enabled,
            'auto_backup_interval': self.auto_backup_interval,
            'max_backups': self.max_backups,
            'last_backup': self.get_last_backup_time()
        }
        
        try:
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Ошибка сохранения настроек резервного копирования: {e}")
    
    def create_backup(self, include_files: bool = True, custom_path: str = None) -> bool:
        """Создание резервной копии"""
        try:
            # Генерируем имя файла
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_type = 'full' if include_files else 'db'
            filename = f'sto_backup_{backup_type}_{timestamp}.zip'
            
            backup_path = custom_path or str(Path(self.backup_dir) / filename)
            
            # Создаем диалог прогресса
            progress = QProgressDialog("Создание резервной копии...", "Отмена", 0, 100)
            progress.setWindowTitle("Резервное копирование")
            progress.setModal(True)
            progress.show()
            
            # Создаем рабочий поток
            self.backup_worker = BackupWorker(backup_path, self.database_path, include_files)
            
            # Подключаем сигналы
            self.backup_worker.progress_updated.connect(progress.setValue)
            self.backup_worker.status_updated.connect(progress.setLabelText)
            self.backup_worker.backup_completed.connect(self.on_backup_completed)
            self.backup_worker.backup_completed.connect(progress.close)
            
            # Обработка отмены
            progress.canceled.connect(self.backup_worker.terminate)
            
            # Запускаем создание резервной копии
            self.backup_worker.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка запуска резервного копирования: {e}")
            self.backup_failed.emit(f"Ошибка: {str(e)}")
            return False
    
    def restore_backup(self, backup_path: str, restore_to: str = None) -> bool:
        """Восстановление из резервной копии"""
        try:
            restore_path = restore_to or str(Path(self.database_path).parent)
            
            # Создаем диалог прогресса
            progress = QProgressDialog("Восстановление из резервной копии...", "Отмена", 0, 100)
            progress.setWindowTitle("Восстановление")
            progress.setModal(True)
            progress.show()
            
            # Создаем рабочий поток
            self.restore_worker = RestoreWorker(backup_path, restore_path)
            
            # Подключаем сигналы
            self.restore_worker.progress_updated.connect(progress.setValue)
            self.restore_worker.status_updated.connect(progress.setLabelText)
            self.restore_worker.restore_completed.connect(self.on_restore_completed)
            self.restore_worker.restore_completed.connect(progress.close)
            
            # Обработка отмены
            progress.canceled.connect(self.restore_worker.terminate)
            
            # Запускаем восстановление
            self.restore_worker.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка запуска восстановления: {e}")
            return False
    
    def on_backup_completed(self, success: bool, message: str):
        """Обработка завершения резервного копирования"""
        if success:
            self.backup_created.emit(message)
            self.cleanup_old_backups()
            self.save_settings()
        else:
            self.backup_failed.emit(message)
    
    def on_restore_completed(self, success: bool, message: str):
        """Обработка завершения восстановления"""
        if success:
            QMessageBox.information(
                None,
                "Восстановление завершено",
                f"{message}\n\nПерезапустите приложение для применения изменений."
            )
        else:
            QMessageBox.critical(None, "Ошибка восстановления", message)
    
    def start_auto_backup(self):
        """Запуск автоматического резервного копирования"""
        if self.auto_backup_enabled:
            interval_ms = self.auto_backup_interval * 60 * 60 * 1000  # часы в миллисекунды
            self.auto_backup_timer.start(interval_ms)
            self.auto_backup_status.emit(f"Автобэкап включен (каждые {self.auto_backup_interval} ч.)")
        else:
            self.auto_backup_timer.stop()
            self.auto_backup_status.emit("Автобэкап отключен")
    
    def stop_auto_backup(self):
        """Остановка автоматического резервного копирования"""
        self.auto_backup_timer.stop()
        self.auto_backup_status.emit("Автобэкап остановлен")
    
    def create_auto_backup(self):
        """Создание автоматической резервной копии"""
        try:
            # Проверяем, нужна ли резервная копия
            if not self.need_backup():
                return
            
            # Создаем резервную копию без диалога прогресса
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'sto_auto_backup_{timestamp}.zip'
            backup_path = str(Path(self.backup_dir) / filename)
            
            self.backup_worker = BackupWorker(backup_path, self.database_path, False)
            self.backup_worker.backup_completed.connect(self.on_auto_backup_completed)
            self.backup_worker.start()
            
        except Exception as e:
            logger.error(f"Ошибка автоматического резервного копирования: {e}")
    
    def on_auto_backup_completed(self, success: bool, message: str):
        """Обработка завершения автоматического резервного копирования"""
        if success:
            self.auto_backup_status.emit("Автобэкап выполнен успешно")
            self.cleanup_old_backups()
        else:
            self.auto_backup_status.emit(f"Ошибка автобэкапа: {message}")
    
    def need_backup(self) -> bool:
        """Проверка необходимости создания резервной копии"""
        last_backup = self.get_last_backup_time()
        
        if not last_backup:
            return True
        
        time_since_backup = datetime.now() - last_backup
        return time_since_backup.total_seconds() >= (self.auto_backup_interval * 3600)
    
    def get_last_backup_time(self) -> Optional[datetime]:
        """Получение времени последней резервной копии"""
        backup_files = list(Path(self.backup_dir).glob('sto_*_backup_*.zip'))
        
        if not backup_files:
            return None
        
        # Сортируем по времени модификации
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Возвращаем время последней резервной копии
        return datetime.fromtimestamp(backup_files[0].stat().st_mtime)
    
    def get_backup_list(self) -> List[Dict]:
        """Получение списка резервных копий"""
        backup_files = list(Path(self.backup_dir).glob('sto_*_backup_*.zip'))
        backups = []
        
        for backup_file in backup_files:
            try:
                stat = backup_file.stat()
                size_mb = stat.st_size / (1024 * 1024)
                
                # Пытаемся получить метаданные
                metadata = {}
                try:
                    with zipfile.ZipFile(backup_file, 'r') as zipf:
                        if 'metadata.json' in zipf.namelist():
                            with zipf.open('metadata.json') as f:
                                metadata = json.load(f)
                except:
                    pass
                
                backups.append({
                    'path': str(backup_file),
                    'name': backup_file.name,
                    'size_mb': round(size_mb, 2),
                    'created_at': datetime.fromtimestamp(stat.st_mtime),
                    'type': metadata.get('backup_type', 'unknown'),
                    'app_version': metadata.get('app_version', 'unknown')
                })
                
            except Exception as e:
                logger.error(f"Ошибка обработки файла резервной копии {backup_file}: {e}")
        
        # Сортируем по дате создания (новые первыми)
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        return backups
    
    def cleanup_old_backups(self):
        """Очистка старых резервных копий"""
        try:
            backups = self.get_backup_list()
            
            if len(backups) <= self.max_backups:
                return
            
            # Удаляем старые резервные копии
            backups_to_delete = backups[self.max_backups:]
            
            for backup in backups_to_delete:
                try:
                    Path(backup['path']).unlink()
                    logger.info(f"Удалена старая резервная копия: {backup['name']}")
                except Exception as e:
                    logger.error(f"Ошибка удаления резервной копии {backup['name']}: {e}")
                    
        except Exception as e:
            logger.error(f"Ошибка очистки старых резервных копий: {e}")
    
    def delete_backup(self, backup_path: str) -> bool:
        """Удаление резервной копии"""
        try:
            Path(backup_path).unlink()
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления резервной копии {backup_path}: {e}")
            return False
    
    def verify_backup(self, backup_path: str) -> Dict:
        """Проверка целостности резервной копии"""
        result = {
            'valid': False,
            'error': None,
            'metadata': None,
            'files': []
        }
        
        try:
            if not zipfile.is_zipfile(backup_path):
                result['error'] = 'Неверный формат архива'
                return result
            
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Проверяем целостность архива
                try:
                    zipf.testzip()
                except Exception as e:
                    result['error'] = f'Архив поврежден: {str(e)}'
                    return result
                
                # Получаем список файлов
                result['files'] = zipf.namelist()
                
                # Проверяем наличие обязательных файлов
                if 'database.db' not in result['files']:
                    result['error'] = 'База данных не найдена в архиве'
                    return result
                
                # Читаем метаданные
                if 'metadata.json' in result['files']:
                    with zipf.open('metadata.json') as f:
                        result['metadata'] = json.load(f)
            
            result['valid'] = True
            
        except Exception as e:
            result['error'] = f'Ошибка проверки: {str(e)}'
        
        return result
    
    def get_database_info(self) -> Dict:
        """Получение информации о базе данных"""
        info = {
            'size_mb': 0,
            'tables_count': 0,
            'records_count': 0,
            'last_modified': None
        }
        
        try:
            if not os.path.exists(self.database_path):
                return info
            
            # Размер файла
            size_bytes = os.path.getsize(self.database_path)
            info['size_mb'] = round(size_bytes / (1024 * 1024), 2)
            
            # Время изменения
            info['last_modified'] = datetime.fromtimestamp(
                os.path.getmtime(self.database_path)
            )
            
            # Информация о таблицах (если возможно)
            try:
                conn = sqlite3.connect(self.database_path)
                cursor = conn.cursor()
                
                # Количество таблиц
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                info['tables_count'] = cursor.fetchone()[0]
                
                # Примерное количество записей (из основных таблиц)
                tables = ['orders', 'clients', 'cars', 'employees']
                total_records = 0
                
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        total_records += cursor.fetchone()[0]
                    except:
                        pass
                
                info['records_count'] = total_records
                
                conn.close()
                
            except Exception as e:
                logger.error(f"Ошибка получения информации о БД: {e}")
                
        except Exception as e:
            logger.error(f"Ошибка получения информации о файле БД: {e}")
        
        return info
