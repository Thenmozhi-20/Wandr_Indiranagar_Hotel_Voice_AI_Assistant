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
_unanswered_sheet = None

FALLBACK_MESSAGE = "I don't have that information"

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


def _get_unanswered_sheet():
    """Gets or creates a separate tab called 'Unanswered' in the same spreadsheet."""
    global _unanswered_sheet
    if _unanswered_sheet is not None:
        return _unanswered_sheet
    try:
        creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")
        sheet_id   = os.environ.get("GOOGLE_SHEET_ID", "")
        if not creds_json or not sheet_id:
            return None
        creds_dict   = json.loads(creds_json)
        creds        = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client       = gspread.authorize(creds)
        spreadsheet  = client.open_by_key(sheet_id)
        try:
            _unanswered_sheet = spreadsheet.worksheet("Unanswered")
        except gspread.WorksheetNotFound:
            _unanswered_sheet = spreadsheet.add_worksheet(title="Unanswered", rows=1000, cols=3)
            _unanswered_sheet.append_row(["Timestamp", "Question", "Mode"])
            print("[Sheets] Created 'Unanswered' tab")
        return _unanswered_sheet
    except Exception as e:
        print(f"[Sheets Error] Unanswered tab: {e}")
        return None


def log_chat(question: str, reply: str):
    """Log a question + reply to Google Sheets. Also flags unanswered questions."""
    try:
        sheet = _get_sheet()
        if sheet is not None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row([timestamp, question, reply])
            print(f"[Sheets] Logged: {question[:50]}")
    except Exception as e:
        print(f"[Sheets Log Error] {e}")

    # ── Flag unanswered questions separately ───────────────────
    try:
        if FALLBACK_MESSAGE.lower() in reply.lower():
            unanswered = _get_unanswered_sheet()
            if unanswered is not None:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                unanswered.append_row([timestamp, question, "text"])
                print(f"[Sheets] Flagged unanswered: {question[:50]}")
    except Exception as e:
        print(f"[Sheets Unanswered Error] {e}")


def get_unanswered_summary(limit: int = 50):
    """Fetches unanswered questions, groups similar ones, returns sorted by frequency."""
    try:
        sheet = _get_unanswered_sheet()
        if sheet is None:
            return []
        rows = sheet.get_all_records()  # [{Timestamp, Question, Mode}, ...]
        if not rows:
            return []

        counts = {}
        latest = {}
        for row in rows:
            q = (row.get("Question") or "").strip()
            if not q:
                continue
            key = q.lower()
            counts[key] = counts.get(key, 0) + 1
            # Keep the most recent original-cased version + timestamp
            latest[key] = {
                "question":  q,
                "timestamp": row.get("Timestamp", "")
            }

        summary = [
            {
                "question":  latest[key]["question"],
                "count":     count,
                "last_asked": latest[key]["timestamp"]
            }
            for key, count in counts.items()
        ]
        summary.sort(key=lambda x: x["count"], reverse=True)
        return summary[:limit]
    except Exception as e:
        print(f"[Sheets Summary Error] {e}")
        return []
