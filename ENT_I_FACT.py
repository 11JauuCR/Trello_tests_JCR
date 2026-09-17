import os
import re
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

P = {
    "key": os.getenv("TRELLO_API_KEY"),
    "token": os.getenv("TRELLO_TOKEN")
}

EXCLUIDAS = ["sub-orden", "archivar tarjeta"]


def get(url, params={}):
    r = requests.get(url, params={**P, **params})
    r.raise_for_status()
    return r.json()


def put(url, data):
    r = requests.put(url, params=P, json=data)
    r.raise_for_status()


def nombre(s):
    return re.sub(r"\s+", "", str(s)).lower()


# Buscar el tablero test y sus campos
tableros = get("https://api.trello.com/1/members/me/boards")
tablero = next(
    (b for b in tableros if nombre(b["name"]) == "test"),
    None
)

if not tablero:
    print("No se encuentra el tablero test")
    exit()

board_id = tablero["id"]
campos = get(f"https://api.trello.com/1/boards/{board_id}/customFields")

fact = next(
    (c for c in campos if nombre(c["name"]) == "fact"),
    None
)

ent = next(
    (c for c in campos if nombre(c["name"]) == "ent"),
    None
)

if not fact or not ent:
    print("No se encuentran FACT y ENT")
    print("Campos encontrados:", [c["name"] for c in campos])
    exit()

print(f"Tablero: {tablero['name']}")
print(f"FACT: {fact['id']}")
print(f"ENT: {ent['id']}")


def tiene_fecha(card, campo):
    for c in card.get("customFieldItems", []):
        if c.get("idCustomField") == campo["id"]:
            return bool(c.get("value", {}).get("date"))
    return False


def poner_fecha(card, campo, fecha):
    put(
        f"https://api.trello.com/1/cards/{card['id']}"
        f"/customField/{campo['id']}/item",
        {"value": {"date": fecha}}
    )


def fecha_entregado(card_id):
    acciones = get(
        f"https://api.trello.com/1/cards/{card_id}/actions",
        {"filter": "commentCard", "limit": 100}
    )

    fechas = [
        a["date"]
        for a in acciones
        if re.search(
            r"\bENTREGADO\s+POR\b",
            a.get("data", {}).get("text", ""),
            re.I
        ) and a.get("date")
    ]

    return max(
        fechas,
        key=lambda x: datetime.fromisoformat(
            x.replace("Z", "+00:00")
        )
    ) if fechas else None


# Listas archivadas
listas = get(
    f"https://api.trello.com/1/boards/{board_id}/lists",
    {"filter": "closed"}
)

for lista in listas:

    print(f"\nLista: {lista['name']}")

    # Desarchivar
    put(
        f"https://api.trello.com/1/lists/{lista['id']}",
        {"closed": False}
    )

    try:
        tarjetas = get(
            f"https://api.trello.com/1/lists/{lista['id']}/cards",
            {"filter": "all", "customFieldItems": "true"}
        )

        for card in tarjetas:

            etiquetas = [
                nombre(x.get("name", ""))
                for x in card.get("labels", [])
            ]

            if any(nombre(x) in etiquetas for x in EXCLUIDAS):
                print(f"[EXCLUIDA] {card['name']}")
                continue

            # FACT
            if not tiene_fecha(card, fact):
                poner_fecha(
                    card,
                    fact,
                    card["dateLastActivity"]
                )
                print(f"{card['name']} -> FACT")

            # ENT
            if not tiene_fecha(card, ent):
                fecha = fecha_entregado(card["id"])

                if fecha:
                    poner_fecha(card, ent, fecha)
                    print(f"{card['name']} -> ENT")

    finally:
        # Volver a archivar
        put(
            f"https://api.trello.com/1/lists/{lista['id']}",
            {"closed": True}
        )

print("\nProceso terminado")
