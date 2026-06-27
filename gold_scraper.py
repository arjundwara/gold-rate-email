import os
import smtplib
import requests
from email.mime.text import MIMEText
from datetime import datetime
from zoneinfo import ZoneInfo

URL = "https://www.malabargoldanddiamonds.com/us/malabarprice/index/getrates/?country=QA&state=Doha"
SOURCE_URL = "https://www.malabargoldanddiamonds.com/ae/goldprice"


def get_gold_rate():
    import requests

    session = requests.Session()

    BASE_URL = "https://www.malabargoldanddiamonds.com"
    SOURCE_URL = BASE_URL + "/us/goldprice"
    API_URL = BASE_URL + "/us/malabarprice/index/getrates/"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": SOURCE_URL,
        "Origin": BASE_URL,
    }

    # Open US page first to obtain cookies
    r = session.get(SOURCE_URL, headers=headers, timeout=30)

    print("Landing URL:", r.url)

    response = session.post(
        API_URL,
        params={
            "country": "QA",
            "state": "Doha"
        },
        headers=headers,
        timeout=30
    )

    print("Status:", response.status_code)
    print("Content-Type:", response.headers.get("Content-Type"))
    print("Response:")
    print(response.text)

    response.raise_for_status()

    data = response.json()

    return (
        data["22kt"],
        data["24kt"],
        data["updated_time"]
    )

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
