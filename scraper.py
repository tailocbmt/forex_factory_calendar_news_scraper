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

import time
import json
import pandas as pd
from datetime import datetime
from config import ALLOWED_ELEMENT_TYPES, ICON_COLOR_MAP, REQUEST_URL, MONTH_NUM_TO_NAME, SERVICE_ACCOUNT_FILE, SHARED_FOLDER_ID, FOLDER_NAME
from utils import reformat_scraped_data, construct_url
from drive_handler import DriveUploader


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


uploader = DriveUploader(
    service_account_file=SERVICE_ACCOUNT_FILE,
    root_folder_id=SHARED_FOLDER_ID
)

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
            browser.get_screenshot_as_file("debug.png")

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

            # Now that we've scrolled to the end, collect the data
            for row in table.find_elements(By.TAG_NAME, "tr"):
                row_data = []
                for element in row.find_elements(By.TAG_NAME, "td"):
                    class_name = element.get_attribute('class')
                    if class_name in ALLOWED_ELEMENT_TYPES:
                        if element.text:
                            row_data.append(element.text)
                        elif "calendar__impact" in class_name:
                            impact_elements = element.find_elements(
                                By.TAG_NAME, "span")
                            for impact in impact_elements:
                                impact_class = impact.get_attribute("class")
                                color = ICON_COLOR_MAP[impact_class]
                            if color:
                                row_data.append(color)
                            else:
                                row_data.append("impact")

                if len(row_data):
                    data.append(row_data)

            local_file_path = reformat_scraped_data(
                data, selected_month, selected_year)
            file_drive_id = uploader.upload_or_replace_file(
                file_path=local_file_path,
                folder_name=str(selected_year)
            )

            structure_data.append([
                selected_year, selected_month, file_drive_id
            ])

structure_df = pd.DataFrame(
    structure_data, columns=['year', 'month', 'drive_id'])
structure_file_name = f"{FOLDER_NAME}/metadata.csv"
structure_df.to_csv(structure_file_name, index=False)
structure_drive_id = uploader.update_file(
    file_path=structure_file_name
)
