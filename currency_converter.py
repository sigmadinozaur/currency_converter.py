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
        self.root.geometry("800x650")
        self.root.resizable(True, True)
        
        # БЕЗ API-КЛЮЧА - используем Frankfurter API (бесплатный, без регистрации)
        self.base_url = "https://api.frankfurter.app"
        
        # Файл истории
        self.history_file = "conversion_history.json"
        self.history = self.load_history()
        
        # Доступные валюты
        self.currencies = []
        
        # Переменные
        self.from_currency = tk.StringVar(value="USD")
        self.to_currency = tk.StringVar(value="EUR")
        self.amount = tk.StringVar(value="1.00")
        
        self.setup_ui()
        self.load_currencies()
        self.update_history_display()
    
    def setup_ui(self):
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="Currency Converter", font=("Arial", 18, "bold"))
        title_label.grid(row=0, column=0, columnspan=5, pady=10)
        
        # Разделитель
        ttk.Separator(main_frame, orient='horizontal').grid(row=1, column=0, columnspan=5, sticky='ew', pady=5)
        
        # Фрейм конвертации
        convert_frame = ttk.LabelFrame(main_frame, text="Конвертация валют", padding="15")
        convert_frame.grid(row=2, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=10)
        
        # Поле ввода суммы
        ttk.Label(convert_frame, text="Сумма:", font=("Arial", 11)).grid(row=0, column=0, sticky=tk.W, padx=5, pady=10)
        amount_entry = ttk.Entry(convert_frame, textvariable=self.amount, width=15, font=("Arial", 11))
        amount_entry.grid(row=0, column=1, padx=5, pady=10)
        
        # Выбор валюты "из"
        ttk.Label(convert_frame, text="Из валюты:", font=("Arial", 11)).grid(row=1, column=0, sticky=tk.W, padx=5, pady=10)
        self.from_combo = ttk.Combobox(convert_frame, textvariable=self.from_currency, width=12, font=("Arial", 11))
        self.from_combo.grid(row=1, column=1, padx=5, pady=10)
        
        # Кнопка перестановки валют
        swap_btn = ttk.Button(convert_frame, text="⇄", command=self.swap_currencies, width=5)
        swap_btn.grid(row=1, column=2, padx=10)
        
        # Выбор валюты "в"
        ttk.Label(convert_frame, text="В валюту:", font=("Arial", 11)).grid(row=1, column=3, sticky=tk.W, padx=5, pady=10)
        self.to_combo = ttk.Combobox(convert_frame, textvariable=self.to_currency, width=12, font=("Arial", 11))
        self.to_combo.grid(row=1, column=4, padx=5, pady=10)
        
        # Кнопка конвертации
        convert_btn = ttk.Button(convert_frame, text="Конвертировать", command=self.convert_currency, width=20)
        convert_btn.grid(row=2, column=0, columnspan=5, pady=15)
        
        # Фрейм результата
        result_frame = ttk.LabelFrame(main_frame, text="Результат", padding="15")
        result_frame.grid(row=3, column=0, columnspan=5, sticky=(tk.W, tk.E), pady=10)
        
        self.result_label = ttk.Label(result_frame, text="", font=("Arial", 14, "bold"), foreground="green")
        self.result_label.grid(row=0, column=0, pady=5)
        
        self.rate_label = ttk.Label(result_frame, text="", font=("Arial", 10), foreground="blue")
        self.rate_label.grid(row=1, column=0, pady=5)
        
        # Фрейм истории
        history_frame = ttk.LabelFrame(main_frame, text="История конвертаций", padding="10")
        history_frame.grid(row=4, column=0, columnspan=5, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Таблица истории
        columns = ("Дата и время", "Сумма", "Из", "В", "Результат", "Курс")
        self.tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=8)
        
        self.tree.heading("Дата и время", text="Дата и время")
        self.tree.heading("Сумма", text="Сумма")
        self.tree.heading("Из", text="Из")
        self.tree.heading("В", text="В")
        self.tree.heading("Результат", text="Результат")
        self.tree.heading("Курс", text="Курс")
        
        self.tree.column("Дата и время", width=140)
        self.tree.column("Сумма", width=80)
        self.tree.column("Из", width=60)
        self.tree.column("В", width=60)
        self.tree.column("Результат", width=120)
        self.tree.column("Курс", width=100)
        
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Кнопки управления
        btn_frame = ttk.Frame(history_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="🗑 Очистить историю", command=self.clear_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="💾 Экспорт в JSON", command=self.export_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 Обновить курсы", command=self.refresh_currencies).pack(side=tk.LEFT, padx=5)
        
        # Настройка весов
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
    
    def load_currencies(self):
        """Загрузка списка валют (без API-ключа)"""
        try:
            # Пробуем загрузить из кэша
            if os.path.exists("currencies_cache.json"):
                with open("currencies_cache.json", 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    if datetime.now().timestamp() - cache['timestamp'] < 86400:
                        self.currencies = cache['currencies']
                        self.from_combo['values'] = self.currencies
                        self.to_combo['values'] = self.currencies
                        return
            
            # Загружаем список валют из Frankfurter API (без ключа!)
            response = requests.get(f"{self.base_url}/currencies", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.currencies = list(data.keys())
                self.currencies.sort()
                self.from_combo['values'] = self.currencies
                self.to_combo['values'] = self.currencies
                
                # Сохраняем кэш
                cache_data = {
                    'timestamp': datetime.now().timestamp(),
                    'currencies': self.currencies
                }
                with open("currencies_cache.json", 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f)
                
                print(f"✅ Загружено {len(self.currencies)} валют без API-ключа")
            else:
                self.use_fallback_currencies()
                
        except Exception as e:
            print(f"Ошибка: {e}")
            self.use_fallback_currencies()
    
    def use_fallback_currencies(self):
        """Резервный список валют"""
        self.currencies = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "CNY", "INR", "RUB"]
        self.currencies.sort()
        self.from_combo['values'] = self.currencies
        self.to_combo['values'] = self.currencies
        messagebox.showwarning("Внимание", "Используются стандартные валюты. Проверьте интернет.")
    
    def get_exchange_rate(self, from_curr, to_curr):
        """Получение курса (без API-ключа)"""
        if from_curr == to_curr:
            return 1.0
        
        try:
            # Frankfurter API endpoint - бесплатно, без ключа!
            url = f"{self.base_url}/latest?from={from_curr}&to={to_curr}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                rate = data['rates'].get(to_curr)
                if rate:
                    return rate
                else:
                    messagebox.showerror("Ошибка", f"Валюта {to_curr} не найдена")
                    return None
            else:
                messagebox.showerror("Ошибка", f"HTTP ошибка: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Ошибка", f"Ошибка сети: {str(e)}")
            return None
    
    def convert_currency(self):
        """Конвертация валюты"""
        try:
            amount_value = float(self.amount.get().replace(',', '.'))
            if amount_value <= 0:
                messagebox.showerror("Ошибка", "Сумма должна быть положительным числом")
                return
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректную сумму (например: 100.50)")
            return
        
        from_curr = self.from_currency.get()
        to_curr = self.to_currency.get()
        
        self.result_label.config(text="Загрузка курса...")
        self.root.update()
        
        rate = self.get_exchange_rate(from_curr, to_curr)
        if rate is None:
            self.result_label.config(text="Ошибка получения курса")
            return
        
        result_value = amount_value * rate
        
        result_text = f"{amount_value:,.2f} {from_curr} = {result_value:,.2f} {to_curr}"
        self.result_label.config(text=result_text)
        self.rate_label.config(text=f"Курс: 1 {from_curr} = {rate:.4f} {to_curr}")
        
        # Сохраняем в историю
        history_entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amount_value,
            "from_currency": from_curr,
            "to_currency": to_curr,
            "result": result_value,
            "rate": rate
        }
        
        self.history.append(history_entry)
        
        if len(self.history) > 100:
            self.history = self.history[-100:]
        
        self.save_history()
        self.update_history_display()
    
    def swap_currencies(self):
        from_val = self.from_currency.get()
        to_val = self.to_currency.get()
        self.from_currency.set(to_val)
        self.to_currency.set(from_val)
    
    def refresh_currencies(self):
        self.load_currencies()
        messagebox.showinfo("Обновлено", "Список валют обновлен")
    
    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_history(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def update_history_display(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for entry in reversed(self.history[-50:]):
            self.tree.insert("", tk.END, values=(
                entry["date"],
                f"{entry['amount']:.2f}",
                entry["from_currency"],
                entry["to_currency"],
                f"{entry['result']:.2f}",
                f"{entry['rate']:.4f}"
            ))
    
    def clear_history(self):
        if messagebox.askyesno("Подтверждение", "Очистить историю?"):
            self.history = []
            self.save_history()
            self.update_history_display()
    
    def export_history(self):
        if not self.history:
            messagebox.showwarning("Предупреждение", "Нет истории для экспорта")
            return
        
        filename = f"history_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Успех", f"Экспортировано в {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка экспорта: {e}")

def main():
    root = tk.Tk()
    app = CurrencyConverter(root)
    root.mainloop()

if __name__ == "__main__":
    main()
