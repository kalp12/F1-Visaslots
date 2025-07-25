import smtplib
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from selenium.webdriver.chrome.service import Service

# ------------ Config ------------
URL = "https://visaslots.info"
TARGET_LOCATIONS_VAC = ["MUMBAI VAC",
                    "NEW DELHI VAC",
                    "HYDERABAD VAC",
                    "CHENNAI VAC",
                    "KOLKATA VAC",]
TARGET_LOCATIONS_CON = ["MUMBAI CONSULAR",
                    "NEW DELHI CONSULAR",
                    "HYDERABAD CONSULAR",
                    "CHENNAI CONSULAR",
                    "KOLKATA CONSULAR"]
# random.randint(300, 600)  # 5–10 min

# Email Settings
from dotenv import load_dotenv
import os


load_dotenv()

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
CHECK_INTERVAL_SECONDS =int(os.getenv("CHECK_INTERVAL_SECONDS", 300)) # Default to 5 minutes if not set
VAC_MINUTES =int(os.getenv("VAC_MINUTES", 5))
CON_MINUTES =int(os.getenv("CON_MINUTES", 5))

# ------------ Selenium Setup ------------
def create_driver_local():
    from fake_useragent import UserAgent
    ua = UserAgent()
    user_agent = ua.random
    print(f"[INFO] Using User-Agent: {user_agent}", flush=True)
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920x1080')
    chrome_options.add_argument(f'user-agent={user_agent}')
    
    return webdriver.Chrome(options=chrome_options)

def create_driver():
    from fake_useragent import UserAgent
    ua = UserAgent()
    user_agent = ua.random
    print(f"[INFO] Using User-Agent: {user_agent}", flush=True)

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920x1080')
    chrome_options.add_argument(f'user-agent={user_agent}')
    
    return webdriver.Chrome(service=Service("/usr/local/bin/chromedriver"), options=chrome_options)

driver = create_driver()
# driver = create_driver_local()


# options = webdriver.ChromeOptions()
# options.add_argument('--headless=new')  # Use --headless=new for recent Chrome
# options.add_argument('--no-sandbox')
# options.add_argument('--disable-dev-shm-usage')
# options.add_argument('--disable-gpu')
# options.add_argument('--window-size=1920x1080')
# options.add_argument('--remote-debugging-port=9222')
# from fake_useragent import UserAgent
# ua = UserAgent()
# options.add_argument(f"user-agent={ua.random}")
# # print(f"[DEBUG] Using User-Agent: {ua.random}", flush=True)


# # Explicitly point to chromedriver if needed
# driver = webdriver.Chrome(service=Service("/usr/local/bin/chromedriver"), options=options)


def send_email(location, earliest, updated, slots):
    body = f"""🎯 Visa Slot Available!

Location: {location}
Earliest Date: {earliest}
Updated: {updated}
Slots Available: {slots}

Visit: {URL}
"""
    msg = MIMEText(body)
    msg["Subject"] = f"Visa Slot Alert - {location}"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
            print("✅ Email Sent!")
    except Exception as e:
        print("❌ Email failed:", e)

import re

def is_fresh(updated_str, max_age_minutes=10):
    updated_str = updated_str.lower().strip()
    # print(f"[DEBUG] Updated string: {updated_str}")

    # Match formats like "00h 33m 15s ago"
    match = re.match(r"(?:(\d+)h)?\s*(?:(\d+)m)?\s*(?:(\d+)s)?", updated_str)
    # print(f"[DEBUG] Match result: {match}")
    if not match:
        return False

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    total_minutes = hours * 60 + minutes + (seconds / 60)
    print(f"[DEBUG] Parsed age: {total_minutes:.2f} minutes")

    return total_minutes <= max_age_minutes


def check_f1_slots():
    print("Checking Visa Slots...", flush=True)
    driver.get(URL)
    # time.sleep(5)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    f1_section = soup.find("details", id="vsloc-f1-f2")
    if not f1_section:
        print("❌ F1 section not found — possible rate limit or layout change.", flush=True)
        print("⏳ Sleeping extra 10 minutes to avoid ban...", flush=True)
        driver.quit()
        time.sleep(10)
        globals()['driver'] = create_driver()  # replace global driver
        time.sleep(600)
        return
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

        if location in TARGET_LOCATIONS_VAC:
     
            if not is_fresh(updated, max_age_minutes=VAC_MINUTES):
                print(f"⚠️ Skipping stale data for {location} (updated {updated})",flush=True)
                continue
    
            print(f"[{location}] Slots: {slots}", flush=True)
            if slots.isdigit() and int(slots) > 0:
            # if True:
                send_email(location, earliest, updated, slots)
            else:
                print(f"No slots available for {location}.", flush=True)
                
        if location in TARGET_LOCATIONS_CON:
            if not is_fresh(updated, max_age_minutes=CON_MINUTES):
                print(f"⚠️ Skipping stale data for {location} (updated {updated})",flush=True)
                continue
    
            print(f"[{location}] Slots: {slots}", flush=True)
            if slots.isdigit() and int(slots) > 0:
                send_email(location, earliest, updated, slots)
            else:
                print(f"No slots available for {location}.", flush=True)

# ------------ Run Loop ------------
# while True:
#     try:
#         check_f1_slots()
#     except Exception as e:
#         print("❌ Error:", e, flush=True)

#     print(f"Waiting {CHECK_INTERVAL_SECONDS} sec...\n", flush=True)
#     time.sleep(CHECK_INTERVAL_SECONDS)

check_count = 0

while True:
    try:
        check_f1_slots()
    except Exception as e:
        print("❌ Error:", e, flush=True)
        print("🔁 Restarting browser due to error...", flush=True)
        driver.quit()
        driver = create_driver()
        

    check_count += 1
    if check_count % 30 == 0:
        print("🔁 Periodic restart after 30 checks", flush=True)
        driver.quit()
        driver = create_driver()
        # driver = create_driver_local()
        

    print(f"Waiting {CHECK_INTERVAL_SECONDS} sec...\n", flush=True)
    time.sleep(CHECK_INTERVAL_SECONDS)
