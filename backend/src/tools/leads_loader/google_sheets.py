from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from .lead_loader_base import LeadLoaderBase
from src.utils import get_google_credentials


def _column_index_to_letter(index: int) -> str:
    """
    Convert a 0-based column index to an Excel-style column letter (A, B, ..., Z, AA, AB, ...).
    """
    index += 1  # Convert to 1-based
    letters = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


class GoogleSheetLeadLoader(LeadLoaderBase):
    def __init__(self, spreadsheet_id, sheet_name=None):
        self.sheet_service = build("sheets", "v4", credentials=get_google_credentials())
        self.spreadsheet_id = spreadsheet_id
        self.sheet_name = sheet_name or self._get_sheet_name_from_id()

    def fetch_records(self, lead_ids=None, status_filter="NEW"):
        """
        Fetches leads from Google Sheets. If lead IDs are provided, fetch those
        specific records. Otherwise, fetch leads matching the given status.

        This is designed to work with an Apollo-style export with headers like:

        NAME | APOLLO ID | ROLE | MAIL ID | LINKEDIN | LOCATION | COMPANY | STATUS
        """
        try:
            result = (
                self.sheet_service.spreadsheets()
                .values()
                .get(spreadsheetId=self.spreadsheet_id, range=self.sheet_name)
                .execute()
            )
            rows = result.get("values", [])
            if not rows:
                return []

            headers = rows[0]
            records = []

            for i, row in enumerate(rows[1:], start=2):  # Data starts at row 2
                record = dict(zip(headers, row))

                # For Google Sheets we use the physical row number as the internal `id`.
                # This is required so that `update_record` can write back to the right row.
                record["id"] = f"{i}"

                # Resolve status (supports both `STATUS` and `Status` and defaults
                # to the filter value when missing).
                status = record.get("STATUS") or record.get("Status") or status_filter

                if lead_ids:
                    # If specific lead_ids are supplied, use them directly (these are
                    # row numbers as strings).
                    if record["id"] in lead_ids:
                        records.append(record)
                else:
                    # If there's no STATUS column, every row behaves like `NEW`
                    # and will be processed on the first run.
                    if status == status_filter:
                        records.append(record)

            return records

        except HttpError as e:
            print(f"Error fetching records from Google Sheets: {e}")
            return []

    def update_record(self, id, fields_to_update):
        try:
            # Fetch the header row to identify column indices
            result = (
                self.sheet_service.spreadsheets()
                .values()
                .get(spreadsheetId=self.spreadsheet_id, range=self.sheet_name)
                .execute()
            )
            rows = result.get("values", [])
            if not rows:
                return None

            headers = rows[0]

            # Ensure any missing headers are appended to the header row
            missing_headers = [
                field for field in fields_to_update.keys() if field not in headers
            ]
            if missing_headers:
                updated_headers = headers + missing_headers
                (
                    self.sheet_service.spreadsheets()
                    .values()
                    .update(
                        spreadsheetId=self.spreadsheet_id,
                        range=f"{self.sheet_name}!1:1",
                        valueInputOption="RAW",
                        body={"values": [updated_headers]},
                    )
                    .execute()
                )
                headers = updated_headers

            # Prepare the update body for all specified fields
            updates = []
            for field, value in fields_to_update.items():
                if field in headers:
                    col_index = headers.index(field)
                    col_letter = _column_index_to_letter(col_index)
                    range_ = f"{self.sheet_name}!{col_letter}{id}"
                    updates.append(
                        {
                            "range": range_,
                            "values": [[value]],
                        }
                    )

            # Execute batch update for efficiency
            if updates:
                body = {"valueInputOption": "RAW", "data": updates}
                (
                    self.sheet_service.spreadsheets()
                    .values()
                    .batchUpdate(
                        spreadsheetId=self.spreadsheet_id,
                        body=body,
                    )
                    .execute()
                )
            return {"id": id, "updated_fields": fields_to_update}

        except HttpError as e:
            print(f"Error updating Google Sheets record: {e}")
            return None

    def _get_sheet_name_from_id(self):
        try:
            result = (
                self.sheet_service.spreadsheets()
                .get(spreadsheetId=self.spreadsheet_id)
                .execute()
            )
            sheets = result.get("sheets", [])
            if not sheets:
                raise ValueError("No sheets found in the spreadsheet.")
            return sheets[0]["properties"]["title"]  # Default to the first sheet
        except HttpError as e:
            print(f"Error fetching sheet name: {e}")
            raise
