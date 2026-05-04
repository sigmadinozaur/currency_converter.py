import requests
import json
import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

class CurrencyConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Currency Converter")
        self.root.geometry("750x600")
        self.root.resizable(True, True)
        
        # API настройки
        self.api_key = "YOUR_API_KEY_HERE"  # Замените на ваш API ключ
        self.api_url = f"https://v6.exchangerate-api.com/v6/{self.api_key}/latest/"
        
        # Файл истории
        self.history_file = "conversion_history.json"
        self.history = self.load_history()
        
        # Доступные валюты
        self.currencies = []
        self.exchange_rates = {}
        
        # Переменные
        self.from_currency = tk.StringVar(value="USD")
        self.to_currency = tk.StringVar(value="EUR")
        self.amount = tk.StringVar(value="1.00")
        self.result = tk.StringVar(value="")
        
        self.setup_ui()
        self.load_currencies()
        self.update_history_display()
    
    def setup_ui(self):
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Конвертер валют", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=10)
        
        # Фрейм конвертации
        convert_frame = ttk.LabelFrame(main_frame, text="Конвертация", padding="10")
        convert_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        # Поле ввода суммы
        ttk.Label(convert_frame, text="Сумма:").grid(row=0, column=0, sticky=tk.W, padx=5)
        amount_entry = ttk.Entry(convert_frame, textvariable=self.amount, width=15)
        amount_entry.grid(row=0, column=1, padx=5)
        
        # Выбор валюты "из"
        ttk.Label(convert_frame, text="Из валюты:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.from_combo = ttk.Combobox(convert_frame, textvariable=self.from_currency, width=10)
        self.from_combo.grid(row=1, column=1, padx=5, pady=5)
        
        # Кнопка перестановки валют
        swap_btn = ttk.Button(convert_frame, text="⇄", command=self.swap_currencies, width=3)
        swap_btn.grid(row=1, column=2, padx=5)
        
        # Выбор валюты "в"
        ttk.Label(convert_frame, text="В валюту:").grid(row=1, column=3, sticky=tk.W, padx=5)
        self.to_combo = ttk.Combobox(convert_frame, textvariable=self.to_currency, width=10)
        self.to_combo.grid(row=1, column=4, padx=5)
        
        # Кнопка конвертации
        convert_btn = ttk.Button(convert_frame, text="Конвертировать", command=self.convert_currency)
        convert_btn.grid(row=2, column=0, columnspan=5, pady=10)
        
        # Результат
        result_frame = ttk.LabelFrame(main_frame, text="Результат", padding="10")
        result_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        self.result_label = ttk.Label(result_frame, text="", font=("Arial", 14, "bold"))
        self.result_label.grid(row=0, column=0, pady=5)
        
        # Курс обмена
        self.rate_label = ttk.Label(result_frame, text="", font=("Arial", 10))
        self.rate_label.grid(row=1, column=0, pady=5)
        
        # История конвертаций
        history_frame = ttk.LabelFrame(main_frame, text="История конвертаций", padding="10")
        history_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Таблица истории
        columns = ("Дата", "Сумма", "Из", "В", "Результат", "Курс")
        self.tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=8)
        
        column_widths = {"Дата": 120, "Сумма": 80, "Из": 60, "В": 60, "Результат": 100, "Курс": 100}
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths.get(col, 100))
        
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Кнопки управления историей
        btn_frame = ttk.Frame(history_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=5)
        
        ttk.Button(btn_frame, text="Очистить историю", command=self.clear_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Экспорт в JSON", command=self.export_history).pack(side=tk.LEFT, padx=5)
        
        # Настройка весов
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
    
    def load_currencies(self):
        """Загрузка списка доступных валют из API"""
        try:
            # Попытка загрузить из кэша
            if os.path.exists("currencies_cache.json"):
                with open("currencies_cache.json", 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    if datetime.now().timestamp() - cache['timestamp'] < 86400:  # 24 часа
                        self.currencies = cache['currencies']
                        self.from_combo['values'] = self.currencies
                        self.to_combo['values'] = self.currencies
                        return
            
            # Загрузка из API
            response = requests.get(f"{self.api_url}USD", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['result'] == 'success':
                    self.currencies = list(data['conversion_rates'].keys())
                    self.currencies.sort()
                    self.from_combo['values'] = self.currencies
                    self.to_combo['values'] = self.currencies
                    
                    # Сохранение в кэш
                    cache_data = {
                        'timestamp': datetime.now().timestamp(),
                        'currencies': self.currencies
                    }
                    with open("currencies_cache.json", 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, ensure_ascii=False, indent=2)
                else:
                    self.show_api_error()
            else:
                self.show_api_error()
        except requests.exceptions.RequestException:
            self.show_api_error()
    
    def show_api_error(self):
        """Показать ошибку API и использовать резервные валюты"""
        self.currencies = ["USD", "EUR", "GBP", "JPY", "CNY", "RUB", "CAD", "AUD", "CHF", "INR"]
        self.from_combo['values'] = self.currencies
        self.to_combo['values'] = self.currencies
        messagebox.showwarning("Предупреждение", 
                              "Не удалось подключиться к API. Используются стандартные валюты.\n"
                              "Проверьте API ключ или интернет-соединение.")
    
    def get_exchange_rate(self, from_curr, to_curr):
        """Получение курса обмена из API"""
        try:
            response = requests.get(f"{self.api_url}{from_curr}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['result'] == 'success':
                    return data['conversion_rates'].get(to_curr)
                else:
                    messagebox.showerror("Ошибка", "Ошибка API: " + data.get('error-type', 'Unknown error'))
                    return None
            else:
                messagebox.showerror("Ошибка", f"Ошибка HTTP: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Ошибка", f"Ошибка сети: {str(e)}")
            return None
    
    def convert_currency(self):
        """Выполнение конвертации валют"""
        try:
            # Проверка суммы
            amount_value = float(self.amount.get())
            if amount_value <= 0:
                messagebox.showerror("Ошибка", "Сумма должна быть положительным числом")
                return
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректную сумму (число)")
            return
        
        from_curr = self.from_currency.get()
        to_curr = self.to_currency.get()
        
        if from_curr == to_curr:
            result_value = float(self.amount.get())
            rate = 1.0
        else:
            # Получение курса
            rate = self.get_exchange_rate(from_curr, to_curr)
            if rate is None:
                return
            result_value = float(self.amount.get()) * rate
        
        # Форматирование результата
        result_text = f"{self.amount.get()} {from_curr} = {result_value:.4f} {to_curr}"
        self.result_label.config(text=result_text)
        self.rate_label.config(text=f"Курс: 1 {from_curr} = {rate:.4f} {to_curr}")
        
        # Сохранение в историю
        history_entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "amount": float(self.amount.get()),
            "from_currency": from_curr,
            "to_currency": to_curr,
            "result": result_value,
            "rate": rate
        }
        
        self.history.append(history_entry)
        self.save_history()
        self.update_history_display()
    
    def swap_currencies(self):
        """Перестановка валют местами"""
        from_val = self.from_currency.get()
        to_val = self.to_currency.get()
        self.from_currency.set(to_val)
        self.to_currency.set(from_val)
    
    def load_history(self):
        """Загрузка истории из JSON файла"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []
    
    def save_history(self):
        """Сохранение истории в JSON файл"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except IOError as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить историю: {e}")
    
    def update_history_display(self):
        """Обновление отображения истории"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for entry in reversed(self.history):
            self.tree.insert("", tk.END, values=(
                entry["date"],
                f"{entry['amount']:.4f}",
                entry["from_currency"],
                entry["to_currency"],
                f"{entry['result']:.4f}",
                f"{entry['rate']:.4f}"
            ))
    
    def clear_history(self):
        """Очистка истории"""
        if messagebox.askyesno("Подтверждение", "Очистить всю историю конвертаций?"):
            self.history = []
            self.save_history()
            self.update_history_display()
            messagebox.showinfo("Успех", "История очищена")
    
    def export_history(self):
        """Экспорт истории в отдельный JSON файл"""
        if not self.history:
            messagebox.showwarning("Предупреждение", "Нет истории для экспорта")
            return
        
        filename = f"history_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Успех", f"История экспортирована в {filename}")
        except IOError as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать: {e}")

def main():
    root = tk.Tk()
    app = CurrencyConverter(root)
    root.mainloop()

if __name__ == "__main__":
    main()
