import os
import requests
from dotenv import load_dotenv
from flask import Flask, request

load_dotenv()

API_KEY = os.getenv("TRELLO_API_KEY")
TOKEN = os.getenv("TRELLO_TOKEN")

if not API_KEY or not TOKEN:
    print("Faltan credenciales en el .env")
    exit()

NOMBRE_TABLERO = "TEST 1 JCR"

# Obtener todos los tableros
url_tableros = "https://api.trello.com/1/members/me/boards"
params = {"key": API_KEY, "token": TOKEN}
tableros = requests.get(url_tableros, params=params).json()

print("Tableros encontrados:")
for t in tableros:
    print("-", t["name"], "-->", t["id"])

# Usa el ID real del tablero
id_tablero = input("Introduce el ID REAL del tablero: ").strip()

print("Tablero:", NOMBRE_TABLERO, "-->", id_tablero)

# Obtener listas del tablero
url_listas = f"https://api.trello.com/1/boards/{id_tablero}/lists"
listas = requests.get(url_listas, params=params).json()

if not listas:
    print("El tablero no tiene listas.")
    exit()

print("\nListas encontradas:")
for l in listas:
    print("-", l["name"], "-->", l["id"])

# ================================
# MONITORIZAR TODAS LAS LISTAS
# ================================
# Sustituimos el polling por webhook

WEBHOOK_URL = "https://repeated-hence-cosmic.ngrok-free.dev/trello"

url_webhook = "https://api.trello.com/1/webhooks"
params_webhook = {
    "key": API_KEY,
    "token": TOKEN,
    "description": "Webhook tablero",
    "callbackURL": WEBHOOK_URL,
    "idModel": id_tablero
}

resp = requests.post(url_webhook, params=params_webhook)

print("\nWebhook creado. Código:", resp.status_code)
print("Respuesta:", resp.text)

# ================================
# SERVIDOR WEB PARA RECIBIR EVENTOS
# ================================

app = Flask(__name__)

@app.route("/trello", methods=["HEAD", "POST"])
def trello_webhook():
    if request.method == "HEAD":
        return ""

    data = request.json

    if data and "action" in data:
        a = data["action"]

        if a["type"] == "createCard":
            card = a["data"]["card"]
            lista = a["data"]["list"]["name"]
            print(f" Nueva tarjeta en '{lista}': {card['name']} → {card['id']}")

    return ""

if __name__ == "__main__":
    print("\nEsperando eventos del webhook...\n")
    app.run(port=5000, debug=False)