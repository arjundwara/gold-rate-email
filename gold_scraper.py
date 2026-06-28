import os
import csv
import smtplib
import requests
from pathlib import Path
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

CSV_FILE = Path("gold_rates.csv")

BASE_URL = "https://www.malabargoldanddiamonds.com"
SOURCE_URL = BASE_URL + "/us/goldprice"
API_URL = BASE_URL + "/us/malabarprice/index/getrates/"


def clean_rate(value):
    return float(value.replace("QAR", "").replace(",", "").strip())


def format_change(value):
    if value is None:
        return "Not enough data"
    if value > 0:
        return f"▲ +{value:.2f} QAR"
    if value < 0:
        return f"▼ {value:.2f} QAR"
    return "— 0.00 QAR"


def get_gold_rate():
    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/148.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": SOURCE_URL,
        "Origin": BASE_URL,
    }

    session.get(SOURCE_URL, headers=headers, timeout=30)

    response = session.post(
        API_URL,
        params={"country": "QA", "state": "Doha"},
        headers=headers,
        timeout=30
    )

    print("Status:", response.status_code)
    print("Response:", response.text)

    response.raise_for_status()
    data = response.json()

    return data["22kt"], data["24kt"], data["updated_time"]


def read_history():
    if not CSV_FILE.exists():
        return []

    with CSV_FILE.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_history(rows):
    fieldnames = [
        "date",
        "checked_time",
        "website_updated",
        "rate_22k",
        "rate_24k",
    ]

    with CSV_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def update_history(rate22, rate24, website_updated):
    now = datetime.now(ZoneInfo("Asia/Qatar"))
    today = now.strftime("%Y-%m-%d")

    rows = read_history()

    new_row = {
        "date": today,
        "checked_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "website_updated": website_updated,
        "rate_22k": f"{clean_rate(rate22):.2f}",
        "rate_24k": f"{clean_rate(rate24):.2f}",
    }

    updated = False
    for i, row in enumerate(rows):
        if row["date"] == today:
            rows[i] = new_row
            updated = True
            break

    if not updated:
        rows.append(new_row)

    rows.sort(key=lambda x: x["date"])
    write_history(rows)

    return rows, new_row


def get_rate_on_or_before(rows, target_date):
    valid_rows = [
        row for row in rows
        if datetime.strptime(row["date"], "%Y-%m-%d").date() <= target_date
    ]

    if not valid_rows:
        return None

    latest_row = max(valid_rows, key=lambda x: x["date"])
    return float(latest_row["rate_22k"])


def calculate_summary(rows, today_row):
    today_date = datetime.strptime(today_row["date"], "%Y-%m-%d").date()
    today_22k = float(today_row["rate_22k"])

    previous_rows = [row for row in rows if row["date"] < today_row["date"]]
    yesterday_change = None

    if previous_rows:
        previous_row = max(previous_rows, key=lambda x: x["date"])
        yesterday_change = today_22k - float(previous_row["rate_22k"])

    rate_30_days_ago = get_rate_on_or_before(rows, today_date - timedelta(days=30))
    change_30_days = None
    if rate_30_days_ago is not None:
        change_30_days = today_22k - rate_30_days_ago

    rows_60_days = [
        row for row in rows
        if datetime.strptime(row["date"], "%Y-%m-%d").date() >= today_date - timedelta(days=60)
    ]

    rows_30_days = [
        row for row in rows
        if datetime.strptime(row["date"], "%Y-%m-%d").date() >= today_date - timedelta(days=30)
    ]

    highest_60 = max(float(row["rate_22k"]) for row in rows_60_days) if rows_60_days else today_22k
    lowest_30 = min(float(row["rate_22k"]) for row in rows_30_days) if rows_30_days else today_22k

    return {
        "yesterday_change": yesterday_change,
        "change_30_days": change_30_days,
        "highest_60": highest_60,
        "lowest_30": lowest_30,
        "total_records": len(rows),
    }


def send_email(rate22, rate24, website_updated, summary):
    checked_time = datetime.now(ZoneInfo("Asia/Qatar")).strftime("%d/%m/%Y %I:%M %p")

    body = f"""Daily Gold Rate - Doha

22 Carat Gold: {rate22}
24 Carat Gold: {rate24}

Daily Change 22K: {format_change(summary["yesterday_change"])}
30 Days Change 22K: {format_change(summary["change_30_days"])}

Highest 22K in Last 60 Days: {summary["highest_60"]:.2f} QAR
Lowest 22K in Last 30 Days: {summary["lowest_30"]:.2f} QAR

Total Stored Records: {summary["total_records"]}

Website Updated: {website_updated}
Checked Time: {checked_time} Doha Time

Source:
https://www.malabargoldanddiamonds.com/ae/goldprice
"""

    msg = MIMEText(body)
    msg["Subject"] = "Daily Doha Gold Rate"
    msg["From"] = os.environ["EMAIL_USER"]
    msg["To"] = os.environ["EMAIL_TO"]

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(os.environ["EMAIL_USER"], os.environ["EMAIL_APP_PASSWORD"])
        server.send_message(msg)


if __name__ == "__main__":
    rate22, rate24, website_updated = get_gold_rate()
    rows, today_row = update_history(rate22, rate24, website_updated)
    summary = calculate_summary(rows, today_row)
    send_email(rate22, rate24, website_updated, summary)
