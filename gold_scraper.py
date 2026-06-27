import os
import re
import smtplib
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from datetime import datetime
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright

URL = "https://www.malabargoldanddiamonds.com/ae/goldprice"


def get_gold_rate():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        page.goto(URL, wait_until="networkidle")

        # Country
        page.select_option("#gold-country-list", label="Qatar")

        # Wait until states are loaded
        page.wait_for_timeout(2000)

        # State
        page.select_option("#gold-state-list", label="Doha")

        # Submit
        page.click("button.submit.gold-rate-btn")

        # Wait for the rates to refresh
        page.wait_for_timeout(3000)

        html = page.content()

        browser.close()

    soup = BeautifulSoup(html, "html.parser")

    rate22 = soup.select_one("span.price.\\32 2kt-price").get_text(strip=True)
    rate24 = soup.select_one("li.right_india-24-carat-rate span.price").get_text(strip=True)
    updated = soup.select_one("span.update-date").get_text(strip=True)

    return rate22, rate24, updated

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
