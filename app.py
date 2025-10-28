
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import os, requests, gspread
from oauth2client.service_account import ServiceAccountCredentials

app = FastAPI(title="Roti Boti Assistant Hooks", version="1.0.0")

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS_PATH = os.getenv("GOOGLE_CREDS_JSON")
SHEET_URL = os.getenv("SHEET_URL")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
OWNER_EMAIL = os.getenv("OWNER_EMAIL", "")

gc = None
sh = None

def _init_sheets():
    global gc, sh
    if CREDS_PATH and SHEET_URL:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_PATH, SCOPE)
        gc = gspread.authorize(creds)
        sh = gc.open_by_url(SHEET_URL).sheet1

_init_sheets()

class Reservation(BaseModel):
    name: str
    party_size: int
    date: str
    time: str
    phone: str
    notes: str | None = None
    request_type: str = "reservation"
    language: str = "en"
    source: str = "gpt"

class Notify(BaseModel):
    subject: str
    message: str

@app.get("/")
def health():
    return {"status": "ok", "service": "Roti Boti Assistant API", "time": datetime.utcnow().isoformat()}

@app.post("/hooks/reservation")
def log_reservation(req: Reservation):
    if not hasattr(app.state, "init") or not sh:
        _init_sheets()
        app.state.init = True

    appended = False
    if sh:
        row = [req.request_type, req.name, req.party_size, req.date, req.time, req.phone, (req.notes or ""), req.language, req.source, datetime.utcnow().isoformat()]
        sh.append_row(row)
        appended = True

    emailed = False
    if SENDGRID_API_KEY and OWNER_EMAIL:
        emailed = send_email(
            subject=f"New {req.request_type.title()} – {req.name} ({req.party_size})",
            message=(
                f"Type: {req.request_type}\n"
                f"Name: {req.name}\n"
                f"Party size: {req.party_size}\n"
                f"When: {req.date} {req.time}\n"
                f"Phone: {req.phone}\n"
                f"Notes: {req.notes or '—'}\n"
                f"Language: {req.language} | Source: {req.source}"
            )
        )

    return {"ok": True, "sheet_logged": appended, "email_sent": emailed}

@app.post("/hooks/notify")
def notify_owner(req: Notify):
    emailed = send_email(req.subject, req.message)
    return {"ok": bool(emailed), "email_sent": emailed}

def send_email(subject: str, message: str):
    if not SENDGRID_API_KEY or not OWNER_EMAIL:
        return False
    r = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "personalizations": [{"to": [{"email": OWNER_EMAIL}]}],
            "from": {"email": "assistant@insightxai.com"},
            "subject": subject,
            "content": [{"type": "text/plain", "value": message}]
        }
    )
    return r.status_code in (200, 202)
