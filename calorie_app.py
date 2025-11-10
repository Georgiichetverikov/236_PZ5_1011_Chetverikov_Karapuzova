import sys
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QTextEdit, QProgressBar, QTabWidget, QMessageBox, QHeaderView,
    QGroupBox, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor


class APIManager:
    """Класс для работы с API Open Food Facts"""

    BASE_URL = "https://world.openfoodfacts.org"

    def __init__(self):
        self.headers = {
            "User-Agent": "CalorieApp/1.0 (PyQt6)"
        }

    def search_by_barcode(self, barcode):
        """Поиск продукта по штрихкоду"""
        try:
            url = f"{self.BASE_URL}/api/v2/product/{barcode}"
            params = {
                "fields": "code,product_name,brands,nutriments,quantity,serving_size",
                "lc": "ru"
            }
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Ошибка при поиске по штрихкоду: {str(e)}")

    def search_by_name(self, query):
        """Поиск продуктов по названию"""
        try:
            url = f"{self.BASE_URL}/api/v2/search"
            params = {
                "search_terms": query,
                "fields": "code,product_name,brands,nutriments,quantity,serving_size",
                "page_size": 10,
                "lc": "ru"
            }
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Ошибка при поиске по названию: {str(e)}")


class SearchWorker(QThread):
    """Поток для выполнения поиска в фоне"""

    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, search_type, query):
        super().__init__()
        self.search_type = search_type
        self.query = query
        self.api = APIManager()

    def run(self):
        try:
            if self.search_type == "barcode":
                result = self.api.search_by_barcode(self.query)
            else:
                result = self.api.search_by_name(self.query)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Главное окно приложения"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Поиск калорийности продуктов - Open Food Facts")
        self.setGeometry(100, 100, 1000, 700)
        self.current_products = []

        self.setup_ui()

    def setup_ui(self):
        """Настройка интерфейса"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Заголовок
        title = QLabel("🔍 Поиск калорийности продуктов")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin: 10px;")
        layout.addWidget(title)

        # Создаем вкладки
        self.tabs = QTabWidget()
        self.setup_barcode_tab()
        self.setup_search_tab()
        layout.addWidget(self.tabs)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Таблица результатов
        self.setup_results_table()
        layout.addWidget(self.results_table)

        # Детальная информация
        self.setup_details_area()
        layout.addWidget(self.details_text)

    def setup_barcode_tab(self):
        """Вкладка поиска по штрихкоду"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        group = QGroupBox("Поиск по штрихкоду")
        group_layout = QHBoxLayout(group)

        group_layout.addWidget(QLabel("Штрихкод:"))
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Например: 5449000000996")
        self.barcode_input.returnPressed.connect(self.search_barcode)
        group_layout.addWidget(self.barcode_input)

        self.barcode_btn = QPushButton("Найти")
        self.barcode_btn.clicked.connect(self.search_barcode)
        self.barcode_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        group_layout.addWidget(self.barcode_btn)

        layout.addWidget(group)

        # Примеры
        examples_label = QLabel(
            "Примеры штрихкодов: 5449000000996 (Coca-Cola), 3017620422003 (Nutella), 7613032629999 (Nesquik)")
        examples_label.setStyleSheet("color: #666; font-size: 11px; margin-top: 5px;")
        layout.addWidget(examples_label)

        self.tabs.addTab(tab, "📦 По штрихкоду")

    def setup_search_tab(self):
        """Вкладка поиска по названию"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        group = QGroupBox("Поиск по названию")
        group_layout = QHBoxLayout(group)

        group_layout.addWidget(QLabel("Название:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Например: творог 5%")
        self.search_input.returnPressed.connect(self.search_name)
        group_layout.addWidget(self.search_input)

        self.search_btn = QPushButton("Найти")
        self.search_btn.clicked.connect(self.search_name)
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        group_layout.addWidget(self.search_btn)

        layout.addWidget(group)

        # Примеры
        examples_label = QLabel("Примеры запросов: творог, яблоко, шоколад, хлеб, молоко")
        examples_label.setStyleSheet("color: #666; font-size: 11px; margin-top: 5px;")
        layout.addWidget(examples_label)

        self.tabs.addTab(tab, "🔍 По названию")

    def setup_results_table(self):
        """Настройка таблицы результатов"""
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "Штрихкод", "Название", "Бренд", "Ккал/100г",
            "Белки/100г", "Жиры/100г", "Углеводы/100г"
        ])

        # Настройка растяжения колонок
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Название
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Бренд

        # Настройка остальных колонок
        for i in [0, 3, 4, 5, 6]:
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        # Подключаем выбор строки
        self.results_table.itemSelectionChanged.connect(self.on_product_selected)

    def setup_details_area(self):
        """Настройка области детальной информации"""
        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(200)
        self.details_text.setPlaceholderText("Детальная информация о продукте появится здесь...")
        self.details_text.setReadOnly(True)

    def search_barcode(self):
        """Поиск по штрихкоду"""
        barcode = self.barcode_input.text().strip()
        if not barcode:
            QMessageBox.warning(self, "Ошибка", "Введите штрихкод")
            return

        self.start_search("barcode", barcode)

    def search_name(self):
        """Поиск по названию"""
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Ошибка", "Введите название продукта")
            return

        self.start_search("name", query)

    def start_search(self, search_type, query):
        """Запуск поиска"""
        # Показываем прогресс
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Бесконечный прогресс

        # Блокируем кнопки
        self.barcode_btn.setEnabled(False)
        self.search_btn.setEnabled(False)

        # Очищаем предыдущие результаты
        self.results_table.setRowCount(0)
        self.details_text.clear()

        # Запускаем поток
        self.worker = SearchWorker(search_type, query)
        self.worker.finished.connect(self.on_search_finished)
        self.worker.error.connect(self.on_search_error)
        self.worker.start()

    def on_search_finished(self, result):
        """Обработка успешного поиска"""
        self.progress_bar.setVisible(False)
        self.barcode_btn.setEnabled(True)
        self.search_btn.setEnabled(True)

        if "product" in result:  # Результат по штрихкоду
            self.display_barcode_result(result)
        elif "products" in result:  # Результат по названию
            self.display_search_results(result)
        else:
            QMessageBox.information(self, "Результат", "Ничего не найдено")

    def on_search_error(self, error_msg):
        """Обработка ошибки поиска"""
        self.progress_bar.setVisible(False)
        self.barcode_btn.setEnabled(True)
        self.search_btn.setEnabled(True)

        QMessageBox.critical(self, "Ошибка", f"Ошибка при поиске:\n{error_msg}")

    def display_barcode_result(self, result):
        """Отображение результата по штрихкоду"""
        product_data = result.get("product")
        if product_data:
            products = [product_data]
            self.display_products(products)
            self.show_product_details(product_data)
            self.statusBar().showMessage("Продукт найден", 3000)
        else:
            self.clear_results()
            QMessageBox.information(self, "Результат", "Продукт не найден")

    def display_search_results(self, result):
        """Отображение результатов поиска по названию"""
        products = result.get("products", [])
        if products:
            self.display_products(products)
            if products:
                self.show_product_details(products[0])
            self.statusBar().showMessage(f"Найдено продуктов: {len(products)}", 3000)
        else:
            self.clear_results()
            QMessageBox.information(self, "Результат", "Продукты не найдены")

    def display_products(self, products):
        """Отображение продуктов в таблице"""
        self.current_products = products
        self.results_table.setRowCount(len(products))

        for row, product in enumerate(products):
            nutriments = product.get("nutriments", {})

            # Штрихкод
            self.results_table.setItem(row, 0, self.create_table_item(product.get("code", "N/A")))

            # Название
            name = product.get("product_name", "Неизвестно") or "Неизвестно"
            self.results_table.setItem(row, 1, self.create_table_item(name))

            # Бренд
            brand = product.get("brands", "Неизвестно") or "Неизвестно"
            self.results_table.setItem(row, 2, self.create_table_item(brand))

            # Нутриенты
            self.results_table.setItem(row, 3, self.create_nutrition_item(nutriments.get("energy-kcal_100g")))
            self.results_table.setItem(row, 4, self.create_nutrition_item(nutriments.get("proteins_100g")))
            self.results_table.setItem(row, 5, self.create_nutrition_item(nutriments.get("fat_100g")))
            self.results_table.setItem(row, 6, self.create_nutrition_item(nutriments.get("carbohydrates_100g")))

    def create_table_item(self, text):
        """Создание элемента таблицы"""
        item = QTableWidgetItem(str(text) if text is not None else "N/A")
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    def create_nutrition_item(self, value):
        """Создание элемента таблицы для нутриентов"""
        text = str(value) if value is not None else "N/A"
        item = self.create_table_item(text)
        if value is not None:
            item.setBackground(QColor(240, 248, 255))  # Светло-голубой фон
        return item

    def clear_results(self):
        """Очистка результатов"""
        self.current_products = []
        self.results_table.setRowCount(0)
        self.details_text.clear()

    def on_product_selected(self):
        """Обработка выбора продукта в таблице"""
        selected_items = self.results_table.selectedItems()
        if selected_items and self.current_products:
            row = selected_items[0].row()
            if row < len(self.current_products):
                product = self.current_products[row]
                self.show_product_details(product)

    def show_product_details(self, product):
        """Показать детальную информацию о продукте"""
        nutriments = product.get("nutriments", {})

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 10px; }}
                .header {{ color: #2c3e50; font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
                .info {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 10px; }}
                .section {{ color: #27ae60; font-weight: bold; margin-top: 15px; margin-bottom: 5px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                td {{ padding: 4px 8px; }}
                .label {{ font-weight: bold; color: #555; }}
            </style>
        </head>
        <body>
            <div class="header">{product.get('product_name', 'Неизвестно')}</div>

            <div class="info">
                <p><span class="label">📦 Бренд:</span> {product.get('brands', 'Неизвестно')}</p>
                <p><span class="label">🏷️ Штрихкод:</span> {product.get('code', 'N/A')}</p>
                <p><span class="label">⚖️ Количество:</span> {product.get('quantity', 'N/A')}</p>
                <p><span class="label">🍽️ Размер порции:</span> {product.get('serving_size', 'N/A')}</p>
            </div>

            <div class="section">🍎 Пищевая ценность на 100г:</div>
            <table border="0">
                <tr>
                    <td class="label">Калории:</td>
                    <td>{nutriments.get('energy-kcal_100g', 'N/A')} ккал</td>
                </tr>
                <tr>
                    <td class="label">Белки:</td>
                    <td>{nutriments.get('proteins_100g', 'N/A')} г</td>
                </tr>
                <tr>
                    <td class="label">Жиры:</td>
                    <td>{nutriments.get('fat_100g', 'N/A')} г</td>
                </tr>
                <tr>
                    <td class="label">Углеводы:</td>
                    <td>{nutriments.get('carbohydrates_100g', 'N/A')} г</td>
                </tr>
            </table>
        """

        # Добавляем информацию о порции если есть
        if nutriments.get('energy-kcal_serving'):
            html += f"""
            <div class="section">🍽️ Пищевая ценность на порцию:</div>
            <table border="0">
                <tr>
                    <td class="label">Калории:</td>
                    <td>{nutriments.get('energy-kcal_serving', 'N/A')} ккал</td>
                </tr>
                <tr>
                    <td class="label">Белки:</td>
                    <td>{nutriments.get('proteins_serving', 'N/A')} г</td>
                </tr>
                <tr>
                    <td class="label">Жиры:</td>
                    <td>{nutriments.get('fat_serving', 'N/A')} г</td>
                </tr>
                <tr>
                    <td class="label">Углеводы:</td>
                    <td>{nutriments.get('carbohydrates_serving', 'N/A')} г</td>
                </tr>
            </table>
            """

        html += "</body></html>"

        self.details_text.setHtml(html)


def main():
    """Запуск приложения"""
    app = QApplication(sys.argv)

    # Устанавливаем стиль приложения
    app.setStyle('Fusion')

    # Создаем и показываем главное окно
    window = MainWindow()
    window.show()

    # Запускаем приложение
    sys.exit(app.exec())


if __name__ == "__main__":
    main()