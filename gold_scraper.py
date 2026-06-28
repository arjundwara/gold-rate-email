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
DISPLAY_SOURCE_URL = BASE_URL + "/ae/goldprice"
API_URL = BASE_URL + "/us/malabarprice/index/getrates/"


def clean_rate(value):
    return float(value.replace("QAR", "").replace(",", "").strip())


def format_change(value, percent=None):
    if value is None:
        return "Not enough data"

    arrow = "▲" if value > 0 else "▼" if value < 0 else "—"
    sign = "+" if value > 0 else ""

    if percent is None:
        return f"{arrow} {sign}{value:.2f} QAR"

    return f"{arrow} {sign}{value:.2f} QAR ({sign}{percent:.2f}%)"


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
        timeout=30,
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

    found_today = False

    for index, row in enumerate(rows):
        if row["date"] == today:
            rows[index] = new_row
            found_today = True
            break

    if not found_today:
        rows.append(new_row)

    rows.sort(key=lambda x: x["date"])
    write_history(rows)

    return rows, new_row


def rate_on_or_before(rows, target_date):
    valid_rows = []

    for row in rows:
        row_date = datetime.strptime(row["date"], "%Y-%m-%d").date()
        if row_date <= target_date:
            valid_rows.append(row)

    if not valid_rows:
        return None

    latest_row = max(valid_rows, key=lambda x: x["date"])
    return float(latest_row["rate_22k"])


def calc_change(current, old):
    if old is None:
        return None, None

    difference = current - old
    percent = (difference / old) * 100 if old != 0 else None

    return difference, percent


def calculate_summary(rows, today_row):
    today_date = datetime.strptime(today_row["date"], "%Y-%m-%d").date()
    today_22k = float(today_row["rate_22k"])

    previous_rows = [row for row in rows if row["date"] < today_row["date"]]
    previous_rate = None

    if previous_rows:
        previous_row = max(previous_rows, key=lambda x: x["date"])
        previous_rate = float(previous_row["rate_22k"])

    rate_7_days_ago = rate_on_or_before(rows, today_date - timedelta(days=7))
    rate_30_days_ago = rate_on_or_before(rows, today_date - timedelta(days=30))

    daily_change, daily_percent = calc_change(today_22k, previous_rate)
    change_7_days, percent_7_days = calc_change(today_22k, rate_7_days_ago)
    change_30_days, percent_30_days = calc_change(today_22k, rate_30_days_ago)

    rows_30_days = [
        row for row in rows
        if datetime.strptime(row["date"], "%Y-%m-%d").date() >= today_date - timedelta(days=30)
    ]

    rows_60_days = [
        row for row in rows
        if datetime.strptime(row["date"], "%Y-%m-%d").date() >= today_date - timedelta(days=60)
    ]

    rates_30 = [float(row["rate_22k"]) for row in rows_30_days]
    rates_60 = [float(row["rate_22k"]) for row in rows_60_days]

    highest_30 = max(rates_30) if rates_30 else today_22k
    lowest_30 = min(rates_30) if rates_30 else today_22k
    average_30 = sum(rates_30) / len(rates_30) if rates_30 else today_22k

    highest_60 = max(rates_60) if rates_60 else today_22k
    lowest_60 = min(rates_60) if rates_60 else today_22k
    average_60 = sum(rates_60) / len(rates_60) if rates_60 else today_22k

    below_60_high = today_22k - highest_60
    above_30_low = today_22k - lowest_30
    above_60_low = today_22k - lowest_60

    if today_22k <= lowest_60 * 1.01:
        buy_signal = "🟢 VERY GOOD BUY - Current rate is within 1% of the 60-day low."
    elif today_22k <= average_60:
        buy_signal = "🟢 GOOD BUY - Current rate is below or near the 60-day average."
    elif today_22k >= highest_60 * 0.99:
        buy_signal = "🔴 WAIT - Current rate is very close to the 60-day high."
    else:
        buy_signal = "🟡 NEUTRAL - Price is between the recent high and low range."

    return {
        "daily_change": daily_change,
        "daily_percent": daily_percent,
        "change_7_days": change_7_days,
        "percent_7_days": percent_7_days,
        "change_30_days": change_30_days,
        "percent_30_days": percent_30_days,
        "highest_30": highest_30,
        "lowest_30": lowest_30,
        "average_30": average_30,
        "highest_60": highest_60,
        "lowest_60": lowest_60,
        "average_60": average_60,
        "below_60_high": below_60_high,
        "above_30_low": above_30_low,
        "above_60_low": above_60_low,
        "buy_signal": buy_signal,
        "total_records": len(rows),
    }


def send_email(rate22, rate24, website_updated, summary):
    checked_time = datetime.now(ZoneInfo("Asia/Qatar")).strftime("%d/%m/%Y %I:%M %p")

    body = f"""📈 Malabar Gold Rate - Doha

Today's Rate
--------------------------
22K : {rate22}
24K : {rate24}

Changes - 22K
--------------------------
Yesterday : {format_change(summary["daily_change"], summary["daily_percent"])}
7 Days    : {format_change(summary["change_7_days"], summary["percent_7_days"])}
30 Days   : {format_change(summary["change_30_days"], summary["percent_30_days"])}

Statistics - 22K
--------------------------
Highest 30 Days : {summary["highest_30"]:.2f} QAR
Lowest 30 Days  : {summary["lowest_30"]:.2f} QAR
Average 30 Days : {summary["average_30"]:.2f} QAR

Highest 60 Days : {summary["highest_60"]:.2f} QAR
Lowest 60 Days  : {summary["lowest_60"]:.2f} QAR
Average 60 Days : {summary["average_60"]:.2f} QAR

Position - 22K
--------------------------
Current vs 60-Day High : {format_change(summary["below_60_high"])}
Current vs 30-Day Low  : {format_change(summary["above_30_low"])}
Current vs 60-Day Low  : {format_change(summary["above_60_low"])}

Buy Signal
--------------------------
{summary["buy_signal"]}

Records Stored
--------------------------
{summary["total_records"]} days

Website Updated
--------------------------
{website_updated}

Checked
--------------------------
{checked_time} Doha Time

Source:
{DISPLAY_SOURCE_URL}
"""

    msg = MIMEText(body, "plain", "utf-8")
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
