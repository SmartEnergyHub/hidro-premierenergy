import json
import requests
import sys

# =========================
# TELEGRAM
# =========================

TELEGRAM_BOT_TOKEN = "8467414975:AAEtcgGiNQBObqTIxgZEsxQw3tsDPb6pmG4"
TELEGRAM_CHAT_ID = "742829836"

# =========================
# LOAD TOKEN
# =========================

with open("/config/premier_energy/token.txt") as f:
    token = f.read().strip()

# =========================
# LOAD DATA
# =========================

with open("/config/premier_energy/data.json") as f:
    data = json.load(f)

# =========================
# ARGUMENT INDEX
# =========================

with open("/config/.storage/core.restore_state") as f:
    restore = json.load(f)

INDEX = None

for item in restore["data"]:

    if item["state"]["entity_id"] == "input_number.index_gaz_premier":

        INDEX = item["state"]["state"]
        break

if not INDEX:
    raise Exception("INDEX_NOT_FOUND")

# =========================
# CLEAN INDEX
# =========================

INDEX = int(float(INDEX))

# =========================
# PAYLOAD
# =========================

payload = {
    "index": str(INDEX),
    "locConsum": "PEYTRVIDE070133",
    "sursa": "portalClienti",
    "contract": "3000197492"
}

# =========================
# HEADERS
# =========================

headers = {
    "Premier-Auth": f"Bearer {token}",
    "Content-Type": "application/json"
}

# =========================
# REQUEST
# =========================

url = "https://peremierenergy-portalclient.azurewebsites.net/api/index"

response = requests.post(
    url,
    headers=headers,
    json=payload,
    timeout=30
)

# =========================
# DEBUG
# =========================

print("STATUS:")
print(response.status_code)

print("\nRESPONSE:")
print(response.text)

# =========================
# TELEGRAM MESSAGE
# =========================

if response.status_code == 200:

    msg = f"""
✅ INDEX GAZ TRIMIS

🔢 Index: {INDEX}

📨 Răspuns Premier:
{response.text}
"""

else:

    msg = f"""
❌ EROARE TRIMITERE INDEX

🔢 Index: {INDEX}

HTTP:
{response.status_code}

📨 Răspuns:
{response.text}
"""

# =========================
# SEND TELEGRAM
# =========================

telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

telegram_response = requests.post(
    telegram_url,
    data={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "disable_notification": False
    },
    timeout=30
)

print("\nTELEGRAM STATUS:")
print(telegram_response.status_code)

print("\nTELEGRAM RESPONSE:")
print(telegram_response.text)