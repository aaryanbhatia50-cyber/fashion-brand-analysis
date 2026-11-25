"""Computes the extra insight numbers shown in the dashboard's insight panels."""
import csv
from collections import defaultdict
from datetime import date
from pathlib import Path

D = Path(__file__).parent / "data"
sales = list(csv.DictReader(open(D / "sales.csv", encoding="utf-8")))
prod = {r["product_id"]: r for r in csv.DictReader(open(D / "products.csv", encoding="utf-8"))}
cust = {r["customer_id"]: r for r in csv.DictReader(open(D / "customers.csv", encoding="utf-8"))}
for r in sales:
    r["net"] = float(r["net_sales"]); r["prof"] = float(r["profit"]); r["ret"] = r["returned"] == "Yes"
    r["d"] = date.fromisoformat(r["order_date"]); r["disc"] = float(r["discount_pct"])
tot = sum(r["net"] for r in sales)

def agg(key):
    a = defaultdict(lambda: {"net": 0, "n": 0, "ret": 0, "prof": 0, "retnet": 0})
    for r in sales:
        x = a[key(r)]; x["net"] += r["net"]; x["n"] += 1; x["ret"] += r["ret"]; x["prof"] += r["prof"]
        x["retnet"] += r["net"] if r["ret"] else 0
    return a

print("== Overview ==")
h1 = sum(r["net"] for r in sales if r["d"].month <= 6); h2 = tot - h1
print(f"H2 vs H1 growth: {h2/h1-1:.1%}  (H1 ${h1:,.0f}, H2 ${h2:,.0f})")
days = defaultdict(float)
for r in sales: days[r["d"]] += r["net"]
we = [v for k, v in days.items() if k.weekday() >= 5]; wd = [v for k, v in days.items() if k.weekday() < 5]
print(f"Avg weekend day ${sum(we)/len(we):,.0f} vs weekday ${sum(wd)/len(wd):,.0f} -> {sum(we)/len(we)/(sum(wd)/len(wd))-1:.0%}")
best = max(days, key=days.get); print(f"Best day {best} ${days[best]:,.0f}")
q = agg(lambda r: (r["d"].month - 1) // 3 + 1)
for k in sorted(q): print(f"Q{k}: ${q[k]['net']:,.0f} {q[k]['net']/tot:.1%}")
cat = agg(lambda r: prod[r["product_id"]]["category"])
for k, v in sorted(cat.items(), key=lambda x: -x[1]["net"]):
    print(f"  {k:12s} sales {v['net']/tot:.1%} margin {v['prof']/v['net']:.1%} returns {v['ret']/v['n']:.1%}")
ow = [r for r in sales if prod[r["product_id"]]["category"] == "Outerwear"]
owq4 = sum(r["net"] for r in ow if r["d"].month >= 10) / sum(r["net"] for r in ow)
print(f"Outerwear sales in Q4: {owq4:.0%}")

print("\n== Products & Returns ==")
size = agg(lambda r: r["size"])
for k in ["XS", "S", "M", "L", "XL"]: print(f"  size {k}: returns {size[k]['ret']/size[k]['n']:.1%}")
ex = [r for r in sales if r["size"] in ("XS", "XL")]; mid = [r for r in sales if r["size"] in ("S", "M", "L")]
print(f"XS/XL return {sum(r['ret'] for r in ex)/len(ex):.1%} vs S-L {sum(r['ret'] for r in mid)/len(mid):.1%}")
retnet = sum(r["net"] for r in sales if r["ret"]); print(f"Returned sales value ${retnet:,.0f} = {retnet/tot:.1%}")
dr = [r for r in sales if prod[r["product_id"]]["category"] == "Dresses" and r["ret"]]
print(f"Dresses share of returned value: {sum(r['net'] for r in dr)/retnet:.1%}")
dro = [r for r in sales if prod[r["product_id"]]["category"] == "Dresses"]
for ch in ("Online", "Store"):
    x = [r for r in dro if r["channel"] == ch]; print(f"  Dresses {ch} return {sum(r['ret'] for r in x)/len(x):.1%}")
reasons = defaultdict(int)
for r in sales:
    if r["ret"]: reasons[r["return_reason"]] += 1
nret = sum(reasons.values()); print({k: f"{v/nret:.0%}" for k, v in reasons.items()})
sz = sum(1 for r in sales if r["ret"] and r["return_reason"] == "Size/Fit issue")
szv = sum(r["net"] for r in sales if r["ret"] and r["return_reason"] == "Size/Fit issue")
print(f"Size/fit returns value ${szv:,.0f}; halving them saves ${szv/2:,.0f}")
pa = agg(lambda r: prod[r["product_id"]]["product_name"])
top10 = sorted(pa.items(), key=lambda x: -x[1]["net"])[:10]
t10 = sum(v["net"] for _, v in top10); print(f"Top 10 products = {t10/tot:.1%} of sales; dresses in top10: {sum('Dress' in k for k,_ in top10)}")
coll = agg(lambda r: prod[r["product_id"]]["collection"])
for k, v in coll.items(): print(f"  coll {k}: {v['net']/tot:.1%}")

print("\n== Customers & Channels ==")
ch = agg(lambda r: r["channel"])
for k, v in ch.items(): print(f"  {k}: sales {v['net']/tot:.1%} returns {v['ret']/v['n']:.1%} margin {v['prof']/v['net']:.1%}")
orders = defaultdict(set); spend = defaultdict(float)
for r in sales: orders[r["customer_id"]].add(r["order_id"]); spend[r["customer_id"]] += r["net"]
rep = sum(1 for v in orders.values() if len(v) >= 2) / len(orders)
print(f"Repeat customers (2+ orders): {rep:.0%}; active {len(orders)}")
tier = defaultdict(list)
for c, v in spend.items(): tier[cust[c]["loyalty_tier"]].append(v)
for k in ("Gold", "Silver", "Bronze"):
    n = len(tier[k]); print(f"  {k}: {n} customers, avg spend ${sum(tier[k])/n:,.0f}, share of customers {n/len(spend):.0%}")
srt = sorted(spend.values(), reverse=True); top20 = sum(srt[: len(srt) // 5]) / sum(srt)
print(f"Top 20% customers = {top20:.0%} of sales")
disc = [r for r in sales if r["disc"] > 0]; full = [r for r in sales if r["disc"] == 0]
print(f"Discounted lines {len(disc)/len(sales):.1%}; margin disc {sum(r['prof'] for r in disc)/sum(r['net'] for r in disc):.1%} vs full {sum(r['prof'] for r in full)/sum(r['net'] for r in full):.1%}")
age = agg(lambda r: cust[r["customer_id"]]["age_group"])
u35 = (age["18-24"]["net"] + age["25-34"]["net"]) / tot; print(f"Under-35 share: {u35:.1%}")
app = ch["Mobile App"]; print(f"App AOV: ${app['net']/len({r['order_id'] for r in sales if r['channel']=='Mobile App'}):,.0f}")
for k in ("Online", "Store", "Mobile App"):
    o = {r["order_id"] for r in sales if r["channel"] == k}; print(f"  AOV {k}: ${ch[k]['net']/len(o):,.0f}")
