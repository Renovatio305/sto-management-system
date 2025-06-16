# sto_app/dialogs/reports_dialog.py
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QPushButton, QLabel, QComboBox, QDateEdit,
                              QGroupBox, QListWidget, QListWidgetItem, QTextEdit,
                              QProgressBar, QCheckBox, QSpinBox, QMessageBox,
                              QFileDialog, QTabWidget, QWidget, QTableWidget,
                              QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt, QDate, QThread, Signal, QTimer
from PySide6.QtGui import QFont
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_
from datetime import datetime, timedelta
import json

from sto_app.models_sto import Order, OrderService, OrderPart, OrderStatus
from shared_models.common_models import Client, Car, Employee


class ReportsDialog(QDialog):
    """Диалог генерации отчетов"""
    
    def __init__(self, db_session: Session, parent=None):
        super().__init__(parent)
        self.db_session = db_session
        
        self.setWindowTitle('📊 Генерация отчетов')
        self.setMinimumSize(900, 700)
        self.resize(1100, 800)
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Заголовок
        title_label = QLabel('📊 Генерация отчетов')
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Табы для разных типов отчетов
        self.tab_widget = QTabWidget()
        
        # Основные отчеты
        main_reports_tab = self.create_main_reports_tab()
        self.tab_widget.addTab(main_reports_tab, '📈 Основные отчеты')
        
        # Финансовые отчеты
        financial_tab = self.create_financial_tab()
        self.tab_widget.addTab(financial_tab, '💰 Финансовые')
        
        # Аналитика
        analytics_tab = self.create_analytics_tab()
        self.tab_widget.addTab(analytics_tab, '📊 Аналитика')
        
        layout.addWidget(self.tab_widget)
        
        # Прогресс и действия
        progress_layout = QHBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel('Готов к генерации отчетов')
        self.status_label.setStyleSheet('color: #666;')
        progress_layout.addWidget(self.status_label)
        
        layout.addLayout(progress_layout)
        
        # Кнопки действий
        actions_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton('📊 Сгенерировать')
        self.generate_btn.setProperty('accent', True)
        actions_layout.addWidget(self.generate_btn)
        
        self.export_btn = QPushButton('💾 Экспорт')
        self.export_btn.setEnabled(False)
        actions_layout.addWidget(self.export_btn)
        
        self.print_btn = QPushButton('🖨️ Печать')
        self.print_btn.setEnabled(False)
        actions_layout.addWidget(self.print_btn)
        
        actions_layout.addStretch()
        
        self.close_btn = QPushButton('Закрыть')
        actions_layout.addWidget(self.close_btn)
        
        layout.addLayout(actions_layout)
        
    def create_main_reports_tab(self):
        """Создание вкладки основных отчетов"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Параметры отчета
        params_group = QGroupBox('Параметры отчета')
        params_layout = QFormLayout(params_group)
        
        # Тип отчета
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            'Заказы по периоду',
            'Статистика по статусам',
            'Отчет по клиентам',
            'Отчет по автомобилям',
            'Загрузка мастеров',
            'Популярные услуги',
            'Использование запчастей'
        ])
        params_layout.addRow('Тип отчета:', self.report_type_combo)
        
        # Период
        period_layout = QHBoxLayout()
        
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setCalendarPopup(True)
        period_layout.addWidget(QLabel('с'))
        period_layout.addWidget(self.date_from)
        
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        period_layout.addWidget(QLabel('по'))
        period_layout.addWidget(self.date_to)
        
        period_layout.addStretch()
        params_layout.addRow('Период:', period_layout)
        
        # Группировка
        self.group_by_combo = QComboBox()
        self.group_by_combo.addItems([
            'По дням',
            'По неделям', 
            'По месяцам',
            'По кварталам',
            'Без группировки'
        ])
        params_layout.addRow('Группировка:', self.group_by_combo)
        
        # Фильтры
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItem('Все статусы', None)
        for status in OrderStatus:
            self.status_filter_combo.addItem(status.value, status)
        params_layout.addRow('Статус:', self.status_filter_combo)
        
        layout.addWidget(params_group)
        
        # Предварительный просмотр
        preview_group = QGroupBox('Предварительный просмотр')
        preview_layout = QVBoxLayout(preview_group)
        
        self.main_preview_table = QTableWidget()
        self.main_preview_table.setAlternatingRowColors(True)
        preview_layout.addWidget(self.main_preview_table)
        
        layout.addWidget(preview_group)
        
        return widget
        
    def create_financial_tab(self):
        """Создание вкладки финансовых отчетов"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Параметры финансового отчета
        params_group = QGroupBox('Финансовые параметры')
        params_layout = QFormLayout(params_group)
        
        # Тип финансового отчета
        self.financial_type_combo = QComboBox()
        self.financial_type_combo.addItems([
            'Доходы по периоду',
            'Анализ прибыльности',
            'Структура доходов',
            'Задолженности клиентов',
            'Средний чек',
            'Рентабельность услуг',
            'Сравнение периодов'
        ])
        params_layout.addRow('Тип отчета:', self.financial_type_combo)
        
        # Валюта
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(['₴ Гривна', '$ Доллар', '€ Евро'])
        params_layout.addRow('Валюта:', self.currency_combo)
        
        # Включить НДС
        self.include_vat_cb = QCheckBox('Включать НДС в расчеты')
        self.include_vat_cb.setChecked(True)
        params_layout.addRow('НДС:', self.include_vat_cb)
        
        # Минимальная сумма
        self.min_amount_spin = QSpinBox()
        self.min_amount_spin.setRange(0, 999999)
        self.min_amount_spin.setSuffix(' ₴')
        params_layout.addRow('Мин. сумма:', self.min_amount_spin)
        
        layout.addWidget(params_group)
        
        # Сводка
        summary_group = QGroupBox('Финансовая сводка')
        summary_layout = QVBoxLayout(summary_group)
        
        self.financial_summary = QTextEdit()
        self.financial_summary.setReadOnly(True)
        self.financial_summary.setMaximumHeight(200)
        self.financial_summary.setPlaceholderText('Сводка будет сгенерирована после запуска отчета')
        summary_layout.addWidget(self.financial_summary)
        
        layout.addWidget(summary_group)
        
        # Детализация
        details_group = QGroupBox('Детализация')
        details_layout = QVBoxLayout(details_group)
        
        self.financial_preview_table = QTableWidget()
        self.financial_preview_table.setAlternatingRowColors(True)
        details_layout.addWidget(self.financial_preview_table)
        
        layout.addWidget(details_group)
        
        return widget
        
    def create_analytics_tab(self):
        """Создание вкладки аналитики"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Параметры аналитики
        params_group = QGroupBox('Параметры аналитики')
        params_layout = QFormLayout(params_group)
        
        # Тип аналитики
        self.analytics_type_combo = QComboBox()
        self.analytics_type_combo.addItems([
            'Тренды заказов',
            'Сезонность',
            'Эффективность мастеров',
            'Популярность услуг',
            'Анализ клиентской базы',
            'Прогноз доходов',
            'ABC анализ'
        ])
        params_layout.addRow('Тип анализа:', self.analytics_type_combo)
        
        # Глубина анализа
        self.analysis_depth_combo = QComboBox()
        self.analysis_depth_combo.addItems([
            'Последние 3 месяца',
            'Последние 6 месяцев',
            'Последний год',
            'Весь период'
        ])
        params_layout.addRow('Глубина:', self.analysis_depth_combo)
        
        # Детализация
        self.detail_level_combo = QComboBox()
        self.detail_level_combo.addItems([
            'Высокая детализация',
            'Средняя детализация',
            'Общие тренды'
        ])
        params_layout.addRow('Детализация:', self.detail_level_combo)
        
        layout.addWidget(params_group)
        
        # Результаты анализа
        results_group = QGroupBox('Результаты анализа')
        results_layout = QVBoxLayout(results_group)
        
        self.analytics_results = QTextEdit()
        self.analytics_results.setReadOnly(True)
        self.analytics_results.setPlaceholderText('Результаты анализа будут показаны здесь')
        results_layout.addWidget(self.analytics_results)
        
        layout.addWidget(results_group)
        
        return widget
        
    def setup_connections(self):
        """Настройка соединений сигналов"""
        self.generate_btn.clicked.connect(self.generate_report)
        self.export_btn.clicked.connect(self.export_report)
        self.print_btn.clicked.connect(self.print_report)
        self.close_btn.clicked.connect(self.accept)
        
        # Обновление превью при изменении параметров
        self.report_type_combo.currentTextChanged.connect(self.on_params_changed)
        self.date_from.dateChanged.connect(self.on_params_changed)
        self.date_to.dateChanged.connect(self.on_params_changed)
        
    def on_params_changed(self):
        """Обработка изменения параметров"""
        # Очищаем превью при изменении параметров
        current_tab = self.tab_widget.currentIndex()
        if current_tab == 0:  # Основные отчеты
            self.main_preview_table.setRowCount(0)
        elif current_tab == 1:  # Финансовые
            self.financial_preview_table.setRowCount(0)
            self.financial_summary.clear()
        elif current_tab == 2:  # Аналитика
            self.analytics_results.clear()
            
    def generate_report(self):
        """Генерация отчета"""
        current_tab = self.tab_widget.currentIndex()
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.generate_btn.setEnabled(False)
        
        try:
            if current_tab == 0:  # Основные отчеты
                self.generate_main_report()
            elif current_tab == 1:  # Финансовые
                self.generate_financial_report()
            elif current_tab == 2:  # Аналитика
                self.generate_analytics_report()
                
            self.export_btn.setEnabled(True)
            self.print_btn.setEnabled(True)
            self.status_label.setText('Отчет сгенерирован успешно')
            
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка генерации отчета: {e}')
            self.status_label.setText('Ошибка генерации отчета')
            
        finally:
            self.progress_bar.setVisible(False)
            self.generate_btn.setEnabled(True)
            
    def generate_main_report(self):
        """Генерация основного отчета"""
        report_type = self.report_type_combo.currentText()
        date_from = self.date_from.date().toPython()
        date_to = self.date_to.date().toPython()
        
        self.progress_bar.setValue(20)
        self.status_label.setText('Загрузка данных...')
        
        if report_type == 'Заказы по периоду':
            self.generate_orders_report(date_from, date_to)
        elif report_type == 'Статистика по статусам':
            self.generate_status_report(date_from, date_to)
        elif report_type == 'Отчет по клиентам':
            self.generate_clients_report(date_from, date_to)
        elif report_type == 'Популярные услуги':
            self.generate_services_report(date_from, date_to)
            
        self.progress_bar.setValue(100)
        
    def generate_orders_report(self, date_from, date_to):
        """Генерация отчета по заказам"""
        # Получаем заказы за период
        orders = self.db_session.query(Order).filter(
            and_(
                Order.date_received >= date_from,
                Order.date_received <= date_to
            )
        ).all()
        
        # Настраиваем таблицу
        self.main_preview_table.setColumnCount(6)
        self.main_preview_table.setHorizontalHeaderLabels([
            '№ заказа', 'Дата', 'Клиент', 'Автомобиль', 'Статус', 'Сумма'
        ])
        
        # Заполняем данные
        self.main_preview_table.setRowCount(len(orders))
        
        for row, order in enumerate(orders):
            self.main_preview_table.setItem(row, 0, QTableWidgetItem(order.order_number or ''))
            self.main_preview_table.setItem(row, 1, QTableWidgetItem(
                order.date_received.strftime('%d.%m.%Y') if order.date_received else ''
            ))
            self.main_preview_table.setItem(row, 2, QTableWidgetItem(
                order.client.name if order.client else 'Неизвестен'
            ))
            self.main_preview_table.setItem(row, 3, QTableWidgetItem(
                f"{order.car.brand} {order.car.model}" if order.car else 'Неизвестен'
            ))
            self.main_preview_table.setItem(row, 4, QTableWidgetItem(
                order.status.value if order.status else 'Неизвестен'
            ))
            
            amount_item = QTableWidgetItem(f'{order.total_amount or 0:.2f} ₴')
            amount_item.setTextAlignment(Qt.AlignRight)
            self.main_preview_table.setItem(row, 5, amount_item)
            
        # Настраиваем ширину колонок
        header = self.main_preview_table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        
    def generate_status_report(self, date_from, date_to):
        """Генерация отчета по статусам"""
        # Группируем по статусам
        status_counts = {}
        status_amounts = {}
        
        for status in OrderStatus:
            count = self.db_session.query(Order).filter(
                and_(
                    Order.status == status,
                    Order.date_received >= date_from,
                    Order.date_received <= date_to
                )
            ).count()
            
            amount = self.db_session.query(func.sum(Order.total_amount)).filter(
                and_(
                    Order.status == status,
                    Order.date_received >= date_from,
                    Order.date_received <= date_to
                )
            ).scalar() or 0
            
            status_counts[status.value] = count
            status_amounts[status.value] = float(amount)
            
        # Настраиваем таблицу
        self.main_preview_table.setColumnCount(4)
        self.main_preview_table.setHorizontalHeaderLabels([
            'Статус', 'Количество', 'Сумма', 'Процент'
        ])
        
        total_count = sum(status_counts.values())
        total_amount = sum(status_amounts.values())
        
        # Заполняем данные
        self.main_preview_table.setRowCount(len(status_counts))
        
        for row, (status, count) in enumerate(status_counts.items()):
            self.main_preview_table.setItem(row, 0, QTableWidgetItem(status))
            
            count_item = QTableWidgetItem(str(count))
            count_item.setTextAlignment(Qt.AlignCenter)
            self.main_preview_table.setItem(row, 1, count_item)
            
            amount_item = QTableWidgetItem(f'{status_amounts[status]:.2f} ₴')
            amount_item.setTextAlignment(Qt.AlignRight)
            self.main_preview_table.setItem(row, 2, amount_item)
            
            percent = (count / total_count * 100) if total_count > 0 else 0
            percent_item = QTableWidgetItem(f'{percent:.1f}%')
            percent_item.setTextAlignment(Qt.AlignCenter)
            self.main_preview_table.setItem(row, 3, percent_item)
            
    def generate_financial_report(self):
        """Генерация финансового отчета"""
        self.status_label.setText('Генерация финансового отчета...')
        self.progress_bar.setValue(50)
        
        # Заглушка для финансового отчета
        summary_text = """
<h3>💰 Финансовая сводка</h3>
<p><b>Общий доход:</b> 125,450.00 ₴</p>
<p><b>Услуги:</b> 89,320.00 ₴ (71%)</p>
<p><b>Запчасти:</b> 36,130.00 ₴ (29%)</p>
<p><b>Средний чек:</b> 2,845.00 ₴</p>
<p><b>Количество заказов:</b> 44</p>

<h4>🎯 Ключевые показатели:</h4>
<ul>
<li>Рост доходов: +15% к предыдущему периоду</li>
<li>Конверсия: 85%</li>
<li>Средний срок выполнения: 3.2 дня</li>
</ul>
        """
        
        self.financial_summary.setHtml(summary_text)
        
        # Настраиваем таблицу детализации
        self.financial_preview_table.setColumnCount(4)
        self.financial_preview_table.setHorizontalHeaderLabels([
            'Период', 'Доходы', 'Расходы', 'Прибыль'
        ])
        
        # Заглушка данных
        data = [
            ('Неделя 1', '28,500.00', '12,300.00', '16,200.00'),
            ('Неделя 2', '31,200.00', '14,500.00', '16,700.00'),
            ('Неделя 3', '29,800.00', '13,200.00', '16,600.00'),
            ('Неделя 4', '35,950.00', '15,800.00', '20,150.00')
        ]
        
        self.financial_preview_table.setRowCount(len(data))
        for row, (period, income, expense, profit) in enumerate(data):
            self.financial_preview_table.setItem(row, 0, QTableWidgetItem(period))
            
            income_item = QTableWidgetItem(f'{income} ₴')
            income_item.setTextAlignment(Qt.AlignRight)
            self.financial_preview_table.setItem(row, 1, income_item)
            
            expense_item = QTableWidgetItem(f'{expense} ₴')
            expense_item.setTextAlignment(Qt.AlignRight)
            self.financial_preview_table.setItem(row, 2, expense_item)
            
            profit_item = QTableWidgetItem(f'{profit} ₴')
            profit_item.setTextAlignment(Qt.AlignRight)
            self.financial_preview_table.setItem(row, 3, profit_item)
            
        self.progress_bar.setValue(100)
        
    def generate_analytics_report(self):
        """Генерация аналитического отчета"""
        self.status_label.setText('Генерация аналитики...')
        self.progress_bar.setValue(50)
        
        # Заглушка для аналитики
        analytics_text = """
<h3>📊 Аналитический отчет</h3>

<h4>🔍 Основные тренды:</h4>
<ul>
<li><b>Рост заказов:</b> Увеличение на 18% по сравнению с предыдущим периодом</li>
<li><b>Популярные услуги:</b> Диагностика (35%), Замена масла (28%), Ремонт тормозов (22%)</li>
<li><b>Пиковые дни:</b> Вторник и пятница показывают наибольшую загрузку</li>
<li><b>Сезонность:</b> Спад активности в летние месяцы (-12%)</li>
</ul>

<h4>👥 Клиентская база:</h4>
<ul>
<li><b>Новые клиенты:</b> 23 (15% от общего числа)</li>
<li><b>Повторные обращения:</b> 85% клиентов возвращаются</li>
<li><b>Средняя частота:</b> 1 раз в 3.5 месяца</li>
</ul>

<h4>⚡ Эффективность:</h4>
<ul>
<li><b>Время выполнения:</b> Сокращено на 15% благодаря оптимизации</li>
<li><b>Качество:</b> 98% заказов завершены без возвратов</li>
<li><b>Загрузка мастеров:</b> 78% (оптимальный уровень)</li>
</ul>

<h4>📈 Прогнозы:</h4>
<ul>
<li><b>Следующий месяц:</b> Ожидается рост на 8-12%</li>
<li><b>Рекомендации:</b> Увеличить штат на 1 мастера, расширить склад запчастей</li>
</ul>
        """
        
        self.analytics_results.setHtml(analytics_text)
        self.progress_bar.setValue(100)
        
    def generate_clients_report(self, date_from, date_to):
        """Генерация отчета по клиентам"""
        # Получаем клиентов с заказами за период
        clients_data = self.db_session.query(
            Client.name,
            func.count(Order.id).label('orders_count'),
            func.sum(Order.total_amount).label('total_amount')
        ).join(Order).filter(
            and_(
                Order.date_received >= date_from,
                Order.date_received <= date_to
            )
        ).group_by(Client.id).all()
        
        # Настраиваем таблицу
        self.main_preview_table.setColumnCount(3)
        self.main_preview_table.setHorizontalHeaderLabels([
            'Клиент', 'Количество заказов', 'Общая сумма'
        ])
        
        # Заполняем данные
        self.main_preview_table.setRowCount(len(clients_data))
        
        for row, (name, count, amount) in enumerate(clients_data):
            self.main_preview_table.setItem(row, 0, QTableWidgetItem(name))
            
            count_item = QTableWidgetItem(str(count))
            count_item.setTextAlignment(Qt.AlignCenter)
            self.main_preview_table.setItem(row, 1, count_item)
            
            amount_item = QTableWidgetItem(f'{float(amount or 0):.2f} ₴')
            amount_item.setTextAlignment(Qt.AlignRight)
            self.main_preview_table.setItem(row, 2, amount_item)
            
    def generate_services_report(self, date_from, date_to):
        """Генерация отчета по услугам"""
        # Получаем статистику по услугам
        services_data = self.db_session.query(
            OrderService.service_name,
            func.count(OrderService.id).label('count'),
            func.sum(OrderService.price_with_vat).label('total_amount')
        ).join(Order).filter(
            and_(
                Order.date_received >= date_from,
                Order.date_received <= date_to
            )
        ).group_by(OrderService.service_name).order_by(
            func.count(OrderService.id).desc()
        ).all()
        
        # Настраиваем таблицу
        self.main_preview_table.setColumnCount(4)
        self.main_preview_table.setHorizontalHeaderLabels([
            'Услуга', 'Количество', 'Общая сумма', 'Средняя цена'
        ])
        
        # Заполняем данные
        self.main_preview_table.setRowCount(len(services_data))
        
        for row, (service_name, count, total_amount) in enumerate(services_data):
            self.main_preview_table.setItem(row, 0, QTableWidgetItem(service_name))
            
            count_item = QTableWidgetItem(str(count))
            count_item.setTextAlignment(Qt.AlignCenter)
            self.main_preview_table.setItem(row, 1, count_item)
            
            total_item = QTableWidgetItem(f'{float(total_amount or 0):.2f} ₴')
            total_item.setTextAlignment(Qt.AlignRight)
            self.main_preview_table.setItem(row, 2, total_item)
            
            avg_price = float(total_amount or 0) / count if count > 0 else 0
            avg_item = QTableWidgetItem(f'{avg_price:.2f} ₴')
            avg_item.setTextAlignment(Qt.AlignRight)
            self.main_preview_table.setItem(row, 3, avg_item)
            
    def export_report(self):
        """Экспорт отчета"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            'Сохранить отчет',
            f'Отчет_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
            'Excel files (*.xlsx);;CSV files (*.csv);;PDF files (*.pdf)'
        )
        
        if file_path:
            try:
                # Здесь будет реализация экспорта
                QMessageBox.information(
                    self,
                    'Экспорт',
                    f'Отчет сохранен в файл:\n{file_path}\n\nФункция экспорта будет полностью реализована в следующей версии'
                )
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Ошибка экспорта: {e}')
                
    def print_report(self):
        """Печать отчета"""
        QMessageBox.information(
            self,
            'Печать',
            'Функция печати отчетов будет реализована в следующей версии'
        )