try:
    import undetected_chromedriver as uc
    from selenium_stealth import stealth

    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except:
    from selenium import webdriver
    from webdriver_manager.chrome import ChromeDriverManager

    print("AF: No Chrome webdriver installed")
    driver = webdriver.Chrome(ChromeDriverManager().install())

import os
import time
import json
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from config import ALLOWED_ELEMENT_TYPES, ICON_COLOR_MAP, REQUEST_URL, MONTH_NUM_TO_NAME, SERVICE_ACCOUNT_FILE, SHARED_FOLDER_ID, FOLDER_NAME
from utils import reformat_scraped_data, construct_url

FOLDER_NAME = "raw_news"


def generate_driver():
    try:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.140 Safari/537.36"
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("user-agent={}".format(user_agent))
        driver = uc.Chrome(options=chrome_options)
        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True
                )
        return driver
    except Exception as e:
        print("Error in Driver: ", e)


current_time = datetime.now()
year = current_time.year
structure_data = []

for selected_year in range(year, year - 3, -1):
    for selected_month in range(1, 13):
        month_param = "{}.{}".format(
            MONTH_NUM_TO_NAME[selected_month],
            selected_year)
        url = construct_url(
            url=REQUEST_URL,
            month=month_param
        )
        driver = generate_driver()
        driver.implicitly_wait(20)

        with driver as browser:
            browser.get(url)

            commentr = WebDriverWait(browser, 20).until(
                EC.visibility_of_element_located((By.CLASS_NAME, 'calendar__table')))

            table = browser.find_element(By.CLASS_NAME, "calendar__table")

            data = []
            previous_row_count = 0
            # Scroll down to the end of the page
            while True:
                # Record the current scroll position
                before_scroll = browser.execute_script(
                    "return window.pageYOffset;")

                # Scroll down a fixed amount
                browser.execute_script(
                    "window.scrollTo(0, window.pageYOffset + 500);")

                # Wait for a short moment to allow content to load
                time.sleep(2)

                # Record the new scroll position
                after_scroll = browser.execute_script(
                    "return window.pageYOffset;")

                # If the scroll position hasn't changed, we've reached the end of the page
                if before_scroll == after_scroll:
                    break

            soup = BeautifulSoup(browser.page_source, "html.parser")
            previous_date = ""
            dictionary = {
                'event_id': [], 'Date': [], 'Time': [], 'Currency': [], 'Impact': [],
                'Description': [], 'Actual': [], 'Forecast': [], 'Previous': []}
            for row in soup.find_all("tr"):
                if "calendar__row" in row.get("class", []):
                    date_cell = row.find("td", {"class": "calendar__date"})
                    if date_cell is not None and date_cell.text.strip() != "":
                        date = date_cell.text.strip()
                        dictionary['Date'].append(date)
                        previous_date = date
                    else:
                        dictionary['Date'].append(previous_date)
                    time_cell = row.find("td", {"class": "calendar__time"})
                    if time_cell is not None:
                        dictionary['Time'].append(time_cell.text.strip())
                    else:
                        dictionary['Time'].append("")
                    currency_cell = row.find(
                        "td", {"class": "calendar__currency"})
                    if currency_cell is not None:
                        dictionary['Currency'].append(
                            currency_cell.text.strip())
                    else:
                        dictionary['Currency'].append("")
                    actual_cell = row.find("td", {"class": "calendar__actual"})
                    if actual_cell is not None:
                        dictionary['Actual'].append(actual_cell.text.strip())
                    else:
                        dictionary['Actual'].append("")
                    forecast_cell = row.find(
                        "td", {"class": "calendar__forecast"})
                    if forecast_cell is not None:
                        dictionary['Forecast'].append(
                            forecast_cell.text.strip())
                    else:
                        dictionary['Forecast'].append("")
                    previous_cell = row.find(
                        "td", {"class": "calendar__previous"})
                    if previous_cell is not None:
                        dictionary['Previous'].append(
                            previous_cell.text.strip())
                    else:
                        dictionary['Previous'].append("")
                    event_cell = row.find("td", {"class": "calendar__event"})
                    if event_cell is not None:

                        event_id = row.get("data-event-id", "")
                        dictionary['event_id'].append(
                            event_id)

                        dictionary['Description'].append(
                            event_cell.text.strip())
                    else:
                        event_id = row.get("data-event-id", "")
                        dictionary['event_id'].append(
                            event_id)
                        dictionary['Description'].append("")
                    impact_cell = row.find("td", {"class": "calendar__impact"})
                    if impact_cell is not None:
                        impact = impact_cell.find('span', {'title': True})
                        if impact is not None:
                            dictionary['Impact'].append(impact['title'])
                        else:
                            dictionary['Impact'].append("")
                    else:
                        dictionary['Impact'].append("")

            data = pd.DataFrame.from_dict(dictionary)

            # Remove rows that only have date information
            data = data[data['Currency'] != '']

            file_name = f"{FOLDER_NAME}/{selected_year}/{selected_month}.csv"

            os.makedirs(f"{FOLDER_NAME}/{selected_year}", exist_ok=True)
            data.to_csv(file_name, index=False)
