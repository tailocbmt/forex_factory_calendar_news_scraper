import os
import re
import json
import pytz
import pandas as pd
from urllib.parse import urlencode
from datetime import datetime, timezone

from tzlocal import get_localzone

from config import ALLOWED_IMPACT_COLORS, FOLDER_NAME


def is_good_for_currency(row):
    """
        Chuyển dự đoán bình thường thành có tốt cho đồng tiền đó (currency) không
        Args: row (Dict): Dictionary chứa dữ liệu từng hàng (row).
        Returns: int: 1 (tốt cho đồng tiền), -1 (Không tốt cho đồng tiền), 0 (không tốt không xấu)
    """
    if row['criteria'] == 1:
        if row['Diff'] > 0:
            return 1
        elif row['Diff'] < 0:
            return -1
        else:
            return 0
    elif row['criteria'] == -1:
        if row['Diff'] < 0:
            return 1
        elif row['Diff'] > 0:
            return -1
        else:
            return 0
    else:
        return 0


def convert_to_float(value):
    if pd.isna(value) or value == '':
        return None
    value = str(value).strip().replace('%', '').replace(
        ',', '').replace('B', '').replace('K', '').replace('M', '').replace('<', '')

    return round(float(value), 4)


def construct_url(url: str, **params):
    url = '{}?{}'.format(url, urlencode(params))

    return url


def read_json(path):
    """
        Read JSON data from a file.
        Args: path (str): The path to the JSON file.
        Returns: dict: The loaded JSON data.
    """
    with open(path, 'r') as f:
        data = json.load(f)
    return data


def contains_day_or_month(text):
    """
    Check if the given text contains a day of the week or a month.

    Args:
        text (str): The input text to check.

    Returns:
        tuple: A tuple containing a boolean indicating whether a match was found,
        and the matched text (day or month) if found.
    """

    # Regular expressions for days of the week and months
    days_of_week = r'\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b'
    months = r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b'
    pattern = f'({days_of_week}|{months})'

    match = re.search(pattern, text, re.IGNORECASE)

    if not match:
        return False, None

    matched_text = match.group(0)
    if re.match(days_of_week, matched_text, re.IGNORECASE):
        return True, matched_text


def find_pattern_category(text):
    """
    Find the category of a specific pattern within the given text.

    Args:
        text (str): The input text to analyze.

    Returns:
        tuple: A tuple containing a boolean indicating whether a match was found,
        the category of the matched pattern, and the matched text.
    """

    # Regular expressions for different patterns
    time_pattern = r'\d{1,2}:\d{2}(am|pm)'
    day_pattern = r'Day\s+\d+'
    date_range_pattern = r'\d{1,2}(st|nd|rd|th)\s*-\s*\d{1,2}(st|nd|rd|th)'
    tentative_pattern = r'\bTentative\b'
    pattern = f'({time_pattern}|{day_pattern}|{date_range_pattern}|{tentative_pattern})'
    match = re.search(pattern, text, re.IGNORECASE)

    if not match:
        return False, None, None

    matched_text = match.group(0)
    if re.match(time_pattern, matched_text, re.IGNORECASE):
        category = "time"
    elif re.match(day_pattern, matched_text, re.IGNORECASE):
        category = "day_reference"
    elif re.match(date_range_pattern, matched_text, re.IGNORECASE):
        category = "date_range"
    elif re.match(tentative_pattern, matched_text, re.IGNORECASE):
        category = "tentative"
    else:
        category = "Unknown"
    return True, category, matched_text


def convert_to_datetime(current_date, current_time, year):
    """
    Convert to datetime

    Args:
        data (list): The scraped data as a list of lists.
        month (str): The month for naming the output CSV file.

    Returns:
        pd.DataFrame: The reformatted data as a DataFrame.
    """
    current_timezone = get_localzone()
    convert_time_zone = pytz.UTC

    if "Day" in current_time or "Tentative" in current_time:
        current_time = "12:00am"
        convert_time_zone = current_timezone

    current_datetime = datetime.strptime(
        f'{current_date} {year} {current_time}', '%b %d %Y %I:%M%p').astimezone(
            current_timezone).astimezone(
                convert_time_zone)

    return current_datetime


def reformat_scraped_data(data, month, year):
    """
    Reformat scraped data and save it as a DataFrame and a CSV file.

    Args:
        data (list): The scraped data as a list of lists.
        month (str): The month for naming the output CSV file.

    Returns:
        pd.DataFrame: The reformatted data as a DataFrame.
    """
    current_date = ''
    current_time = ''
    structured_rows = []

    for row in data:
        if len(row) == 1 or len(row) == 5:
            match, day = contains_day_or_month(row[0])
            if match:
                current_date = row[0].replace(day, "").replace("\n", "")
        if len(row) == 4:
            current_time = row[0]

        if len(row) == 5:
            current_time = row[1]

        if len(row) > 1:
            if row[-2] not in ALLOWED_IMPACT_COLORS or current_date == "" or current_time == "":
                continue

            current_datetime = convert_to_datetime(
                current_date, year)
            current_datetime_str = current_datetime.strftime(
                '%Y.%m.%d %H:%M:%S')

            event = row[-1]
            impact = row[-2]
            currency = row[-3]

            structured_rows.append(
                [current_datetime, current_datetime_str, currency, impact, event]
            )

    file_name = f"{FOLDER_NAME}/{year}/{month}.csv"
    df = pd.DataFrame(
        structured_rows, columns=['temp_datetime', 'datetime', 'currency', 'impact', 'event'])
    df = df.loc[df['currency'] != "All", :]
    df = df.sort_values(['datetime'])
    df = df.drop(columns=['temp_datetime'])

    os.makedirs(f"{FOLDER_NAME}/{year}", exist_ok=True)
    df.to_csv(file_name, index=False)

    return file_name
