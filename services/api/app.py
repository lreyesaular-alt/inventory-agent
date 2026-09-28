from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parents[2]
PRODUCTS_FILE = BASE_DIR / "products.csv"

app = FastAPI(title="Inventory Agent API")


class Product(BaseModel):
    name: str
    quantity: float
    unit: str


class ProductUpdate(BaseModel):
    quantity: float


def load_products():
    return pd.read_csv(PRODUCTS_FILE)


def save_products(df):
    df.to_csv(PRODUCTS_FILE, index=False)


@app.get("/inventory")
def get_inventory():
    df = load_products()
    return df.to_dict(orient="records")


@app.post("/inventory")
def add_product(product: Product):
    df = load_products()

    new_id = int(df["id"].max()) + 1 if not df.empty else 1

    new_row = {
        "id": new_id,
        "name": product.name,
        "quantity": product.quantity,
        "unit": product.unit,
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_products(df)

    return new_row


@app.patch("/inventory/{product_id}")
def update_product(product_id: int, product: ProductUpdate):
    df = load_products()

    matches = df["id"] == product_id

    if not matches.any():
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    df.loc[matches, "quantity"] = product.quantity
    save_products(df)

    return df.loc[matches].iloc[0].to_dict()


@app.get("/inventory/alerts")
def inventory_alerts(threshold: float = 10):
    df = load_products()
    alerts = df[df["quantity"] < threshold]

    return alerts.to_dict(orient="records")