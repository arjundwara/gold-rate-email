import os
import re
import smtplib
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from datetime import datetime
from zoneinfo import ZoneInfo

URL = "https://goldpricez.com/qar/gram"

def get_gold_rate():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    r = requests.get(URL, timeout=30, headers=headers)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text(" ", strip=True)

    print("Page title:", soup.title.get_text(strip=True) if soup.title else "No title")

    rate_22k_raw = None
    rate_24k_raw = None

    # Strategy 1: look for table rows with "22 Karat" / "24 Karat" labels
    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) >= 2:
            label = cells[0].get_text(strip=True)
            if re.search(r'\b22\s*(?:K|Karat)\b', label, re.I) and not rate_22k_raw:
                for cell in cells[1:]:
                    val = re.sub(r'[^\d.]', '', cell.get_text(strip=True))
                    if re.match(r'\d+\.?\d*$', val):
                        rate_22k_raw = val
                        break
            elif re.search(r'\b24\s*(?:K|Karat)\b', label, re.I) and not rate_24k_raw:
                for cell in cells[1:]:
                    val = re.sub(r'[^\d.]', '', cell.get_text(strip=True))
                    if re.match(r'\d+\.?\d*$', val):
                        rate_24k_raw = val
                        break

    # Strategy 2: fallback regex on full page text
    if not rate_22k_raw:
        m = re.search(r'22\s*(?:K|Karat)[^0-9]{1,60}?([\d]+\.[\d]+)', text, re.I)
        if m:
            rate_22k_raw = m.group(1)

    if not rate_24k_raw:
        m = re.search(r'24\s*(?:K|Karat)[^0-9]{1,60}?([\d]+\.[\d]+)', text, re.I)
        if m:
            rate_24k_raw = m.group(1)

    if not rate_22k_raw:
        raise Exception("22K gold rate not found. The source page may have changed structure.")

    rate_22k = f"QAR {rate_22k_raw} / gram"
    rate_24k = f"QAR {rate_24k_raw} / gram" if rate_24k_raw else "Not found"

    updated = datetime.now(ZoneInfo("Asia/Qatar")).strftime("%d-%m-%Y %I:%M %p")

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
