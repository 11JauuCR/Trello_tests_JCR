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

tableros_nombres = ["test1"]


def buscar_tableros():
    url = "https://api.trello.com/1/members/me/boards"
    return requests.get(url, params=params).json()


def buscar_campos(board_id):
    url = f"https://api.trello.com/1/boards/{board_id}/customFields"
    return requests.get(url, params=params).json()


def buscar_tarjetas(board_id):
    url = f"https://api.trello.com/1/boards/{board_id}/cards"

    params_tarjetas = {
        **params,
        "customFieldItems": "true"
    }

    return requests.get(url, params=params_tarjetas).json()


def actualizar_campo(card_id, campo_id, fecha):
    url = f"https://api.trello.com/1/cards/{card_id}/customField/{campo_id}/item"

    data = {
        "value": {
            "date": fecha
        }
    }

    respuesta = requests.put(
        url,
        params=params,
        json=data
    )

    if respuesta.ok:
        print("Campo actualizado:", fecha)
    else:
        print("Error:", respuesta.status_code)
        print(respuesta.text)


def buscar_fecha_comentario(card_id):
    url = f"https://api.trello.com/1/cards/{card_id}/actions"

    respuesta = requests.get(
        url,
        params={
            **params,
            "filter": "commentCard"
        }
    )

    acciones = respuesta.json()

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

    for campo in campos:

        if campo["name"] == "FACT":
            fact_id = campo["id"]

        elif campo["name"] == "ENT":
            ent_id = campo["id"]

    if not fact_id or not ent_id:
        print("No se encontraron los campos FACT o ENT")
        continue

    tarjetas = buscar_tarjetas(board_id)

    for tarjeta in tarjetas:

        print("\nTarjeta:", tarjeta["name"])

        # Última modificación de la tarjeta -> ENT

        ultima_modificacion = tarjeta.get("dateLastActivity")

        if ultima_modificacion:

            actualizar_campo(
                tarjeta["id"],
                ent_id,
                ultima_modificacion
            )

            print(
                "ENT:",
                ultima_modificacion
            )

        # Fecha del comentario -> FACT

        fecha = buscar_fecha_comentario(
            tarjeta["id"]
        )

        if fecha:

            dia, mes, año = fecha.split("/")

            fecha_fact = (
                f"{año}-{mes}-{dia}T00:00:00.000Z"
            )

            actualizar_campo(
                tarjeta["id"],
                fact_id,
                fecha_fact
            )

            print(
                "FACT:",
                fecha
            )