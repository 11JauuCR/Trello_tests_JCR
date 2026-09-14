import os
import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("TRELLO_API_KEY")
token = os.getenv("TRELLO_TOKEN")

nombre_tablero = "TEST 1 JCR"

params = {
    "key": key,
    "token": token
}

url = "https://api.trello.com/1/members/me/boards"
tableros = requests.get(url, params=params).json()

for tablero in tableros:
    if tablero["name"] == nombre_tablero:
        board_id = tablero["id"]
        break

url = f"https://api.trello.com/1/boards/{board_id}/cards"
tarjetas = requests.get(url, params=params).json()

print("Tablero:", nombre_tablero)

if len(tarjetas) == 0:
    print("No hay tarjetas en este tablero.")
else:
    print("Tarjetas:", len(tarjetas))

    confirmar = input("¿Eliminar todas? (s/n): ")

    if confirmar.lower() == "s":
        for tarjeta in tarjetas:
            url = f"https://api.trello.com/1/cards/{tarjeta['id']}"
            requests.delete(url, params=params)
            print("Eliminada:", tarjeta["name"])

        print("Listo.")
    else:
        print("Cancelado.")
