import os
import smtplib
import requests
from email.mime.text import MIMEText
from datetime import datetime
from zoneinfo import ZoneInfo

URL = "https://www.malabargoldanddiamonds.com/us/malabarprice/index/getrates/?country=QA&state=Doha"
SOURCE_URL = "https://www.malabargoldanddiamonds.com/ae/goldprice"


def get_gold_rate():
    session = requests.Session()

    base = "https://www.malabargoldanddiamonds.com"
    api_url = base + "/ae/malabarprice/index/getrates/"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/148.0.0.0 Safari/537.36",
        "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.malabargoldanddiamonds.com/ae/goldprice",
        "Origin": base,
    }

    # Force AE store path
    session.cookies.set("store", "ae", domain="www.malabargoldanddiamonds.com", path="/")
    session.cookies.set("country", "QA", domain="www.malabargoldanddiamonds.com", path="/")
    session.cookies.set("currency", "QAR", domain="www.malabargoldanddiamonds.com", path="/")

    response = session.post(
        api_url,
        params={"country": "QA", "state": "Doha"},
        headers=headers,
        timeout=30,
        allow_redirects=False,
    )

    print("Status:", response.status_code)
    print("Location:", response.headers.get("location"))
    print("Content-Type:", response.headers.get("content-type"))
    print("Response preview:", response.text[:300])

    response.raise_for_status()

    if "application/json" not in response.headers.get("content-type", "") and not response.text.strip().startswith("{"):
        raise Exception("Malabar returned HTML instead of JSON. GitHub IP is being redirected/blocked by geo rules.")

    data = response.json()
    return data["22kt"], data["24kt"], data["updated_time"]

def send_email(rate22, rate24, updated):
    checked_time = datetime.now(ZoneInfo("Asia/Qatar")).strftime("%d/%m/%Y %I:%M %p")

    body = f"""Daily Gold Rate - Doha

22 Carat Gold: {rate22}
24 Carat Gold: {rate24}

Website Updated: {updated}
Checked Time: {checked_time} Doha Time

Source:
{SOURCE_URL}
"""

    msg = MIMEText(body)
    msg["Subject"] = "Daily Doha Gold Rate"
    msg["From"] = os.environ["EMAIL_USER"]
    msg["To"] = os.environ["EMAIL_TO"]

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(os.environ["EMAIL_USER"], os.environ["EMAIL_APP_PASSWORD"])
        server.send_message(msg)


if __name__ == "__main__":
    rate22, rate24, updated = get_gold_rate()
    send_email(rate22, rate24, updated)
