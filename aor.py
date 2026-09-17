import os
import requests
from dotenv import load_dotenv
from datetime import datetime, UTC

# Carrego variables del .env
load_dotenv()

KEY = os.getenv("TRELLO_API_KEY")
TOKEN = os.getenv("TRELLO_TOKEN")
BASE = "https://api.trello.com/1"
AUTH = {"key": KEY, "token": TOKEN}

# Etiquetes que no vull processar
EXCLUIDAS = ["sub-orden", "archivar targeta"]


def get(url, **params):
    """GET bàsic amb autenticació."""
    r = requests.get(url, params={**AUTH, **params})
    r.raise_for_status()
    return r.json()


def put(url, json=None, **params):
    """PUT bàsic amb autenticació i suport per JSON."""
    r = requests.put(url, params={**AUTH, **params}, json=json)
    r.raise_for_status()
    return r.json()


def fecha_creacion_real(card_id):
    """
    Trello no sempre guarda la data de creació al ID,
    així que agafo la data real de l'acció createCard.
    """
    acciones = get(
        f"{BASE}/cards/{card_id}/actions",
        filter="createCard",
        limit=1000  
    )

    for a in acciones:
        if a["type"] == "createCard":
            return a["date"]

    return None


def parse_fecha(fecha_str):
    """Converteix ISO a datetime. Si falla, retorno None."""
    try:
        return datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
    except:
        return None


def fecha_incorrecta(fecha_actual, fecha_real):
    """
    Comprovo si la data AOR és incorrecta.
    Criteris simples però útils.
    """
    if fecha_actual is None:
        return True

    # Data futura → incorrecta
    if fecha_actual > datetime.now(UTC):
        return True

    # Trello no existia abans del 2010
    if fecha_actual.year < 2010:
        return True

    # Si la data AOR és posterior a la creació real → incorrecta
    if fecha_actual > fecha_real:
        return True

    return False


def buscar_tablero(nombre):
    """Retorno el tauler pel nom."""
    for b in get(f"{BASE}/members/me/boards"):
        if b["name"].strip().lower() == nombre.strip().lower():
            return b


def main():

    nombre = input("Tablero: ").strip()
    tablero = buscar_tablero(nombre)

    if not tablero:
        print("No se ha encontrado el tablero.")
        return

    print(f"\nTablero: {tablero['name']}\n")

    # Només vull les llistes arxivades
    listas_archivadas = [
        l for l in get(f"{BASE}/boards/{tablero['id']}/lists", filter="all")
        if l["closed"] is True
    ]

    if not listas_archivadas:
        print("No hay listas archivadas.")
        return

    print(f"Listas archivadas encontradas: {len(listas_archivadas)}")

    campos = get(f"{BASE}/boards/{tablero['id']}/customFields")

    # Busco el camp AOR
    aor = next(
        (x for x in campos if x["name"].strip().upper() == "AOR"),
        None
    )

    if not aor:
        print("No se ha encontrado el campo AOR.")
        return

    print(f"\nCampo AOR detectado como tipo: {aor['type']}\n")

    for lista in listas_archivadas:

        print(f"\n=== Lista archivada: {lista['name']} ===")

        # Desarxivo per poder modificar
        print("Desarchivando lista...")
        put(f"{BASE}/lists/{lista['id']}", closed="false")

        tarjetas = get(
            f"{BASE}/lists/{lista['id']}/cards",
            fields="name,labels",
            customFieldItems="true"
        )

        print(f"Tarjetas: {len(tarjetas)}")

        for tarjeta in tarjetas:

            nombre = tarjeta["name"]

            # Si té alguna etiqueta exclosa, la salto
            etiquetas = [
                x.get("name", "").strip().lower()
                for x in tarjeta.get("labels", [])
            ]

            if any(x in etiquetas for x in EXCLUIDAS):
                print(f"⏭️ {nombre} -> excluida")
                continue

            # Data real de creació
            fecha_real_str = fecha_creacion_real(tarjeta["id"])
            if not fecha_real_str:
                print(f"⏭️ {nombre} -> sin fecha de creación")
                continue

            fecha_real_dt = parse_fecha(fecha_real_str)

            # Data actual del camp AOR
            fecha_actual_str = None
            for item in tarjeta.get("customFieldItems", []):
                if item["idCustomField"] == aor["id"]:
                    fecha_actual_str = item.get("value", {}).get("date")

            fecha_actual_dt = parse_fecha(fecha_actual_str) if fecha_actual_str else None

            # Validació
            if fecha_incorrecta(fecha_actual_dt, fecha_real_dt):
                payload = {"value": {"date": fecha_real_str}}
                try:
                    put(
                        f"{BASE}/cards/{tarjeta['id']}/customField/{aor['id']}/item",
                        json=payload
                    )
                    print(f"🔧 {nombre} -> corregida a {fecha_real_str}")
                except requests.HTTPError as e:
                    print(f"❌ {nombre} -> {e}")
            else:
                print(f"✔ {nombre} -> fecha correcta, no se modifica")

        # Torno a arxivar la llista
        print("Archivando lista...")
        put(f"{BASE}/lists/{lista['id']}", closed="true")

    print("\nTerminado.")


if __name__ == "__main__":
    main()
