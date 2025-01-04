import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
import requests

# File path for saving data
file_path = "crypto_tracking_data.xlsx"

# Load data at startup
def load_data():
    if os.path.exists(file_path):
        return pd.read_excel(file_path)
    else:
        columns = [
            "วันที่", "เหรียญ", "ราคาซื้อ (USDT)", "จำนวนที่ซื้อ",
            "ค่าธรรมเนียมซื้อ (เหรียญ)", "จำนวนสุทธิซื้อ (เหรียญ)",
            "ต้นทุนรวม (USDT)", "มูลค่าปัจจุบัน (USDT)", "มูลค่ารวมปัจจุบัน (USDT)", 
            "การเปลี่ยนแปลง (%)", "ราคาขาย (USDT)", "จำนวนที่ขาย", 
            "ค่าธรรมเนียมขาย (USDT)", "มูลค่าหลังขาย (USDT)", "กำไร/ขาดทุน (USDT)"
        ]
        return pd.DataFrame(columns=columns)

# Save data to the file
def save_data():
    global df
    df.to_excel(file_path, index=False)

# Add a new entry (buy or sell)
def add_entry():
    global df
    try:
        selected_coin = coin_listbox.get(coin_listbox.curselection())
        if selected_coin:
            is_sell = sell_mode.get()
            quantity = float(entry_quantity.get())
            price = float(entry_buy_price.get())
            fee = float(entry_fee_buy.get())

            if is_sell:  # Sell transaction
                # Check if there are enough coins to sell
                coin_data = df[df["เหรียญ"] == selected_coin]
                total_coins = coin_data["จำนวนสุทธิซื้อ (เหรียญ)"].sum()

                if quantity > total_coins:
                    messagebox.showerror("Error", f"Not enough {selected_coin} to sell!")
                    return

                sell_value = (price * quantity) - fee
                cost_per_coin = coin_data["ต้นทุนรวม (USDT)"].sum() / total_coins if total_coins > 0 else 0
                sell_cost = cost_per_coin * quantity

                # Add sell entry
                new_entry = pd.DataFrame([{
                    "วันที่": entry_date.get(),
                    "เหรียญ": selected_coin,
                    "ราคาซื้อ (USDT)": 0,
                    "จำนวนที่ซื้อ": 0,
                    "ค่าธรรมเนียมซื้อ (เหรียญ)": 0,
                    "จำนวนสุทธิซื้อ (เหรียญ)": -quantity,
                    "ต้นทุนรวม (USDT)": -sell_cost,
                    "มูลค่าปัจจุบัน (USDT)": 0,
                    "มูลค่ารวมปัจจุบัน (USDT)": 0,
                    "การเปลี่ยนแปลง (%)": 0,
                    "ราคาขาย (USDT)": price,
                    "จำนวนที่ขาย": quantity,
                    "ค่าธรรมเนียมขาย (USDT)": fee,
                    "มูลค่าหลังขาย (USDT)": sell_value,
                    "กำไร/ขาดทุน (USDT)": -sell_cost - sell_value
                }])
            else:  # Buy transaction
                net_quantity = quantity - fee
                total_cost = price * quantity
                new_entry = pd.DataFrame([{
                    "วันที่": entry_date.get(),
                    "เหรียญ": selected_coin,
                    "ราคาซื้อ (USDT)": price,
                    "จำนวนที่ซื้อ": quantity,
                    "ค่าธรรมเนียมซื้อ (เหรียญ)": fee,
                    "จำนวนสุทธิซื้อ (เหรียญ)": net_quantity,
                    "ต้นทุนรวม (USDT)": total_cost,
                    "มูลค่าปัจจุบัน (USDT)": 0,
                    "มูลค่ารวมปัจจุบัน (USDT)": 0,
                    "การเปลี่ยนแปลง (%)": 0,
                    "ราคาขาย (USDT)": 0,
                    "จำนวนที่ขาย": 0,
                    "ค่าธรรมเนียมขาย (USDT)": 0,
                    "มูลค่าหลังขาย (USDT)": 0,
                    "กำไร/ขาดทุน (USDT)": total_cost  # Initial cost
                }])

            df = pd.concat([df, new_entry], ignore_index=True)
            save_data()
            update_table()
            calculate_summary()
            clear_entries()
    except Exception as e:
        messagebox.showerror("Error", f"Invalid input: {e}")

# Update current prices from Binance API
def update_prices():
    global df
    try:
        for index, row in df.iterrows():
            coin = row["เหรียญ"]
            if coin:
                response = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={coin.upper()}USDT")
                if response.status_code == 200:
                    current_price = float(response.json()["price"])
                    df.loc[index, "มูลค่าปัจจุบัน (USDT)"] = current_price

        save_data()
        calculate_summary()  # อัปเดตสรุปหลังจากดึงราคาปัจจุบัน
        update_table()
    except Exception as e:
        messagebox.showerror("Error", f"ไม่สามารถดึงราคาปัจจุบันได้: {e}")


# Calculate summary of all coins
def calculate_summary():
    summary = df.groupby("เหรียญ").agg({
        "จำนวนสุทธิซื้อ (เหรียญ)": "sum",  # คำนวณจำนวนสุทธิของเหรียญที่เหลือ
        "ต้นทุนรวม (USDT)": "sum",
        "มูลค่าปัจจุบัน (USDT)": "last"  # ใช้ราคาล่าสุดจาก Binance
    }).reset_index()

    for row in summary_table.get_children():
        summary_table.delete(row)

    for _, row in summary.iterrows():
        remaining_coins = row["จำนวนสุทธิซื้อ (เหรียญ)"]
        total_cost = row["ต้นทุนรวม (USDT)"]
        current_price = row["มูลค่าปัจจุบัน (USDT)"]

        # มูลค่ารวมปัจจุบัน
        current_value = remaining_coins * current_price if remaining_coins > 0 else 0

        # กำไร/ขาดทุน
        gain_loss = total_cost - current_value

        # เพิ่มข้อมูลในตารางสรุป
        summary_table.insert("", "end", values=(
            row["เหรียญ"], 
            remaining_coins, 
            total_cost, 
            current_value, 
            gain_loss
        ))


# Update the main data table
def update_table():
    for row in table.get_children():
        table.delete(row)
    for index, row in df.iterrows():
        table.insert("", "end", values=list(row))

# Clear entry fields
def clear_entries():
    entry_date.delete(0, tk.END)
    entry_buy_price.delete(0, tk.END)
    entry_quantity.delete(0, tk.END)
    entry_fee_buy.delete(0, tk.END)

# Initial data load
df = load_data()

# GUI setup
root = tk.Tk()
root.title("Crypto Tracker")
root.geometry("1400x800")

frame_form = tk.Frame(root)
frame_form.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

tk.Label(frame_form, text="วันที่").grid(row=0, column=0, padx=5, pady=5)
entry_date = ttk.Entry(frame_form)
entry_date.grid(row=0, column=1, padx=5, pady=5)

tk.Label(frame_form, text="เหรียญ").grid(row=0, column=2, padx=5, pady=5)
coin_listbox = tk.Listbox(frame_form, height=5, exportselection=False)
coin_listbox.grid(row=0, column=3, padx=5, pady=5)
coins = ["BTC", "ETH", "XRP", "DOT", "ADA", "FTM", "TROY", "MAGIC"]
for coin in coins:
    coin_listbox.insert(tk.END, coin)

tk.Label(frame_form, text="ราคาซื้อ/ขาย (USDT)").grid(row=1, column=0, padx=5, pady=5)
entry_buy_price = ttk.Entry(frame_form)
entry_buy_price.grid(row=1, column=1, padx=5, pady=5)

tk.Label(frame_form, text="จำนวน").grid(row=1, column=2, padx=5, pady=5)
entry_quantity = ttk.Entry(frame_form)
entry_quantity.grid(row=1, column=3, padx=5, pady=5)

tk.Label(frame_form, text="ค่าธรรมเนียม").grid(row=2, column=0, padx=5, pady=5)
entry_fee_buy = ttk.Entry(frame_form)
entry_fee_buy.grid(row=2, column=1, padx=5, pady=5)

sell_mode = tk.BooleanVar(value=False)
chk_sell_mode = ttk.Checkbutton(frame_form, text="เพิ่มข้อมูลขาย", variable=sell_mode)
chk_sell_mode.grid(row=3, column=0, padx=5, pady=5)

btn_add = ttk.Button(frame_form, text="เพิ่มข้อมูล", command=add_entry)
btn_add.grid(row=3, column=3, padx=5, pady=5)

btn_update_prices = ttk.Button(frame_form, text="อัปเดตราคาปัจจุบัน", command=update_prices)
btn_update_prices.grid(row=3, column=4, padx=5, pady=5)

frame_table = tk.Frame(root)
frame_table.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

columns = df.columns.tolist()
table = ttk.Treeview(frame_table, columns=columns, show="headings")
for col in columns:
    table.heading(col, text=col)
    table.column(col, width=100)
table.pack(fill=tk.BOTH, expand=True)

summary_columns = ["เหรียญ", "จำนวนสุทธิ", "ต้นทุนรวม (USDT)", "มูลค่ารวมปัจจุบัน (USDT)", "กำไร/ขาดทุน (USDT)"]
summary_table = ttk.Treeview(frame_table, columns=summary_columns, show="headings")
for col in summary_columns:
    summary_table.heading(col, text=col)
    summary_table.column(col, width=150)
summary_table.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

update_table()
calculate_summary()

root.mainloop()
