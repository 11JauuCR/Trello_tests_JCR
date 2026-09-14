import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("TRELLO_API_KEY")
token = os.getenv("TRELLO_TOKEN")

params = {
    "key": key,
    "token": token
}

tableros_nombres = ["SCAITT", "AUTOVIGATANA"]

def buscar_tableros():
    url = "https://api.trello.com/1/members/me/boards"
    return requests.get(url, params=params).json()


def buscar_campos(board_id):
    url = f"https://api.trello.com/1/boards/{board_id}/customFields"
    return requests.get(url, params=params).json()


def buscar_tarjetas(board_id):
    url = f"https://api.trello.com/1/boards/{board_id}/cards"
    return requests.get(url, params=params).json()


def actualizar_campo(card_id, campo_id, valor):
    url = f"https://api.trello.com/1/cards/{card_id}/customField/{campo_id}/item"

    data = {
        "value": {
            "text": valor
        }
    }

    requests.put(url, params=params, json=data)


def buscar_fecha_comentario(card_id):
    url = f"https://api.trello.com/1/cards/{card_id}/actions"
    
    acciones = requests.get(
        url,
        params={
            **params,
            "filter": "commentCard"
        }
    ).json()

    for accion in acciones:
        texto = accion["data"]["text"]

        fecha = re.search(
            r"(\d{1,2}/\d{1,2}/\d{4})",
            texto
        )

        if fecha:
            return fecha.group(1)

    return None


tableros = buscar_tableros()

for tablero in tableros:

    if tablero["name"] not in tableros_nombres:
        continue

    print("\nTablero:", tablero["name"])

    board_id = tablero["id"]

    campos = buscar_campos(board_id)

    fact_id = None
    ent_id = None
    last_update_id = None

    for campo in campos:
        if campo["name"] == "FACT":
            fact_id = campo["id"]

        if campo["name"] == "ENT":
            ent_id = campo["id"]

        if campo["name"] == "last_update":
            last_update_id = campo["id"]

    if not fact_id or not ent_id:
        print("No se encontraron los campos FACT o ENT.")
        continue

    tarjetas = buscar_tarjetas(board_id)

    for tarjeta in tarjetas:

        print("\nTarjeta:", tarjeta["name"])

        # Buscar last_update
        last_update = None

        for campo in tarjeta.get("customFieldItems", []):
            if campo["idCustomField"] == last_update_id:
                if "value" in campo and "text" in campo["value"]:
                    last_update = campo["value"]["text"]

        # Copiar last_update a FACT
        if last_update:
            actualizar_campo(
                tarjeta["id"],
                fact_id,
                last_update
            )
            print("FACT actualizado:", last_update)

        # Buscar fecha en comentarios
        fecha = buscar_fecha_comentario(tarjeta["id"])

        if fecha:
            actualizar_campo(
                tarjeta["id"],
                ent_id,
                fecha
            )
            print("ENT actualizado:", fecha)
