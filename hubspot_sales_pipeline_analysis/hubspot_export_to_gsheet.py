import requests
import gspread
from google.oauth2.service_account import Credentials
import random
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from collections import defaultdict

# 🔐 Auth für Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

SPREADSHEET_NAME = "HubSpot - Sales Pipeline Analysis"
DEAL_TAB = "HubSpot - Deal"
COMPANY_TAB = "HubSpot - Company"
OWNER_TAB = "HubSpot - Deal Owner"

creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
client = gspread.authorize(creds)
deal_sheet = client.open(SPREADSHEET_NAME).worksheet(DEAL_TAB)

# 🔐 HubSpot Auth
load_dotenv()
ACCESS_TOKEN = os.getenv("HUBSPOT_API_KEY")
URL = "https://api.hubapi.com/crm/v3/objects/deals?limit=100&properties=company_name,dealname,amount,probability,dealstage,closedate,createdate,hubspot_owner_id&associations=companies"
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

DEAL_TYPE = ["newbusiness", "existingbusiness"]

# 🔹 Dummy-Daten für Deal Owners
DEAL_OWNERS = [
    "John Peterson", "Celine Dupont", "Margaret Wilson", "Charlotte Becker", "David Klein",
    "Andre Moreau", "Philip Schneider", "Emily Carter", "Lucas Hoffmann", "Anna Fischer",
    "Noah Müller", "Isabelle Lang", "Leon Weber", "Nina Schröder", "Tom Berger"
]
DEAL_OWNER_IDS = {name: i + 1001 for i, name in enumerate(DEAL_OWNERS)}

STAGE_PROBABILITIES = {
    "appointmentscheduled": 0.10,
    "qualifiedtobuy": 0.25,
    "presentationscheduled": 0.40,
    "decisionmakerboughtin": 0.60,
    "contractsent": 0.80,
    "closedwon": 1.00,
    "closedlost": 0.00
}
LEAD_SOURCES = ["Website", "Referral", "Outbound", "Email Campaign", "Social Media", "Inbound Lead", "Event", "Cold Call", "Referral Partner", "Content Marketing"]
INDUSTRIES = ["FMCG", "SaaS", "Healthcare", "Finance", "Retail", "Durable Goods", "Agency", "Mobility & Automotive"]
COMPANY_SIZES = ["Small", "Medium", "Enterprise"]
ICP_TIER = ["ICP 1", "ICP 2", "ICP 3"]

# Dictionaries zur Speicherung
companies = {}         # {our_company_id: {Company ID, Company Name, Industry, Company Size, Country, ICP Tier, Lifecycle Stage}}
owners = {}            # {owner_id: owner_name}
company_mapping = {}   # {company_name: {"company_id": x, "first_closed_won": False, "deal_count": 0}}
company_deals_map = defaultdict(list)  # {our_company_id: [final_stage1, final_stage2, ...]}

# Funktion: Generiere Stage History für einen Deal
# computed_deal_type wird extern berechnet
def generate_stage_history(deal, company_id, deal_id, computed_deal_type):
    deal_name = deal.get("dealname", "")
    company_name = deal.get("company_name", "")
    amount = deal.get("amount", "")
    create_date = deal.get("createdate", "")[:10]
    try:
        current_date = datetime.strptime(create_date, "%Y-%m-%d")
    except:
        return []
    selected_stages = random.choice([
        ["appointmentscheduled", "qualifiedtobuy", "presentationscheduled", "decisionmakerboughtin", "contractsent", "closedwon"],
        ["appointmentscheduled", "qualifiedtobuy", "closedlost"],
        ["appointmentscheduled", "qualifiedtobuy", "presentationscheduled", "closedlost"],
        ["appointmentscheduled", "qualifiedtobuy", "contractsent", "closedlost"],
        ["appointmentscheduled", "qualifiedtobuy", "presentationscheduled", "decisionmakerboughtin", "closedlost"],
        ["appointmentscheduled"],
        ["appointmentscheduled", "qualifiedtobuy"],
        ["appointmentscheduled", "qualifiedtobuy", "presentationscheduled"],
        ["appointmentscheduled", "qualifiedtobuy", "presentationscheduled", "decisionmakerboughtin"]
    ])
    deal_owner_name = random.choice(DEAL_OWNERS)
    owner_id = DEAL_OWNER_IDS[deal_owner_name]
    owners[owner_id] = deal_owner_name

    stage_rows = []
    previous_date = current_date
    entered_stage_dates = []
    for i, stage in enumerate(selected_stages):
        entered_stage_date = previous_date + timedelta(days=random.randint(2,25)) if i > 0 else current_date
        entered_stage_dates.append(entered_stage_date)
        previous_date = entered_stage_date
    for i, stage in enumerate(selected_stages):
        entered_stage_date = entered_stage_dates[i]
        next_date = entered_stage_dates[i+1] if i+1 < len(entered_stage_dates) else ""
        days_in_stage = (next_date - entered_stage_date).days if next_date else ""
        probability = STAGE_PROBABILITIES[stage]
        forecast_amount = round(float(amount)*probability,2) if amount else ""
        closed_date_value = entered_stage_date.strftime("%Y-%m-%d") if stage in ["closedwon", "closedlost"] else ""
        stage_rows.append([
            deal_id, company_id, owner_id, deal_name, amount, forecast_amount, probability, stage,
            computed_deal_type, closed_date_value, create_date if i==0 else "", entered_stage_date.strftime("%Y-%m-%d"),
            days_in_stage, "Sales Pipeline"
        ])
    return stage_rows

# Funktion: Lifecycle Stage Mapping basierend auf allen finalen Deal Stages
def map_to_lifecycle_stage(deal_stages):
    mapping = {
        "appointmentscheduled": "MQL",
        "qualifiedtobuy": "SQL",
        "presentationscheduled": "Opportunity",
        "decisionmakerboughtin": "Opportunity",
        "contractsent": "Opportunity",
        "closedwon": "Customer",
        "closedlost": "Disqualified"
    }
    for stage in reversed(deal_stages):
        if stage in mapping:
            return mapping[stage]
    return "MQL"

# API-Abfrage
deals = []
deal_id_counter = 1001  # Deal IDs beginnen bei 1001
company_id_counter = 1013  # Company IDs beginnen bei 1013
after = None

while True:
    url = URL + (f"&after={after}" if after else "")
    response = requests.get(url, headers=headers).json()
    for deal in response.get("results", []):
        props = deal["properties"]
        company_assoc = deal.get("associations", {}).get("companies", {}).get("results", [])
        company_name_from_deal = props.get("company_name", "").strip()
        if company_assoc:
            company_id_hs = company_assoc[0]["id"]
            company_resp = requests.get(
                f"https://api.hubapi.com/crm/v3/objects/companies/{company_id_hs}?properties=name",
                headers=headers
            ).json()
            company_name_from_deal = company_resp.get("properties", {}).get("name", "Unknown Company").strip()
        # Aufbau des Company Mappings: Jede Company (realer Name) nur einmal
        if company_name_from_deal not in company_mapping:
            company_mapping[company_name_from_deal] = {"company_id": company_id_counter, "first_closed_won": False, "deal_count": 0}
            companies[company_id_counter] = {
                "Company ID": company_id_counter,
                "Company Name": company_name_from_deal,
                "Industry": random.choice(INDUSTRIES),
                "Company Size": random.choice(COMPANY_SIZES),
                "Country": random.choice(["Germany", "France", "USA", "UK", "Australia", "Canada"]),
                "ICP Tier": random.choice(ICP_TIER),
                "Lifecycle Stage": ""  # wird später gesetzt
            }
            company_id = company_id_counter
            company_id_counter += 1
        else:
            company_id = company_mapping[company_name_from_deal]["company_id"]
        
        # Berechnung des Deal Typs:
        comp_info = company_mapping[company_name_from_deal]
        if comp_info["deal_count"] == 0:
            computed_deal_type = "newbusiness"
        else:
            computed_deal_type = "existingbusiness" if comp_info["first_closed_won"] else "newbusiness"
        
        stage_rows = generate_stage_history(props, company_id, deal_id_counter, computed_deal_type)
        if stage_rows:
            final_stage = stage_rows[-1][7]  # Index 7 = Deal Stage
            company_mapping[company_name_from_deal]["deal_count"] += 1
            if company_mapping[company_name_from_deal]["deal_count"] == 1 and final_stage == "closedwon":
                company_mapping[company_name_from_deal]["first_closed_won"] = True
            deals.extend(stage_rows)
            company_deals_map[company_id].append(final_stage)
            deal_id_counter += 1
    if not response.get("paging"):
        break
    after = response["paging"]["next"]["after"]

# Nachträgliche Berechnung der Lifecycle Stage für jede Company anhand aller Deal-Stages
for comp in companies.values():
    comp_id = comp["Company ID"]
    all_stages = company_deals_map[comp_id]
    comp["Lifecycle Stage"] = map_to_lifecycle_stage(all_stages)

# Google Sheets: Befüllen
deal_sheet.clear()
deal_sheet.append_row([
    "Deal ID", "Company ID", "Owner ID", "Deal Name", "Amount", "Forecast Amount", "Probability",
    "Deal Stage", "Deal Type", "Close Date", "Create Date", "Entered Stage Date", "Days in Stage", "Pipeline"
])
deal_sheet.append_rows(deals)

company_sheet = client.open(SPREADSHEET_NAME).worksheet(COMPANY_TAB)
company_sheet.clear()
company_sheet.append_row(["Company ID", "Company Name", "Industry", "Company Size", "Country", "ICP Tier", "Lifecycle Stage"])
company_sheet.append_rows([list(comp.values()) for comp in companies.values()])

owner_sheet = client.open(SPREADSHEET_NAME).worksheet(OWNER_TAB)
owner_sheet.clear()
owner_sheet.append_row(["Owner ID", "Deal Owner", "Department", "Team", "Region"])
owner_rows = []
for owner_id, owner_name in owners.items():
    owner_rows.append([
        owner_id, owner_name,
        random.choice(["Sales", "Account Management", "Enterprise Sales"]),
        random.choice(["Team A", "Team B", "Team C"]),
        random.choice(["EMEA", "AMER", "APAC"])
    ])
owner_sheet.append_rows(owner_rows)

print("✅ Alle drei Tabs wurden erfolgreich befüllt.")
