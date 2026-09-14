# Where Is the Profit Going? — Craft Sausage & Park Kiosk

A profit-leakage analysis for a craft sausage business running a park kiosk and wholesale operation. The dashboard traces where revenue is generated and where profit is quietly lost — across channels, products, and seasons.

**[View the interactive dashboard on Tableau Public →](https://public.tableau.com/app/profile/dmytro.patseliuk/viz/WhereIstheProfitGoingCraftSausageParkKiosk/WhereIstheProfitGoingCraftSausageParkKiosk)**

---

## Dataset

- `sales_raw.csv` — deliberately messy generated data (mixed date formats, spelling variants, duplicates, missing values)
- `sales_clean.csv` — 84,147 analysis-ready transaction rows after cleaning
- Fields: order date, channel, product family, product, quantity, unit price, unit cost, discount, spoiled flag
- **Revenue, Profit and Margin % are computed inside Tableau as calculated fields**, not stored in the CSV.

The pipeline runs `generate_sales_data.py` → `sales_raw.csv` → `clean_sales_data.py` → `sales_clean.csv`, demonstrating the full generate-and-clean workflow.

## Tools

- **Tableau Public** — dashboard and all four worksheets
- **Python** (pandas, numpy) — data generation (`generate_sales_data.py`) and cleaning (`clean_sales_data.py`)

## Dashboard Worksheets

1. **Revenue vs Profit** — monthly revenue and profit over time
2. **Profit by Channel** — revenue and profit per sales channel
3. **Product Margin Traps** — margin % per product, ranked
4. **Seasonality** — monthly revenue by product family

---

## Key Findings

**1. Revenue is growing, but profit is not.**
Monthly revenue rose from 494K to 1.27M over the period (x2.6), yet monthly profit stayed flat in the 20K-123K band and fell to just 20,456 in the final month — its lowest point — despite record revenue. Growth is not translating into earnings: margins are being squeezed as the business scales.

**2. The Wholesale channel drives volume but barely any profit.**
Wholesale generates 20.3M in revenue (roughly two-thirds of the total) but only 1.03M in profit — a 5.1% margin. Kiosk, by contrast, earns 910K on just 2.1M revenue — a 42.5% margin. The business is chasing high-revenue, low-margin sales while its most profitable channel stays small.

**3. Spoilage is a direct, unrecovered loss of 758K.**
The Spoilage channel produces zero revenue and -758,502 in profit. This is not a margin problem but pure waste — inventory that was produced and never sold. Cutting spoilage in half would add ~380K to the bottom line, more than a third of total Wholesale profit.

**4. Several premium products sell at a loss.**
While Coffee (64%), Buns (52%) and sandwiches (40-44%) carry the business, several premium sausages have negative margins: Turkey Sausages Sundried Tomato (-12.1%), Duck Sausages (-9.0%), Chicken Sausages Dor Blue (-9.0%). Expensive ingredients (duck, turkey, blue cheese, cheddar) are not being priced to cover cost — a classic margin trap where complexity destroys profit.

**5. The business is highly seasonal.**
Summer-family revenue peaks at 446K in July and collapses to ~15K in winter — a ~30x swing. Coffee, however, holds a steady 8-27K year-round. Off-season cash flow depends almost entirely on the stable, low-seasonality product lines.
