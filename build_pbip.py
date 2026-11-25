"""
Builds the Power BI Project (PBIP) for the Velora Sales Dashboard.
Run:  python build_pbip.py
Then open  Velora_Sales_Dashboard.pbip  in Power BI Desktop and click Refresh.
"""
import json
import shutil
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NAME = "Velora_Sales_Dashboard"
DATA_DIR = str(ROOT / "data") + "\\"
SM = ROOT / f"{NAME}.SemanticModel"
RP = ROOT / f"{NAME}.Report"
BASE_THEME_SRC = Path(r"C:\Program Files\WindowsApps\Microsoft.MicrosoftPowerBIDesktop_2.160.1151.0_x64__8wekyb3d8bbwe"
                      r"\bin\WebView2Resources\minerva\sharedresources\BaseThemes\CY24SU06.json")

# ---------- palette & fonts ----------
INK = "#231F1C"       # header / primary text
CAMEL = "#B08D57"     # primary accent
TERRA = "#A9553F"     # returns / warning accent
OLIVE = "#6B705C"
ROSE = "#C9A9A6"
SLATE = "#5D6D7E"
TAUPE = "#8C7B6B"
BLUSH = "#E3C9B8"
PAGE_BG = "#F4EFE9"
CARD_BG = "#FFFFFF"
BORDER = "#E6DCD0"
MUTED = "#7A6F66"
FONT = "Segoe UI"
FONT_SEMI = "Segoe UI Semibold"
FONT_BRAND = "Georgia"


def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def gid():
    return str(uuid.uuid4())


# =====================================================================
#  SEMANTIC MODEL (model.bim)
# =====================================================================
def csv_partition(table, file, types):
    type_list = ", ".join(f'{{"{c}", {t}}}' for c, t in types)
    return [
        "let",
        f'    Source = Csv.Document(File.Contents(DataFolder & "{file}"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),',
        "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),",
        f'    Typed = Table.TransformColumnTypes(Promoted, {{{type_list}}}, "en-US")',
        "in",
        "    Typed",
    ]


M_TO_BIM = {"Int64.Type": "int64", "type text": "string", "type date": "dateTime",
            "type number": "double", "Currency.Type": "decimal"}


def table_from_csv(name, file, cols, hidden=(), fmt=None, measures=None, sort_by=None):
    fmt = fmt or {}
    columns = []
    for c, t in cols:
        col = {"name": c, "dataType": M_TO_BIM[t], "sourceColumn": c, "lineageTag": gid(),
               "summarizeBy": "none"}
        if t == "type date":
            col["formatString"] = "yyyy-mm-dd"
        if c in fmt:
            col["formatString"] = fmt[c]
        if c in hidden:
            col["isHidden"] = True
        columns.append(col)
    t = {"name": name, "lineageTag": gid(), "columns": columns,
         "partitions": [{"name": name, "mode": "import",
                         "source": {"type": "m", "expression": csv_partition(name, file, cols)}}],
         "annotations": [{"name": "PBI_ResultType", "value": "Table"}]}
    if measures:
        t["measures"] = measures
    return t


CUR0 = "\\$#,0;(\\$#,0);\\$#,0"
CUR2 = "\\$#,0.00;(\\$#,0.00);\\$#,0.00"
PCT1 = "0.0%;-0.0%;0.0%"
INT0 = "#,0"
DEC2 = "#,0.00"

MEASURES = [
    ("Total Sales", "SUM ( sales[net_sales] )", CUR0),
    ("Total Profit", "SUM ( sales[profit] )", CUR0),
    ("Profit Margin %", "DIVIDE ( [Total Profit], [Total Sales] )", PCT1),
    ("Total Orders", "DISTINCTCOUNT ( sales[order_id] )", INT0),
    ("Avg Order Value", "DIVIDE ( [Total Sales], [Total Orders] )", CUR2),
    ("Units Sold", "SUM ( sales[quantity] )", INT0),
    ("Active Customers", "DISTINCTCOUNT ( sales[customer_id] )", INT0),
    ("Avg Discount %", "AVERAGE ( sales[discount_pct] )", PCT1),
    ("Returned Items", 'CALCULATE ( COUNTROWS ( sales ), sales[returned] = "Yes" )', INT0),
    ("Return Rate %", "DIVIDE ( [Returned Items], COUNTROWS ( sales ) )", PCT1),
    ("Returned Sales", 'CALCULATE ( [Total Sales], sales[returned] = "Yes" )', CUR0),
    ("Orders per Customer", "DIVIDE ( [Total Orders], [Active Customers] )", DEC2),
    ("Sales MoM %",
     "VAR PrevMonth = CALCULATE ( [Total Sales], DATEADD ( 'Calendar'[Date], -1, MONTH ) )\n"
     "RETURN DIVIDE ( [Total Sales] - PrevMonth, PrevMonth )", PCT1),
    ("Top 10 Product Sales",
     "VAR r = RANKX ( ALLSELECTED ( products[product_name] ), [Total Sales] )\n"
     "RETURN IF ( ISINSCOPE ( products[product_name] ) && r <= 10, [Total Sales] )", CUR0),
]


def build_model():
    measures = [{"name": n, "expression": e, "formatString": f, "lineageTag": gid()} for n, e, f in MEASURES]

    sales = table_from_csv("sales", "sales.csv", [
        ("order_line_id", "Int64.Type"), ("order_id", "type text"), ("order_date", "type date"),
        ("customer_id", "type text"), ("product_id", "type text"), ("channel", "type text"),
        ("size", "type text"), ("quantity", "Int64.Type"), ("unit_price", "Currency.Type"),
        ("discount_pct", "type number"), ("gross_sales", "Currency.Type"), ("net_sales", "Currency.Type"),
        ("cost", "Currency.Type"), ("profit", "Currency.Type"), ("returned", "type text"),
        ("return_reason", "type text"),
    ], hidden=("customer_id", "product_id"),
        fmt={"unit_price": CUR2, "gross_sales": CUR2, "net_sales": CUR2, "cost": CUR2, "profit": CUR2,
             "discount_pct": "0%", "order_line_id": "0", "quantity": "0"},
        measures=measures)

    products = table_from_csv("products", "products.csv", [
        ("product_id", "type text"), ("product_name", "type text"), ("category", "type text"),
        ("sub_category", "type text"), ("collection", "type text"), ("color", "type text"),
        ("list_price", "Currency.Type"), ("unit_cost", "Currency.Type"),
    ], fmt={"list_price": CUR2, "unit_cost": CUR2})

    customers = table_from_csv("customers", "customers.csv", [
        ("customer_id", "type text"), ("gender", "type text"), ("age_group", "type text"),
        ("city", "type text"), ("region", "type text"), ("signup_date", "type date"),
        ("loyalty_tier", "type text"),
    ])
    for c in customers["columns"]:
        if c["name"] == "city":
            c["dataCategory"] = "City"

    calendar_m = [
        "let",
        "    Dates = List.Dates(#date(2025, 1, 1), 365, #duration(1, 0, 0, 0)),",
        '    T = Table.FromList(Dates, Splitter.SplitByNothing(), {"Date"}),',
        '    Typed = Table.TransformColumnTypes(T, {{"Date", type date}}),',
        '    AddMonth = Table.AddColumn(Typed, "Month", each Date.ToText([Date], [Format = "MMM", Culture = "en-US"]), type text),',
        '    AddMonthNum = Table.AddColumn(AddMonth, "MonthNum", each Date.Month([Date]), Int64.Type),',
        '    AddQuarter = Table.AddColumn(AddMonthNum, "Quarter", each "Q" & Text.From(Date.QuarterOfYear([Date])), type text),',
        '    AddWeekday = Table.AddColumn(AddQuarter, "Weekday", each Date.ToText([Date], [Format = "ddd", Culture = "en-US"]), type text),',
        '    AddWeekdayNum = Table.AddColumn(AddWeekday, "WeekdayNum", each Date.DayOfWeek([Date], Day.Monday) + 1, Int64.Type)',
        "in",
        "    AddWeekdayNum",
    ]
    calendar = {
        "name": "Calendar", "lineageTag": gid(), "dataCategory": "Time",
        "columns": [
            {"name": "Date", "dataType": "dateTime", "isKey": True, "sourceColumn": "Date",
             "formatString": "yyyy-mm-dd", "summarizeBy": "none", "lineageTag": gid()},
            {"name": "Month", "dataType": "string", "sourceColumn": "Month", "sortByColumn": "MonthNum",
             "summarizeBy": "none", "lineageTag": gid()},
            {"name": "MonthNum", "dataType": "int64", "sourceColumn": "MonthNum", "isHidden": True,
             "formatString": "0", "summarizeBy": "none", "lineageTag": gid()},
            {"name": "Quarter", "dataType": "string", "sourceColumn": "Quarter", "summarizeBy": "none",
             "lineageTag": gid()},
            {"name": "Weekday", "dataType": "string", "sourceColumn": "Weekday", "sortByColumn": "WeekdayNum",
             "summarizeBy": "none", "lineageTag": gid()},
            {"name": "WeekdayNum", "dataType": "int64", "sourceColumn": "WeekdayNum", "isHidden": True,
             "formatString": "0", "summarizeBy": "none", "lineageTag": gid()},
        ],
        "partitions": [{"name": "Calendar", "mode": "import", "source": {"type": "m", "expression": calendar_m}}],
        "annotations": [{"name": "PBI_ResultType", "value": "Table"}],
    }

    rels = [
        ("sales", "product_id", "products", "product_id"),
        ("sales", "customer_id", "customers", "customer_id"),
        ("sales", "order_date", "Calendar", "Date"),
    ]
    model = {
        "compatibilityLevel": 1567,
        "model": {
            "culture": "en-US",
            "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True},
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "sourceQueryCulture": "en-US",
            "tables": [sales, products, customers, calendar],
            "relationships": [{"name": gid(), "fromTable": a, "fromColumn": b, "toTable": c, "toColumn": d}
                              for a, b, c, d in rels],
            "expressions": [{
                "name": "DataFolder", "kind": "m", "lineageTag": gid(),
                "expression": f'"{DATA_DIR}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]',
                "annotations": [{"name": "PBI_ResultType", "value": "Text"}],
            }],
            "annotations": [
                {"name": "PBI_QueryOrder", "value": json.dumps(["DataFolder", "sales", "products", "customers", "Calendar"])},
                {"name": "__PBI_TimeIntelligenceEnabled", "value": "0"},
            ],
        },
    }
    write_json(SM / "model.bim", model)
    write_json(SM / "definition.pbism", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "1.0", "settings": {}})


# =====================================================================
#  REPORT (PBIR)
# =====================================================================
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/"
VC_SCHEMA = SCHEMA + "definition/visualContainer/1.4.0/schema.json"


def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


def s(text):           # string literal
    return lit("'" + text.replace("'", "''") + "'")


def num(n):
    return lit(f"{n}D")


def true():
    return lit("true")


def false():
    return lit("false")


def color(hexv):
    return {"solid": {"color": s(hexv)}}


def col(table, column):
    return {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": column}}


def meas(name, table="sales"):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}


def proj(field, display=None):
    inner = field.get("Column") or field.get("Measure")
    table, prop = inner["Expression"]["SourceRef"]["Entity"], inner["Property"]
    p = {"field": field, "queryRef": f"{table}.{prop}", "nativeQueryRef": display or prop}
    if display:
        p["displayName"] = display
    return p


def container(title=None, bg=CARD_BG, border=True):
    o = {
        "background": [{"properties": {"show": true(), "color": color(bg), "transparency": num(0)}}],
        "border": [{"properties": {"show": true() if border else false(), "color": color(BORDER),
                                   "radius": num(10)}}],
        "dropShadow": [{"properties": {"show": false()}}],
        "padding": [{"properties": {"top": num(8), "bottom": num(8), "left": num(12), "right": num(12)}}],
    }
    if title:
        o["title"] = [{"properties": {"show": true(), "text": s(title), "fontColor": color(INK),
                                      "fontSize": num(12), "fontFamily": s(FONT_SEMI)}}]
    else:
        o["title"] = [{"properties": {"show": false()}}]
    return o


class Page:
    def __init__(self, name, display, subtitle):
        self.name, self.display, self.subtitle = name, display, subtitle
        self.visuals = []
        self.z = 0

    def add(self, vname, vtype, pos, roles=None, objects=None, cobj=None, sort=None, sync=None, filters=None):
        x, y, w, h = pos
        self.z += 1000
        visual = {"visualType": vtype}
        if roles:
            q = {"queryState": {r: {"projections": p} for r, p in roles.items()}}
            if sort:
                q["sortDefinition"] = {"sort": [{"field": f, "direction": d} for f, d in sort], "isDefaultSort": True}
            visual["query"] = q
        if objects:
            visual["objects"] = objects
        visual["visualContainerObjects"] = cobj if cobj is not None else container()
        if sync:
            visual["syncGroup"] = {"groupName": sync, "fieldChanges": True, "filterChanges": True}
        v = {"$schema": VC_SCHEMA, "name": f"{self.name}_{vname}",
             "position": {"x": x, "y": y, "z": self.z, "width": w, "height": h, "tabOrder": self.z},
             "visual": visual}
        if filters:
            v["filterConfig"] = {"filters": filters}
        self.visuals.append(v)

    # ---- building blocks ----
    def header(self):
        paragraphs = [
            {"textRuns": [
                {"value": "VELORA", "textStyle": {"fontFamily": FONT_BRAND, "fontSize": "20pt", "fontWeight": "bold",
                                                  "color": "#FFFFFF"}},
                {"value": "    " + self.display, "textStyle": {"fontFamily": FONT_SEMI, "fontSize": "13pt",
                                                                "color": BLUSH}}]},
            {"textRuns": [{"value": self.subtitle + "   ·   FY 2025   ·   USD",
                           "textStyle": {"fontFamily": FONT, "fontSize": "9pt", "color": "#B9ADA1"}}]},
        ]
        self.add("header", "textbox", (0, 0, 1280, 72),
                 objects={"general": [{"properties": {"paragraphs": paragraphs}}]},
                 cobj={"background": [{"properties": {"show": true(), "color": color(INK), "transparency": num(0)}}],
                       "border": [{"properties": {"show": false()}}],
                       "title": [{"properties": {"show": false()}}],
                       "padding": [{"properties": {"top": num(8), "left": num(24)}}],
                       "visualHeader": [{"properties": {"show": false()}}]})

    def slicers(self):
        """Compact dropdown filters sitting inside the dark header band (right side)."""
        specs = [("Quarter", col("Calendar", "Quarter"), "Quarter"),
                 ("Category", col("products", "category"), "Category"),
                 ("Channel", col("sales", "channel"), "Channel"),
                 ("Region", col("customers", "region"), "Region")]
        w, gap = 140, 10
        x0 = 1256 - (w * 4 + gap * 3)
        for i, (label, field, sync) in enumerate(specs):
            cobj = container()
            cobj["padding"] = [{"properties": {"top": num(2), "bottom": num(2), "left": num(8), "right": num(8)}}]
            cobj["border"] = [{"properties": {"show": false()}}]
            cobj["background"] = [{"properties": {"show": true(), "color": color("#38322D"), "transparency": num(0)}}]
            cobj["visualHeader"] = [{"properties": {"show": false()}}]
            self.add(f"slicer_{label.lower()}", "slicer", (x0 + i * (w + gap), 10, w, 52),
                     roles={"Values": [proj(field, label)]},
                     objects={"data": [{"properties": {"mode": s("Dropdown")}}],
                              "header": [{"properties": {"show": true(), "fontColor": color(BLUSH),
                                                         "textSize": num(8), "fontFamily": s(FONT_SEMI)}}],
                              "items": [{"properties": {"fontColor": color(INK), "background": color("#FFFFFF"),
                                                        "textSize": num(9), "fontFamily": s(FONT)}}],
                              "selection": [{"properties": {"selectAllCheckboxEnabled": true()}}]},
                     cobj=cobj, sync=sync)

    def insights(self, items, pos=(896, 192, 360, 512)):
        """Right-hand 'Key Insights' panel: big accent number + headline + one-line explanation."""
        def para(text, size, colr, font=FONT, bold=False):
            st = {"fontFamily": font, "fontSize": f"{size}pt", "color": colr}
            if bold:
                st["fontWeight"] = "bold"
            return {"textRuns": [{"value": text, "textStyle": st}]}
        ps = [para("KEY INSIGHTS", 10, CAMEL, FONT_SEMI, True), para(" ", 6, MUTED)]
        for big, accent, headline, detail in items:
            ps += [para(big, 20, accent, FONT_SEMI),
                   para(headline, 10.5, INK, FONT_SEMI),
                   para(detail, 9, MUTED),
                   para(" ", 9, MUTED)]
        ps.append(para("Insights based on full-year 2025 data.", 8, "#A89C90"))
        cobj = container()
        cobj["padding"] = [{"properties": {"top": num(14), "bottom": num(10), "left": num(18), "right": num(14)}}]
        cobj["visualHeader"] = [{"properties": {"show": false()}}]
        self.add("insights", "textbox", pos,
                 objects={"general": [{"properties": {"paragraphs": ps}}]}, cobj=cobj)

    def cards(self, items, y=88, h=88):
        n = len(items)
        gap = 12
        w = (1232 - gap * (n - 1)) / n
        for i, (m, label, accent) in enumerate(items):
            cobj = container()
            cobj["border"] = [{"properties": {"show": true(), "color": color(BORDER), "radius": num(10)}}]
            self.add(f"card_{i}", "card", (24 + i * (w + gap), y, w, h),
                     roles={"Values": [proj(meas(m), label)]},
                     objects={"labels": [{"properties": {"color": color(accent), "fontSize": num(24),
                                                         "fontFamily": s(FONT_SEMI)}}],
                              "categoryLabels": [{"properties": {"show": true(), "color": color(MUTED),
                                                                 "fontSize": num(10), "fontFamily": s(FONT)}}]},
                     cobj=cobj)

    def bar(self, vname, title, pos, cat, measure, fill=CAMEL, vtype="clusteredBarChart",
            sort_desc=True, cat_sort=None, filters=None):
        cat_field, cat_label = cat
        m_field, m_label = measure
        sort = [(m_field, "Descending")] if sort_desc else ([(cat_sort, "Ascending")] if cat_sort else None)
        self.add(vname, vtype, pos,
                 roles={"Category": [proj(cat_field, cat_label)], "Y": [proj(m_field, m_label)]},
                 objects={"dataPoint": [{"properties": {"fill": color(fill)}}],
                          "labels": [{"properties": {"show": true(), "color": color(INK), "fontSize": num(9),
                                                     "fontFamily": s(FONT)}}],
                          "valueAxis": [{"properties": {"show": false(), "gridlineShow": false()}}],
                          "categoryAxis": [{"properties": {"showAxisTitle": false(), "labelColor": color(MUTED),
                                                           "fontSize": num(9), "fontFamily": s(FONT)}}]},
                 cobj=container(title), sort=sort, filters=filters)

    def donut(self, vname, title, pos, cat, measure):
        self.add(vname, "donutChart", pos,
                 roles={"Category": [proj(*cat)], "Y": [proj(*measure)]},
                 objects={"legend": [{"properties": {"show": true(), "position": s("Right"), "labelColor": color(INK),
                                                     "fontSize": num(9), "fontFamily": s(FONT)}}],
                          "labels": [{"properties": {"show": true(), "labelStyle": s("Percent of total"),
                                                     "color": color(INK), "fontSize": num(9)}}],
                          "slices": [{"properties": {"innerRadiusRatio": num(62)}}]},
                 cobj=container(title))


def m(name, label=None):
    return (meas(name), label or name)


def c(table, column, label):
    return (col(table, column), label)


def build_pages():
    pages = []
    month = col("Calendar", "Month")
    # layout grid (page 1280 x 720)
    L, TOP_Y, BOT_Y, H = 24, 192, 456, 248          # left column charts
    FULL_W, HALF_W = 856, 420
    R_X = L + HALF_W + 16

    def line_axes():
        return {"legend": [{"properties": {"show": true(), "position": s("TopRight"), "labelColor": color(INK),
                                           "fontSize": num(9)}}],
                "valueAxis": [{"properties": {"gridlineShow": true(), "gridlineColor": color("#F1EBE3"),
                                              "labelColor": color(MUTED), "fontSize": num(9),
                                              "showAxisTitle": false()}}],
                "categoryAxis": [{"properties": {"labelColor": color(MUTED), "fontSize": num(9),
                                                 "showAxisTitle": false()}}]}

    # ---------------- Page 1: Executive Overview ----------------
    p = Page("overview", "Executive Overview", "How is the business performing?")
    p.header(); p.slicers()
    p.cards([("Total Sales", "Net Sales", INK), ("Profit Margin %", "Profit Margin", OLIVE),
             ("Total Orders", "Orders", INK), ("Avg Order Value", "Avg Order Value", CAMEL)])
    obj = line_axes()
    obj.update({"dataPoint": [{"properties": {"fill": color(INK)}, "selector": {"metadata": "sales.Total Sales"}},
                              {"properties": {"fill": color(CAMEL)}, "selector": {"metadata": "sales.Total Profit"}}],
                "lineStyles": [{"properties": {"strokeWidth": num(3), "showMarker": true()}}]})
    p.add("trend", "lineChart", (L, TOP_Y, FULL_W, H),
          roles={"Category": [proj(month, "Month")],
                 "Y": [proj(meas("Total Sales"), "Net Sales"), proj(meas("Total Profit"), "Gross Profit")]},
          objects=obj, cobj=container("Monthly Sales & Profit"), sort=[(month, "Ascending")])
    p.bar("category", "Sales by Category", (L, BOT_Y, HALF_W, H), c("products", "category", "Category"),
          m("Total Sales", "Net Sales"), fill=INK)
    p.donut("channel", "Sales by Channel", (R_X, BOT_Y, HALF_W, H),
            c("sales", "channel", "Channel"), m("Total Sales", "Net Sales"))
    p.insights([
        ("+38%", OLIVE, "Second half beat the first",
         "H2 sales reached $1.12M vs $0.81M in H1 - strong momentum into 2026."),
        ("33.9%", CAMEL, "of revenue lands in Q4",
         "December alone is 2.6x January. The best day was 7 Dec ($12.4K)."),
        ("+25%", INK, "Weekends outsell weekdays",
         "An average weekend day brings $6.2K vs $4.9K. Launch drops Fri-Sun."),
        ("67.9%", TERRA, "Accessories: best margin, low share",
         "Highest margin of any category but only 7% of sales - push as add-ons."),
    ])
    pages.append(p)

    # ---------------- Page 2: Products & Returns ----------------
    p = Page("products", "Products & Returns", "What sells, and what comes back?")
    p.header(); p.slicers()
    p.cards([("Units Sold", "Units Sold", INK), ("Return Rate %", "Return Rate", TERRA),
             ("Returned Items", "Items Returned", TERRA), ("Returned Sales", "Sales Value Returned", TERRA)])
    p.bar("top10", "Top 10 Products by Sales", (L, TOP_Y, FULL_W, H),
          c("products", "product_name", "Product"), m("Top 10 Product Sales", "Net Sales"), fill=INK)
    p.bar("retcat", "Return Rate by Category", (L, BOT_Y, HALF_W, H),
          c("products", "category", "Category"), m("Return Rate %", "Return Rate"), fill=TERRA)
    p.bar("reasons", "Why Customers Return Items", (R_X, BOT_Y, HALF_W, H),
          c("sales", "return_reason", "Return Reason"), m("Returned Items", "Items Returned"), fill=ROSE)
    p.insights([
        ("52%", TERRA, "of returns are Size / Fit",
         "Worth $166K in sales. Halving fit returns would save about $83K a year."),
        ("27.2%", TERRA, "of dresses bought online come back",
         "vs 18.5% in store. Dresses alone make up 31% of all returned value."),
        ("18.6%", CAMEL, "return rate for XS & XL sizes",
         "vs 15.8% for S-L. Edge sizes need better fit guidance and models."),
        ("34%", INK, "of sales come from just 10 products",
         "4 of the top 10 are dresses - protect their stock, fix their fit."),
    ])
    pages.append(p)

    # ---------------- Page 3: Customers & Channels ----------------
    p = Page("customers", "Customers & Channels", "Who buys, and how?")
    p.header(); p.slicers()
    p.cards([("Active Customers", "Active Customers", INK), ("Orders per Customer", "Orders per Customer", INK),
             ("Avg Order Value", "Avg Order Value", CAMEL), ("Avg Discount %", "Avg Discount", TERRA)])
    p.add("chanmonth", "columnChart", (L, TOP_Y, FULL_W, H),
          roles={"Category": [proj(month, "Month")], "Y": [proj(meas("Total Sales"), "Net Sales")],
                 "Series": [proj(col("sales", "channel"), "Channel")]},
          objects=line_axes(), cobj=container("Monthly Sales by Channel"), sort=[(month, "Ascending")])
    p.donut("loyalty", "Sales by Loyalty Tier", (L, BOT_Y, HALF_W, H),
            c("customers", "loyalty_tier", "Loyalty Tier"), m("Total Sales", "Net Sales"))
    p.bar("retchan", "Return Rate by Channel", (R_X, BOT_Y, HALF_W, H), c("sales", "channel", "Channel"),
          m("Return Rate %", "Return Rate"), fill=TERRA, vtype="clusteredColumnChart")
    p.insights([
        ("13% → 30%", CAMEL, "Gold members punch above their weight",
         "13% of customers drive 30% of sales, spending 3.8x Bronze ($1,517 vs $400)."),
        ("47%", INK, "of revenue from the top 20% of customers",
         "A small loyal core - reward them before chasing new buyers."),
        ("11.0%", OLIVE, "store return rate vs 19.8% online",
         "Trying on works. Push buy-online-pick-up-in-store and fit tools."),
        ("-8.7 pts", TERRA, "margin lost on discounted items",
         "53% of items sold at a discount earn 52.9% margin vs 61.6% at full price."),
    ])
    pages.append(p)
    return pages


def build_theme():
    return {
        "name": "Velora",
        "dataColors": [INK, CAMEL, TERRA, OLIVE, ROSE, SLATE, TAUPE, BLUSH],
        "foreground": INK, "foregroundNeutralSecondary": MUTED, "foregroundNeutralTertiary": "#B9ADA1",
        "background": CARD_BG, "backgroundLight": "#FAF7F3", "backgroundNeutral": BORDER,
        "tableAccent": CAMEL, "good": OLIVE, "neutral": CAMEL, "bad": TERRA,
        "maximum": INK, "center": CAMEL, "minimum": "#F1E8DD",
        "textClasses": {
            "callout": {"fontFace": FONT_SEMI, "fontSize": 24, "color": INK},
            "title": {"fontFace": FONT_SEMI, "fontSize": 12, "color": INK},
            "header": {"fontFace": FONT_SEMI, "fontSize": 12, "color": INK},
            "label": {"fontFace": FONT, "fontSize": 9, "color": MUTED},
        },
        "visualStyles": {
            "*": {"*": {
                "background": [{"show": True, "color": {"solid": {"color": CARD_BG}}, "transparency": 0}],
                "border": [{"show": True, "color": {"solid": {"color": BORDER}}, "radius": 10}],
                "dropShadow": [{"show": False}],
                "title": [{"fontColor": {"solid": {"color": INK}}, "fontFamily": FONT_SEMI, "fontSize": 12}],
            }},
            "page": {"*": {
                "background": [{"color": {"solid": {"color": PAGE_BG}}, "transparency": 0}],
                "outspace": [{"color": {"solid": {"color": PAGE_BG}}, "transparency": 0}],
            }},
        },
    }


def build_report():
    pages = build_pages()
    defn = RP / "definition"
    write_json(RP / "definition.pbir", {
        "$schema": SCHEMA + "definitionProperties/1.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}})
    write_json(defn / "version.json", {
        "$schema": SCHEMA + "definition/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
    write_json(defn / "report.json", {
        "$schema": SCHEMA + "definition/report/1.2.0/schema.json",
        "themeCollection": {
            "baseTheme": {"name": "CY24SU06", "reportVersionAtImport": "5.55", "type": "SharedResources"},
            "customTheme": {"name": "VeloraTheme.json", "reportVersionAtImport": "5.55", "type": "RegisteredResources"}},
        "layoutOptimization": "None",
        "resourcePackages": [
            {"name": "SharedResources", "type": "SharedResources",
             "items": [{"name": "CY24SU06", "path": "BaseThemes/CY24SU06.json", "type": "BaseTheme"}]},
            {"name": "RegisteredResources", "type": "RegisteredResources",
             "items": [{"name": "VeloraTheme.json", "path": "VeloraTheme.json", "type": "CustomTheme"}]}],
    })
    write_json(defn / "pages" / "pages.json", {
        "$schema": SCHEMA + "definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": [p.name for p in pages], "activePageName": pages[0].name})
    for p in pages:
        pdir = defn / "pages" / p.name
        write_json(pdir / "page.json", {
            "$schema": SCHEMA + "definition/page/1.3.0/schema.json",
            "name": p.name, "displayName": p.display, "displayOption": "FitToPage",
            "height": 720, "width": 1280,
            "objects": {
                "background": [{"properties": {"color": color(PAGE_BG), "transparency": num(0)}}],
                "outspace": [{"properties": {"color": color(PAGE_BG), "transparency": num(0)}}]}})
        for v in p.visuals:
            write_json(pdir / "visuals" / v["name"] / "visual.json", v)

    res = RP / "StaticResources"
    (res / "SharedResources" / "BaseThemes").mkdir(parents=True, exist_ok=True)
    shutil.copy(BASE_THEME_SRC, res / "SharedResources" / "BaseThemes" / "CY24SU06.json")
    write_json(res / "RegisteredResources" / "VeloraTheme.json", build_theme())
    write_json(ROOT / "VeloraTheme.json", build_theme())   # handy copy for re-importing the theme


def build_pbip():
    write_json(ROOT / f"{NAME}.pbip", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0",
        "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
        "settings": {"enableAutoRecovery": True}})


if __name__ == "__main__":
    for d in (SM, RP):
        if d.exists():
            shutil.rmtree(d)
    build_model()
    build_report()
    build_pbip()
    print("Built", NAME, "->", ROOT)
