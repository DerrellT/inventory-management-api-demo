import sqlite3
from models import Product, ProductUpdate
from fastapi import FastAPI, HTTPException, Depends
app = FastAPI()


def get_db_connection():
    conn = sqlite3.connect("inventory.db")
    conn.row_factory = sqlite3.Row  # lets us return dict-like rows
    return conn


@app.get("/products/")
def get_all_products(conn = Depends(get_db_connection)):
    """Returns all products"""
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()

    conn.close()

    return [dict(row) for row in rows]

@app.get("/products/{sku}")
def get_product(sku: str, conn = Depends(get_db_connection)):        #name is extraced as parameter and calls get_char
    """Return a product by exact sku match."""
    sku = sku.upper()

    cursor = conn.cursor()      #cursor is created to send SQL commands from python

    cursor.execute("SELECT * FROM products WHERE sku = ? COLLATE NOCASE ", (sku,))
    row = cursor.fetchone() 
    conn.close()            
    if row is None:         
        raise HTTPException(status_code=404, detail="Product not found") 
    return {
        "message": "Product found",
        "product": dict(row)
        }

@app.post("/products/")
def create_product(product : Product, conn = Depends(get_db_connection)):
    """Create a new product."""
    product.sku = product.sku.upper()
    u_sku = product.sku
  
    if product.quantity == 0:
        status = "Sold Out"
    else:
        status = "Available" 
    
    cursor = conn.cursor()    

    cursor.execute("SELECT * FROM products WHERE sku = ? ", (u_sku,)) #SQL is exectuted
    product_row = cursor.fetchone()
    if product_row:
        raise HTTPException(status_code=409, detail="Product sku already exists")

    cursor.execute("INSERT INTO products (sku, color, quantity, cost_per_item, price) VALUES (?, ?, ?, ?, ?) ", (u_sku, product.color, product.quantity, product.cost_per_item, product.price))
    conn.commit()
    cursor.execute( "SELECT * FROM products WHERE sku = ?", (u_sku,))
    new_product = cursor.fetchone()
    conn.close()

    return {
        "message": "Product added successfully",
        "product": dict(new_product),
        "quantity_status": status
        
    }

@app.put("/products/{sku}")
def update_product(sku: str, product: ProductUpdate, conn = Depends(get_db_connection)):
    "Update product details"
    sku = sku.upper()
    
    if product.quantity == 0:
        status = "Sold Out"
    else:
        status = "Available" 
    
    cursor = conn.cursor()    

    cursor.execute("SELECT * FROM products WHERE sku = ? COLLATE NOCASE ", (sku,))
    product_row = cursor.fetchone()
    if product_row is None:
        raise HTTPException(status_code=404, detail="Product sku does not exist")

    cursor.execute("UPDATE products SET quantity = ?, cost_per_item = ?, price = ? WHERE sku =?", (product.quantity, product.cost_per_item, product.price, sku))
    conn.commit()
    conn.close()
    
    return {
        "message": "Product updated successfully",
        "product": {"sku": sku, 
        "quantity": product.quantity,
        "quantity_status": status,
        "cost_per_item": product.cost_per_item,
        "price": product.price
        }
        
    }

@app.delete("/products/{sku}")
def delete_product(sku: str, conn = Depends(get_db_connection)):
    """Delete a product"""
    sku = sku.upper()
        
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products WHERE sku = ? COLLATE NOCASE ", (sku,))
    product_row = cursor.fetchone()
    if not product_row:
        raise HTTPException(status_code=404, detail="SKU does not exist")  
    
    cursor.execute("DELETE FROM products WHERE sku = ? ", (sku,))
    conn.commit()
    conn.close()
    return {
        "message": "Product deleted successfully",
        "product": sku
        }
