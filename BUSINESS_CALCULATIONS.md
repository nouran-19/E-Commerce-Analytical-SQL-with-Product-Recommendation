# 21 Business Calculations — Code Reference Map

Each calculation below is mapped to its **exact location** in both the MySQL SQL files and the SQLite dashboard layer (`db.py`).

---

## Group 1: Time-Based Analysis (Calculations 1–7)

### 1. Monthly Revenue
**What it answers:** "How much revenue did we generate each month?"
**SQL Technique:** `SUM()` with `GROUP BY`

| Location | File | Line(s) |
|----------|------|---------|
| MySQL View | [`05_kpi_views.sql`](sql/05_kpi_views.sql) | L17–32 `v_monthly_kpis` — `SUM(f.net_amount)` |
| SQLite View | [`db.py`](db.py) | `_create_views()` → `v_monthly_kpis` |
| Dashboard | [`app.py`](app.py) | Overview page → `db.get_monthly_kpis()` |

---

### 2. Month-over-Month Revenue Growth (MoM %)
**What it answers:** "Is revenue growing or shrinking vs last month?"
**SQL Technique:** `LAG()` window function

| Location | File | Line(s) |
|----------|------|---------|
| MySQL View | [`05_kpi_views.sql`](sql/05_kpi_views.sql) | L37–49 `v_monthly_revenue_growth` — `LAG(revenue) OVER (ORDER BY year_num, month_num)` |
| Python calc | [`db.py`](db.py) | `get_monthly_revenue_growth()` — `df["revenue"].shift(1)` |
| Dashboard | [`app.py`](app.py) | Revenue Analysis page → MoM Growth bar chart |

---

### 3. Cumulative Revenue (Running Total)
**What it answers:** "What is the total revenue accumulated over time?"
**SQL Technique:** `SUM() OVER (ORDER BY ... ROWS UNBOUNDED PRECEDING)`

| Location | File | Line(s) |
|----------|------|---------|
| Python calc | [`db.py`](db.py) | `get_monthly_revenue_growth()` — `df["revenue"].cumsum()` |
| Dashboard | [`app.py`](app.py) | Revenue Analysis page → Cumulative Revenue area chart |

---

### 4. 3-Month Moving Average
**What it answers:** "What is the smoothed revenue trend, ignoring monthly volatility?"
**SQL Technique:** `AVG() OVER (ORDER BY ... ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)`

| Location | File | Line(s) |
|----------|------|---------|
| Python calc | [`db.py`](db.py) | `get_monthly_revenue_growth()` — `df["revenue"].rolling(window=3, min_periods=1).mean()` |
| Dashboard | [`app.py`](app.py) | Revenue Analysis page → Revenue vs 3-Month MA chart |

---

### 5. Monthly Gross Profit
**What it answers:** "How much profit did we make each month?"
**SQL Technique:** `SUM(profit_amount)` grouped by month

| Location | File | Line(s) |
|----------|------|---------|
| MySQL View | [`05_kpi_views.sql`](sql/05_kpi_views.sql) | L17–32 `v_monthly_kpis` — `SUM(f.profit_amount) AS gross_profit` |
| Dashboard | [`app.py`](app.py) | Overview page → Monthly Gross Profit bar chart |

---

### 6. Monthly Profit Margin (%)
**What it answers:** "What percentage of revenue is profit each month?"
**SQL Technique:** `SUM(profit) / SUM(revenue) * 100`

| Location | File | Line(s) |
|----------|------|---------|
| MySQL View | [`05_kpi_views.sql`](sql/05_kpi_views.sql) | L29 — `(SUM(f.profit_amount) / NULLIF(SUM(f.net_amount), 0)) * 100 AS profit_margin_pct` |
| SQLite View | [`db.py`](db.py) | `v_monthly_kpis` → `profit_margin_pct` |
| Dashboard | [`app.py`](app.py) | Overview page → KPI card "Profit Margin" |

---

### 7. Monthly Active Customers
**What it answers:** "How many unique customers placed orders each month?"
**SQL Technique:** `COUNT(DISTINCT customer_key)`

| Location | File | Line(s) |
|----------|------|---------|
| MySQL View | [`05_kpi_views.sql`](sql/05_kpi_views.sql) | L24 — `COUNT(DISTINCT f.customer_key) AS unique_customers` |
| Dashboard | [`app.py`](app.py) | Overview page → Monthly Active Customers line chart |

---

## Group 2: Ranking & Product Analytics (Calculations 8–11)

### 8. Top Products by Revenue (DENSE_RANK)
**What it answers:** "Which products generate the most revenue?"
**SQL Technique:** `DENSE_RANK() OVER (ORDER BY SUM(net_amount) DESC)`

| Location | File | Line(s) |
|----------|------|---------|
| MySQL View | [`05_kpi_views.sql`](sql/05_kpi_views.sql) | L54–68 `v_top_products_by_revenue` — `DENSE_RANK()` |
| SQLite View | [`db.py`](db.py) | `v_top_products_by_revenue` |
| Dashboard | [`app.py`](app.py) | Product Analytics page → Horizontal bar chart |

---

### 9. Category Revenue Share (% of Total)
**What it answers:** "What percentage of total revenue does each category contribute?"
**SQL Technique:** `SUM(revenue) / SUM(SUM(revenue)) OVER ()` — nested window function

| Location | File | Line(s) |
|----------|------|---------|
| MySQL View | [`05_kpi_views.sql`](sql/05_kpi_views.sql) | L73–82 `v_category_revenue_share` — `revenue_share_pct` |
| SQLite View | [`db.py`](db.py) | `v_category_revenue_share` |
| Dashboard | [`app.py`](app.py) | Product Analytics page → Category Revenue Share donut chart |

---

### 10. Category Revenue Ranking
**What it answers:** "Which categories are top performers?"
**SQL Technique:** `DENSE_RANK() OVER (ORDER BY SUM(net_amount) DESC)`

| Location | File | Line(s) |
|----------|------|---------|
| MySQL View | [`05_kpi_views.sql`](sql/05_kpi_views.sql) | L79 — `DENSE_RANK() OVER (...) AS category_rank` |
| Dashboard | [`app.py`](app.py) | Product Analytics page → donut chart (sorted by rank) |

---

### 11. Product Revenue vs Profit Scatter (Units as Bubble Size)
**What it answers:** "Are high-revenue products also high-profit?"
**SQL Technique:** Multi-measure aggregation (`SUM(net_amount)`, `SUM(profit_amount)`, `SUM(quantity)`)

| Location | File | Line(s) |
|----------|------|---------|
| MySQL View | [`05_kpi_views.sql`](sql/05_kpi_views.sql) | L54–68 `v_top_products_by_revenue` — `product_revenue`, `product_profit`, `units_sold` |
| Dashboard | [`app.py`](app.py) | Product Analytics page → Revenue vs Profit scatter plot |

---

## Group 3: Customer Behavior (Calculations 12–16)

### 12. Customer Lifetime Value (CLV)
**What it answers:** "How much total revenue has each customer generated?"
**SQL Technique:** `SUM(net_amount)` grouped by customer

| Location | File | Line(s) |
|----------|------|---------|
| MySQL View | [`05_kpi_views.sql`](sql/05_kpi_views.sql) | L87–100 `v_customer_lifetime_value` — `SUM(f.net_amount) AS lifetime_revenue` |
| SQLite View | [`db.py`](db.py) | `v_customer_lifetime_value` |
| Dashboard | [`app.py`](app.py) | Customer Analytics page → CLV histogram |

---

### 13. Customer Spending Quartiles (NTILE)
**What it answers:** "Which customers are top 25%, bottom 25%, etc.?"
**SQL Technique:** `NTILE(4) OVER (ORDER BY SUM(net_amount) DESC)`

| Location | File | Line(s) |
|----------|------|---------|
| MySQL View | [`05_kpi_views.sql`](sql/05_kpi_views.sql) | L97 — `NTILE(4) OVER (ORDER BY SUM(f.net_amount) DESC) AS spending_quartile` |
| Dashboard | [`app.py`](app.py) | Customer Analytics page → Spending Quartile pie chart |

---

### 14. Repeat Purchase Rate
**What it answers:** "What % of customers have ordered more than once?"
**SQL Technique:** `COUNT(CASE WHEN orders > 1 ...)` / `COUNT(*)`

| Location | File | Line(s) |
|----------|------|---------|
| MySQL View | [`05_kpi_views.sql`](sql/05_kpi_views.sql) | L105–120 `v_repeat_purchase_rate` |
| SQLite View | [`db.py`](db.py) | `v_repeat_purchase_rate` |
| Dashboard | [`app.py`](app.py) | Customer Analytics page → KPI card "Repeat Rate" |

---

### 15. Average Order Value (AOV)
**What it answers:** "On average, how much does each order generate?"
**SQL Technique:** `SUM(net_amount) / COUNT(DISTINCT order_id)`

| Location | File | Line(s) |
|----------|------|---------|
| MySQL View | [`05_kpi_views.sql`](sql/05_kpi_views.sql) | L28 — `SUM(f.net_amount) / NULLIF(COUNT(DISTINCT f.order_id), 0) AS aov` |
| Aggregate | [`db.py`](db.py) | `get_overview_kpis()` — overall AOV |
| Dashboard | [`app.py`](app.py) | Overview page → KPI card "Avg Order Value" |

---

### 16. Revenue by Customer Segment
**What it answers:** "How do VIP, Regular, and New customers compare?"
**SQL Technique:** `AVG()` with `GROUP BY customer_segment`

| Location | File | Line(s) |
|----------|------|---------|
| Python query | [`db.py`](db.py) | `get_customer_segments()` — `AVG(lifetime_revenue)` by segment |
| Dashboard | [`app.py`](app.py) | Customer Analytics page → Avg Revenue by Segment bar chart |

---

## Group 4: Advanced Product & Recommendation Analytics (Calculations 17–21)

### 17. Co-Purchase Frequency (Product Pair Mining)
**What it answers:** "Which products are frequently bought together?"
**SQL Technique:** Self-join on `order_id`, `product_key < product_key` + `COUNT(*)`

| Location | File | Line(s) |
|----------|------|---------|
| MySQL View | [`06_recommendation_top4.sql`](sql/06_recommendation_top4.sql) | `product_pairs` CTE — self-join + `COUNT(*)` |
| SQLite View | [`db.py`](db.py) | `v_recommendation_top4` → `product_pairs` CTE |

---

### 18. Recency-Weighted Scoring (Exponential Decay)
**What it answers:** "Are these co-purchases recent or stale?"
**SQL Technique:** `EXP(-DATEDIFF(...) / 90.0)` with `PARTITION BY` normalization

| Location | File | Line(s) |
|----------|------|---------|
| MySQL View | [`06_recommendation_top4.sql`](sql/06_recommendation_top4.sql) | `scored` CTE — `EXP(-DATEDIFF(...) / 90.0)` |
| SQLite View | [`db.py`](db.py) | `v_recommendation_top4` → `EXP(-(JULIANDAY('now') - JULIANDAY(...)) / 90.0)` |

---

### 19. Multi-Factor Composite Scoring (Normalized + Weighted)
**What it answers:** "What is the overall recommendation strength combining all signals?"
**SQL Technique:** Per-source `PARTITION BY` normalization + weighted sum + `COALESCE`

| Location | File | Line(s) |
|----------|------|---------|
| MySQL View | [`06_recommendation_top4.sql`](sql/06_recommendation_top4.sql) | `ranked` CTE — `0.40 * freq + 0.25 * recency + 0.10 * category + ...` |
| SQLite View | [`db.py`](db.py) | `v_recommendation_top4` → `ranked` CTE |
| Dashboard | [`app.py`](app.py) | Recommendations page → score values on cards |

---

### 20. Top-4 Recommendation Ranking (ROW_NUMBER + PARTITION BY)
**What it answers:** "For each product, what are the best 4 recommendations?"
**SQL Technique:** `ROW_NUMBER() OVER (PARTITION BY source_product_key ORDER BY score DESC)`

| Location | File | Line(s) |
|----------|------|---------|
| MySQL View | [`06_recommendation_top4.sql`](sql/06_recommendation_top4.sql) | `ranked` CTE → `WHERE recommendation_rank <= 4` |
| SQLite View | [`db.py`](db.py) | `v_recommendation_top4` |
| Dashboard | [`app.py`](app.py) | Recommendations page → 4 cards on right side |

---

### 21. Category Hierarchy Matching (Subcategory + Parent Category)
**What it answers:** "Are the recommended products in a related category?"
**SQL Technique:** `CASE WHEN subcategory = subcategory THEN 1.0 WHEN parent = parent THEN 0.5 ELSE 0`

| Location | File | Line(s) |
|----------|------|---------|
| MySQL View | [`06_recommendation_top4.sql`](sql/06_recommendation_top4.sql) | `scored` CTE — `category_match` with `LEFT JOIN dim_category` |
| SQLite View | [`db.py`](db.py) | `v_recommendation_top4` → `category_match` |

---

## Summary Table

| # | Calculation | SQL Technique | Primary File |
|---|-------------|---------------|-------------|
| 1 | Monthly Revenue | `SUM()` + `GROUP BY` | `05_kpi_views.sql` |
| 2 | MoM Revenue Growth | `LAG()` window function | `05_kpi_views.sql` |
| 3 | Cumulative Revenue | Running total (`cumsum`) | `db.py` |
| 4 | 3-Month Moving Average | `rolling(3).mean()` | `db.py` |
| 5 | Monthly Gross Profit | `SUM(profit_amount)` | `05_kpi_views.sql` |
| 6 | Profit Margin % | `SUM(profit) / SUM(revenue)` | `05_kpi_views.sql` |
| 7 | Monthly Active Customers | `COUNT(DISTINCT)` | `05_kpi_views.sql` |
| 8 | Product Revenue Ranking | `DENSE_RANK()` | `05_kpi_views.sql` |
| 9 | Category Revenue Share | `SUM / SUM OVER()` | `05_kpi_views.sql` |
| 10 | Category Ranking | `DENSE_RANK()` | `05_kpi_views.sql` |
| 11 | Revenue vs Profit Analysis | Multi-measure aggregation | `05_kpi_views.sql` |
| 12 | Customer Lifetime Value | `SUM()` per customer | `05_kpi_views.sql` |
| 13 | Spending Quartiles | `NTILE(4)` | `05_kpi_views.sql` |
| 14 | Repeat Purchase Rate | Conditional aggregation | `05_kpi_views.sql` |
| 15 | Average Order Value | `SUM / COUNT DISTINCT` | `05_kpi_views.sql` |
| 16 | Segment Comparison | `AVG()` + `GROUP BY` | `db.py` |
| 17 | Co-Purchase Frequency | Self-join + `COUNT` | `06_recommendation_top4.sql` |
| 18 | Recency Decay Scoring | `EXP()` exponential decay | `06_recommendation_top4.sql` |
| 19 | Composite Scoring | Weighted normalized sum | `06_recommendation_top4.sql` |
| 20 | Top-4 Ranking | `ROW_NUMBER() OVER (PARTITION BY)` | `06_recommendation_top4.sql` |
| 21 | Category Hierarchy Match | `CASE` + `LEFT JOIN` hierarchy | `06_recommendation_top4.sql` |
