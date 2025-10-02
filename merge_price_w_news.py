from glob import glob
import pandas as pd

from config import SELECTED_CURRENCY_PAIRS, FILTER_NEWS_W_PRICE_FOLDER_NAME, DATA_FOLDER_NAME
from utils import convert_to_datetime, convert_to_float, is_good_for_currency

FOLDER_NAME = "high_impact_news"
PERIOD = "PERIOD_H1"


news_df_list = []
files = glob(f'{DATA_FOLDER_NAME}/{FOLDER_NAME}/**/*.csv', recursive=True)
for file_path in files:
    file_name = file_path.split("/")[-1]
    year = file_path.split("/")[-2]

    df = pd.read_csv(file_path)
    df = df.loc[df["criteria"] != 0, :]
    df = df.loc[df["Currency"] != "CNY", :]

    # Convert datetime
    # Chuẩn hoá datetime để cùng thời gian với giá (lấy xuống)
    df['DateTime'] = df.apply(lambda row: convert_to_datetime(
        ' '.join(row['Date'].split()[1:]), row['Time'], year).replace(minute=0), axis=1)

    # Apply conversion
    df['Actual_float'] = df['Actual'].apply(convert_to_float)
    df['Forecast_float'] = df['Forecast'].apply(convert_to_float)

    # Create difference column
    df['Diff'] = df['Actual_float'] - df['Forecast_float']
    df['Good_for_Currency'] = df.apply(is_good_for_currency, axis=1)

    news_df_list.append(df)

# --- Concat news list ---
news_df = pd.concat(news_df_list)
news_df = news_df.reset_index(drop=True)
news_df['DateTime'] = pd.to_datetime(news_df['DateTime'], utc=True)
# --- Sort news data ---
news_df = news_df.sort_values(['DateTime', 'Currency'])


# --- Load price data ---
for currency_pair in SELECTED_CURRENCY_PAIRS:
    price_df = pd.read_csv(
        f"{DATA_FOLDER_NAME}/price_data_raw/{currency_pair}_{PERIOD}_2015-2025.csv", encoding="utf-16")
    price_df['DateTime'] = pd.to_datetime(
        price_df['time'], format="%Y.%m.%d %H:%M", utc=True)
    price_df = price_df.drop('time', axis=1)

    # --- Add preClose (shifted close) ---
    price_df['preClose'] = price_df['close'].shift(1)
    price_df['pctChg'] = (price_df['close'] -
                          price_df['preClose']) / price_df['preClose'] * 100

    # --- Merge on datetime ---
    merged_df = pd.merge(news_df, price_df, on="DateTime", how="left")

    # --- Sort merged data ---
    merged_df = merged_df.sort_values(['DateTime', 'Currency'])

    # --- Save merged data ---
    merged_df.to_csv(
        f"{DATA_FOLDER_NAME}/{FILTER_NEWS_W_PRICE_FOLDER_NAME}/{currency_pair}_{PERIOD}.csv", index=False)


# - Cần kiểm tra xem giá tại 1 thời điểm đó, có những tin gì và giá sẽ đi như thế nào
# + Nếu có nhiều tin thì gía như thế nào
# + Nếu chỉ có 1 tin thì giá như thế nào
# - Có thể đoán trước được là trong thời gian đấy những tin sẽ ảnh hưởng như thế nào tới giá

# + Với tin của đúng đồng thì liệu forecast có đúng với giá chạy không (accuracy và các metric thế nào)? (VD forecast lớn hơn actual tốt cho USD —> XAUUSD giảm)
# + Với nhiều tin néu +/- thì sẽ như thế nào với giá?
# + Với tin của đồng khác khác thì liệu có ảnh hưởng tới giá của đồng khác không (ảnh hưởng thế nào?, các metric thế nào?)? (VD tốt cho USD —> AUDJPY bị ảnh hưởng như thế nào?)
