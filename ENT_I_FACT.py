import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

PARAMS = {
    "key": os.getenv("TRELLO_API_KEY"),
    "token": os.getenv("TRELLO_TOKEN")
}

TABLEROS = ["test1"]


def get(url, params_extra=None):
    params = {**PARAMS, **(params_extra or {})}

    respuesta = requests.get(url, params=params)
    respuesta.raise_for_status()

    return respuesta.json()


def actualizar_fecha(card_id, campo_id, fecha):
    url = f"https://api.trello.com/1/cards/{card_id}/customField/{campo_id}/item"

    respuesta = requests.put(
        url,
        params=PARAMS,
        json={"value": {"date": fecha}}
    )

    respuesta.raise_for_status()


def actualizar_opcion(card_id, campo_id, opcion_id):
    url = f"https://api.trello.com/1/cards/{card_id}/customField/{campo_id}/item"

    respuesta = requests.put(
        url,
        params=PARAMS,
        json={"idValue": opcion_id}
    )

    respuesta.raise_for_status()


def buscar_ent(card_id):
    url = f"https://api.trello.com/1/cards/{card_id}/actions"

    acciones = get(
        url,
        {"filter": "commentCard"}
    )

    for accion in acciones:
        texto = accion["data"]["text"]

        match = re.search(
            r"ENTREGADO\s+POR\s+(.+)",
            texto,
            re.IGNORECASE
        )

        if match:
            return match.group(1).strip()

    return None


tableros = get(
    "https://api.trello.com/1/members/me/boards"
)

for tablero in tableros:

    if tablero["name"] not in TABLEROS:
        continue

    board_id = tablero["id"]

    print(f"\nTablero: {tablero['name']}")

    campos = get(
        f"https://api.trello.com/1/boards/{board_id}/customFields"
    )

    fact = next(
        (c for c in campos if c["name"] == "FACT"),
        None
    )

    ent = next(
        (c for c in campos if c["name"] == "ENT"),
        None
    )

    if not fact or not ent:
        print("Falta FACT o ENT")
        continue

    tarjetas = get(
        f"https://api.trello.com/1/boards/{board_id}/cards",
        {"customFieldItems": "true"}
    )

    for tarjeta in tarjetas:

        card_id = tarjeta["id"]

        print(f"\nTarjeta: {tarjeta['name']}")

        # FACT = última modificación de la tarjeta
        fecha = tarjeta.get("dateLastActivity")

        if fecha:
            actualizar_fecha(
                card_id,
                fact["id"],
                fecha
            )

            print("FACT:", fecha)

        # ENT = persona de "ENTREGADO POR X"
        nombre = buscar_ent(card_id)

        if not nombre:
            print("Sin comentario ENTREGADO POR")
            continue

        # Buscar X entre las opciones de ENT
        opcion = next(
            (
                o for o in ent.get("options", [])
                if o.get("value", {}).get("text", "").strip().lower()
                == nombre.lower()
            ),
            None
        )

        if not opcion:
            print(f"No existe la opción ENT: {nombre}")
            continue

        # Actualizar ENT
        actualizar_opcion(
            card_id,
            ent["id"],
            opcion["id"]
        )

        print("ENT:", nombre)
