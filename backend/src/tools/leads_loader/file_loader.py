import pandas as pd
from .lead_loader_base import LeadLoaderBase

class FileLeadLoader(LeadLoaderBase):
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def fetch_records(self, status_filter=""):
        # Convert DataFrame to list of dicts
        # We assume the DataFrame has the necessary columns (validated in server.py or caller)
        
        # Filter by status if 'STATUS' column exists
        # Note: server.py ensures STATUS column exists and is uppercase
        if "STATUS" in self.df.columns:
            filtered_df = self.df[self.df["STATUS"] == status_filter]
        else:
            # Fallback if validation skipped for some reason
            if status_filter == "":
                filtered_df = self.df
            else:
                filtered_df = pd.DataFrame()
        
        # Add an 'id' column if not present, using index
        if "id" not in filtered_df.columns and "ID" not in filtered_df.columns:
            filtered_df["id"] = filtered_df.index.astype(str)
            
        return filtered_df.to_dict(orient="records")

    def update_record(self, lead_id, update_data):
        # In-memory update
        # update_data can be a dictionary of {column: value}
        
        if not isinstance(update_data, dict):
            update_data = {"STATUS": update_data}
            
        # Ensure columns exist
        for col in update_data.keys():
            if col not in self.df.columns:
                self.df[col] = None

        if "id" in self.df.columns:
            mask = self.df["id"] == lead_id
        else:
            # Fallback to index if id column not explicitly created or used as index
            mask = self.df.index == int(lead_id)
            
        if mask.any():
            for col, val in update_data.items():
                self.df.loc[mask, col] = val
                
        return True
