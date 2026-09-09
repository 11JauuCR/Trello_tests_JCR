import os
import time
import requests
from dotenv import load_dotenv

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

id_tablero = "qRXD9TvK"  # Valor por defecto del tablero

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

# Diccionario: lista_id → ids de tarjetas previas
tarjetas_previas = {}

for lista in listas:
    url_tarjetas = f"https://api.trello.com/1/lists/{lista['id']}/cards"
    tarjetas = requests.get(url_tarjetas, params=params).json()
    tarjetas_previas[lista["id"]] = {t["id"] for t in tarjetas}

print("\nEsperando nuevas tarjetas en TODAS las listas...\n")

while True:
    time.sleep(2)

    for lista in listas:
        url_tarjetas = f"https://api.trello.com/1/lists/{lista['id']}/cards"
        tarjetas_actuales = requests.get(url_tarjetas, params=params).json()
        ids_actuales = {t["id"] for t in tarjetas_actuales}

        nuevas = ids_actuales - tarjetas_previas[lista["id"]]

        for t in tarjetas_actuales:
            if t["id"] in nuevas:
                print(f" Nueva tarjeta en '{lista['name']}': {t['name']} → {t['id']}")

        tarjetas_previas[lista["id"]] = ids_actuales