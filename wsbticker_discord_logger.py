import requests
import time

WEBHOOK_URL = "https://discord.com/api/webhooks/1434574084850843840/A0g7thttJeNJ2r0vXeFiJCXK3kkCkV_0ld6EUoxv185U3mz9DYI9fM9vT4845LoAsdK4"  # <-- Pon aquí tu URL de webhook

def send_log_to_discord(message):
    data = {"content": message}
    try:
        response = requests.post(WEBHOOK_URL, json=data)
        if response.status_code != 204:
            print(f"Error enviando a Discord: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Excepción enviando a Discord: {e}")

def log(message):
    print(message)              # Muestra el log en la consola
    send_log_to_discord(message) # Envía el log a Discord

if __name__ == "__main__":
    # Ejemplo de uso
    log("Bot iniciado correctamente.")
    for i in range(5):
        log(f"Log número {i+1}")
        time.sleep(1)  # Simula actividad
    log("Bot finalizado.")
