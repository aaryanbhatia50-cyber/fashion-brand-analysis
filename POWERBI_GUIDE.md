# Power BI Build Guide — Velora Sales Dashboard

This guide gets you from the CSV files to a finished 3-page dashboard. It takes about 2–3 hours.

---

## Step 1 — Load the data (10 min)

1. Open **Power BI Desktop**. Go to **Home → Get Data → Text/CSV**.
2. Load all 3 files from the `data` folder: `sales.csv`, `products.csv` and `customers.csv`.
   For each file, click **Transform Data** instead of Load and check the column types:
   - `sales`: `order_date` = **Date**. `discount_pct` = **Percentage**. `unit_price`, `gross_sales`, `net_sales`, `cost` and `profit` = **Fixed decimal (currency)**.
   - `customers`: `signup_date` = **Date**.
3. Click **Close & Apply**.

## Step 2 — Data model (10 min)

Open **Model view**. Power BI usually creates the relationships below automatically. If it doesn't, drag one column onto the other to create each one:

```
products[product_id]   1 ──── *  sales[product_id]
customers[customer_id] 1 ──── *  sales[customer_id]
Calendar[Date]         1 ──── *  sales[order_date]
```

**Create the Calendar table.** Go to **Modeling → New Table** and paste:

```DAX
Calendar =
ADDCOLUMNS (
    CALENDAR ( DATE ( 2025, 1, 1 ), DATE ( 2025, 12, 31 ) ),
    "Month", FORMAT ( [Date], "MMM" ),
    "MonthNum", MONTH ( [Date] ),
    "Quarter", "Q" & QUARTER ( [Date] ),
    "Weekday", FORMAT ( [Date], "ddd" ),
    "WeekdayNum", WEEKDAY ( [Date], 2 )
)
```

Then make three changes:
- Right-click Calendar → **Mark as date table** → choose `Date`.
- Select the `Month` column → **Sort by column** → `MonthNum`.
- Select the `Weekday` column → **Sort by column** → `WeekdayNum`.

## Step 3 — DAX measures (15 min)

First create an empty table to hold the measures. Go to **Home → Enter Data**, name it `_Measures` and click Load.
Then select `_Measures` and use **New Measure** for each measure below:

```DAX
Total Sales      = SUM ( sales[net_sales] )
Total Profit     = SUM ( sales[profit] )
Profit Margin %  = DIVIDE ( [Total Profit], [Total Sales] )
Total Orders     = DISTINCTCOUNT ( sales[order_id] )
Avg Order Value  = DIVIDE ( [Total Sales], [Total Orders] )
Units Sold       = SUM ( sales[quantity] )
Active Customers = DISTINCTCOUNT ( sales[customer_id] )
Avg Discount %   = AVERAGE ( sales[discount_pct] )

Return Rate % =
DIVIDE (
    CALCULATE ( COUNTROWS ( sales ), sales[returned] = "Yes" ),
    COUNTROWS ( sales )
)

Returned Sales = CALCULATE ( [Total Sales], sales[returned] = "Yes" )

Sales MoM % =
VAR PrevMonth = CALCULATE ( [Total Sales], DATEADD ( 'Calendar'[Date], -1, MONTH ) )
RETURN DIVIDE ( [Total Sales] - PrevMonth, PrevMonth )

Orders per Customer = DIVIDE ( [Total Orders], [Active Customers] )
```

Set the display format for each measure:
- **Currency** with 0 decimals: Total Sales, Total Profit, Returned Sales.
- **Percentage** with 1 decimal: the four `%` measures.
- **Currency** with 2 decimals: Avg Order Value.

## Step 4 — Build the pages (1.5–2 hrs)

Use one color theme throughout, for example **View → Themes → Executive**, or pick 2–3 brand colors such as black, beige and one accent. Put a title text box at the top of each page.

### Page 1: Executive Overview
| Visual | Fields |
|---|---|
| 5 **Card** visuals (top row) | Total Sales, Total Profit, Profit Margin %, Total Orders, Avg Order Value |
| **Line chart** — Monthly sales trend | X: Calendar[Month] · Y: Total Sales (add Total Profit as a 2nd line) |
| **Bar chart** — Sales by category | Y: products[category] · X: Total Sales |
| **Donut** — Sales by channel | Legend: sales[channel] · Values: Total Sales |
| **Map** or **bar chart** — Sales by region | customers[region] · Total Sales |
| **Slicers** (left side or top) | Calendar[Quarter], products[category], sales[channel] |

### Page 2: Products & Returns
| Visual | Fields |
|---|---|
| 3 Cards | Units Sold, Return Rate %, Returned Sales |
| **Table / bar chart** — Top 10 products | products[product_name], Total Sales, Return Rate %. Use the **Top N filter** (10 by Total Sales) |
| **Clustered bar** — Return rate by category | products[category] · Return Rate % |
| **Bar chart** — Return reasons | sales[return_reason] · Count of order_line_id. Filter out blank values |
| **Matrix** — Category × Collection | Rows: category · Columns: collection · Values: Total Sales |
| **Column chart** — Sales by size | sales[size] · Units Sold |

Add **conditional formatting** to the Return Rate % column: red if above 20%, green if below 14%.

### Page 3: Customers & Channels
| Visual | Fields |
|---|---|
| 3 Cards | Active Customers, Orders per Customer, Avg Discount % |
| **Column chart** — Sales by age group | customers[age_group] · Total Sales |
| **Clustered column** — Channel × Return rate | sales[channel] · Return Rate % |
| **Donut** — Sales by loyalty tier | customers[loyalty_tier] · Total Sales |
| **Stacked column** — Monthly sales by channel | Calendar[Month] · Total Sales · Legend: channel |
| **Bar chart** — Sales by city | customers[city] · Total Sales |

### Finishing touches (15 min)
- **Sync slicers** across all pages: View → Sync slicers.
- Add **page navigation buttons**: Insert → Buttons → Navigator → Page navigator.
- Turn on **Tooltips** so hovering a bar shows Profit Margin % as well.
- Save as `Velora_Sales_Dashboard.pbix`, then **File → Export → PDF** to get a portfolio copy.

---

## If you use Tableau instead

Connect to all 3 CSVs and relate them on `product_id` and `customer_id`. Then create these calculated fields:

```
Profit Margin    : SUM([Profit]) / SUM([Net Sales])
Avg Order Value  : SUM([Net Sales]) / COUNTD([Order Id])
Return Rate      : SUM(IF [Returned] = "Yes" THEN 1 ELSE 0 END) / COUNT([Order Line Id])
Orders/Customer  : COUNTD([Order Id]) / COUNTD([Customer Id])
```

Build the same visuals as separate sheets and arrange them on 3 dashboards. Use the
`Order Date` field set to *Month* for the trend charts.
