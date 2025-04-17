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
    "appointmentscheduled",
    "qualifiedtobuy",
    "presentationscheduled",
    "decisionmakerboughtin",
    "contractsent",
    "closedwon",
    "closedlost"
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

# 🔹 Fake Company Names
COMPANY_NAMES = [
    "Innovative Solutions Inc.",
    "GlobalTech Industries",
    "NextGen Enterprises",
    "CyberCore Technologies",
    "Vanguard Digital Group",
    "Apex Analytics",
    "Fusion Strategies",
    "Bright Horizons Media",
    "Quantum Innovations Ltd.",
    "Peak Performance Consulting",
    "Pioneer Systems",
    "Elevate Global Ventures",
    "BlueWave Technologies",
    "SilverPeak Consulting",
    "CoreVision Solutions",
    "Starpoint International",
    "GreenTech Innovations",
    "SmartEdge Software",
    "Pathfinder Solutions",
    "DataLink Global",
    "FutureX Industries",
    "BlueSky Enterprises",
    "Velocity Ventures",
    "TechnoBridge Networks",
    "OmniCore Technologies",
    "TrueNorth Innovations",
    "NovaFusion Inc.",
    "Zenith Data Solutions",
    "Summit Strategies",
    "PrimeTech Solutions"
]

# 🔹 Deal Name Variations
DEAL_NAME_VARIATIONS = [
    "New Business Proposal",
    "Service Agreement",
    "Strategic Partnership",
    "Consulting Opportunity",
    "Technology Integration",
    "Expansion Contract",
    "Investment Deal",
    "Joint Venture",
    "Growth Opportunity",
    "Acquisition Negotiations",
    "Renewal Proposal",
    "Collaborative Partnership",
    "Exclusive Offer",
    "Exclusive Licensing Deal",
    "Sales Expansion",
    "Strategic Alliance",
    "Business Development Proposal",
    "Long-Term Partnership",
    "Custom Solution",
    "New Market Entry",
    "Merger Proposal",
    "Contract Renewal",
    "Consulting Engagement",
    "Market Expansion Proposal"
]

# 🔹 Generate Deals
companies = {}  # Dictionary to store companies and their deals

for i in range(100):
    company_name = random.choice(COMPANY_NAMES)

    # Create a company entry if it doesn't exist
    if company_name not in companies:
        companies[company_name] = {"deals": []}

    # Determine deal type based on previous deals
    company_deals = companies[company_name]["deals"]
    deal_name = f"{random.choice(DEAL_NAME_VARIATIONS)}"
    amount = random.randint(500, 50000)
    stage = random.choice(DEAL_STAGES)
    probability = STAGE_PROBABILITIES[stage]
    forecast_amount = round(amount * probability, 2)

    days_ago = random.randint(1, 90)
    days_offset = random.randint(5, 20)
    close_date_obj = datetime.now() - timedelta(days=days_ago)
    create_date_obj = close_date_obj - timedelta(days=days_offset)
    create_date = create_date_obj.strftime("%Y-%m-%d")
    close_date = close_date_obj.strftime("%Y-%m-%d")

    # If there are existing deals, we now allow open deals in addition to closed deals
    if not company_deals:
        # First deal for this company: open or closed-won
        dealstage = random.choice([s for s in DEAL_STAGES if s != "closedlost"])  # Exclude "closedlost" for the first deal
    else:
        # If there are deals, we will include open deals regardless of closed-won or closed-lost deals
        closed_won_deals = [deal for deal in company_deals if deal['dealstage'] == "closedwon"]
        closed_lost_deals = [deal for deal in company_deals if deal['dealstage'] == "closedlost"]
        
        if closed_won_deals:
            # If the company already has a closed-won deal, create another open deal
            dealstage = random.choice([s for s in DEAL_STAGES if s != "closedwon" and s != "closedlost"])  # Avoid "closedwon" and "closedlost"
        else:
            # If the company has no closed-won deal, create an open deal
            dealstage = random.choice([s for s in DEAL_STAGES if s != "closedlost"])  # Avoid "closedlost"
        
    deal_data = {
        "properties": {
            "dealname": deal_name,
            "amount": str(amount),
            "probability_amount": str(forecast_amount),
            "probability": float(probability),
            "dealstage": dealstage,
            "closedate": close_date,
            "createdate": create_date,
            "company_name": company_name,
            "pipeline": "default"
        }
    }

    # Add the generated deal to the company
    company_deals.append(deal_data["properties"])

    # Send request to HubSpot API
    response = requests.post(URL, json=deal_data, headers=HEADERS)

    if response.status_code == 201:
        print(f"✅ Deal {i+1} created: {deal_name} - {amount}€ - {forecast_amount}€ - {probability} - {dealstage} - {company_name} - {close_date} - {create_date}")
    else:
        print(f"❌ Error with Deal {i+1}: {response.status_code} - {response.text}")
