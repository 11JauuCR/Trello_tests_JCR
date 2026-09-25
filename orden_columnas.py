import os
import time
import requests
from threading import Thread
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TRELLO_API_KEY")
TOKEN = os.getenv("TRELLO_TOKEN")

app = Flask(__name__)


@app.route("/trello", methods=["HEAD"])
def verificar():
    return "", 200


@app.route("/trello", methods=["POST"])
def recibir():
    datos = request.get_json()

    print("\n--- Evento recibido ---")

    if datos:
        accion = datos.get("action", {})
        tipo = accion.get("type")
        data = accion.get("data", {})

        print("Tipo:", tipo)
        print("Datos:", data)

        if tipo == "updateList":
            print("Se ha modificado una lista")

        if tipo == "updateCard":
            print("Se ha modificado una tarjeta")

    return "", 200


def iniciar_servidor():
    app.run(
        host="0.0.0.0",
        port=5001,
        debug=False,
        use_reloader=False
    )


def get_tableros():
    respuesta = requests.get(
        "https://api.trello.com/1/members/me/boards",
        params={
            "key": API_KEY,
            "token": TOKEN
        }
    )

    if respuesta.status_code != 200:
        print("Error:", respuesta.text)
        return []

    return respuesta.json()


def crear_webhook(board_id, url):
    respuesta = requests.post(
        "https://api.trello.com/1/webhooks",
        params={
            "key": API_KEY,
            "token": TOKEN,
            "idModel": board_id,
            "callbackURL": url,
            "description": "Control orden listas"
        }
    )

    print("\nRespuesta:", respuesta.status_code)

    if respuesta.status_code != 200:
        print(respuesta.text)

    return respuesta.status_code == 200


if __name__ == "__main__":

    if not API_KEY or not TOKEN:
        print("Faltan las claves de Trello en el .env")
        exit()

    Thread(
        target=iniciar_servidor,
        daemon=True
    ).start()

    time.sleep(2)

    print("\nServidor iniciado")
    print("http://localhost:5001/trello")

    tableros = get_tableros()

    if not tableros:
        print("No se han encontrado tableros")
        exit()

    print("\nTableros:")

    for tablero in tableros:
        print("-", tablero["name"])

    nombre = input("\nNombre del tablero: ").strip()

    tablero = None

    for t in tableros:
        if t["name"].lower() == nombre.lower():
            tablero = t
            break

    if tablero is None:
        print("No se ha encontrado el tablero")
        exit()

    print("\nTablero:", tablero["name"])
    print("ID:", tablero["id"])

    cloudflare = input("\nURL de Cloudflare: ").strip().rstrip("/")
    url = cloudflare + "/trello"

    print("\nWebhook:", url)

    if crear_webhook(tablero["id"], url):
        print("Webhook creado correctamente")
        print("Mueve una lista o tarjeta para probarlo")

    while True:
        time.sleep(1)