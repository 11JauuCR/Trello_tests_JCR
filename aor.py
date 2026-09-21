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


def put(url, json=None, **params):
    r = requests.put(url, params={**AUTH, **params}, json=json)
    r.raise_for_status()
    return r.json()


def fecha_creacion(card_id):
    try:
        fecha = int(card_id[:8], 16)
        return datetime.fromtimestamp(fecha, UTC)
    except:
        return None


def fecha_incorrecta(actual, real):
    if actual is None:
        return True

    return False


def buscar_tablero(nombre):
    tableros = get(f"{BASE}/members/me/boards")

    for tablero in tableros:
        if tablero["name"].lower() == nombre.lower():
            return tablero

    return None


def main():
    nombre = input("Tablero: ").strip()
    tablero = buscar_tablero(nombre)

    if not tablero:
        print("No se ha encontrado el tablero.")
        return

    print(f"\nTablero: {tablero['name']}\n")

    listas = get(
        f"{BASE}/boards/{tablero['id']}/lists",
        filter="all"
    )

    listas = [x for x in listas if x["closed"]]

    if not listas:
        print("No hay listas archivadas.")
        return

    print(f"Listas archivadas encontradas: {len(listas)}")

    campos = get(f"{BASE}/boards/{tablero['id']}/customFields")

    aor = None

    for campo in campos:
        if campo["name"].strip().upper() == "AOR":
            aor = campo
            break

    if not aor:
        print("No se ha encontrado el campo AOR.")
        return

    for lista in listas:
        print(f"\n=== Lista archivada: {lista['name']} ===")

        put(f"{BASE}/lists/{lista['id']}", closed="false")

        tarjetas = get(
            f"{BASE}/lists/{lista['id']}/cards",
            fields="name,labels",
            customFieldItems="true"
        )

        print(f"Tarjetas: {len(tarjetas)}")

        for tarjeta in tarjetas:
            nombre = tarjeta["name"]

            etiquetas = []
            for etiqueta in tarjeta.get("labels", []):
                etiquetas.append(
                    etiqueta.get("name", "").strip().lower()
                )

            if any(x in etiquetas for x in EXCLUIDAS):
                print(f"⏭️ {nombre} -> excluida")
                continue

            fecha_real = fecha_creacion(tarjeta["id"])

            if not fecha_real:
                print(f"⏭️ {nombre} -> sin fecha de creación")
                continue

            fecha_actual = None

            for item in tarjeta.get("customFieldItems", []):
                if item["idCustomField"] == aor["id"]:
                    fecha_actual = item.get("value", {}).get("date")
                    break

            if fecha_actual:
                fecha_actual = datetime.fromisoformat(
                    fecha_actual.replace("Z", "+00:00")
                )

            if fecha_incorrecta(fecha_actual, fecha_real):
                fecha = fecha_real.isoformat().replace("+00:00", "Z")

                try:
                    put(
                        f"{BASE}/cards/{tarjeta['id']}/customField/{aor['id']}/item",
                        json={"value": {"date": fecha}}
                    )

                    print(f"🔧 {nombre} -> corregida a {fecha}")

                except requests.HTTPError as e:
                    print(f"❌ {nombre} -> {e}")
            else:
                print(f"✔ {nombre} -> fecha correcta")

        put(f"{BASE}/lists/{lista['id']}", closed="true")

    print("\nTerminado.")


if __name__ == "__main__":
    main()
