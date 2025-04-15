import requests
import json
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# 🔐 .env laden
load_dotenv()
ACCESS_TOKEN = os.getenv("HUBSPOT_API_KEY")

URL = "https://api.hubapi.com/crm/v3/objects/deals"

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

# 🔹 Mögliche Deal-Stages in HubSpot
DEAL_STAGES = [
    "appointmentscheduled",  # 1. Erstgespräch geplant
    "qualifiedtobuy",        # 2. Qualifiziert
    "presentationscheduled", # 3. Angebot gesendet
    "decisionmakerboughtin", # 4. In Verhandlung
    "contractsent",          # 5. Contact Sent            
    "closedwon",             # 6. Deal gewonnen
    "closedlost"             # 7. Deal verloren
]

# 🔹 200 Deals generieren
for i in range(2):
    deal_name = f"Deal {i+1}"
    amount = random.randint(500, 20000)  # Zufälliger Betrag zwischen 500€ und 20.000€
    stage = random.choice(DEAL_STAGES)  # Zufällige Deal-Stage auswählen
    
    # Zufälliges Erstellungsdatum in den letzten 90 Tagen
    days_ago = random.randint(1, 90)
    close_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

    deal_data = {
        "properties": {
            "dealname": deal_name,
            "amount": str(amount),
            "dealstage": stage,
            "closedate": close_date,
            "pipeline": "default"
        }
    }

    response = requests.post(URL, json=deal_data, headers=HEADERS)
    
    # Status ausgeben
    if response.status_code == 201:
        print(f"✅ Deal {i+1} erstellt: {deal_name} - {amount}€ - {stage} - {close_date}")
    else:
        print(f"❌ Fehler bei Deal {i+1}: {response.text}")
