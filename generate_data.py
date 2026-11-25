"""
Generates a realistic sample dataset for "Velora", a fictional fashion brand.
Uses only the Python standard library. Run:  python generate_data.py
Outputs 3 CSV files into ./data  (sales, products, customers)
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)

# ---------------- PRODUCTS ----------------
CATALOG = {
    # category: (sub_categories, price range, cost ratio, base demand weight)
    "Tops":        (["T-Shirt", "Shirt", "Blouse", "Sweater"], (25, 70), 0.38, 30),
    "Bottoms":     (["Jeans", "Trousers", "Skirt", "Shorts"], (35, 90), 0.40, 22),
    "Dresses":     (["Maxi Dress", "Midi Dress", "Mini Dress"], (55, 140), 0.36, 16),
    "Outerwear":   (["Jacket", "Coat", "Blazer"], (90, 260), 0.42, 9),
    "Footwear":    (["Sneakers", "Boots", "Sandals"], (60, 180), 0.45, 12),
    "Accessories": (["Bag", "Belt", "Scarf", "Sunglasses"], (15, 95), 0.30, 11),
}
COLORS = ["Black", "White", "Navy", "Beige", "Olive", "Burgundy", "Sky Blue", "Grey"]
COLLECTIONS = ["Core", "Spring/Summer", "Fall/Winter"]
ADJ = ["Classic", "Relaxed", "Slim", "Everyday", "Studio", "Weekend", "Signature", "Linen", "Cotton", "Urban"]

products = []
pid = 1
for cat, (subs, (lo, hi), cost_ratio, weight) in CATALOG.items():
    for sub in subs:
        for _ in range(3):
            price = round(random.uniform(lo, hi) / 5) * 5 - 0.01
            if cat == "Outerwear" or sub in ("Boots", "Sweater", "Scarf"):
                coll = "Fall/Winter"
            elif sub in ("Shorts", "Sandals", "Sunglasses", "Maxi Dress", "Linen"):
                coll = "Spring/Summer"
            else:
                coll = random.choice(COLLECTIONS)
            while True:
                color, adj = random.choice(COLORS), random.choice(ADJ)
                name = f"{adj} {sub} - {color}"
                if name not in {p["product_name"] for p in products}:
                    break
            products.append({
                "product_id": f"P{pid:03d}",
                "product_name": name,
                "category": cat,
                "sub_category": sub,
                "collection": coll,
                "color": color,
                "list_price": price,
                "unit_cost": round(price * cost_ratio * random.uniform(0.9, 1.1), 2),
                "_weight": weight / len(subs) * random.uniform(0.5, 1.8),
            })
            pid += 1

# ---------------- CUSTOMERS ----------------
REGIONS = {
    "North": ["Chicago", "Minneapolis", "Detroit"],
    "South": ["Houston", "Atlanta", "Miami"],
    "East":  ["New York", "Boston", "Philadelphia"],
    "West":  ["Los Angeles", "San Francisco", "Seattle"],
}
REGION_W = {"North": 0.20, "South": 0.24, "East": 0.30, "West": 0.26}
AGE_GROUPS = [("18-24", 0.24), ("25-34", 0.36), ("35-44", 0.22), ("45-54", 0.12), ("55+", 0.06)]

customers = []
for i in range(1, 3001):
    region = random.choices(list(REGION_W), weights=REGION_W.values())[0]
    signup = date(2023, 1, 1) + timedelta(days=random.randint(0, 1050))
    customers.append({
        "customer_id": f"C{i:04d}",
        "gender": random.choices(["Female", "Male", "Non-binary"], [0.62, 0.35, 0.03])[0],
        "age_group": random.choices([a for a, _ in AGE_GROUPS], [w for _, w in AGE_GROUPS])[0],
        "city": random.choice(REGIONS[region]),
        "region": region,
        "signup_date": signup.isoformat(),
        "loyalty_tier": random.choices(["Bronze", "Silver", "Gold"], [0.60, 0.28, 0.12])[0],
    })
# loyal customers buy more often
cust_w = [{"Bronze": 1, "Silver": 2.2, "Gold": 4}[c["loyalty_tier"]] for c in customers]

# ---------------- SALES ----------------
# monthly demand multiplier (holiday peak, summer sale)
MONTH_MULT = {1: 0.75, 2: 0.70, 3: 0.90, 4: 0.95, 5: 1.00, 6: 1.05,
              7: 1.25, 8: 0.95, 9: 0.90, 10: 1.00, 11: 1.45, 12: 1.60}
SALE_MONTHS = {7: 0.25, 11: 0.20, 12: 0.15, 1: 0.20}   # avg discount in sale months
CHANNELS = [("Online", 0.48), ("Store", 0.34), ("Mobile App", 0.18)]
SIZES = ["XS", "S", "M", "L", "XL"]
SIZE_W = [0.08, 0.24, 0.34, 0.23, 0.11]
RETURN_REASONS = [("Size/Fit issue", 0.52), ("Changed mind", 0.18), ("Quality issue", 0.12),
                  ("Looks different from photo", 0.13), ("Arrived late", 0.05)]

def season_boost(p, month):
    if p["collection"] == "Fall/Winter":
        return 1.8 if month in (10, 11, 12, 1, 2) else 0.45
    if p["collection"] == "Spring/Summer":
        return 1.7 if month in (4, 5, 6, 7, 8) else 0.5
    return 1.0

rows = []
order_no = 100000
line_no = 1
start, end = date(2025, 1, 1), date(2025, 12, 31)
d = start
while d <= end:
    m = d.month
    weekend = 1.25 if d.weekday() >= 5 else 1.0
    growth = 1 + (d - start).days / 365 * 0.18          # ~18% growth through the year
    n_orders = int(random.gauss(30, 5) * MONTH_MULT[m] * weekend * growth)
    pw = [p["_weight"] * season_boost(p, m) for p in products]
    for _ in range(max(n_orders, 5)):
        order_no += 1
        cust = random.choices(customers, weights=cust_w)[0]
        channel = random.choices([c for c, _ in CHANNELS], [w for _, w in CHANNELS])[0]
        n_items = random.choices([1, 2, 3, 4], [0.55, 0.28, 0.12, 0.05])[0]
        for p in random.choices(products, weights=pw, k=n_items):
            qty = random.choices([1, 2, 3], [0.82, 0.14, 0.04])[0]
            base_disc = SALE_MONTHS.get(m, 0.0)
            disc = max(0.0, min(0.5, random.gauss(base_disc, 0.06))) if base_disc else \
                   random.choices([0, 0.10, 0.15], [0.78, 0.15, 0.07])[0]
            disc = round(disc * 20) / 20     # round to 5% steps
            unit_price = p["list_price"]
            gross = round(unit_price * qty, 2)
            net = round(gross * (1 - disc), 2)
            cost = round(p["unit_cost"] * qty, 2)
            size = "One Size" if p["category"] == "Accessories" else \
                   (random.choice(["6", "7", "8", "9", "10", "11"]) if p["category"] == "Footwear"
                    else random.choices(SIZES, SIZE_W)[0])

            # return probability: higher online, for dresses/footwear, extreme sizes
            r = 0.08
            r += {"Online": 0.08, "Mobile App": 0.06, "Store": 0.0}[channel]
            r += {"Dresses": 0.09, "Footwear": 0.05, "Bottoms": 0.04}.get(p["category"], 0)
            r += 0.04 if size in ("XS", "XL") else 0
            returned = random.random() < r
            reason = random.choices([x for x, _ in RETURN_REASONS], [w for _, w in RETURN_REASONS])[0] if returned else ""

            rows.append({
                "order_line_id": line_no,
                "order_id": f"ORD{order_no}",
                "order_date": d.isoformat(),
                "customer_id": cust["customer_id"],
                "product_id": p["product_id"],
                "channel": channel,
                "size": size,
                "quantity": qty,
                "unit_price": unit_price,
                "discount_pct": disc,
                "gross_sales": gross,
                "net_sales": net,
                "cost": cost,
                "profit": round(net - cost, 2),
                "returned": "Yes" if returned else "No",
                "return_reason": reason,
            })
            line_no += 1
    d += timedelta(days=1)

# ---------------- WRITE ----------------
def write(name, data, drop=()):
    fields = [k for k in data[0] if k not in drop]
    with open(OUT / name, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(data)
    print(f"{name:15s} {len(data):>6,} rows")

write("products.csv", products, drop=("_weight",))
write("customers.csv", customers)
write("sales.csv", rows)

# ---------------- QUICK SUMMARY (used for insights) ----------------
from collections import defaultdict
pmap = {p["product_id"]: p for p in products}
cmap = {c["customer_id"]: c for c in customers}
tot = sum(r["net_sales"] for r in rows)
prof = sum(r["profit"] for r in rows)
orders = len({r["order_id"] for r in rows})
ret_rate = sum(r["returned"] == "Yes" for r in rows) / len(rows)
print(f"\nNet sales ${tot:,.0f} | Profit ${prof:,.0f} ({prof/tot:.1%}) | Orders {orders:,} | "
      f"AOV ${tot/orders:,.2f} | Return rate {ret_rate:.1%} | Customers {len({r['customer_id'] for r in rows}):,}")

def breakdown(label, keyfn):
    s, rt, n = defaultdict(float), defaultdict(int), defaultdict(int)
    for r in rows:
        k = keyfn(r); s[k] += r["net_sales"]; n[k] += 1; rt[k] += r["returned"] == "Yes"
    print(f"\n{label}")
    for k in sorted(s, key=s.get, reverse=True):
        print(f"  {k:28s} ${s[k]:>11,.0f}  {s[k]/tot:5.1%}  returns {rt[k]/n[k]:.1%}")

breakdown("By month", lambda r: r["order_date"][:7])
breakdown("By category", lambda r: pmap[r["product_id"]]["category"])
breakdown("By channel", lambda r: r["channel"])
breakdown("By region", lambda r: cmap[r["customer_id"]]["region"])
breakdown("By loyalty tier", lambda r: cmap[r["customer_id"]]["loyalty_tier"])
breakdown("By age group", lambda r: cmap[r["customer_id"]]["age_group"])
breakdown("Top 5 products", lambda r: pmap[r["product_id"]]["product_id"] + " " + pmap[r["product_id"]]["product_name"])
reasons = defaultdict(int)
for r in rows:
    if r["return_reason"]: reasons[r["return_reason"]] += 1
print("\nReturn reasons:", dict(sorted(reasons.items(), key=lambda x: -x[1])))
disc_rows = [r for r in rows if r["discount_pct"] > 0]
print(f"Lines discounted: {len(disc_rows)/len(rows):.1%}, avg margin discounted "
      f"{sum(r['profit'] for r in disc_rows)/sum(r['net_sales'] for r in disc_rows):.1%} vs full price "
      f"{sum(r['profit'] for r in rows if r['discount_pct']==0)/sum(r['net_sales'] for r in rows if r['discount_pct']==0):.1%}")
