import os
import sys
import json
import argparse
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from src.graph import OutReachAutomation
from src.state import *
from src.tools.leads_loader.file_loader import FileLeadLoader

import logging

# Load environment variables from a .env file
load_dotenv()

# Configure logging for CLI usage
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Run InsightFlow AI Analysis')
    parser.add_argument('file_path', type=str, help='Path to the input file (.csv, .xlsx, .xls)')
    
    args = parser.parse_args()
    file_path = args.file_path
    
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        sys.exit(1)

    print(f"Starting analysis for: {file_path}")
    sys.stdout.flush()

    try:
        # Load data
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file_path)
        else:
            print("Error: Invalid file format")
            sys.exit(1)
            
        # --- Column Validation & Normalization ---
        # Normalize existing columns to uppercase for consistent checking
        df.columns = [c.strip().upper() for c in df.columns]
        
        # Required columns and their default values
        required_columns = {
            "STATUS": "NEW",
            "LEAD_SCORE": 0,
            "QUALIFIED": "NO"  # Using "NO" string instead of False to match typical CSV/Excel data
        }
        
        for col, default_val in required_columns.items():
            if col not in df.columns:
                print(f"Adding missing column: {col} with default: {default_val}")
                df[col] = default_val
                
        print(f"Loaded {len(df)} records.")
        sys.stdout.flush()

        # Initialize loader
        lead_loader = FileLeadLoader(df)

        # Instantiate the OutReachAutomation class
        # Note: We are creating a new instance here. 
        # In a real production env, we might want to share resources, but for a subprocess this is fine.
        automation = OutReachAutomation(lead_loader)
        app = automation.app

        # initial graph inputs:
        inputs = {"leads_ids": []}

        # Run the outreach automation
        config = {"recursion_limit": 1000}
        
        print("Initializing automation graph...")
        sys.stdout.flush()
        
        # We can't easily stream "internal" graph steps unless we add callbacks or print statements inside nodes.
        # Assuming nodes.py has print statements, they will be captured.
        
        result = app.invoke(inputs, config)
        
        print("Analysis complete. Generating output...")
        sys.stdout.flush()

        # Save the processed data to a local Excel file
        # We'll save it in the same directory or a temp one, but let's output the path
        output_dir = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        output_path = os.path.join(output_dir, f"Processed_{filename}")
        
        # The loader.df should have been updated in-place if the graph uses it correctly
        # If not, we might need to extract from result if result contains the updated leads
        
        # Check if we need to rely on loader.df or result
        # The nodes.py updates loader.df in place via update_record
        
        df_to_save = lead_loader.df.copy()
        if "id" in df_to_save.columns and df_to_save["id"].equals(df_to_save.index.astype(str)):
            df_to_save = df_to_save.drop(columns=["id"])
            
        # Ensure extension is xlsx for output
        if not output_path.endswith('.xlsx'):
            output_path = os.path.splitext(output_path)[0] + '.xlsx'
            
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df_to_save.to_excel(writer, index=False)
            
        print(f"OUTPUT_FILE:{output_path}")
        sys.stdout.flush()

    except Exception as e:
        print(f"Error during execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
