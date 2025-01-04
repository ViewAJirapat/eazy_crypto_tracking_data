import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import os
import requests

# ชื่อไฟล์สำหรับบันทึกข้อมูล
file_path = "crypto_tracking_data.xlsx"

# ฟังก์ชันโหลดข้อมูลเมื่อเปิดโปรแกรม
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

# ฟังก์ชันบันทึกข้อมูล
def save_data():
    global df
    df.to_excel(file_path, index=False)
    messagebox.showinfo("สำเร็จ", "ข้อมูลถูกบันทึกเรียบร้อยแล้ว!")

# ฟังก์ชันเพิ่มข้อมูลใหม่
def add_entry():
    global df
    try:
        selected_coin = coin_listbox.get(coin_listbox.curselection())
        new_entry = pd.DataFrame([{
            "วันที่": entry_date.get(),
            "เหรียญ": selected_coin,
            "ราคาซื้อ (USDT)": float(entry_buy_price.get()),
            "จำนวนที่ซื้อ": float(entry_quantity.get()),
            "ค่าธรรมเนียมซื้อ (เหรียญ)": float(entry_fee_buy.get()),
            "จำนวนสุทธิซื้อ (เหรียญ)": float(entry_quantity.get()) - float(entry_fee_buy.get()),
            "ต้นทุนรวม (USDT)": float(entry_buy_price.get()) * float(entry_quantity.get()),
            "มูลค่าปัจจุบัน (USDT)": 0,  # กรอกทีหลัง
            "มูลค่ารวมปัจจุบัน (USDT)": 0,  # คำนวณภายหลัง
            "การเปลี่ยนแปลง (%)": 0,  # คำนวณภายหลัง
            "ราคาขาย (USDT)": 0,
            "จำนวนที่ขาย": 0,
            "ค่าธรรมเนียมขาย (USDT)": 0,
            "มูลค่าหลังขาย (USDT)": 0,
            "กำไร/ขาดทุน (USDT)": 0
        }])
        
        # ใช้ pd.concat() แทน append()
        df = pd.concat([df, new_entry], ignore_index=True)
        
        save_data()
        update_table()
        clear_entries()
    except Exception as e:
        messagebox.showerror("ข้อผิดพลาด", f"กรุณากรอกข้อมูลให้ถูกต้อง: {e}")


# ฟังก์ชันอัปเดตราคาปัจจุบันจาก API Binance
def update_prices():
    global df
    try:
        for index, row in df.iterrows():
            coin = row["เหรียญ"]
            if coin:
                # ดึงข้อมูลจาก Binance API
                check_api_data(coin);
                response = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={coin.upper()}USDT")
                if response.status_code == 200:
                    current_price = float(response.json()["price"])
                    df.loc[index, "มูลค่าปัจจุบัน (USDT)"] = current_price
                    df.loc[index, "มูลค่ารวมปัจจุบัน (USDT)"] = current_price * row["จำนวนสุทธิซื้อ (เหรียญ)"]
                    # คำนวณ % การเปลี่ยนแปลง
                    df.loc[index, "การเปลี่ยนแปลง (%)"] = ((df.loc[index, "มูลค่ารวมปัจจุบัน (USDT)"] - row["ต้นทุนรวม (USDT)"]) / row["ต้นทุนรวม (USDT)"]) * 100
        save_data()
        update_table()
    except Exception as e:
        messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถดึงราคาปัจจุบันได้: {e}")

def check_api_data(coin):
    response = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={coin.upper()}USDT")
    
    if response.status_code == 200:
        # Print the raw response data (as JSON)
        print(response.json())  # This will show the data returned from Binance API
    else:
        print(f"Error: {response.status_code}")

# ฟังก์ชันอัปเดตตาราง
def update_table():
    for row in table.get_children():
        table.delete(row)
    for index, row in df.iterrows():
        table.insert("", "end", values=list(row))

# ฟังก์ชันล้างข้อมูลในช่องกรอก
def clear_entries():
    entry_date.delete(0, tk.END)
    #entry_coin.delete(0, tk.END)
    entry_buy_price.delete(0, tk.END)
    entry_quantity.delete(0, tk.END)
    entry_fee_buy.delete(0, tk.END)

# โหลดข้อมูลเริ่มต้น
df = load_data()

# สร้างหน้าต่าง GUI
root = tk.Tk()
root.title("Crypto Tracker")
root.geometry("1400x600")

# ส่วนกรอกข้อมูล
frame_form = tk.Frame(root)
frame_form.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

tk.Label(frame_form, text="วันที่").grid(row=0, column=0, padx=5, pady=5)
entry_date = ttk.Entry(frame_form)
entry_date.grid(row=0, column=1, padx=5, pady=5)

# tk.Label(frame_form, text="เหรียญ").grid(row=0, column=2, padx=5, pady=5)
# entry_coin = ttk.Entry(frame_form)
# entry_coin.grid(row=0, column=3, padx=5, pady=5)
tk.Label(frame_form, text="เหรียญ").grid(row=0, column=2, padx=5, pady=5)
coin_listbox = tk.Listbox(frame_form, height=5, exportselection=False)
coin_listbox.grid(row=0, column=3, padx=5, pady=5)
coins = ["BTC", "ETH", "XRP", "DOT", "ADA", "FTM", "TROY", "MAGIC"]  # Add more coins as needed
for coin in coins:
    coin_listbox.insert(tk.END, coin)

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

# ส่วนตารางแสดงข้อมูล
frame_table = tk.Frame(root)
frame_table.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

columns = df.columns.tolist()
table = ttk.Treeview(frame_table, columns=columns, show="headings")
for col in columns:
    table.heading(col, text=col)
    table.column(col, width=100)
table.pack(fill=tk.BOTH, expand=True)

update_table()

# เริ่มโปรแกรม
root.mainloop()
