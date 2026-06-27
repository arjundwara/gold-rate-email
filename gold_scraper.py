import os
import smtplib
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright

URL = "https://www.malabargoldanddiamonds.com/ae/goldprice"


def get_gold_rate():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )

        page = browser.new_page(
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
        )

        page.goto(URL, wait_until="networkidle", timeout=90000)

        print("Title:", page.title())
        print("URL:", page.url)

        # Debug information
        print("Country dropdown count:", page.locator("#gold-country-list").count())
        print("State dropdown count:", page.locator("#gold-state-list").count())

        if page.locator("#gold-country-list").count() == 0:
            page.screenshot(path="page.png", full_page=True)
            html = page.content()
            print(html[:5000])   # Print first 5000 characters
            raise Exception("Country dropdown not found.")

        page.select_option("#gold-country-list", value="QA")
        page.wait_for_timeout(2000)

        page.select_option("#gold-state-list", value="Doha")
        page.wait_for_timeout(1000)

        page.click("button.submit.gold-rate-btn")

        page.wait_for_timeout(4000)

        rate22 = page.locator("span[class*='22kt-price']").inner_text().strip()
        rate24 = page.locator("li.right_india-24-carat-rate span.price").inner_text().strip()
        updated = page.locator("span.update-date").inner_text().strip()

        browser.close()

        return rate22, rate24, updated

def send_email(rate22, rate24, updated):
    body = f"""Daily Gold Rate - Doha

22 Carat Gold: {rate22}
24 Carat Gold: {rate24}

Updated Time: {updated}

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
    rate22, rate24, updated = get_gold_rate()
    send_email(rate22, rate24, updated)
