import requests
import json
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# 🔐 Load .env file
load_dotenv()
ACCESS_TOKEN = os.getenv("HUBSPOT_API_KEY")

# Ensure that the API key is loaded
if not ACCESS_TOKEN:
    raise ValueError("HubSpot API Key not found. Please set the HUBSPOT_API_KEY in your .env file.")

URL = "https://api.hubapi.com/crm/v3/objects/deals"

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

# 🔹 Possible Deal Stages in HubSpot
DEAL_STAGES = [
    "appointmentscheduled",  # 1. Appointment scheduled
    "qualifiedtobuy",        # 2. Qualified to buy
    "presentationscheduled", # 3. Presentation scheduled
    "decisionmakerboughtin", # 4. Decision maker bought in
    "contractsent",          # 5. Contract sent
    "closedwon",             # 6. Deal won
    "closedlost"             # 7. Deal lost
]

# 🔹 Generate 200 Deals
for i in range(200):
    deal_name = f"Deal {i+1}"
    amount = random.randint(500, 20000)  # Random amount between 500€ and 20,000€
    formatted_amount = f"{amount:,}".replace(",", ".")  # Format amount with thousands separator
    stage = random.choice(DEAL_STAGES)  # Randomly select a deal stage
    
    # Generate a random close date within the last 90 days
    days_ago = random.randint(1, 90)
    close_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

    deal_data = {
    "properties": {
        "dealname": deal_name,
        "amount": str(formatted_amount),  # No commas here
        "dealstage": stage,
        "closedate": close_date,
        "pipeline": "default"
    }
}

    response = requests.post(URL, json=deal_data, headers=HEADERS)
    
    # Print status
    if response.status_code == 201:
        print(f"✅ Deal {i+1} created: {deal_name} - {formatted_amount}€ - {stage} - {close_date}")
    else:
        print(f"❌ Error with Deal {i+1}: {response.status_code} - {response.text}")
