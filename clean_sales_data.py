#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean the raw sales dataset (sales_raw.csv) into an analysis-ready file
(sales_clean.csv).

Cleaning steps (documented for the portfolio README):
  1. Normalise product names  - strip whitespace, collapse double spaces,
     unify capitalisation  (95 spelling variants -> ~23 real products)
  2. Remove full duplicate rows
  3. Handle missing values:
        - discount : NaN -> 0        (no discount was applied)
        - family   : NaN -> refilled from the product's known family
        - quantity : NaN -> row dropped (a sale with no quantity is unusable)
  4. Normalise dates - parse the three mixed formats into one ISO format
  5. Normalise decimals - ensure numeric columns are real numbers

Input : sales_raw.csv
Output: sales_clean.csv
"""

import pandas as pd
import numpy as np
import re

SRC = "sales_raw.csv"
OUT = "sales_clean.csv"

df = pd.read_csv(SRC)
start_rows = len(df)
print(f"Loaded: {start_rows:,} rows")

# ---------------------------------------------------------------------------
# 1. NORMALISE PRODUCT NAMES
# ---------------------------------------------------------------------------
def clean_name(x):
    if pd.isna(x):
        return x
    x = str(x).strip()              # trim edges
    x = re.sub(r"\s+", " ", x)      # collapse multiple spaces
    x = x.title()                   # unify capitalisation
    # fix the few words .title() breaks
    x = x.replace("(Dried)", "(dried)")
    return x

df["product"] = df["product"].apply(clean_name)
n_products = df["product"].nunique()
print(f"Product name variants after cleaning: {n_products}")

# ---------------------------------------------------------------------------
# 2. REMOVE FULL DUPLICATES
# ---------------------------------------------------------------------------
before = len(df)
df = df.drop_duplicates()
print(f"Removed {before - len(df):,} duplicate rows")

# ---------------------------------------------------------------------------
# 3. MISSING VALUES
# ---------------------------------------------------------------------------
# 3a. discount NaN -> 0
df["discount"] = df["discount"].fillna(0)

# 3b. family NaN -> refill from the most common family per product
fam_map = (df.dropna(subset=["family"])
             .groupby("product")["family"]
             .agg(lambda s: s.mode().iloc[0]))
mask = df["family"].isna()
df.loc[mask, "family"] = df.loc[mask, "product"].map(fam_map)

# 3c. quantity NaN -> drop
before = len(df)
df = df.dropna(subset=["quantity"])
print(f"Dropped {before - len(df):,} rows with missing quantity")

# ---------------------------------------------------------------------------
# 4. NORMALISE DATES  (three formats -> ISO yyyy-mm-dd)
# ---------------------------------------------------------------------------
def parse_date(s):
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%m/%d/%Y"):
        try:
            return pd.to_datetime(s, format=fmt)
        except ValueError:
            continue
    return pd.NaT

df["order_date"] = df["order_date"].apply(parse_date)
bad_dates = df["order_date"].isna().sum()
print(f"Unparseable dates: {bad_dates}")
df = df.dropna(subset=["order_date"])
df["order_date"] = df["order_date"].dt.strftime("%Y-%m-%d")

# ---------------------------------------------------------------------------
# 5. NUMERIC COLUMNS - ensure proper types
# ---------------------------------------------------------------------------
for col in ["quantity", "unit_price", "unit_cost", "discount"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df["spoiled"] = df["spoiled"].astype(int)

# ---------------------------------------------------------------------------
# SAVE
# ---------------------------------------------------------------------------
df = df.reset_index(drop=True)
df.to_csv(OUT, index=False, encoding="utf-8")

print("-" * 50)
print(f"Final: {len(df):,} rows  ({start_rows - len(df):,} removed total)")
print(f"Products: {df['product'].nunique()}")
print(f"Saved -> {OUT}")
