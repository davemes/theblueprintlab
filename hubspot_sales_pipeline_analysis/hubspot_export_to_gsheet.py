import requests
import gspread
from google.oauth2.service_account import Credentials
import random

# Auth for Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
# Dein JSON-File
SPREADSHEET_NAME = "HubSpot - Sales Pipeline Analysis"
TAB_NAME = "HubSpot Raw Data"

creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open(SPREADSHEET_NAME).worksheet(TAB_NAME)

# HubSpot Auth
import os
from dotenv import load_dotenv
load_dotenv()
ACCESS_TOKEN = os.getenv("HUBSPOT_API_KEY")

URL = "https://api.hubapi.com/crm/v3/objects/deals?limit=100&properties=dealname,amount,probability_amount,probability,dealstage,dealtype,closedate,createdate"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

# 🔹 Random Deal Owners
DEAL_OWNERS = [
    "John",  
    "Celine",       
    "Margaret", 
    "Charlotte", 
    "David",          
    "Andre",             
    "Philip"             
]

# Fetch deals from HubSpot
deals = []
after = None

while True:
    url = URL + (f"&after={after}" if after else "")
    response = requests.get(url, headers=headers).json()
    
    for deal in response.get("results", []):
        props = deal["properties"]
        deals.append([
            random.choice(DEAL_OWNERS),
            props.get("dealname", ""),
            props.get("amount", ""),
            props.get("probability_amount", ""),
            props.get("probability", ""),
            props.get("dealstage", ""),
            props.get("dealtype", ""),
            props.get("closedate", "")[:10],
            props.get("createdate", "")[:10]
        ])
    
    if not response.get("paging"):
        break
    after = response["paging"]["next"]["after"]

# Write to Google Sheet
sheet.clear()
sheet.append_row(["Deal Owner", "Deal Name", "Amount", "Forecast Amount", "Probability", "Deal Stage", "Deal Type", "Close Date", "Create Date"])
sheet.append_rows(deals)

print("✅ Export complete. Deals written to Google Sheet.")

