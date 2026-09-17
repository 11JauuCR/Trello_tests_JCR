import os
import requests
from dotenv import load_dotenv
from datetime import datetime, UTC

load_dotenv()

KEY = os.getenv("TRELLO_API_KEY")
TOKEN = os.getenv("TRELLO_TOKEN")
BASE = "https://api.trello.com/1"
AUTH = {"key": KEY, "token": TOKEN}

EXCLUIDAS = ["sub-orden", "archivar targeta"]


def get(url, **params):
    r = requests.get(url, params={**AUTH, **params})
    r.raise_for_status()
    return r.json()


def fecha_creacion(card_id):
    ts_hex = card_id[:8]
    ts = int(ts_hex, 16)
    return datetime.fromtimestamp(ts, UTC).isoformat().replace("+00:00", "Z")


def buscar_tablero(nombre):
    for b in get(f"{BASE}/members/me/boards"):
        if b["name"].strip().lower() == nombre.strip().lower():
            return b


def elegir_lista(board_id):
    listas = get(f"{BASE}/boards/{board_id}/lists", filter="all")

    for i, l in enumerate(listas, 1):
        estado = " (archivada)" if l["closed"] else ""
        print(f"{i}. {l['name']}{estado}")

    while True:
        try:
            n = int(input("\nElige una lista: "))
            if 1 <= n <= len(listas):
                return listas[n - 1]
        except ValueError:
            pass

        print("Número no válido.")


def main():

    nombre = input("Tablero: ").strip()
    tablero = buscar_tablero(nombre)

    if not tablero:
        print("No se ha encontrado el tablero.")
        return

    print(f"\nTablero: {tablero['name']}\n")
    print("Listas:")

    lista = elegir_lista(tablero["id"])

    print(f"\nLista seleccionada: {lista['name']}")

    campos = get(f"{BASE}/boards/{tablero['id']}/customFields")

    aor = next(
        (
            x for x in campos
            if x["name"].strip().upper() == "AOR"
            and x["type"] == "date"
        ),
        None
    )

    if not aor:
        print("No se ha encontrado el campo AOR.")
        return

    tarjetas = get(
        f"{BASE}/lists/{lista['id']}/cards",
        fields="name,labels",
        customFieldItems="true"
    )

    print(f"Tarjetas: {len(tarjetas)}\n")

    for tarjeta in tarjetas:

        nombre = tarjeta["name"]

        etiquetas = [
            x.get("name", "").strip().lower()
            for x in tarjeta.get("labels", [])
        ]

        if any(x in etiquetas for x in EXCLUIDAS):
            print(f"⏭️ {nombre} -> excluida")
            continue

        tiene_aor = any(
            x["idCustomField"] == aor["id"]
            and x.get("value", {}).get("date")
            for x in tarjeta.get("customFieldItems", [])
        )

        if tiene_aor:
            print(f"⏭️ {nombre} -> AOR ya tiene fecha")
            continue

        fecha = fecha_creacion(tarjeta["id"])

        try:
            requests.put(
                f"{BASE}/cards/{tarjeta['id']}/customField/{aor['id']}/item",
                params=AUTH,
                json={"value": {"date": fecha}}
            ).raise_for_status()

            print(f"✅ {nombre} -> {fecha}")

        except requests.HTTPError as e:
            print(f"❌ {nombre} -> {e}")

    print("\nTerminado.")


if __name__ == "__main__":
    main()
