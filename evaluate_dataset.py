import os
import pandas as pd
from evaluation.utils import IMAGE_FOLDER, evaluate, get_direction_value, get_groupby_values
from config import FILTER_NEWS_W_PRICE_FOLDER_NAME, DATA_FOLDER_NAME, ALLOWED_CURRENCY_CODES, SELECTED_CURRENCY_PAIRS

PERIOD = "PERIOD_H1"

for CURRENCY_PAIR in SELECTED_CURRENCY_PAIRS:
    os.makedirs(f"{IMAGE_FOLDER}/{CURRENCY_PAIR}", exist_ok=True)

    price_news_df = pd.read_csv(
        f"{DATA_FOLDER_NAME}/{FILTER_NEWS_W_PRICE_FOLDER_NAME}/{CURRENCY_PAIR}_{PERIOD}.csv")

    # Lọc ra những tin trong những cặp quan sát thôi
    price_news_df = price_news_df.loc[price_news_df["Currency"].isin(
        ALLOWED_CURRENCY_CODES), :]
    price_news_df = price_news_df[price_news_df['pctChg'].notna()]

    price_news_df = price_news_df.sort_values(['DateTime', 'Currency'])

    price_news_df["price_direction"] = price_news_df["pctChg"].apply(
        lambda x: -get_direction_value(x))

    # Đánh giá toàn bộ các tin có ảnh hưởng tới giá không?
    total_naive_prediction_result = evaluate(
        price_news_df["price_direction"],
        price_news_df["Good_for_Currency"],
        CURRENCY_PAIR,
        "total"
    )
    print("TOTAL")
    print(total_naive_prediction_result)
    total_naive_prediction_result["classification_report"].to_csv(
        f"{IMAGE_FOLDER}/{CURRENCY_PAIR}/total_classification_report.csv")

    # Đánh giá toàn bộ các tin gộp theo giờ có ảnh hưởng thế nào giá không?
    groupby_df = price_news_df.groupby(["DateTime"]).apply(get_groupby_values)
    groupby_df = groupby_df.sort_index()
    groupby_naive_prediction_result = evaluate(
        groupby_df["price_direction"],
        groupby_df["Good_for_Currency"],
        CURRENCY_PAIR,
        "total_groupby"
    )
    print("TOTAL GROUPBY")
    print(groupby_naive_prediction_result)
    groupby_naive_prediction_result["classification_report"].to_csv(
        f"{IMAGE_FOLDER}/{CURRENCY_PAIR}/total_groupby_classification_report.csv")

    for CURRENCY_CODE in ALLOWED_CURRENCY_CODES:
        # Đánh giá từng loại tin có ảnh hưởng tới giá không?
        if CURRENCY_CODE != "CURRENCY":
            separate_price_news_df = price_news_df.loc[
                price_news_df["Currency"]
                == CURRENCY_CODE, :]

            separate_naive_prediction_result = evaluate(
                separate_price_news_df["price_direction"],
                separate_price_news_df["Good_for_Currency"],
                CURRENCY_PAIR,
                CURRENCY_CODE
            )

            print(CURRENCY_CODE)
            print(separate_naive_prediction_result)
            separate_naive_prediction_result["classification_report"].to_csv(
                f"{IMAGE_FOLDER}/{CURRENCY_PAIR}/{CURRENCY_CODE}_classification_report.csv")
        else:
            CURRENCY_CODE = CURRENCY_PAIR
            CURRENCY_CODES = [CURRENCY_PAIR[:3], CURRENCY_PAIR[3:]]
            separate_price_news_df = price_news_df.loc[
                (price_news_df["Currency"] == CURRENCY_CODES[0]) | ((price_news_df["Currency"] == CURRENCY_CODES[1])), :]

        # Đánh giá từng loại tin gộp theo giờ có ảnh hưởng thế nào giá không?
        groupby_separate_price_news_df = separate_price_news_df.groupby(
            ["DateTime"]).apply(get_groupby_values)
        groupby_separate_price_news_df = groupby_separate_price_news_df.sort_index()
        groupby_separate_naive_prediction_result = evaluate(
            groupby_separate_price_news_df["price_direction"],
            groupby_separate_price_news_df["Good_for_Currency"],
            CURRENCY_PAIR,
            f"{CURRENCY_CODE}_groupby"
        )
        print(f"{CURRENCY_CODE} groupby")
        print(groupby_separate_naive_prediction_result)
        groupby_separate_naive_prediction_result["classification_report"].to_csv(
            f"{IMAGE_FOLDER}/{CURRENCY_PAIR}/groupby_{CURRENCY_CODE}_classification_report.csv")
