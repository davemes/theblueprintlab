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
CREDS_FILE = "hs-sales-pipeline-analysis-0d212e642d40.json"
SPREADSHEET_NAME = "HubSpot - Sales Pipeline Analysis"
DEAL_TAB = "HubSpot - Deal"
COMPANY_TAB = "HubSpot - Company"
OWNER_TAB = "HubSpot - Sales Reps"

creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
client = gspread.authorize(creds)
deal_sheet = client.open(SPREADSHEET_NAME).worksheet(DEAL_TAB)

# 🔐 HubSpot Auth
load_dotenv()
ACCESS_TOKEN = os.getenv("HUBSPOT_API_KEY")
URL = "https://api.hubapi.com/crm/v3/objects/deals?limit=100&properties=company_name,dealname,amount,probability,deal_type,deal_stage_sales,closedate,createdate,hubspot_owner_id&associations=companies"
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}
# Deal Types
DEAL_TYPE = ["newbusiness", "existingbusiness"]

# 🔹 Dummy-Daten für Deal Owners
SALES_REPS = [
    "John Peterson", "Celine Dupont", "Margaret Wilson", "Charlotte Becker", "David Klein",
    "Andre Moreau", "Philip Schneider", "Emily Carter", "Lucas Hoffmann", "Anna Fischer",
    "Noah Müller", "Isabelle Lang", "Leon Weber", "Nina Schröder", "Tom Berger"
]
SALES_REPS_IDS = {name: i + 1001 for i, name in enumerate(SALES_REPS)}

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
LEAD_SOURCES = ["Website", "Referral", "Outbound", "Email Campaign", "Social Media", "Inbound Lead", "Event", "Cold Call", "Referral Partner", "Content Marketing"]
INDUSTRIES = ["FMCG", "SaaS", "Healthcare", "Finance", "Retail", "Durable Goods", "Agency", "Mobility & Automotive"]
COMPANY_SIZES = ["Small", "Medium", "Enterprise"]
ICP_TIER = ["ICP 1", "ICP 2", "ICP 3"]

# Dictionaries zur Speicherung
companies = {}         # {our_company_id: {Company ID, Company Name, Industry, Company Size, Country, ICP Tier, Lifecycle Stage}}
sales_reps = {}            # {sales_reps_id: sales_reps}
company_mapping = {}   # {company_name: {"company_id": x, "first_closed_won": False, "deal_count": 0}}
company_deals_map = defaultdict(list)  # {our_company_id: [final_stage1, final_stage2, ...]}

# Funktion: Generiere Stage History für einen Deal
def generate_stage_history(deal, company_id, deal_id):
    deal_name = deal.get("dealname", "")
    deal_type = deal.get("deal_type", "")
    company_name = deal.get("company_name", "")
    amount = deal.get("amount", "")
    create_date = deal.get("createdate", "")[:10]
    try:
        current_date = datetime.strptime(create_date, "%Y-%m-%d")
    except:
        return []
    selected_stages = random.choices([
    # Closed Deals (Won & Lost)
    ["sql", "appointmentscheduled", "qualifiedtobuy", "presentationscheduled", "decisionmakerboughtin", "contractsent", "closedwon"],
    ["sql", "appointmentscheduled", "qualifiedtobuy", "presentationscheduled", "decisionmakerboughtin", "contractsent", "closedlost"],
    ["sql", "appointmentscheduled", "qualifiedtobuy", "presentationscheduled", "decisionmakerboughtin", "closedlost"],
    ["sql", "appointmentscheduled", "qualifiedtobuy", "presentationscheduled", "closedlost"],
    ["sql", "appointmentscheduled", "qualifiedtobuy", "closedlost"],
    ["sql", "appointmentscheduled", "closedlost"],
    ["sql", "closedlost"],
    
    # Open Deals (keine closedwon/closedlost)
    ["sql"],
    ["sql", "appointmentscheduled"],
    ["sql", "appointmentscheduled", "qualifiedtobuy"],
    ["sql", "appointmentscheduled", "qualifiedtobuy", "presentationscheduled"],
    ["sql", "appointmentscheduled", "qualifiedtobuy", "presentationscheduled", "decisionmakerboughtin"],
    ["sql", "appointmentscheduled", "qualifiedtobuy", "presentationscheduled", "decisionmakerboughtin", "contractsent"],
    ], weights=[
    # Closed Weights
    0.15,  # closedwon
    0.01,
    0.02,
    0.30,
    0.03,
    0.03,
    0.03,

    # Open Weights (mehr frühe offene Deals, abnehmend in späteren Stufen)
    0.07,  # nur sql
    0.06,
    0.05,
    0.06,
    0.06,
    0.06
    ], k=1)

    selected_stages = selected_stages[0] 

    sales_reps_name = random.choice(SALES_REPS)
    sales_reps_id = SALES_REPS_IDS[sales_reps_name]
    sales_reps[sales_reps_id] = sales_reps_name

    stage_rows = []
    previous_date = current_date
    entered_stage_dates = []

    for i, stage in enumerate(selected_stages):
        entered_stage_date = previous_date + timedelta(days=random.randint(2,30)) if i > 0 else current_date
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
            deal_id, company_id, sales_reps_id, deal_name, amount, forecast_amount, probability, stage,
            computed_deal_type, closed_date_value, create_date if i==0 else "", entered_stage_date.strftime("%Y-%m-%d"),
            days_in_stage, "Sales Pipeline", deal_type
        ])
    return stage_rows

# API-Abfrage
deals = []
deal_id_counter = 1001  # Deal IDs beginnen bei 1001
company_id_counter = 111111  # Company IDs beginnen bei 111111
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
                "Country": random.choice(["Albania", "Andorra", "Armenia", "Austria", "Belarus", "Belgium", "Bosnia and Herzegovina", "Bulgaria", "Croatia", "Cyprus", "Czech Republic", "Denmark", "Estonia",  
                                          "Finland", "France", "Georgia", "Germany", "Greece", "Hungary", "Iceland", "Ireland", "Italy", "Kosovo", "Latvia", "Lithuania", "Luxembourg",  
                                          "Malta", "Moldova", "Monaco", "Montenegro", "Netherlands", "North Macedonia", "Norway", "Poland", "Portugal", "Romania", "Serbia", "Slovakia", "Slovenia",  
                                          "Spain", "Sweden", "Switzerland", "Turkey", "Ukraine", "United Kingdom"]),
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
        
        stage_rows = generate_stage_history(props, company_id, deal_id_counter)
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

# Schritt 1: Deals pro Company nach `create_date` sortieren und nummerieren
company_deals = defaultdict(list)

# Alle Deals in company_deals_map einfügen, gruppiert nach Company
for deal in deals:
    company_id = deal[1]  # Company ID
    company_deals[company_id].append(deal)

# Schritt 2: Sortiere die Deals pro Company nach `create_date` für den "appointmentscheduled"-Stage und nummeriere sie
numbered_deals = []
deal_number_mapping = {}  # Eine Map, um Deals die gleiche Nummer zuzuweisen, basierend auf Deal ID
company_deal_numbers = defaultdict(int)  # Für jede Company, um die Deal-Nummer zu tracken

for company_id, company_deals_list in company_deals.items():
    # Schritt 2a: Finde alle Deals mit dem Stage "appointmentscheduled"
    appointment_scheduled_deals = [deal for deal in company_deals_list if deal[7] == "sql"]  # Stage ist an Index 7
    
    # Schritt 2b: Sortiere Deals nach create_date (Index 10)
    sorted_deals = sorted(appointment_scheduled_deals, key=lambda x: x[10])  # x[10] ist die "Create Date"
    
    # Schritt 2c: Nummeriere Deals basierend auf ihrem Create Date (die Deals mit `appointmentscheduled`-Stage)
    for deal in sorted_deals:
        deal_id = deal[0]  # Deal ID
        
        # Wenn es der erste Deal dieser Company ist oder ein neuer Deal, dem eine neue Nummer zugewiesen werden muss
        if deal_id not in deal_number_mapping:
            # Erhöhe die Deal Nummer für die Company
            company_deal_numbers[company_id] += 1
            deal_number_mapping[deal_id] = company_deal_numbers[company_id]
        
        # Hole die Deal Nummer für den aktuellen Deal
        deal_number = deal_number_mapping[deal_id]
        
        # Füge die Deal-Nummer an der richtigen Stelle hinzu (Index 14, da 0-basierte Indizes)
        numbered_deals.append(deal[:14] + [deal_number] + deal[14:])  # Deal Number an Index 14 anfügen

    # Schritt 2d: Für alle anderen Deals (auch die, die den `appointmentscheduled`-Stage nicht haben), ebenfalls die gleiche Nummer vergeben
    for deal in company_deals_list:
        if deal[7] != "sql":  # Wenn der Stage nicht `appointmentscheduled` ist
            deal_id = deal[0]  # Deal ID
            # Setze die Deal Nummer auf die, die für das zugehörige `appointmentscheduled` Deal vergeben wurde
            deal_number = deal_number_mapping.get(deal_id, None)
            if deal_number:  # Nur, wenn es einen Deal mit diesem Deal ID gibt, der bereits eine Nummer hat
                numbered_deals.append(deal[:14] + [deal_number] + deal[14:])

# Google Sheets: Befüllen
deal_sheet.clear()
deal_sheet.append_row([
    "Deal ID", "Company ID", "Sales Rep ID", "Deal Name", "Amount", "Forecast Amount", "Probability",
    "Deal Stage", "Deal Type", "Close Date", "Create Date", "Entered Stage Date", "Days in Stage", "Pipeline", "Deal Number"
])
deal_sheet.append_rows(numbered_deals)  # Verwende numbered_deals statt deals

company_sheet = client.open(SPREADSHEET_NAME).worksheet(COMPANY_TAB)
company_sheet.clear()
company_sheet.append_row(["Company ID", "Company Name", "Industry", "Company Size", "Country", "ICP Tier"])
company_sheet.append_rows([list(comp.values()) for comp in companies.values()])

owner_sheet = client.open(SPREADSHEET_NAME).worksheet(OWNER_TAB)
owner_sheet.clear()
owner_sheet.append_row(["Sales Rep ID", "Sales Rep", "Department", "Team", "Region"])
owner_rows = []
for sales_reps_id, sales_reps_name in sales_reps.items():
    owner_rows.append([
        sales_reps_id, sales_reps_name,
        random.choice(["Sales", "Account Management", "Enterprise Sales"]),
        random.choice(["Team A", "Team B", "Team C"]),
        random.choice(["EMEA", "AMER", "APAC"])
    ])
owner_sheet.append_rows(owner_rows)

print("✅ Alle drei Tabs im Sheet wurden erfolgreich befüllt.")
