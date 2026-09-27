import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from pathlib import Path


DB_NAME = Path(__file__).resolve().parent / "food_ordering.db"
ADMIN_PASSWORD = "admin123"  # Change this before submitting if you want.


class FoodOrderingSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Food Ordering Management System")
        self.root.geometry("920x620")
        self.root.minsize(820, 540)
        self.cart = []

        self.create_database()
        self.make_style()
        self.build_customer_screen()
        self.load_menu()

    def connection(self):
        return sqlite3.connect(DB_NAME)

    def create_database(self):
        con = self.connection()
        cur = con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS food_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            price REAL NOT NULL,
            available INTEGER NOT NULL DEFAULT 1
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            order_date TEXT NOT NULL
        )""")
        cur.execute("""CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            food_name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        )""")

        cur.execute("SELECT COUNT(*) FROM food_items")
        if cur.fetchone()[0] == 0:
            cur.executemany("INSERT INTO food_items(name, price) VALUES (?, ?)", [
                ("Burger", 80), ("Pizza", 150), ("Sandwich", 60),
                ("French Fries", 70), ("Cold Drink", 40), ("Pasta", 120)
            ])
        con.commit()
        con.close()

    def make_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Title.TLabel", font=("Arial", 18, "bold"), foreground="#17324d")
        style.configure("Heading.TLabel", font=("Arial", 11, "bold"))
        style.configure("TButton", font=("Arial", 10), padding=7)
        style.configure("Treeview", rowheight=28, font=("Arial", 10))
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

    def build_customer_screen(self):
        main = ttk.Frame(self.root, padding=18)
        main.pack(fill="both", expand=True)

        top = ttk.Frame(main)
        top.pack(fill="x", pady=(0, 12))
        ttk.Label(top, text="Food Ordering System", style="Title.TLabel").pack(side="left")
        ttk.Button(top, text="Admin Panel", command=self.open_admin_login).pack(side="right")

        info = ttk.LabelFrame(main, text="Customer Details", padding=10)
        info.pack(fill="x", pady=(0, 12))
        ttk.Label(info, text="Your Name:", style="Heading.TLabel").pack(side="left")
        self.customer_name = ttk.Entry(info, width=35)
        self.customer_name.pack(side="left", padx=8)
        ttk.Label(info, text="Enter your name before placing the order.").pack(side="left")

        body = ttk.Frame(main)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        menu_box = ttk.LabelFrame(body, text="Food Menu", padding=10)
        menu_box.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        self.menu_tree = ttk.Treeview(menu_box, columns=("id", "food", "price"), show="headings", height=13)
        self.menu_tree.heading("id", text="ID")
        self.menu_tree.heading("food", text="Food Item")
        self.menu_tree.heading("price", text="Price")
        self.menu_tree.column("id", width=50, anchor="center")
        self.menu_tree.column("food", width=190)
        self.menu_tree.column("price", width=90, anchor="center")
        self.menu_tree.pack(fill="both", expand=True)

        add_row = ttk.Frame(menu_box)
        add_row.pack(fill="x", pady=(10, 0))
        ttk.Label(add_row, text="Quantity:").pack(side="left")
        self.quantity = tk.IntVar(value=1)
        ttk.Spinbox(add_row, from_=1, to=20, textvariable=self.quantity, width=5).pack(side="left", padx=7)
        ttk.Button(add_row, text="Add to Cart", command=self.add_to_cart).pack(side="right")

        cart_box = ttk.LabelFrame(body, text="Your Cart", padding=10)
        cart_box.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        self.cart_tree = ttk.Treeview(cart_box, columns=("food", "price", "qty", "total"), show="headings", height=13)
        for col, heading, width in [("food", "Food Item", 140), ("price", "Price", 70), ("qty", "Qty", 45), ("total", "Total", 80)]:
            self.cart_tree.heading(col, text=heading)
            self.cart_tree.column(col, width=width, anchor="center" if col != "food" else "w")
        self.cart_tree.pack(fill="both", expand=True)

        bottom = ttk.Frame(cart_box)
        bottom.pack(fill="x", pady=(10, 0))
        self.total_label = ttk.Label(bottom, text="Total: Rs. 0.00", style="Heading.TLabel")
        self.total_label.pack(side="left")
        ttk.Button(bottom, text="Remove Selected", command=self.remove_cart_item).pack(side="right")
        ttk.Button(bottom, text="Place Order", command=self.place_order).pack(side="right", padx=6)

    def load_menu(self):
        for item in self.menu_tree.get_children():
            self.menu_tree.delete(item)
        con = self.connection()
        rows = con.execute("SELECT id, name, price FROM food_items WHERE available=1 ORDER BY name").fetchall()
        con.close()
        for row in rows:
            self.menu_tree.insert("", "end", values=(row[0], row[1], f"Rs. {row[2]:.2f}"))

    def add_to_cart(self):
        selected = self.menu_tree.selection()
        if not selected:
            messagebox.showwarning("Select Food", "Please select a food item from the menu.")
            return
        values = self.menu_tree.item(selected[0], "values")
        food_id, name = int(values[0]), values[1]
        price = float(values[2].replace("Rs. ", ""))
        qty = self.quantity.get()
        if qty < 1:
            return
        for item in self.cart:
            if item["food_id"] == food_id:
                item["quantity"] += qty
                self.refresh_cart()
                return
        self.cart.append({"food_id": food_id, "name": name, "price": price, "quantity": qty})
        self.refresh_cart()

    def refresh_cart(self):
        for item in self.cart_tree.get_children():
            self.cart_tree.delete(item)
        total = 0
        for index, item in enumerate(self.cart):
            amount = item["price"] * item["quantity"]
            total += amount
            self.cart_tree.insert("", "end", iid=str(index), values=(
                item["name"], f"Rs. {item['price']:.2f}", item["quantity"], f"Rs. {amount:.2f}"))
        self.total_label.config(text=f"Total: Rs. {total:.2f}")

    def remove_cart_item(self):
        selected = self.cart_tree.selection()
        if not selected:
            messagebox.showwarning("Select Item", "Select an item from your cart first.")
            return
        del self.cart[int(selected[0])]
        self.refresh_cart()

    def place_order(self):
        name = self.customer_name.get().strip()
        if not name:
            messagebox.showwarning("Name Required", "Please enter your name.")
            return
        if not self.cart:
            messagebox.showwarning("Cart Empty", "Add at least one food item to the cart.")
            return
        total = sum(x["price"] * x["quantity"] for x in self.cart)
        con = self.connection()
        cur = con.cursor()
        cur.execute("INSERT INTO orders(customer_name, total_amount, status, order_date) VALUES (?, ?, ?, ?)",
                    (name, total, "Pending", datetime.now().strftime("%d-%m-%Y %I:%M %p")))
        order_id = cur.lastrowid
        for item in self.cart:
            cur.execute("INSERT INTO order_items(order_id, food_name, price, quantity) VALUES (?, ?, ?, ?)",
                        (order_id, item["name"], item["price"], item["quantity"]))
        con.commit()
        con.close()
        messagebox.showinfo("Order Placed", f"Order #{order_id} placed successfully!\nTotal amount: Rs. {total:.2f}")
        self.cart.clear()
        self.customer_name.delete(0, "end")
        self.refresh_cart()

    def open_admin_login(self):
        password = simpledialog.askstring("Admin Login", "Enter admin password:", show="*")
        if password is None:
            return
        if password != ADMIN_PASSWORD:
            messagebox.showerror("Access Denied", "Incorrect password.")
            return
        self.open_admin_panel()

    def open_admin_panel(self):
        win = tk.Toplevel(self.root)
        win.title("Admin Panel")
        win.geometry("900x550")
        win.transient(self.root)
        notebook = ttk.Notebook(win)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)
        orders_tab = ttk.Frame(notebook, padding=12)
        menu_tab = ttk.Frame(notebook, padding=12)
        notebook.add(orders_tab, text="Manage Orders")
        notebook.add(menu_tab, text="Manage Menu")
        self.build_orders_tab(orders_tab)
        self.build_menu_tab(menu_tab)

    def build_orders_tab(self, tab):
        ttk.Label(tab, text="Customer Orders", style="Title.TLabel").pack(anchor="w", pady=(0, 10))
        # Colours are shown only for orders updated during this admin session.
        # Opening the panel always starts with normal, uncoloured rows.
        coloured_order_ids = set()
        tree = ttk.Treeview(tab, columns=("id", "customer", "total", "status", "date"), show="headings")
        for col, heading, width in [("id", "Order ID", 70), ("customer", "Customer", 170), ("total", "Total", 100), ("status", "Status", 110), ("date", "Date & Time", 190)]:
            tree.heading(col, text=heading)
            tree.column(col, width=width, anchor="center")
        tree.pack(fill="both", expand=True)
        # Row colours make order status easy to identify at a glance.
        tree.tag_configure("pending", background="#ffd6d6")
        tree.tag_configure("preparing", background="#fff1bf")
        tree.tag_configure("ready", background="#dbeafe")
        tree.tag_configure("delivered", background="#d8f3dc")
        tree.tag_configure("cancelled", background="#e5e7eb", foreground="#555555")

        def load_orders():
            tree.delete(*tree.get_children())
            con = self.connection()
            rows = con.execute("SELECT id, customer_name, total_amount, status, order_date FROM orders ORDER BY id DESC").fetchall()
            con.close()
            for row in rows:
                status_tag = row[3].lower()
                tags = (status_tag,) if row[0] in coloured_order_ids else ()
                tree.insert("", "end", values=(row[0], row[1], f"Rs. {row[2]:.2f}", row[3], row[4]), tags=tags)

        def update_status():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Select Order", "Select an order first.")
                return
            order_id = tree.item(selected[0], "values")[0]
            status = status_box.get()
            if status not in ["Pending", "Preparing", "Ready", "Delivered", "Cancelled"]:
                messagebox.showwarning("Select Status", "Please choose a new status first.")
                return
            con = self.connection()
            con.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
            con.commit()
            con.close()
            coloured_order_ids.add(int(order_id))
            load_orders()

        def clear_all_orders():
            confirm = messagebox.askyesno(
                "Clear All Orders",
                "Delete all order history?\n\nYour food menu will not be deleted."
            )
            if not confirm:
                return
            con = self.connection()
            cur = con.cursor()
            cur.execute("DELETE FROM order_items")
            cur.execute("DELETE FROM orders")
            cur.execute("DELETE FROM sqlite_sequence WHERE name IN ('orders', 'order_items')")
            con.commit()
            con.close()
            coloured_order_ids.clear()
            load_orders()
            messagebox.showinfo("Orders Cleared", "All order history has been deleted.")

        controls = ttk.Frame(tab)
        controls.pack(fill="x", pady=10)
        ttk.Label(controls, text="New Status:").pack(side="left")
        status_box = ttk.Combobox(controls, values=["Pending", "Preparing", "Ready", "Delivered", "Cancelled"], state="readonly", width=15)
        status_box.set("Select status")
        status_box.pack(side="left", padx=7)
        ttk.Button(controls, text="Update Selected Order", command=update_status).pack(side="left")
        ttk.Button(controls, text="Clear All Orders", command=clear_all_orders).pack(side="right")
        ttk.Button(controls, text="Refresh", command=load_orders).pack(side="right")
        load_orders()

    def build_menu_tab(self, tab):
        ttk.Label(tab, text="Food Menu", style="Title.TLabel").pack(anchor="w", pady=(0, 10))
        tree = ttk.Treeview(tab, columns=("id", "food", "price", "available"), show="headings", height=13)
        for col, heading, width in [("id", "ID", 60), ("food", "Food Item", 250), ("price", "Price", 120), ("available", "Available", 100)]:
            tree.heading(col, text=heading)
            tree.column(col, width=width, anchor="center" if col != "food" else "w")
        tree.pack(fill="both", expand=True)

        def load_admin_menu():
            tree.delete(*tree.get_children())
            con = self.connection()
            rows = con.execute("SELECT id, name, price, available FROM food_items ORDER BY id DESC").fetchall()
            con.close()
            for row in rows:
                tree.insert("", "end", values=(row[0], row[1], f"Rs. {row[2]:.2f}", "Yes" if row[3] else "No"))

        def add_food():
            name = food_name.get().strip()
            try:
                price = float(food_price.get())
                if not name or price <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Invalid Details", "Enter a food name and a valid positive price.")
                return
            try:
                con = self.connection()
                con.execute("INSERT INTO food_items(name, price) VALUES (?, ?)", (name, price))
                con.commit()
                con.close()
            except sqlite3.IntegrityError:
                messagebox.showwarning("Already Exists", "This food item already exists.")
                return
            food_name.delete(0, "end")
            food_price.delete(0, "end")
            load_admin_menu()
            self.load_menu()

        def toggle_availability():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Select Food", "Select a food item first.")
                return
            values = tree.item(selected[0], "values")
            new_value = 0 if values[3] == "Yes" else 1
            con = self.connection()
            con.execute("UPDATE food_items SET available=? WHERE id=?", (new_value, values[0]))
            con.commit()
            con.close()
            load_admin_menu()
            self.load_menu()

        form = ttk.Frame(tab)
        form.pack(fill="x", pady=12)
        ttk.Label(form, text="Food Name:").pack(side="left")
        food_name = ttk.Entry(form, width=23)
        food_name.pack(side="left", padx=5)
        ttk.Label(form, text="Price:").pack(side="left")
        food_price = ttk.Entry(form, width=10)
        food_price.pack(side="left", padx=5)
        ttk.Button(form, text="Add Food", command=add_food).pack(side="left", padx=5)
        ttk.Button(form, text="Show/Hide Selected", command=toggle_availability).pack(side="right")
        load_admin_menu()


if __name__ == "__main__":
    root = tk.Tk()
    FoodOrderingSystem(root)
    root.mainloop()
