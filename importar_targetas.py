import os
import json
import requests
from dotenv import load_dotenv

# Cargar variables del .env
load_dotenv()

API_KEY = os.getenv("TRELLO_API_KEY")
TOKEN = os.getenv("TRELLO_TOKEN")

params = {
    "key": API_KEY,
    "token": TOKEN
}

# Cargar tarjetas archivadas desde el JSON
with open("tarjetas_archivadas.json", "r", encoding="utf-8") as archivo:
    tarjetas_archivadas = json.load(archivo)

print(f"Tarjetas a importar: {len(tarjetas_archivadas)}")

# ID del tablero destino
ID_TABLERO_DESTINO = "WzCZFZTt"

# Obtener listas del tablero destino
url_listas = f"https://api.trello.com/1/boards/{ID_TABLERO_DESTINO}/lists"
listas = requests.get(url_listas, params=params).json()

if not listas:
    print("El tablero destino no tiene listas.")
    exit()

print("\nListas del tablero destino:")
for i, lista in enumerate(listas, start=1):
    print(f"{i}. {lista['name']} → {lista['id']}")

# Elegir lista destino
opcion = int(input("\nSelecciona el número de la lista donde importar las tarjetas: "))

if opcion < 1 or opcion > len(listas):
    print("Opción no válida.")
    exit()

id_lista_destino = listas[opcion - 1]["id"]
print("Lista destino seleccionada:", id_lista_destino)

# Importar tarjetas
for tarjeta in tarjetas_archivadas:
    nombre = tarjeta.get("name", "Sin nombre")
    descripcion = tarjeta.get("desc", "")

    url_crear = "https://api.trello.com/1/cards"
    datos = {
        "key": API_KEY,
        "token": TOKEN,
        "idList": id_lista_destino,
        "name": nombre,
        "desc": descripcion
    }

    respuesta = requests.post(url_crear, data=datos)

    if respuesta.status_code == 200:
        print("Tarjeta importada:", nombre)
    else:
        print("Error al importar:", nombre)
        print(respuesta.text)
