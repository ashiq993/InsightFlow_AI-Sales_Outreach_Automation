import pandas as pd
from .lead_loader_base import LeadLoaderBase

class FileLeadLoader(LeadLoaderBase):
    def __init__(self, df: pd.DataFrame):
        """
        Initialize the loader with an in-memory pandas DataFrame used as the source of lead records.
        
        Parameters:
            df (pd.DataFrame): DataFrame containing lead records; stored and mutated in-place by the loader's methods.
        """
        self.df = df

    def fetch_records(self, status_filter="NEW"):
        # Convert DataFrame to list of dicts
        # We assume the DataFrame has the necessary columns
        # Filter by status if 'STATUS' column exists, otherwise return all
        """
        Retrieve lead records from the loader's DataFrame, optionally filtering by a STATUS value.
        
        Parameters:
            status_filter (str): Status value used to filter records. Defaults to "NEW".
            
        Returns:
            list[dict]: List of row dictionaries with an ensured `"id"` field (string). If the DataFrame contains a `"STATUS"` column, only rows with `STATUS == status_filter` are returned. If no `"STATUS"` column exists, all rows are returned when `status_filter` is `"NEW"`, otherwise an empty list is returned.
        
        Notes:
            If the DataFrame lacks an `"id"` column, one is created from the DataFrame index (stringified) and will appear in both the returned records and the DataFrame itself.
        """
        if "STATUS" in self.df.columns:
            filtered_df = self.df[self.df["STATUS"] == status_filter]
        else:
            # If no status column, treat all as NEW if filter is NEW
            if status_filter == "NEW":
                filtered_df = self.df
            else:
                filtered_df = pd.DataFrame()
        
        # Add an 'id' column if not present, using index
        if "id" not in filtered_df.columns:
            filtered_df["id"] = filtered_df.index.astype(str)
            
        return filtered_df.to_dict(orient="records")

    def update_record(self, lead_id, update_data):
        # In-memory update
        # update_data can be a dictionary of {column: value}
        
        """
        Update fields of an existing lead record in the in-memory DataFrame.
        
        If `update_data` is not a dict it is treated as a `STATUS` value. The method ensures any keys in `update_data` exist as columns (new columns are created with default None), locates rows matching `lead_id` by the `"id"` column when present or by integer index otherwise, and applies the updates in-place. The operation is performed on `self.df` and does not persist beyond the DataFrame.
        
        Parameters:
            lead_id: Identifier of the lead to update. Matched against the `"id"` column when present, otherwise matched against the DataFrame index (converted to int).
            update_data: A dict mapping column names to values, or a single value which will be used as the `STATUS` field.
        
        Returns:
            bool: `True` after attempting the update (always returns `True`).
        """
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