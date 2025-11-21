import os
import json
from datetime import datetime
from dotenv import load_dotenv
from src.graph import OutReachAutomation
from src.state import *
from src.tools.leads_loader.airtable import AirtableLeadLoader
from src.tools.leads_loader.google_sheets import GoogleSheetLeadLoader

# Load environment variables from a .env file
load_dotenv()

if __name__ == "__main__":
    # Use Airtable for accessing your leads list
    # lead_loader = AirtableLeadLoader(
    #     access_token=os.getenv("AIRTABLE_ACCESS_TOKEN"),
    #     base_id=os.getenv("AIRTABLE_BASE_ID"),
    #     table_name=os.getenv("AIRTABLE_TABLE_NAME"),
    # )

    # Use Sheet for accessing your leads list
    lead_loader = GoogleSheetLeadLoader(
        spreadsheet_id=os.getenv("SHEET_ID"),
    )

    # Instantiate the OutReachAutomation class
    automation = OutReachAutomation(lead_loader)
    app = automation.app

    # initial graph inputs:
    # Lead ids to be processed, leave empty to fetch all news leads
    inputs = {"leads_ids": []}

    # Run the outreach automation with the provided lead name and email
    config = {"recursion_limit": 1000}
    app.invoke(inputs, config)


    # output = app.invoke(inputs, config)

    # # Save the full run output as JSON locally
    # try:
    #     os.makedirs("Leads_Report", exist_ok=True)
    #     ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    #     out_path = os.path.join("Leads_Report", f"run_{ts}.json")
    #     with open(out_path, "w", encoding="utf-8", newline="") as f:
    #         json.dump(output, f, ensure_ascii=False, indent=2, default=str)
    #     print(f"Saved run output to {out_path}")
    # except Exception as e:
    #     print(f"Failed to save run output JSON: {e}")
