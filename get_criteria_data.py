from glob import glob
import json
import os
import pandas as pd
import requests


SAVED_FOLDER_NAME = "high_impact_news"
FOLDER_NAME = "raw_news"
URL_FORMAT = "https://www.forexfactory.com/calendar/details/1-{}"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.forexfactory.com/",
}

files = glob(f'{FOLDER_NAME}/**/*.csv', recursive=True)
for file_path in files:
    df = pd.read_csv(file_path)
    df.loc[:, ["Date", "Time"]] = df.loc[:, ["Date", "Time"]].ffill()
    df = df.loc[df["Impact"] == "High Impact Expected", :]

    file_name = file_path.split("/")[-1]
    year = file_path.split("/")[-2]

    usual_effect_raw_data, usual_effect_data = [], []
    for _, row in df.iterrows():
        request_url = URL_FORMAT.format(row["event_id"])
        response = requests.get(
            request_url, headers=headers)

        usual_effect_raw_value = ""
        usual_effect_value = 0
        if response.status_code == 200:
            print(request_url)
            json_data = json.loads(response.text)
            specs_data = json_data.get("data", []).get('specs', [])

            for spec in specs_data:
                if "Usual Effect" == spec["title"].strip():
                    usual_effect_raw_value = spec["html"]
                    if usual_effect_raw_value == "'Actual' greater than 'Forecast' is good for currency;":
                        usual_effect_value = 1
                    elif usual_effect_raw_value == "'Actual' less than 'Forecast' is good for currency;":
                        usual_effect_value = -1
                    else:
                        usual_effect_value = 0
        else:
            print(f"Request failed. Status code: {response.status_code}")

        usual_effect_raw_data.append(usual_effect_raw_value)
        usual_effect_data.append(usual_effect_value)

    df["raw_criteria"] = usual_effect_raw_data
    df["criteria"] = usual_effect_data

    os.makedirs(f"{SAVED_FOLDER_NAME}/{year}", exist_ok=True)
    df.to_csv(f"{SAVED_FOLDER_NAME}/{year}/{file_name}", index=False)
