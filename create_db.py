import sqlite3

conn = sqlite3.connect(“demo_inventory.db”)

cursor = conn.cursor()

cursor.execute(”””
CREATE TABLE IF NOT EXISTS products (
id INTEGER PRIMARY KEY AUTOINCREMENT,
sku TEXT NOT NULL UNIQUE,
color TEXT NOT NULL,
quantity INTEGER NOT NULL CHECK(quantity >= 0),
cost_per_item REAL NOT NULL CHECK(cost_per_item >= 0),
price REAL NOT NULL CHECK(price >= 0)
)
“””)

cursor.execute(“SELECT COUNT(*) FROM products”)

if cursor.fetchone()[0] == 0:

cursor.execute("""
INSERT INTO products (sku, color, quantity, cost_per_item, price)
VALUES
('BOOK1', 'Blue', 10, 5, 12),
('TOY1', 'Red', 5, 8, 15),
('MUG1', 'White', 3, 4, 10)
""")

conn.commit()

cursor.execute(“SELECT * FROM products”)
rows = cursor.fetchall()

print(rows)

conn.close()
