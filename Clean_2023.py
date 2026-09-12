"""
تمیزکاری دیتاست ۲۰۲۳ دیوار (Divar_2023.csv)
تبدیل قیمت فارسی به عدد، استخراج منطقه از آدرس،
و هماهنگ‌سازی اسکیما با دیتاست ۲۰۲۱.

نحوه‌ی اجرا:
این فایل باید داخل پوشه‌ی اصلی پروژه باشد (کنار پوشه‌ی data)، یعنی:
tehran_housing_market_analysis/
    clean_2023.py   <-- همینجا
    data/
        Divar_2023.csv
"""

import re
import pandas as pd
import numpy as np

INPUT_PATH = "data/Divar_2023.csv"
OUTPUT_PATH = "data/divar_2023_clean.csv"

CURRENT_JALALI_YEAR = 1402  # داده‌های ۲۰۲۳ ~ سال شمسی ۱۴۰۲

PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ENGLISH_DIGITS = "0123456789"
DIGIT_MAP = str.maketrans(PERSIAN_DIGITS, ENGLISH_DIGITS)


def persian_price_to_number(text):
    """تبدیل رشته‌ی قیمت فارسی (مثل '۱۸٬۳۶۰٬۰۰۰٬۰۰۰ تومان') به عدد صحیح."""
    if pd.isna(text):
        return np.nan
    text = str(text).translate(DIGIT_MAP)
    if "توافقی" in text:
        return np.nan
    # حذف هر چیزی جز رقم
    digits = re.sub(r"[^\d]", "", text)
    if not digits:
        return np.nan
    return int(digits)


def extract_neighborhood(address):
    """استخراج نام منطقه از رشته‌ی آدرس (بعد از 'در تهران،')."""
    if pd.isna(address):
        return None
    address = str(address)
    match = re.search(r"در تهران،\s*(.+)", address)
    if not match:
        return None
    remainder = match.group(1).strip()
    # اگر چند بخش با ویرگول جدا شده (مثلاً منطقه، خیابان)، اولین بخش را می‌گیریم
    first_part = remainder.split("،")[0].strip()
    return first_part


def clean():
    df = pd.read_csv(INPUT_PATH, encoding="utf-8", low_memory=False)
    print(f"تعداد کل رکوردهای خام: {len(df):,}")

    # تبدیل قیمت فارسی به عدد
    df["price_toman"] = df["Price"].apply(persian_price_to_number)

    # تبدیل ارقام فارسی متراژ و سال ساخت و اتاق به عدد انگلیسی
    for col in ["Area", "Construction", "Room"]:
        df[col] = df[col].astype(str).str.translate(DIGIT_MAP)
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["neighborhood"] = df["Address"].apply(extract_neighborhood)

    # بولین‌ها
    for col in ["Warehouse", "Parking", "Elevator"]:
        df[col] = df[col].map({"True": True, "False": False, True: True, False: False})
        df[col] = df[col].fillna(False)

    df = df.rename(columns={
        "Area": "area_sqm",
        "Room": "rooms",
        "Warehouse": "warehouse",
        "Parking": "parking",
        "Elevator": "elevator",
    })

    df = df[[
        "neighborhood", "price_toman", "area_sqm", "Construction",
        "rooms", "warehouse", "parking", "elevator"
    ]]

    # حذف رکوردهای بدون قیمت، متراژ یا منطقه
    before = len(df)
    df = df.dropna(subset=["price_toman", "area_sqm", "neighborhood"])
    print(f"حذف {before - len(df):,} رکورد به دلیل نبود قیمت/متراژ/منطقه")

    # حذف outlier های واضح متراژ
    before = len(df)
    df = df[(df["area_sqm"] >= 15) & (df["area_sqm"] <= 1000)]
    df = df[df["price_toman"] > 0]
    print(f"حذف {before - len(df):,} رکورد outlier (متراژ/قیمت نامعقول)")

    df["price_per_sqm"] = df["price_toman"] / df["area_sqm"]

    # برش صدک ۰.۵٪ و ۹۹.۵٪ برای حذف خطاهای تایپی قیمت
    lower, upper = df["price_per_sqm"].quantile([0.005, 0.995])
    before = len(df)
    df = df[(df["price_per_sqm"] >= lower) & (df["price_per_sqm"] <= upper)]
    print(f"حذف {before - len(df):,} رکورد outlier قیمت هر متر (صدک ۰.۵٪-۹۹.۵٪)")

    # سن بنا
    df["building_age"] = CURRENT_JALALI_YEAR - df["Construction"]
    df.loc[(df["building_age"] < 0) | (df["building_age"] > 60), "building_age"] = np.nan
    df = df.drop(columns=["Construction"])

    df["neighborhood"] = df["neighborhood"].str.replace("\u200c", " ", regex=False).str.strip()

    df["year"] = 2023

    return df.reset_index(drop=True)


def main():
    df = clean()

    print("\nخلاصه‌ی آماری قیمت هر متر مربع (تومان):")
    print(df["price_per_sqm"].describe())

    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    print(f"\nذخیره شد: {OUTPUT_PATH}  ({len(df):,} رکورد تمیز)")


if __name__ == "__main__":
    main()
