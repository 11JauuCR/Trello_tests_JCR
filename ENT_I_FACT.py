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
    "archivar tarjeta"
]


def get(url, params=None):
    respuesta = requests.get(
        url,
        params={**PARAMS, **(params or {})}
    )
    respuesta.raise_for_status()
    return respuesta.json()


def actualizar_fecha(card_id, campo_id, fecha):
    url = (
        f"https://api.trello.com/1/cards/"
        f"{card_id}/customField/{campo_id}/item"
    )

    respuesta = requests.put(
        url,
        params=PARAMS,
        json={
            "value": {
                "date": fecha
            }
        }
    )

    respuesta.raise_for_status()


def tiene_fecha(tarjeta, campo_id):
    for campo in tarjeta.get("customFieldItems", []):
        if campo["idCustomField"] == campo_id:
            return bool(
                campo.get("value", {}).get("date")
            )

    return False


def buscar_fecha_entregado(card_id):
    """
    Busca el último comentario que contenga:
    
        ENTREGADO POR X
    
    y devuelve la fecha de ese comentario.
    """

    acciones = get(
        f"https://api.trello.com/1/cards/{card_id}/actions",
        {
            "filter": "commentCard",
            "limit": 100
        }
    )

    comentarios_entregado = []

    for accion in acciones:

        texto = accion.get("data", {}).get("text", "")

        # Busca "ENTREGADO POR" independientemente
        # de mayúsculas/minúsculas.
        if re.search(
            r"\bENTREGADO\s+POR\b",
            texto,
            re.IGNORECASE
        ):
            fecha_comentario = accion.get("date")

            if fecha_comentario:
                comentarios_entregado.append(
                    fecha_comentario
                )

    if not comentarios_entregado:
        return None

    # Nos quedamos con el comentario más reciente
    return max(
        comentarios_entregado,
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

    print(f"\nProcesando tablero: {tablero['name']}")

    # -----------------------------------------
    # CAMPOS PERSONALIZADOS
    # -----------------------------------------

    campos = get(
        f"https://api.trello.com/1/boards/"
        f"{board_id}/customFields"
    )

    fact = next(
        (
            c for c in campos
            if c["name"].strip().upper() == "FACT"
        ),
        None
    )

    ent = next(
        (
            c for c in campos
            if c["name"].strip().upper() == "ENT"
        ),
        None
    )

    if not fact or not ent:
        print("Falta FACT o ENT")
        continue

    # Comprobar que ENT es realmente un campo de fecha
    if ent["type"] != "date":
        print(
            f"El campo ENT no es de tipo fecha. "
            f"Tipo encontrado: {ent['type']}"
        )
        continue

    # -----------------------------------------
    # TARJETAS ARCHIVADAS
    # -----------------------------------------

    tarjetas = get(
        f"https://api.trello.com/1/boards/"
        f"{board_id}/cards",
        {
            "filter": "closed",
            "customFieldItems": "true"
        }
    )

    for tarjeta in tarjetas:

        # Solo cards archivadas
        if not tarjeta.get("closed"):
            continue

        # -----------------------------------------
        # ETIQUETAS EXCLUIDAS
        # -----------------------------------------

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

        # -----------------------------------------
        # COMPROBAR FACT Y ENT
        # -----------------------------------------

        fact_relleno = tiene_fecha(
            tarjeta,
            fact["id"]
        )

        ent_relleno = tiene_fecha(
            tarjeta,
            ent["id"]
        )

        # -----------------------------------------
        # FACT
        # Última modificación de la tarjeta
        # -----------------------------------------

        if not fact_relleno:

            fecha_fact = tarjeta.get(
                "dateLastActivity"
            )

            if fecha_fact:

                actualizar_fecha(
                    card_id,
                    fact["id"],
                    fecha_fact
                )

                print(
                    f"{tarjeta['name']} -> "
                    f"FACT: {fecha_fact}"
                )

        # -----------------------------------------
        # ENT
        # Fecha del comentario "ENTREGADO POR..."
        # -----------------------------------------

        if not ent_relleno:

            fecha_ent = buscar_fecha_entregado(
                card_id
            )

            if fecha_ent:

                actualizar_fecha(
                    card_id,
                    ent["id"],
                    fecha_ent
                )

                print(
                    f"{tarjeta['name']} -> "
                    f"ENT: {fecha_ent}"
                )

            else:

                print(
                    f"{tarjeta['name']} -> "
                    f"ENT: no encontrado"
                )


print("\nProceso terminado")
