import csv
import os
from datetime import datetime

import requests
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

API_URL = "http://127.0.0.1:8000"
LOG_FILE = "conversation_log.csv"


def log_conversation(role, message):
    exists = os.path.exists(LOG_FILE)

    with open(LOG_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        if not exists:
            writer.writerow(["timestamp", "role", "message"])

        writer.writerow([
            datetime.now().isoformat(),
            role,
            message,
        ])


def observe():
    response = requests.get(f"{API_URL}/inventory")
    response.raise_for_status()
    return response.json()


def act(product_id, quantity):
    response = requests.patch(
        f"{API_URL}/inventory/{product_id}",
        json={"quantity": quantity},
    )
    response.raise_for_status()
    return response.json()


def ask_llm(inventory):
    prompt = f"""
Eres un agente de inventario.

Observa este inventario:

{inventory}

Identifica los productos con cantidad inferior a 10.

Responde indicando:
1. Qué productos necesitan atención.
2. Qué acción debería realizarse.

No inventes productos ni cantidades.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    return response.choices[0].message.content


def run_agent():
    print("🤖 Agente de inventario iniciado.")

    # 1. Observar
    inventory = observe()

    print("\n📦 INVENTARIO:")
    print(inventory)

    log_conversation("observation", str(inventory))

    # 2. Analizar / decidir
    decision = ask_llm(inventory)

    print("\n🧠 DECISIÓN DEL AGENTE:")
    print(decision)

    log_conversation("assistant", decision)

    # 3. Actuar
    low_stock = [
        product for product in inventory
        if product["quantity"] < 10
    ]

    for product in low_stock:
        new_quantity = 20

        updated = act(
            product["id"],
            new_quantity,
        )

        print(
            f"\n🔧 ACTUALIZADO: "
            f"{product['name']} → {new_quantity} {product['unit']}"
        )

        log_conversation(
            "action",
            str(updated),
        )

    # 4. Actualizar / comprobar
    updated_inventory = observe()

    log_conversation(
        "update",
        str(updated_inventory),
    )

    print("\n🔄 Ciclo completado.")


if __name__ == "__main__":
    run_agent()


