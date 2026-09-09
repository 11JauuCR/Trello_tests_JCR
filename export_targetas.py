import os
import json
import requests
from dotenv import load_dotenv

# Cargar variables del .env
load_dotenv()

API_KEY = os.getenv("TRELLO_API_KEY")
TOKEN = os.getenv("TRELLO_TOKEN")

# ID del tablero
ID_TABLERO = "qRXD9TvK"

# Parámetros
params = {
    "key": API_KEY,
    "token": TOKEN
}

# Obtener tarjetas archivadas
url = f"https://api.trello.com/1/boards/qRXD9TvK/cards/closed"

respuesta = requests.get(url, params=params)

if respuesta.status_code != 200:
    print("Error:", respuesta.status_code)
    print(respuesta.text)
    exit()

tarjetas = respuesta.json()

print(f"Tarjetas archivadas encontradas: {len(tarjetas)}")

# Guardar en JSON
with open("tarjetas_archivadas.json", "w", encoding="utf-8") as archivo:
    json.dump(tarjetas, archivo, ensure_ascii=False, indent=4)

print("Archivo creado: tarjetas_archivadas.json")