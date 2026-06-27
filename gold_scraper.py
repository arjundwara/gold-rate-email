import os
import smtplib
import requests
from email.mime.text import MIMEText
from datetime import datetime
from zoneinfo import ZoneInfo

URL = "https://www.malabargoldanddiamonds.com/ae/malabarprice/index/getrates/?country=QA&state=Doha"
SOURCE_URL = "https://www.malabargoldanddiamonds.com/ae/goldprice"


def get_gold_rate():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": SOURCE_URL,
        "Origin": "https://www.malabargoldanddiamonds.com",
    }

    response = requests.post(URL, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()

    rate22 = data["22kt"]
    rate24 = data["24kt"]
    updated = data["updated_time"]

    return rate22, rate24, updated


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
