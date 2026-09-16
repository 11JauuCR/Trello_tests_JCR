import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TRELLO_API_KEY")
TOKEN = os.getenv("TRELLO_TOKEN")

URL = "https://api.trello.com/1"

PARAMS = {
    "key": API_KEY,
    "token": TOKEN
}

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


def buscar_tablero(nombre):
    tableros = get(
        f"{URL}/members/me/boards"
    )

    for tablero in tableros:
        if tablero["name"].strip().lower() == nombre.strip().lower():
            return tablero["id"]

    return None


def actualizar_aor(card_id, campo_id, fecha):
    url = (
        f"{URL}/cards/{card_id}"
        f"/customField/{campo_id}/item"
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


def tiene_etiqueta_excluida(tarjeta):
    for etiqueta in tarjeta.get("labels", []):

        nombre = etiqueta["name"].strip().lower()

        if nombre in ETIQUETAS_EXCLUIDAS:
            return True

    return False


def main():

    if not API_KEY or not TOKEN:
        print("Faltan la API key o el token en el .env")
        return

    nombre_tablero = input(
        "Introduce el nombre del tablero: "
    ).strip()

    board_id = buscar_tablero(nombre_tablero)

    if not board_id:
        print(
            f"No se ha encontrado el tablero "
            f"'{nombre_tablero}'"
        )
        return

    print(f"Tablero encontrado: {board_id}")

    campos = get(
        f"{URL}/boards/{board_id}/customFields"
    )

    aor = None

    for campo in campos:
        if campo["name"].strip().upper() == "AOR":
            aor = campo
            break

    if not aor:
        print("No se ha encontrado el campo AOR")
        return

    if aor["type"] != "date":
        print("El campo AOR no es de tipo fecha")
        return

    print(f"Campo AOR encontrado: {aor['id']}")

    tarjetas = get(
        f"{URL}/boards/{board_id}/cards",
        {
            "fields": "name,start,labels",
            "customFieldItems": "true"
        }
    )

    print(f"Tarjetas encontradas: {len(tarjetas)}")
    print()

    for tarjeta in tarjetas:

        nombre = tarjeta["name"]
        card_id = tarjeta["id"]

        # Saltar tarjetas con etiquetas excluidas
        if tiene_etiqueta_excluida(tarjeta):
            print(
                f"⏭️ {nombre} -> tarjeta excluida"
            )
            continue

        # Si AOR ya tiene una fecha, no hacer nada
        if tiene_fecha(tarjeta, aor["id"]):
            print(
                f"⏭️ {nombre} -> AOR ya tiene fecha"
            )
            continue

        # Obtener fecha de inicio
        fecha_inicio = tarjeta.get("start")

        if not fecha_inicio:
            print(
                f"⏭️ {nombre} -> sin fecha de inicio"
            )
            continue

        try:

            actualizar_aor(
                card_id,
                aor["id"],
                fecha_inicio
            )

            print(
                f"✅ {nombre} -> "
                f"AOR: {fecha_inicio}"
            )

        except requests.HTTPError as error:

            print(
                f"❌ {nombre} -> "
                f"error: {error}"
            )

    print()
    print("Proceso terminado.")


if __name__ == "__main__":
    main()