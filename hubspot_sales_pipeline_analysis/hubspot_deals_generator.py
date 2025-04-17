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

# 🔹 Deal Probabilities
STAGE_PROBABILITIES = {
    "appointmentscheduled": 0.10,
    "qualifiedtobuy": 0.25,
    "presentationscheduled": 0.40,
    "decisionmakerboughtin": 0.60,
    "contractsent": 0.80,
    "closedwon": 1.00,
    "closedlost": 0.00
}

# 🔹 Possible Deal Types in HubSpot 
DEAL_TYPES = [
    "newbusiness", # 1. New Business Deal - New Logo
    "existingbusiness" # 2. Existing Business Deal - Existing Logo
]

# 🔹 Generate Deals
for i in range(1000):
    deal_name = f"Deal {i+1}"
    amount = random.randint(500, 20000)  # Random amount between 500€ and 20,000€
    stage = random.choice(DEAL_STAGES)  # Randomly select a deal stage
    probability = STAGE_PROBABILITIES[stage]
    forecast_amount = round(amount * probability, 2)
    
    # Generate a random close date within the last 90 days
    days_ago = random.randint(1, 90)
    days_offset = random.randint(5, 20)
    close_date_obj = datetime.now() - timedelta(days=days_ago)
    create_date_obj = close_date_obj - timedelta(days=days_offset)
    create_date = create_date_obj.strftime("%Y-%m-%d")
    close_date = close_date_obj.strftime("%Y-%m-%d")

    deal_type = random.choice(DEAL_TYPES)

    deal_data = {
    "properties": {
        "dealname": deal_name,
        "amount": str(amount),  # No commas here
        "probability_amount": str(forecast_amount),
        "probability": float(probability),
        "dealstage": stage,
        "dealtype": deal_type,
        "closedate": close_date,
        "createdate": create_date,
        "pipeline": "default"
    }
}

    response = requests.post(URL, json=deal_data, headers=HEADERS)
    
    # Print status
    if response.status_code == 201:
        print(f"✅ Deal {i+1} created: {deal_name} - {amount}€ - {forecast_amount}€ - {probability} - {stage} - {deal_type} - {close_date} - {create_date}")
    else:
        print(f"❌ Error with Deal {i+1}: {response.status_code} - {response.text}")
