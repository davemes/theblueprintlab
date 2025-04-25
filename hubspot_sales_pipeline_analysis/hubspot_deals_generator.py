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
    "sql",
    "appointmentscheduled",
    "qualifiedtobuy",
    "presentationscheduled",
    "decisionmakerboughtin",
    "contractsent",
    "closedwon",
    "closedlost"
]

# 🔹 Deal Types
DEAL_TYPE = ["newbusiness"]

# 🔹 Deal Probabilities
STAGE_PROBABILITIES = {
    "sql": 0.05,
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
    "PrimeTech Solutions",
    "Orbitra Digital",
    "Veridex Ventures",
    "Brightforge Innovations",
    "Quantico Metrics",
    "Stratosync Systems",
    "Lumeno Labs",
    "Zenithon Consulting",
    "Corevista Technologies",
    "Blueleaf Analytics",
    "Nexora Solutions"
]

# 🔹 Deal Name Variations
DEAL_NAME_VARIATIONS = [
    "Onboarding – CloudOps Starter Package",
    "Infrastructure Audit & Optimization",
    "Managed IT Services – Annual Contract",
    "Custom API Integration",
    "Enterprise Monitoring Setup",
    "Cybersecurity Bundle",
    "DevOps Automation Rollout",
    "Private Cloud Migration",
    "License Expansion – ProSecure SaaS Suite",
    "ITSM Implementation",
    "Q2 Service Extension",
    "Cloud Cost Optimization Sprint",
    "Multi-Tenant Setup – SecureAccess Platform",
    "Infrastructure-as-Code Workshop",
    "Platform Uptime SLA Upgrade",
    "Cloud Data Integration – Custom Solutions",
    "SaaS Migration & Implementation",
    "IT Infrastructure Automation",
    "Cyber Defense Enhancement",
    "Platform Customization",
    "24/7 Support Package – IT Operations",
    "Cloud Backup & Disaster Recovery",
    "Hybrid Cloud Deployment – Enterprise Solution",
    "License Renewal – Premium Plan",
    "AI-Powered Analytics Integration – DeepData Insights",
    "Infrastructure Optimization & Scaling – GrowthTier SaaS",
    "Enterprise Solution Package – SaaS Integration",
    "Security Audit & Compliance – GDPR Readiness",
    "API Management & Gateway Setup – RedShift Networks",
    "Data Warehousing Setup – Cloud-based Reporting"
]

# 🔹 Generate Deals
companies = {}  # Dictionary to store companies and their deals

for i in range(1500):  # Loop to generate 100 deals
    company_name = random.choice(COMPANY_NAMES)

    # Create a company entry if it doesn't exist
    if company_name not in companies:
        companies[company_name] = {"deals": []}

    # 🔹 Determine deal type based on previous deals
    company_deals = companies[company_name]["deals"]
    deal_name = f"{random.choice(DEAL_NAME_VARIATIONS)}"
    amount = random.randint(500, 50000)

    days_ago = random.randint(1, 60)
    days_offset = random.randint(5, 30)
    close_date_obj = datetime.now() - timedelta(days=days_ago)
    create_date_obj = close_date_obj - timedelta(days=days_offset)
    create_date = create_date_obj.strftime("%Y-%m-%d")
    close_date = close_date_obj.strftime("%Y-%m-%d")
    deal_stage_sales = random.choice(DEAL_STAGES)
    probability = STAGE_PROBABILITIES[deal_stage_sales]
    forecast_amount = round(amount * probability, 2)
    deal_type = random.choice(DEAL_TYPE)

    # 🔹 Assemble deal
    deal_data = {
        "properties": {
            "dealname": deal_name,
            "amount": str(amount),
            "probability_amount": str(forecast_amount),
            "probability": float(probability),
            "deal_stage_sales": deal_stage_sales,
            "closedate": close_date,
            "createdate": create_date,
            "company_name": company_name,
            "pipeline": "default",
            "dealtype": deal_type
        }
    }

    # 🔹 Append the full deal to the company's deals
    company_deals.append(deal_data)

    # Send request to HubSpot API
    response = requests.post(URL, json=deal_data, headers=HEADERS)

    if response.status_code == 201:
        print(f"✅ Deal {i+1} created: {deal_name} - {amount}€ - {forecast_amount}€ - {probability} - {deal_type} - {deal_stage_sales} - {company_name} - {close_date} - {create_date}")
    else:
        print(f"❌ Error with Deal {i+1}: {response.status_code} - {response.text}")
