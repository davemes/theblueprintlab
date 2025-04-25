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
URL = "https://api.hubapi.com/crm/v3/objects/deals?limit=100&properties=company_name,dealname,amount,probability,deal_type,dealstage,closedate,createdate,hubspot_owner_id&associations=companies"
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

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
    selected_stages = random.choice([
        #Closed Deals
        ["sql", "appointmentscheduled", "qualifiedtobuy", "presentationscheduled", "decisionmakerboughtin", "contractsent", "closedwon"],
        ["sql", "appointmentscheduled", "qualifiedtobuy", "presentationscheduled", "decisionmakerboughtin", "contractsent", "closedlost"],
        ["sql", "appointmentscheduled", "qualifiedtobuy", "presentationscheduled", "decisionmakerboughtin", "closedlost"],
        ["sql", "appointmentscheduled", "qualifiedtobuy", "presentationscheduled", "closedlost"],
        ["sql", "appointmentscheduled", "qualifiedtobuy", "closedlost"],
        ["sql", "appointmentscheduled", "closedlost"],
        ["sql", "closedlost"],
        #Open Deals
        ["sql"], 
        ["sql", "appointmentscheduled"],
        ["sql", "appointmentscheduled", "qualifiedtobuy"],
        ["sql", "appointmentscheduled", "qualifiedtobuy", "presentationscheduled"],
        ["sql", "appointmentscheduled", "qualifiedtobuy", "presentationscheduled", "decisionmakerboughtin"],
        ["sql", "appointmentscheduled", "qualifiedtobuy", "presentationscheduled", "decisionmakerboughtin", "contractsent"]
    ])
    sales_reps_name = random.choice(SALES_REPS)
    sales_reps_id = SALES_REPS_IDS[sales_reps_name]
    sales_reps[sales_reps_id] = sales_reps_name

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
        forecast_amount = round(float(amount) * probability, 2) if amount else ""
        closed_date_value = entered_stage_date.strftime("%Y-%m-%d") if stage in ["closedwon", "closedlost"] else ""
        
        stage_rows.append([
            deal_id, company_id, sales_reps_id, deal_name, amount, forecast_amount, probability, stage,
            closed_date_value, create_date if i == 0 else "", entered_stage_date.strftime("%Y-%m-%d"),
            days_in_stage, "Sales Pipeline", deal_type
        ])
    
    print(stage_rows)  # Sicherstellen, dass es korrekt eingerückt ist
    return stage_rows
    
# # Google Sheets: Befüllen
# deal_sheet.clear()
# deal_sheet.append_row([
#     "Deal ID", "Company ID", "Sales Rep ID", "Deal Name", "Amount", "Forecast Amount", "Probability",
#     "Deal Stage", "Close Date", "Create Date", "Entered Stage Date", "Days in Stage", "Pipeline", "Deal_Type", "Deal Number"
# ])
# deal_sheet.append_rows(stage_rows)  

# company_sheet = client.open(SPREADSHEET_NAME).worksheet(COMPANY_TAB)
# company_sheet.clear()
# company_sheet.append_row(["Company ID", "Company Name", "Industry", "Company Size", "Country", "ICP Tier", "Lifecycle Stage"])
# company_sheet.append_rows([list(comp.values()) for comp in companies.values()])

# owner_sheet = client.open(SPREADSHEET_NAME).worksheet(OWNER_TAB)
# owner_sheet.clear()
# owner_sheet.append_row(["Sales Rep ID", "Sales Rep", "Department", "Team", "Region"])
# owner_rows = []
# for sales_reps_id, sales_reps_name in sales_reps.items():
#     owner_rows.append([
#         sales_reps_id, sales_reps_name,
#         random.choice(["Sales", "Account Management", "Enterprise Sales"]),
#         random.choice(["Team A", "Team B", "Team C"]),
#         random.choice(["EMEA", "AMER", "APAC"])
#     ])
# owner_sheet.append_rows(owner_rows)

# print("✅ Alle drei Tabs wurden erfolgreich befüllt.")