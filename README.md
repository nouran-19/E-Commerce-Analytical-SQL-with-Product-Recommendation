# E-Commerce Analytical SQL with Product Recommendation

A data warehouse and analytics project featuring a **Star Schema** design, **21+ analytical SQL queries** (window functions, rankings, CLV, etc.), and a **multi-factor product recommendation system** — all served through an interactive **Streamlit dashboard**.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Launch the dashboard
streamlit run app.py
```

The app creates an in-memory SQLite database on startup — **no MySQL server needed**.

## Project Structure

```
├── sql/                          # Original MySQL DDL & seed scripts
│   ├── 01_create_dw_schema.sql   # Star schema (6 dims + 1 fact)
│   ├── 02_seed_dimensions.sql    # Dimension seed data
│   ├── 03_seed_fact_order_lines.sql  # 1,000 order lines
│   ├── 04_validation_checks.sql  # Data quality checks
│   ├── 05_kpi_views.sql          # Monthly KPIs, CLV, repeat rate views
│   └── 06_recommendation_top4.sql    # Top-4 recommendation view
├── db.py                         # SQLite data layer (mirrors MySQL schema)
├── app.py                        # Streamlit dashboard (5 pages)
├── requirements.txt              # Python dependencies
└── README.md
```

## Dashboard Pages

| Page | Description |
|------|-------------|
| 📊 **Overview** | KPI cards (Revenue, Profit, AOV, Orders, Customers, Margin) + monthly trends |
| 📈 **Revenue Analysis** | MoM growth, cumulative revenue, 3-month moving average |
| 📦 **Product Analytics** | Top products, category share donut, revenue vs profit scatter |
| 👥 **Customer Analytics** | CLV distribution, spending quartiles, segment comparison |
| 🎯 **Recommendations** | Select a product → see top-4 recommendations with composite scores |

## Data Warehouse Schema

**Star Schema** with 1 fact table and 6 dimensions:
- `fact_order_line` — 1,000 order lines (grain: one product per order)
- `dim_date` — 730 days (2 years)
- `dim_customer` — 120 customers
- `dim_product` — 140 products
- `dim_category` — 12 categories
- `dim_payment` — 8 payment methods
- `dim_shipping` — 8 shipping options

## Recommendation Scoring

Composite score (0–100) using:
- **45%** Co-purchase frequency
- **25%** Recency (time-decay)
- **15%** Candidate popularity
- **10%** Profit margin
- **5%** Same-subcategory bonus

## Tech Stack

- **Backend**: Python, SQLite (in-memory)
- **Frontend**: Streamlit, Plotly
- **Data**: Faker (deterministic synthetic data)
- **Original SQL**: MySQL 8.0 compatible
