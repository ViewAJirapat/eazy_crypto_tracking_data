import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar  # Calendar widget from tkcalendar
import pandas as pd
import os
import requests

# File path for saving data
file_path = "crypto_tracking_data.xlsx"

# Function to load data when the program starts
def load_data():
    if os.path.exists(file_path):
        return pd.read_excel(file_path)
    else:
        columns = [
            "วันที่", "เหรียญ", "ราคาซื้อ (USDT)", "จำนวนที่ซื้อ",
            "ค่าธรรมเนียมซื้อ (เหรียญ)", "จำนวนสุทธิซื้อ (เหรียญ)",
            "ต้นทุนรวม (USDT)", "มูลค่าปัจจุบัน (USDT)", "มูลค่ารวมปัจจุบัน (USDT)", 
            "การเปลี่ยนแปลง (%)", "ราคาขาย (USDT)", "จำนวนที่ขาย", 
            "ค่าธรรมเนียมขาย (USDT)", "มูลค่าหลังขาย (USDT)", "กำไร/ขาดทุน (USDT)",
            "ต้นทุนรวม (THB)", "มูลค่าปัจจุบัน (THB)", "ความแตกต่าง (THB)", "สถานะการเปลี่ยนแปลง"
        ]
        return pd.DataFrame(columns=columns)

# Function to save data
def save_data():
    global df
    df.to_excel(file_path, index=False)
    messagebox.showinfo("สำเร็จ", "ข้อมูลถูกบันทึกเรียบร้อยแล้ว!")

# Function to add a new entry
def add_entry():
    global df
    try:
        selected_coin = coin_listbox.get(coin_listbox.curselection())  # Get selected coin
        selected_date = calendar.get_date()  # Get selected date from calendar
        buy_price = float(entry_buy_price.get())
        quantity = float(entry_quantity.get())
        fee_buy = float(entry_fee_buy.get())
        
        # Calculations
        net_quantity = quantity - fee_buy
        total_cost_usdt = buy_price * quantity
        total_cost_thb = total_cost_usdt * exchange_rate  # Convert to THB
        
        # Add new entry to DataFrame
        new_entry = pd.DataFrame([{
            "วันที่": selected_date,
            "เหรียญ": selected_coin,
            "ราคาซื้อ (USDT)": buy_price,
            "จำนวนที่ซื้อ": quantity,
            "ค่าธรรมเนียมซื้อ (เหรียญ)": fee_buy,
            "จำนวนสุทธิซื้อ (เหรียญ)": net_quantity,
            "ต้นทุนรวม (USDT)": total_cost_usdt,
            "มูลค่าปัจจุบัน (USDT)": 0,  # Placeholder for current value
            "มูลค่ารวมปัจจุบัน (USDT)": 0,  # Placeholder for total current value
            "การเปลี่ยนแปลง (%)": 0,  # Placeholder for % change
            "ราคาขาย (USDT)": 0,
            "จำนวนที่ขาย": 0,
            "ค่าธรรมเนียมขาย (USDT)": 0,
            "มูลค่าหลังขาย (USDT)": 0,
            "กำไร/ขาดทุน (USDT)": 0,
            "ต้นทุนรวม (THB)": total_cost_thb,
            "มูลค่าปัจจุบัน (THB)": 0,  # Placeholder for current value in THB
            "ความแตกต่าง (THB)": 0,  # Placeholder for difference
            "สถานะการเปลี่ยนแปลง": "ไม่เปลี่ยนแปลง"  # Placeholder
        }])
        
        # Use pd.concat() instead of append()
        df = pd.concat([df, new_entry], ignore_index=True)
        
        save_data()
        update_table()
        clear_entries()
    except Exception as e:
        messagebox.showerror("ข้อผิดพลาด", f"กรุณากรอกข้อมูลให้ถูกต้อง: {e}")

# Function to update current prices using Binance API
def update_prices():
    global df
    try:
        for index, row in df.iterrows():
            coin = row["เหรียญ"]
            if coin:
                # Fetch data from Binance API
                response = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={coin.upper()}USDT")
                if response.status_code == 200:
                    current_price_usdt = float(response.json()["price"])
                    df.loc[index, "มูลค่าปัจจุบัน (USDT)"] = current_price_usdt
                    df.loc[index, "มูลค่ารวมปัจจุบัน (USDT)"] = current_price_usdt * row["จำนวนสุทธิซื้อ (เหรียญ)"]
                    
                    # Convert to THB
                    current_value_thb = current_price_usdt * row["จำนวนสุทธิซื้อ (เหรียญ)"] * exchange_rate
                    df.loc[index, "มูลค่าปัจจุบัน (THB)"] = current_value_thb
                    
                    # Calculate difference in THB
                    difference_thb = current_value_thb - row["ต้นทุนรวม (THB)"]
                    df.loc[index, "ความแตกต่าง (THB)"] = difference_thb
                    
                    # Update change status
                    if difference_thb > 0:
                        df.loc[index, "สถานะการเปลี่ยนแปลง"] = "เพิ่มขึ้น"
                    elif difference_thb < 0:
                        df.loc[index, "สถานะการเปลี่ยนแปลง"] = "ลดลง"
                    else:
                        df.loc[index, "สถานะการเปลี่ยนแปลง"] = "ไม่เปลี่ยนแปลง"
        
        save_data()
        update_table()
    except Exception as e:
        messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถดึงราคาปัจจุบันได้: {e}")

# Function to update table
def update_table():
    for row in table.get_children():
        table.delete(row)
    for index, row in df.iterrows():
        table.insert("", "end", values=list(row))

# Function to clear input fields
def clear_entries():
    calendar.selection_set("")  # Clear calendar selection
    coin_listbox.selection_clear(0, tk.END)  # Clear Listbox selection
    entry_buy_price.delete(0, tk.END)
    entry_quantity.delete(0, tk.END)
    entry_fee_buy.delete(0, tk.END)

# Function to get exchange rate from API
def get_exchange_rate():
    global exchange_rate
    try:
        response = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=USDTTHB")
        data = response.json()
        exchange_rate = float(data['price'])
        exchange_rate_label.config(text=f"เรตอัตราแลกเปลี่ยน (USDT -> THB): {exchange_rate}")
    except Exception as e:
        messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถดึงอัตราแลกเปลี่ยนได้: {e}")

# Load initial data
df = load_data()

# Create GUI
root = tk.Tk()
root.title("Crypto Tracker")
root.geometry("1400x600")

# Input frame
frame_form = tk.Frame(root)
frame_form.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

# Calendar widget
tk.Label(frame_form, text="วันที่").grid(row=0, column=0, padx=5, pady=5)
calendar = Calendar(frame_form, date_pattern="dd/mm/yyyy")
calendar.grid(row=0, column=1, padx=5, pady=5)

# Listbox for coins
tk.Label(frame_form, text="เหรียญ").grid(row=0, column=2, padx=5, pady=5)
coin_listbox = tk.Listbox(frame_form, height=5, exportselection=False)
coin_listbox.grid(row=0, column=3, padx=5, pady=5)
coins = ["BTC", "ETH", "XRP", "DOT", "ADA", "FTM", "TROY", "MAGIC"]  # Add more coins as needed
for coin in coins:
    coin_listbox.insert(tk.END, coin)

# Input fields
tk.Label(frame_form, text="ราคาซื้อ (USDT)").grid(row=1, column=0, padx=5, pady=5)
entry_buy_price = ttk.Entry(frame_form)
entry_buy_price.grid(row=1, column=1, padx=5, pady=5)

tk.Label(frame_form, text="จำนวนที่ซื้อ").grid(row=1, column=2, padx=5, pady=5)
entry_quantity = ttk.Entry(frame_form)
entry_quantity.grid(row=1, column=3, padx=5, pady=5)

tk.Label(frame_form, text="ค่าธรรมเนียมซื้อ (เหรียญ)").grid(row=2, column=0, padx=5, pady=5)
entry_fee_buy = ttk.Entry(frame_form)
entry_fee_buy.grid(row=2, column=1, padx=5, pady=5)

btn_add = ttk.Button(frame_form, text="เพิ่มข้อมูล", command=add_entry)
btn_add.grid(row=2, column=3, padx=5, pady=5)

btn_update_prices = ttk.Button(frame_form, text="อัปเดตราคาปัจจุบัน", command=update_prices)
btn_update_prices.grid(row=2, column=4, padx=5, pady=5)

# Exchange rate label
exchange_rate_label = tk.Label(frame_form, text="เรตอัตราแลกเปลี่ยน (USDT -> THB): Loading...")
exchange_rate_label.grid(row=3, column=0, columnspan=5, padx=5, pady=5)

# Fetch exchange rate on startup
get_exchange_rate()

# Table frame
frame_table = tk.Frame(root)
frame_table.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

columns = df.columns.tolist()
table = ttk.Treeview(frame_table, columns=columns, show="headings")
for col in columns:
    table.heading(col, text=col)
    table.column(col, width=100)
table.pack(fill=tk.BOTH, expand=True)

update_table()

# Run the program
root.mainloop()
