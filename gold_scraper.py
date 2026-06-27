import os
import re
import smtplib
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from datetime import datetime
from zoneinfo import ZoneInfo

URL = "https://www.malabargoldanddiamonds.com/ae/goldprice"


def get_gold_rate():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(URL, timeout=30, headers=headers)
    r.raise_for_status()

    html = r.text
    soup = BeautifulSoup(html, "html.parser")

    print("Page title:", soup.title.get_text(strip=True) if soup.title else "No title")
    print("22kt-price found:", "22kt-price" in html)
    print("QAR found:", "QAR" in html)

    rate_22k_tag = soup.find("span", class_=lambda c: c and "22kt-price" in c)
    rate_24k_tag = soup.find("span", class_=lambda c: c and "24kt-price" in c)
    updated_tag = soup.find("span", class_=lambda c: c and "update-date" in c)

    if not rate_22k_tag:
        raise Exception("22K gold rate not found from Malabar page")

    rate_22k = rate_22k_tag.get_text(strip=True)
    rate_24k = rate_24k_tag.get_text(strip=True) if rate_24k_tag else "Not found"
    updated = updated_tag.get_text(strip=True) if updated_tag else datetime.now(ZoneInfo("Asia/Qatar")).strftime("%d-%m-%Y %I:%M %p")

    return rate_22k, rate_24k, updated

def send_email(rate_22k, rate_24k, updated):
    body = f"""Daily Gold Rate - Doha

22 Carat Gold: {rate_22k}
24 Carat Gold: {rate_24k}

Checked Time: {updated} Doha Time

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
