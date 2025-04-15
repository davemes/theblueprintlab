import requests
import gspread
from google.oauth2.service_account import Credentials

# Auth for Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive"]
CREDS_FILE = "hs-sales-pipeline-analysis-0d212e642d40.json"  # Dein JSON-File
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

URL = "https://api.hubapi.com/crm/v3/objects/deals?limit=100&properties=dealname,amount,dealstage,closedate"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

# Fetch deals from HubSpot
deals = []
after = None

while True:
    url = URL + (f"&after={after}" if after else "")
    response = requests.get(url, headers=headers).json()
    
    for deal in response.get("results", []):
        props = deal["properties"]
        deals.append([
            props.get("dealname", ""),
            props.get("amount", ""),
            props.get("dealstage", ""),
            props.get("closedate", "")
        ])
    
    if not response.get("paging"):
        break
    after = response["paging"]["next"]["after"]

# Write to Google Sheet
sheet.clear()
sheet.append_row(["Deal Name", "Amount", "Deal Stage", "Close Date"])
sheet.append_rows(deals)

print("✅ Export complete. Deals written to Google Sheet.")

