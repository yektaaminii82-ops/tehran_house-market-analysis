
import json
import pandas as pd
import numpy as np

INPUT_PATH = "data/Divar_2021.json"
OUTPUT_PATH = "data/divar_2021_clean.csv"

# فرض: داده‌های ۲۰۲۱ از سال شمسی ۱۴۰۰ (~۲۰۲۱-۲۰۲۲ میلادی) جمع‌آوری شده‌اند
CURRENT_JALALI_YEAR = 1400


def load_and_filter():
    with open(INPUT_PATH, encoding="utf-8") as f:
        data = json.load(f)

    print(f"تعداد کل رکوردهای خام: {len(data):,}")

    # فقط فروش آپارتمان مسکونی
    apt = [d for d in data if d.get("sub_category") == "apartment-sell"]
    print(f"تعداد آگهی‌های فروش آپارتمان: {len(apt):,}")

    return apt


def to_dataframe(records):
    df = pd.DataFrame(records)

    # ستون‌های مورد نیاز را انتخاب و استاندارد می‌کنیم
    df = df[[
        "district", "price", "area", "year", "room",
        "floor", "elevator", "parking", "storage"
    ]].copy()

    df = df.rename(columns={
        "district": "neighborhood",
        "price": "price_toman",
        "area": "area_sqm",
        "year": "build_year_jalali",
        "room": "rooms",
        "storage": "warehouse",
    })

    return df


def clean(df):
    # حذف رکوردهای بدون قیمت یا بدون متراژ (غیرقابل استفاده برای تحلیل قیمت)
    before = len(df)
    df = df.dropna(subset=["price_toman", "area_sqm"])
    print(f"حذف {before - len(df):,} رکورد به دلیل نبود قیمت/متراژ")

    # قیمت و متراژ باید عدد مثبت معقول باشند
    df["price_toman"] = pd.to_numeric(df["price_toman"], errors="coerce")
    df["area_sqm"] = pd.to_numeric(df["area_sqm"], errors="coerce")
    df = df.dropna(subset=["price_toman", "area_sqm"])

    # حذف outlier های واضح: متراژ آپارتمان مسکونی منطقی بین ۱۵ تا ۱۰۰۰ متر
    before = len(df)
    df = df[(df["area_sqm"] >= 15) & (df["area_sqm"] <= 1000)]
    df = df[df["price_toman"] > 0]
    print(f"حذف {before - len(df):,} رکورد outlier (متراژ/قیمت نامعقول)")

    # قیمت هر متر مربع - مهم‌ترین شاخص برای مقایسه‌ی مناطق
    df["price_per_sqm"] = df["price_toman"] / df["area_sqm"]

    # حذف outlier های شدید قیمت هر متر (خطاهای تایپی در آگهی‌ها) با برش صدک ۰.۵٪ و ۹۹.۵٪
    lower, upper = df["price_per_sqm"].quantile([0.005, 0.995])
    before = len(df)
    df = df[(df["price_per_sqm"] >= lower) & (df["price_per_sqm"] <= upper)]
    print(f"حذف {before - len(df):,} رکورد outlier قیمت هر متر (صدک ۰.۵٪-۹۹.۵٪)")

    # سن بنا بر اساس سال ساخت شمسی
    df["build_year_jalali"] = pd.to_numeric(df["build_year_jalali"], errors="coerce")
    df["building_age"] = CURRENT_JALALI_YEAR - df["build_year_jalali"]
    df.loc[(df["building_age"] < 0) | (df["building_age"] > 60), "building_age"] = np.nan

    # بولین‌ها را یکدست می‌کنیم
    for col in ["elevator", "parking", "warehouse"]:
        df[col] = df[col].fillna(False).astype(bool)

    # نام منطقه را پاک‌سازی می‌کنیم (حذف نویسه‌ی نیم‌فاصله برای یکدست‌سازی)
    df["neighborhood"] = (
        df["neighborhood"]
        .astype(str)
        .str.replace("\u200c", " ", regex=False)
        .str.strip()
    )

    df["year"] = 2021  # برچسب سال دیتاست برای مقایسه‌ی بعدی

    # حذف ستون سال ساخت خام (سن بنا جایگزین آن شد)
    df = df.drop(columns=["build_year_jalali"])

    return df.reset_index(drop=True)


def main():
    records = load_and_filter()
    df = to_dataframe(records)
    df = clean(df)

    print("\nخلاصه‌ی آماری قیمت هر متر مربع (تومان):")
    print(df["price_per_sqm"].describe())

    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"\nذخیره شد: {OUTPUT_PATH}  ({len(df):,} رکورد تمیز)")


if __name__ == "__main__":
    main()
