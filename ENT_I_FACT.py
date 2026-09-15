import os
import re
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

PARAMS = {
    "key": os.getenv("TRELLO_API_KEY"),
    "token": os.getenv("TRELLO_TOKEN")
}

TABLEROS = ["test1"]

ETIQUETAS_EXCLUIDAS = [
    "sub-orden",
    "archivar targeta"
]


def get(url, params=None):
    respuesta = requests.get(
        url,
        params={**PARAMS, **(params or {})}
    )
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


def tiene_fecha(tarjeta, campo_id):
    for campo in tarjeta.get("customFieldItems", []):
        if campo["idCustomField"] == campo_id:
            return bool(campo.get("value", {}).get("date"))

    return False


def buscar_fecha_entregado(card_id):
    acciones = get(
        f"https://api.trello.com/1/cards/{card_id}/actions",
        {
            "filter": "commentCard",
            "limit": 100
        }
    )

    fechas = []

    for accion in acciones:
        texto = accion["data"].get("text", "")

        if re.search(
            r"ENTREGADO\s+POR",
            texto,
            re.IGNORECASE
        ):
            fechas.append(accion["date"])

    if not fechas:
        return None

    return max(
        fechas,
        key=lambda fecha: datetime.fromisoformat(
            fecha.replace("Z", "+00:00")
        )
    )


tableros = get(
    "https://api.trello.com/1/members/me/boards"
)

for tablero in tableros:

    if tablero["name"] not in TABLEROS:
        continue

    board_id = tablero["id"]

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
        {
            "filter": "closed",
            "customFieldItems": "true"
        }
    )

    for tarjeta in tarjetas:

        # Solo cards archivadas
        if not tarjeta.get("closed"):
            continue

        # Ignorar SUB-ORDEN y ARCHIVAR TARGETA
        etiquetas = [
            e["name"].strip().lower()
            for e in tarjeta.get("labels", [])
        ]

        if any(
            etiqueta in ETIQUETAS_EXCLUIDAS
            for etiqueta in etiquetas
        ):
            continue

        card_id = tarjeta["id"]

        fact_relleno = tiene_fecha(
            tarjeta,
            fact["id"]
        )

        ent_relleno = tiene_fecha(
            tarjeta,
            ent["id"]
        )

        # Si los dos están rellenados, no modificar nada
        if fact_relleno and ent_relleno:
            continue

        # FACT = última modificación de la card
        if not fact_relleno:

            fecha = tarjeta.get("dateLastActivity")

            if fecha:
                actualizar_fecha(
                    card_id,
                    fact["id"],
                    fecha
                )

                print(
                    f"{tarjeta['name']} -> FACT: {fecha}"
                )

        # ENT = fecha del comentario "ENTREGADO POR..."
        if not ent_relleno:

            fecha = buscar_fecha_entregado(card_id)

            if fecha:
                actualizar_fecha(
                    card_id,
                    ent["id"],
                    fecha
                )

                print(
                    f"{tarjeta['name']} -> ENT: {fecha}"
                )

print("Proceso terminado")
