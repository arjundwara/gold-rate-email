import os
import smtplib
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from datetime import datetime
from zoneinfo import ZoneInfo

URL = "https://www.malabargoldanddiamonds.com/ae/goldprice"

def get_gold_rate():
    r = requests.get(URL, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    rate_22k = soup.select_one(".price.22kt-price").get_text(strip=True)
    rate_24k = soup.select_one(".right_india-24-carat-rate .price").get_text(strip=True)
    updated = soup.select_one(".update-date").get_text(strip=True)

    return rate_22k, rate_24k, updated

def send_email(rate_22k, rate_24k, updated):
    now = datetime.now(ZoneInfo("Asia/Qatar")).strftime("%d-%m-%Y %I:%M %p")

    body = f"""Daily Gold Rate - Doha

22 Carat Gold: {rate_22k}
24 Carat Gold: {rate_24k}

Website Updated: {updated}
Email Sent: {now} Doha Time

Source:
{URL}
"""

    msg = MIMEText(body)
    msg["Subject"] = "Daily Doha Gold Rate"
    msg["From"] = os.environ["EMAIL_USER"]
    msg["To"] = os.environ["EMAIL_TO"]

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(os.environ["EMAIL_USER"], os.environ["EMAIL_APP_PASSWORD"])
        server.send_message(msg)

if __name__ == "__main__":
    rate_22k, rate_24k, updated = get_gold_rate()
    send_email(rate_22k, rate_24k, updated)
