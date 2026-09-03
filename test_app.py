import os
import sys
import sqlite3
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  #TestClient lets us make fake HTTP requests to our API
from app import app, get_db_connection

def get_test_db_connection():
    conn = sqlite3.connect("test_inventory.db")
    conn.row_factory = sqlite3.Row  
    return conn


@pytest.fixture
def test_database():

    if os.path.exists("test_inventory.db"):
        os.remove("test_inventory.db")
        
    conn = sqlite3.connect("test_inventory.db")

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT UNIQUE NOT NULL,
        color TEXT NOT NULL,
        quantity INTEGER NOT NULL CHECK(quantity >= 0),
        cost_per_item REAL NOT NULL CHECK(cost_per_item >= 0),
        price REAL NOT NULL CHECK(price >= 0)
    )
    """)

    cursor.execute("""
        INSERT INTO products (sku, color, quantity, cost_per_item, price)
        VALUES   
        ('BOOK1', 'Blue', 10, 5, 12), ('TOY1', 'Red', 5, 8, 15), ('MUG1', 'White', 3, 4, 10)
        """)
    
    conn.commit()

    try:
        yield
    finally:
        conn.close()
        if os.path.exists("test_inventory.db"):
            os.remove("test_inventory.db")


    
@pytest.fixture
def client(test_database):
    app.dependency_overrides[get_db_connection] = get_test_db_connection
    yield TestClient(app)
    app.dependency_overrides.clear()



def test_get_products(client):
    response = client.get("/products/")    
    assert response.status_code == 200   
    
    products = response.json()  

    assert isinstance(products, list)

    assert products[0]["sku"] == "BOOK1"

    assert products[0]["color"] == "Blue"

    assert products[0]["quantity"] == 1

    assert products[0]["cost_per_item"] == 1

    assert products[0]["price"] == 5

def test_create_product(client):
    response = client.post("/products/",
        json={
        "sku": "Pen1",
        "color": "Black",
        "quantity": 5,
        "cost_per_item": 5,
        "price": 10}
     )

    assert response.status_code == 200
    assert response.json()["product"]["sku"] == "Pen1"
    assert response.json()["product"]["color"] == "Black"
    assert response.json()["product"]["quantity"] == 5
    assert response.json()["product"]["cost_per_item"] == 5
    assert response.json()["product"]["price"] == 10
    assert response.json()["quantity_status"] == "Available"

def test_duplicate_product(client):
    response = client.post("/products/",        
        json={
        "sku": "TOY1",
        "color": "Lime",
        "quantity": 0,
        "cost_per_item": 1,
        "price": 2}
     )
    assert response.status_code == 409
    assert response.json()["detail"] == "Product sku already exists"

def test_negative_quantity(client):
    response = client.post("/products/",        
        json={
        "sku": "PEN2",
        "color": "Lime",
        "quantity": -5,
        "cost_per_item": 1,
        "price": 2}
     )
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Input should be greater than or equal to 0"

def test_negative_cost(client):
    response = client.post("/products/",        
        json={
        "sku": "PEN3",
        "color": "Lime",
        "quantity": 5,
        "cost_per_item": -1,
        "price": 10}
     )
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Input should be greater than or equal to 0"

def test_negative_price(client):
    response = client.post("/products/",        
        json={
        "sku": "PEN4",
        "color": "Gray",
        "quantity": 5,
        "cost_per_item": 1,
        "price": -1}
     )
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Input should be greater than or equal to 0"

def test_empty_sku(client):
    response = client.post("/products/",        
        json={
        "sku": "",
        "color": "Gray",
        "quantity": 5,
        "cost_per_item": 1,
        "price": 2}
     )
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "String should have at least 1 character"

def test_empty_color(client):
    response = client.post("/products/",        
        json={
        "sku": "PEN5",
        "color": "",
        "quantity": 5,
        "cost_per_item": 1,
        "price": 2}
     )
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "String should have at least 1 character"

def test_case_sensitivity(client):
    response = client.post("/products/",        
        json={
        "sku": "toy1",
        "color": "Black",
        "quantity": 5,
        "cost_per_item": 5,
        "price": 10}
     )
    assert response.status_code == 409
    assert response.json()["detail"] == "Product sku already exists"


def test_update_product(client):
    response = client.put("/products/JWL2",        
        json={
        "sku": "TOY1",
        "color": "Green",
        "quantity": 6,
        "cost_per_item": 8,
        "price": 12
        }
     )
    assert response.status_code == 200
    product = response.json()["product"]
    assert product["sku"] == "TOY1"
    assert product["quantity"] == 6
    assert product["cost_per_item"] == 8
    assert product["price"] == 12
    assert product["quantity_status"] == "Available"

def test_direct_product_lookup(client):
    response = client.get("/products/TOY1")
    assert response.status_code == 200
    assert response.json()["product"]["sku"] == "TOY1"
    assert response.json()["product"]["color"] == "Red"
    assert response.json()["product"]["quantity"] == 1
    assert response.json()["product"]["cost_per_item"] == 2
    assert response.json()["product"]["price"] == 3


def test_direct_product_lookup_failure(client):
    response = client.get("/products/UNKNOWN")
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_update_non_existing_product(client):
    response = client.put("/products/UNKNOWN",        
        json={
        "sku": "UNKNOWN",
        "quantity": 6,
        "cost_per_item": 8,
        "price": 12}
     )
    assert response.status_code == 404
    assert response.json()["detail"] == "Product sku does not exist"

def test_delete_product(client):
    response = client.delete("/products/BOOK1")
    assert response.status_code == 200
    assert response.json()["product"] == "BOOK1"
    
def test_delete_non_existing_product(client):
    client.delete("/products/BOOK1")
    response = client.delete("/products/BOOK1")
    assert response.status_code == 404
    assert response.json()["detail"] == "SKU does not exist"
