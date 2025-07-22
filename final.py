import smtplib
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import random

# ------------ Config ------------
URL = "https://visaslots.info"
TARGET_LOCATIONS = ["MUMBAI CONSULAR", "MUMBAI VAC",
                    "NEW DELHI CONSULAR", "NEW DELHI VAC",
                    "HYDERABAD CONSULAR", "HYDERABAD VAC"]
# random.randint(300, 600)  # 5–10 min

# Email Settings
from dotenv import load_dotenv
import os

load_dotenv()

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
CHECK_INTERVAL_SECONDS =int(os.getenv("CHECK_INTERVAL_SECONDS", 300)) # Default to 5 minutes if not set

# ------------ Selenium Setup ------------
# options = Options()
# options.headless = True
# options.add_argument("--no-sandbox")
# options.add_argument("--disable-gpu")
# options.add_argument("--disable-dev-shm-usage")
# options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/114.0.0.0 Safari/537.36")

# driver = webdriver.Chrome(options=options)

from selenium.webdriver.chrome.service import Service

options = webdriver.ChromeOptions()
options.add_argument('--headless=new')  # Use --headless=new for recent Chrome
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
options.add_argument('--window-size=1920x1080')
options.add_argument('--remote-debugging-port=9222')

# Explicitly point to chromedriver if needed
driver = webdriver.Chrome(service=Service("/usr/local/bin/chromedriver"), options=options)


def send_email(location, earliest, updated, slots):
    body = f"""🎯 Visa Slot Available!

Location: {location}
Earliest Date: {earliest}
Updated: {updated}
Slots Available: {slots}

Visit: {URL}
"""
    msg = MIMEText(body)
    msg["Subject"] = f"Visa Slot Alert – {location}"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
            print("✅ Email Sent!")
    except Exception as e:
        print("❌ Email failed:", e)

def check_f1_slots():
    print("Checking Visa Slots...", flush=True)
    driver.get(URL)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    f1_section = soup.find("details", id="vsloc-f1-f2")
    table = f1_section.find("table", class_="sortable")
    rows = table.find("tbody").find_all("tr")

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 5:
            continue

        location = cols[0].text.strip()
        visa_type = cols[1].text.strip()
        updated = cols[2].text.strip()
        earliest = cols[3].text.strip()
        slots = cols[4].text.strip()

        if location in TARGET_LOCATIONS:
            print(f"[{location}] Slots: {slots}", flush=True)
            if slots.isdigit() and int(slots) > 0:
            # if True:
                send_email(location, earliest, updated, slots)
            else:
                print(f"No slots available for {location}.", flush=True)

# ------------ Run Loop ------------
while True:
    try:
        check_f1_slots()
    except Exception as e:
        print("❌ Error:", e, flush=True)

    print(f"Waiting {CHECK_INTERVAL_SECONDS} sec...\n", flush=True)
    time.sleep(CHECK_INTERVAL_SECONDS)
