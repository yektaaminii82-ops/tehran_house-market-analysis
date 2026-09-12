
import pandas as pd

MIN_LISTINGS_PER_YEAR = 15  # حداقل تعداد آگهی برای اینکه میانگین منطقه معتبر باشد

INPUT_2021 = "data/divar_2021_clean.csv"
INPUT_2023 = "data/divar_2023_clean.csv"
OUTPUT_PATH = "data/neighborhood_growth.csv"


def main():
    d21 = pd.read_csv(INPUT_2021)
    d23 = pd.read_csv(INPUT_2023)

    # میانگین قیمت هر متر مربع و تعداد آگهی به تفکیک منطقه، برای هر سال
    agg21 = (
        d21.groupby("neighborhood")["price_per_sqm"]
        .agg(["mean", "median", "count"])
        .rename(columns=lambda c: f"{c}_2021")
    )
    agg23 = (
        d23.groupby("neighborhood")["price_per_sqm"]
        .agg(["mean", "median", "count"])
        .rename(columns=lambda c: f"{c}_2023")
    )

    merged = agg21.join(agg23, how="inner")

    # فقط مناطقی که در هر دو سال داده‌ی کافی دارند
    merged = merged[
        (merged["count_2021"] >= MIN_LISTINGS_PER_YEAR)
        & (merged["count_2023"] >= MIN_LISTINGS_PER_YEAR)
    ].copy()

    merged["growth_pct"] = (
        (merged["median_2023"] - merged["median_2021"]) / merged["median_2021"] * 100
    )

    merged = merged.sort_values("growth_pct", ascending=False)

    merged_reset = merged.reset_index().rename(columns={"neighborhood": "منطقه"})

    # گرد کردن برای خوانایی
    for col in ["mean_2021", "median_2021", "mean_2023", "median_2023"]:
        merged_reset[col] = merged_reset[col].round(0).astype(int)
    merged_reset["growth_pct"] = merged_reset["growth_pct"].round(1)

    output_cols = [
        "منطقه", "median_2021", "median_2023", "growth_pct",
        "count_2021", "count_2023"
    ]
    result = merged_reset[output_cols]
    result.columns = [
        "منطقه", "قیمت میانه هر متر (۱۴۰۰)", "قیمت میانه هر متر (۱۴۰۲)",
        "رشد قیمت (٪)", "تعداد آگهی ۲۰۲۱", "تعداد آگهی ۲۰۲۳"
    ]

    result.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"تعداد مناطق قابل مقایسه (حداقل {MIN_LISTINGS_PER_YEAR} آگهی در هر سال): {len(result)}\n")

    print("=== ۱۰ منطقه با بیشترین رشد قیمت ===")
    print(result.head(10).to_string(index=False))

    print("\n=== ۱۰ منطقه با کمترین رشد قیمت ===")
    print(result.tail(10).to_string(index=False))

    print(f"\nمیانگین رشد قیمت کل تهران (بر اساس میانه‌ی مناطق): {result['رشد قیمت (٪)'].mean():.1f}٪")
    print(f"میانه‌ی رشد قیمت کل تهران: {result['رشد قیمت (٪)'].median():.1f}٪")
    print(f"\nذخیره شد: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
