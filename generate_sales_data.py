#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate three years of raw, messy transactional sales data for a craft
sausage + park kiosk business.

The data intentionally hides five profit-leakage effects, all built in
mathematically so a Tableau dashboard can genuinely surface them:

  1. Trap products      - high revenue, thin margin (expensive raw meat)
  2. Discounts          - promo / bulk discounts give away margin
  3. Spoilage           - unsold perishable batches written off
  4. Raw-mat inflation  - pork/chicken cost +~29% YoY, retail price lags
  5. Low-margin wholesale - wholesale drives volume growth, not profit

Real Ukrainian market anchors (2024->2025):
  - pork mince retail ~175 -> ~225 UAH/kg (~+29%)
  - chicken fillet    ~155 -> ~200 UAH/kg (~+29%)
  - espresso cost ~15 UAH, sold ~45-55 UAH (very high margin)

Output: sales_raw.csv (deliberately dirty) in the current directory.
Prices/costs are parameters at the top of the file and can be edited freely.
"""

import numpy as np
import pandas as pd
from datetime import date, timedelta

RNG = np.random.default_rng(42)  # reproducible

# ---------------------------------------------------------------------------
# 1. TIME RANGE  (three full years)
# ---------------------------------------------------------------------------
START = date(2023, 1, 1)
END   = date(2025, 12, 31)
N_DAYS = (END - START).days + 1
ALL_DAYS = [START + timedelta(days=i) for i in range(N_DAYS)]

# ---------------------------------------------------------------------------
# 2. INFLATION  - monthly multiplier on raw-material cost.
#    ~29% per year compounding, applied to COST only (retail price lags -> see below)
# ---------------------------------------------------------------------------
def cost_inflation(d: date) -> float:
    """Raw-material cost multiplier relative to Jan 2023 (=1.0).
    ~18% annual on cost — real market saw ~29% on some cuts, but averaged
    across the line (spices, casings, buns barely move) ~18% is realistic."""
    months_elapsed = (d.year - 2023) * 12 + (d.month - 1)
    monthly_rate = 1.18 ** (1 / 12)
    return monthly_rate ** months_elapsed

def price_inflation(d: date) -> float:
    """Retail price multiplier — deliberately LAGS cost (~12% annual vs 18%).
    The ~6pp gap is what silently compresses margin over three years."""
    months_elapsed = (d.year - 2023) * 12 + (d.month - 1)
    monthly_rate = 1.12 ** (1 / 12)
    return monthly_rate ** months_elapsed

# ---------------------------------------------------------------------------
# 3. SEASONALITY  - multiplier by month for different product families
# ---------------------------------------------------------------------------
# Grill / sandwiches / ice cream / cold drinks: summer peak
SUMMER = {1:0.35, 2:0.40, 3:0.55, 4:0.80, 5:1.15, 6:1.55,
          7:1.75, 8:1.70, 9:1.20, 10:0.80, 11:0.50, 12:0.40}
# Coffee: winter support (inverse-ish, milder)
COFFEE = {1:1.30, 2:1.25, 3:1.15, 4:1.00, 5:0.90, 6:0.80,
          7:0.75, 8:0.78, 9:0.95, 10:1.15, 11:1.28, 12:1.32}
# Core sausage line (venue + wholesale): mild, slight winter-holiday bump
CORE   = {1:1.05, 2:0.95, 3:1.00, 4:1.00, 5:1.00, 6:1.00,
          7:0.95, 8:0.95, 9:1.00, 10:1.05, 11:1.10, 12:1.25}

# ---------------------------------------------------------------------------
# 4. GROWTH  - overall business growth over three years.
#    Growth is driven MOSTLY by wholesale (that's the trap in the story).
# ---------------------------------------------------------------------------
def year_growth(d: date, channel: str) -> float:
    y = d.year - 2023  # 0,1,2
    if channel == "Wholesale":
        return 1.0 + 0.35 * y      # wholesale grows fast: +35%/yr (drives volume)
    if channel == "Venue":
        return 1.0 + 0.08 * y      # venue grows slowly
    if channel == "Kiosk":
        return 1.0 + 0.15 * y      # kiosk moderate
    return 1.0

# ---------------------------------------------------------------------------
# 5. PRODUCT CATALOGUE
#    base_price / base_cost are Jan-2023 UAH per unit (kg for meat, piece otherwise).
#    'family' drives seasonality; 'trap'=True marks deliberate low-margin sellers.
# ---------------------------------------------------------------------------
# Core meat line (from real технологічні карти, names in EN for the dataset)
CORE_PRODUCTS = [
    # name,                         base_price, base_cost, family, trap
    ("Homemade Sausages",                150,      95,   "core", False),
    ("Frankfurt Sausages",               170,     105,   "core", False),
    ("Nuremberg Sausages",               180,     110,   "core", False),
    ("Lyon Sausages",                    175,     108,   "core", False),
    ("Pork Sausages with Chili",         185,     120,   "core", False),
    ("Chicken Sausages with Cheddar",    190,     140,   "core", True),   # trap: pricey cheese/meat
    ("Chicken Sausages Mexican Style",   185,     135,   "core", True),   # trap
    ("Chicken Sausages Dor Blue",        220,     175,   "core", True),   # trap: expensive blue cheese
    ("Turkey Sausages Sundried Tomato",  230,     185,   "core", True),   # trap: turkey + sundried tomato
    ("Duck Sausages",                    260,     205,   "core", True),   # trap: duck is costly
    ("Pork Sausages with Tongue",        240,     165,   "core", False),
    ("Hunter Sausages (dried)",          320,     190,   "core", False),  # dried snack, good margin
    ("Sliced Ham",                       210,     140,   "core", False),
]

# Kiosk grill menu — own production sandwiches (summer)
KIOSK_GRILL = [
    ("Grill Sausage Sandwich",            85,      38,   "summer", False),
    ("Beef Burger",                      110,      55,   "summer", False),
    ("Mackerel Sandwich",                 95,      45,   "summer", False),
]

# Kiosk resale — high margin coffee (winter), summer ice cream & drinks
KIOSK_RESALE = [
    ("Coffee",                            50,      15,   "coffee", False),  # very high margin
    ("Ice Cream",                         45,      28,   "summer", False),  # resale, thinner
    ("Cold Drinks",                       40,      22,   "summer", False),  # resale, thinner
]

# ---------------------------------------------------------------------------
# 6. CHANNEL CONFIG
# ---------------------------------------------------------------------------
# Wholesale: bulk kg of core line + buns, discounted price, manager's cut lowers margin
# Venue: full price core line
# Kiosk: grill + resale, full price, seasonal
WHOLESALE_DISCOUNT = 0.80   # wholesale pays 80% of retail (bulk discount)
MANAGER_CUT = 0.05          # 5% of wholesale revenue goes to the sales manager

records = []

def messy_name(name: str) -> str:
    """Occasionally introduce spelling / spacing inconsistencies (dirty data)."""
    r = RNG.random()
    if r < 0.04:
        return name.upper()
    if r < 0.08:
        return name.lower()
    if r < 0.11:
        return "  " + name + " "        # stray whitespace
    if r < 0.13:
        return name.replace(" ", "  ")  # double space
    return name

def messy_date(d: date) -> str:
    """Mixed date formats (dirty data)."""
    r = RNG.random()
    if r < 0.75:
        return d.strftime("%Y-%m-%d")
    if r < 0.90:
        return d.strftime("%d.%m.%Y")
    return d.strftime("%m/%d/%Y")

order_id = 1000

for d in ALL_DAYS:
    ci = cost_inflation(d)
    pi = price_inflation(d)

    # ---------------- VENUE ----------------
    n_venue = RNG.poisson(25 * CORE[d.month] * year_growth(d, "Venue"))
    for _ in range(n_venue):
        name, bp, bc, fam, trap = CORE_PRODUCTS[RNG.integers(len(CORE_PRODUCTS))]
        qty = round(float(RNG.uniform(0.3, 1.5)), 2)          # kg
        price = bp * pi
        cost  = bc * ci
        disc = RNG.choice([0, 0, 0, 0, 0.10, 0.15], p=[.55,.15,.10,.08,.07,.05])
        records.append([order_id, messy_date(d), "Venue", messy_name(name),
                        fam, qty, round(price,2), round(cost,2), disc, 0])
        order_id += 1

    # ---------------- WHOLESALE ----------------
    n_ws = RNG.poisson(10 * CORE[d.month] * year_growth(d, "Wholesale"))
    for _ in range(n_ws):
        name, bp, bc, fam, trap = CORE_PRODUCTS[RNG.integers(len(CORE_PRODUCTS))]
        qty = round(float(RNG.uniform(4, 8)), 1)              # bulk kg
        price = bp * pi * WHOLESALE_DISCOUNT
        cost  = bc * ci
        # manager cut modelled as extra cost fraction on wholesale
        cost_eff = cost + price * MANAGER_CUT
        records.append([order_id, messy_date(d), "Wholesale", messy_name(name),
                        fam, qty, round(price,2), round(cost_eff,2), 0, 0])
        order_id += 1
        # buns sold alongside
        if RNG.random() < 0.6:
            bun_qty = round(float(RNG.uniform(10, 30)), 0)
            records.append([order_id, messy_date(d), "Wholesale", "Buns",
                            "core", bun_qty, round(8*pi,2), round(3.5*ci,2), 0, 0])
            order_id += 1

    # ---------------- KIOSK ----------------
    kiosk_base = 50  # up to ~50 orders/day in peak
    n_kiosk = RNG.poisson(kiosk_base * SUMMER[d.month] * 0.7 * year_growth(d, "Kiosk"))
    for _ in range(n_kiosk):
        pool = KIOSK_GRILL + KIOSK_RESALE
        name, bp, bc, fam, trap = pool[RNG.integers(len(pool))]
        # seasonal weighting: pick coffee more in winter, summer items in summer
        seasonal_mult = {"summer": SUMMER[d.month], "coffee": COFFEE[d.month],
                         "core": 1.0}[fam]
        if RNG.random() > min(seasonal_mult, 1.75) / 1.75:
            continue
        qty = 1
        # kiosk street-food prices are stickier: use half the retail inflation
        kiosk_pi = 1.0 + (pi - 1.0) * 0.5
        price = bp * kiosk_pi
        cost  = bc * ci
        records.append([order_id, messy_date(d), "Kiosk", messy_name(name),
                        fam, qty, round(price,2), round(cost,2), 0, 0])
        order_id += 1

    # ---------------- SPOILAGE (write-offs) ----------------
    # perishable core + grill: some unsold units written off, more in low-season
    # recorded as qty sold=0 style rows with a spoilage flag -> negative profit
    spoil_events = RNG.poisson(2.5)
    for _ in range(spoil_events):
        # spoilage hits perishable items
        pool = CORE_PRODUCTS + KIOSK_GRILL
        name, bp, bc, fam, trap = pool[RNG.integers(len(pool))]
        qty = round(float(RNG.uniform(0.5, 3.0)), 2)
        cost = bc * ci
        records.append([order_id, messy_date(d), "Spoilage", messy_name(name),
                        fam, qty, 0.0, round(cost,2), 0, 1])   # spoiled=1, price=0
        order_id += 1

df = pd.DataFrame(records, columns=[
    "order_id", "order_date", "channel", "product", "family",
    "quantity", "unit_price", "unit_cost", "discount", "spoiled"])

# ---------------------------------------------------------------------------
# 7. INJECT ADDITIONAL DIRT
# ---------------------------------------------------------------------------
# 7a. duplicate rows (~1%)
dupes = df.sample(frac=0.01, random_state=1)
df = pd.concat([df, dupes], ignore_index=True)

# 7b. missing values scattered in non-critical fields
for col, frac in [("family", 0.02), ("quantity", 0.01), ("discount", 0.03)]:
    idx = df.sample(frac=frac, random_state=2).index
    df.loc[idx, col] = np.nan

# 7c. shuffle so duplicates/dirty rows aren't clustered
df = df.sample(frac=1, random_state=3).reset_index(drop=True)

df.to_csv("sales_raw.csv", index=False, encoding="utf-8")
print(f"Rows: {len(df):,}")
print(df.head(8).to_string())
