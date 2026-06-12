# ============================================================
#  sheets_logger.py  —  Logs chat questions to Google Sheets
# ============================================================

import gspread
from google.oauth2.service_account import Credentials
import json
import os
from datetime import datetime

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

_sheet = None

def _get_sheet():
    global _sheet
    if _sheet is not None:
        return _sheet
    try:
        creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")
        sheet_id   = os.environ.get("GOOGLE_SHEET_ID", "")
        if not creds_json or not sheet_id:
            print("[Sheets] Missing GOOGLE_CREDENTIALS_JSON or GOOGLE_SHEET_ID")
            return None
        creds_dict = json.loads(creds_json)
        creds      = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client     = gspread.authorize(creds)
        _sheet     = client.open_by_key(sheet_id).sheet1
        print("[Sheets] Connected to Google Sheet successfully")
        return _sheet
    except Exception as e:
        print(f"[Sheets Error] {e}")
        return None


def log_chat(question: str, reply: str):
    """Log a question + reply to Google Sheets."""
    try:
        sheet = _get_sheet()
        if sheet is None:
            return
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([timestamp, question, reply])
        print(f"[Sheets] Logged: {question[:50]}")
    except Exception as e:
        print(f"[Sheets Log Error] {e}")
