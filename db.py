"""
db.py – SQLite data layer for the E-Commerce Data Warehouse dashboard.

Creates an in-memory SQLite database that mirrors the MySQL star schema,
seeds it with realistic synthetic data (deterministic), and exposes
query helpers used by the Streamlit app.
"""

import sqlite3
import random
import math
from datetime import date, timedelta
from contextlib import contextmanager

import pandas as pd
from faker import Faker

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
_SEED = 42
_NUM_CUSTOMERS = 120
_NUM_PRODUCTS = 140
_NUM_FACT_ROWS = 1000
_DATE_SPAN_DAYS = 730  # 2 years

_CATEGORIES = [
    ("CAT001", "Smartphones", "Mobile Devices", False),
    ("CAT002", "Laptops", "Computing", False),
    ("CAT003", "Tablets", "Mobile Devices", False),
    ("CAT004", "Smartwatches", "Wearables", False),
    ("CAT005", "Headphones", "Audio", False),
    ("CAT006", "Earbuds", "Audio", False),
    ("CAT007", "Gaming Consoles", "Gaming", False),
    ("CAT008", "Keyboards", "Computer Accessories", False),
    ("CAT009", "Mice", "Computer Accessories", False),
    ("CAT010", "Monitors", "Displays", False),
    ("CAT011", "Chargers", "Accessories", False),
    ("CAT012", "Power Banks", "Accessories", True),
]

_PAYMENTS = [
    ("PAY001", "Credit Card", "Visa"),
    ("PAY002", "Credit Card", "Mastercard"),
    ("PAY003", "Debit Card", "Visa Electron"),
    ("PAY004", "Digital Wallet", "PayPal"),
    ("PAY005", "Digital Wallet", "Apple Pay"),
    ("PAY006", "Digital Wallet", "Google Pay"),
    ("PAY007", "Cash on Delivery", "Courier"),
    ("PAY008", "Bank Transfer", "Local Bank"),
]

_SHIPPINGS = [
    ("SHP001", "Standard", "Aramex", 5, 35.00),
    ("SHP002", "Standard", "DHL eCommerce", 6, 30.00),
    ("SHP003", "Express", "DHL Express", 2, 70.00),
    ("SHP004", "Express", "FedEx", 2, 75.00),
    ("SHP005", "Same-Day", "Local Courier", 0, 95.00),
    ("SHP006", "Next-Day", "Aramex", 1, 55.00),
    ("SHP007", "Pickup Point", "Partner Store", 1, 15.00),
    ("SHP008", "Economy", "Egypt Post", 8, 20.00),
]

_SUBCATEGORIES = [
    "Smartphones", "Laptops", "Tablets", "Smartwatches",
    "Headphones", "Earbuds", "Gaming Consoles", "Keyboards",
    "Mice", "Monitors", "Chargers", "Power Banks",
]

_BRANDS = [
    "Apple", "Samsung", "Xiaomi", "Sony", "Lenovo",
    "HP", "Dell", "Asus", "Logitech", "Anker",
]

_PRICE_RANGES = {
    "Smartphones": (25000, 45000),
    "Laptops": (28000, 70000),
    "Tablets": (12000, 28000),
    "Smartwatches": (7000, 18000),
    "Headphones": (1800, 9000),
    "Earbuds": (1200, 6000),
    "Gaming Consoles": (18000, 25000),
    "Keyboards": (450, 3500),
    "Mice": (300, 2800),
    "Monitors": (4500, 30000),
    "Chargers": (200, 1600),
    "Power Banks": (350, 4200),
}

_CITIES = ["Cairo", "Giza", "Alexandria", "Mansoura", "Tanta", "Asyut", "Hurghada", "Suez"]
_REGIONS = ["Greater Cairo", "Delta", "Alexandria", "Upper Egypt", "Canal"]
_AGE_GROUPS = ["18-25", "26-35", "36-50", "51+"]
_GENDERS = ["Male", "Female", "Other", "Prefer not to say"]

# ---------------------------------------------------------------------------
# Singleton connection
# ---------------------------------------------------------------------------
_conn: sqlite3.Connection | None = None


def get_connection() -> sqlite3.Connection:
    """Return (and lazily create) the singleton in-memory SQLite database."""
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(":memory:", check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _create_schema(_conn)
        _seed_all(_conn)
        _create_views(_conn)
    return _conn


def query_df(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Run *sql* and return a pandas DataFrame."""
    return pd.read_sql_query(sql, get_connection(), params=params)


# ---------------------------------------------------------------------------
# Schema creation  (SQLite-compatible DDL)
# ---------------------------------------------------------------------------
def _create_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS dim_date (
            date_key     INTEGER PRIMARY KEY,
            full_date    TEXT NOT NULL UNIQUE,
            day_of_week  INTEGER NOT NULL,
            day_name     TEXT NOT NULL,
            day_of_month INTEGER NOT NULL,
            day_of_year  INTEGER NOT NULL,
            week_number  INTEGER NOT NULL,
            month        INTEGER NOT NULL,
            month_name   TEXT NOT NULL,
            quarter      INTEGER NOT NULL,
            year         INTEGER NOT NULL,
            is_weekend   INTEGER NOT NULL DEFAULT 0,
            is_holiday   INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS dim_customer (
            customer_key      INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id       TEXT NOT NULL UNIQUE,
            customer_name     TEXT NOT NULL,
            email             TEXT,
            gender            TEXT DEFAULT 'Prefer not to say',
            age_group         TEXT,
            city              TEXT,
            region            TEXT,
            country           TEXT DEFAULT 'Egypt',
            registration_date TEXT NOT NULL,
            customer_segment  TEXT,
            created_at        TEXT DEFAULT (datetime('now')),
            updated_at        TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS dim_category (
            category_key    INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id     TEXT NOT NULL UNIQUE,
            category_name   TEXT NOT NULL,
            parent_category TEXT,
            seasonal_flag   INTEGER DEFAULT 0,
            created_at      TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS dim_product (
            product_key  INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id   TEXT NOT NULL UNIQUE,
            product_name TEXT NOT NULL,
            brand        TEXT,
            subcategory  TEXT,
            unit_price   REAL,
            cost_price   REAL,
            launch_date  TEXT,
            is_active    INTEGER DEFAULT 1,
            created_at   TEXT DEFAULT (datetime('now')),
            updated_at   TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS dim_payment (
            payment_key     INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_id      TEXT NOT NULL UNIQUE,
            payment_method  TEXT NOT NULL,
            payment_provider TEXT,
            created_at      TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS dim_shipping (
            shipping_key  INTEGER PRIMARY KEY AUTOINCREMENT,
            shipping_id   TEXT NOT NULL UNIQUE,
            shipping_type TEXT NOT NULL,
            carrier       TEXT,
            delivery_days INTEGER,
            shipping_cost REAL,
            created_at    TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS fact_order_line (
            order_line_key  INTEGER PRIMARY KEY AUTOINCREMENT,
            date_key        INTEGER NOT NULL REFERENCES dim_date(date_key),
            customer_key    INTEGER NOT NULL REFERENCES dim_customer(customer_key),
            product_key     INTEGER NOT NULL REFERENCES dim_product(product_key),
            category_key    INTEGER NOT NULL REFERENCES dim_category(category_key),
            payment_key     INTEGER NOT NULL REFERENCES dim_payment(payment_key),
            shipping_key    INTEGER NOT NULL REFERENCES dim_shipping(shipping_key),
            order_id        TEXT NOT NULL,
            quantity        REAL NOT NULL,
            gross_amount    REAL NOT NULL,
            discount_amount REAL NOT NULL DEFAULT 0,
            net_amount      REAL NOT NULL,
            cost_amount     REAL NOT NULL,
            profit_amount   REAL NOT NULL,
            created_at      TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_fact_date     ON fact_order_line(date_key);
        CREATE INDEX IF NOT EXISTS idx_fact_customer  ON fact_order_line(customer_key);
        CREATE INDEX IF NOT EXISTS idx_fact_product   ON fact_order_line(product_key);
        CREATE INDEX IF NOT EXISTS idx_fact_category  ON fact_order_line(category_key);
        CREATE INDEX IF NOT EXISTS idx_fact_order     ON fact_order_line(order_id);
    """)
    conn.commit()


# ---------------------------------------------------------------------------
# Data seeding
# ---------------------------------------------------------------------------
_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
_HOLIDAYS_MMDD = {"01-01", "04-25", "05-01", "07-23", "10-06"}


def _seed_dates(conn: sqlite3.Connection) -> None:
    today = date.today()
    start = today - timedelta(days=_DATE_SPAN_DAYS - 1)
    rows = []
    for i in range(_DATE_SPAN_DAYS):
        d = start + timedelta(days=i)
        dow = d.isoweekday()  # 1=Mon … 7=Sun
        rows.append((
            int(d.strftime("%Y%m%d")),
            d.isoformat(),
            dow,
            _DAY_NAMES[dow - 1],
            d.day,
            d.timetuple().tm_yday,
            int(d.strftime("%W")),
            d.month,
            _MONTH_NAMES[d.month],
            (d.month - 1) // 3 + 1,
            d.year,
            1 if dow >= 6 else 0,
            1 if d.strftime("%m-%d") in _HOLIDAYS_MMDD else 0,
        ))
    conn.executemany(
        "INSERT INTO dim_date VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", rows
    )
    conn.commit()


def _seed_categories(conn: sqlite3.Connection) -> None:
    conn.executemany(
        "INSERT INTO dim_category (category_id, category_name, parent_category, seasonal_flag) "
        "VALUES (?,?,?,?)",
        _CATEGORIES,
    )
    conn.commit()


def _seed_payments(conn: sqlite3.Connection) -> None:
    conn.executemany(
        "INSERT INTO dim_payment (payment_id, payment_method, payment_provider) VALUES (?,?,?)",
        _PAYMENTS,
    )
    conn.commit()


def _seed_shippings(conn: sqlite3.Connection) -> None:
    conn.executemany(
        "INSERT INTO dim_shipping (shipping_id, shipping_type, carrier, delivery_days, shipping_cost) "
        "VALUES (?,?,?,?,?)",
        _SHIPPINGS,
    )
    conn.commit()


def _seed_customers(conn: sqlite3.Connection) -> None:
    rng = random.Random(_SEED)
    fake = Faker()
    Faker.seed(_SEED)
    today = date.today()
    rows = []
    for n in range(1, _NUM_CUSTOMERS + 1):
        seg = "VIP" if n % 10 == 0 else ("Regular" if n % 3 == 0 else "New")
        reg_date = today - timedelta(days=rng.randint(0, 720))
        rows.append((
            f"CUST{n:04d}",
            fake.name(),
            f"customer{n:04d}@example.com",
            rng.choice(_GENDERS),
            rng.choice(_AGE_GROUPS),
            rng.choice(_CITIES),
            rng.choice(_REGIONS),
            "Egypt",
            reg_date.isoformat(),
            seg,
        ))
    conn.executemany(
        "INSERT INTO dim_customer "
        "(customer_id, customer_name, email, gender, age_group, city, region, country, "
        "registration_date, customer_segment) VALUES (?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()


def _seed_products(conn: sqlite3.Connection) -> None:
    rng = random.Random(_SEED + 1)
    today = date.today()
    rows = []
    for n in range(1, _NUM_PRODUCTS + 1):
        subcat = _SUBCATEGORIES[(n - 1) % 12]
        brand = rng.choice(_BRANDS)
        lo, hi = _PRICE_RANGES[subcat]
        unit_price = round(lo + rng.random() * (hi - lo), 2)
        cost_price = round(unit_price * (0.62 + rng.random() * 0.22), 2)
        launch_date = today - timedelta(days=rng.randint(0, 900))
        is_active = 0 if n % 20 == 0 else 1
        rows.append((
            f"PROD{n:04d}",
            f"{brand} {subcat} Model {n:03d}",
            brand,
            subcat,
            unit_price,
            cost_price,
            launch_date.isoformat(),
            is_active,
        ))
    conn.executemany(
        "INSERT INTO dim_product "
        "(product_id, product_name, brand, subcategory, unit_price, cost_price, "
        "launch_date, is_active) VALUES (?,?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()


def _seed_facts(conn: sqlite3.Connection) -> None:
    rng = random.Random(_SEED + 2)
    # Grab date keys
    date_keys = [r[0] for r in conn.execute("SELECT date_key FROM dim_date ORDER BY date_key").fetchall()]
    num_customers = conn.execute("SELECT COUNT(*) FROM dim_customer").fetchone()[0]
    num_products = conn.execute("SELECT COUNT(*) FROM dim_product").fetchone()[0]
    num_categories = conn.execute("SELECT COUNT(*) FROM dim_category").fetchone()[0]
    num_payments = conn.execute("SELECT COUNT(*) FROM dim_payment").fetchone()[0]
    num_shippings = conn.execute("SELECT COUNT(*) FROM dim_shipping").fetchone()[0]

    rows = []
    for n in range(1, _NUM_FACT_ROWS + 1):
        order_id = f"ORD{((n - 1) // 2) + 1:06d}"
        dk = rng.choice(date_keys)
        ck = rng.randint(1, num_customers)
        pk = rng.randint(1, num_products)
        cat_k = rng.randint(1, num_categories)
        pay_k = rng.randint(1, num_payments)
        shp_k = rng.randint(1, num_shippings)
        qty = rng.randint(1, 3)

        # Price band: 25% low, 50% mid, 25% high
        r = rng.random()
        if r < 0.25:
            unit_price = round(350 + rng.random() * 2000, 2)
        elif r < 0.75:
            unit_price = round(1800 + rng.random() * 12000, 2)
        else:
            unit_price = round(12000 + rng.random() * 65000, 2)

        # Discount: 50% small, 35% medium, 15% large
        r2 = rng.random()
        if r2 < 0.50:
            disc_pct = rng.random() * 0.05
        elif r2 < 0.85:
            disc_pct = 0.05 + rng.random() * 0.10
        else:
            disc_pct = 0.15 + rng.random() * 0.15

        cost_ratio = 0.62 + rng.random() * 0.25

        gross = round(qty * unit_price, 2)
        discount = round(gross * disc_pct, 2)
        net = round(gross - discount, 2)
        cost = round(net * cost_ratio, 2)
        profit = round(net - cost, 2)

        rows.append((dk, ck, pk, cat_k, pay_k, shp_k, order_id, qty, gross, discount, net, cost, profit))

    conn.executemany(
        "INSERT INTO fact_order_line "
        "(date_key, customer_key, product_key, category_key, payment_key, shipping_key, "
        "order_id, quantity, gross_amount, discount_amount, net_amount, cost_amount, profit_amount) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    conn.commit()


def _seed_all(conn: sqlite3.Connection) -> None:
    _seed_dates(conn)
    _seed_categories(conn)
    _seed_payments(conn)
    _seed_shippings(conn)
    _seed_customers(conn)
    _seed_products(conn)
    _seed_facts(conn)


# ---------------------------------------------------------------------------
# Analytical views  (ported from 05_kpi_views.sql & 06_recommendation_top4.sql)
# ---------------------------------------------------------------------------
def _create_views(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    # Monthly KPIs
    cur.execute("""
        CREATE VIEW IF NOT EXISTS v_monthly_kpis AS
        SELECT
            d.year                                                       AS year_num,
            d.month                                                      AS month_num,
            d.year || '-' || printf('%02d', d.month)                     AS ym_label,
            COUNT(*)                                                     AS order_lines,
            COUNT(DISTINCT f.order_id)                                   AS total_orders,
            COUNT(DISTINCT f.customer_key)                               AS unique_customers,
            ROUND(SUM(f.net_amount), 2)                                  AS revenue,
            ROUND(SUM(f.profit_amount), 2)                               AS gross_profit,
            ROUND(SUM(f.quantity), 2)                                    AS units_sold,
            ROUND(SUM(f.net_amount) * 1.0 / MAX(COUNT(DISTINCT f.order_id), 1), 2) AS aov,
            ROUND(SUM(f.profit_amount) * 100.0 / MAX(SUM(f.net_amount), 0.01), 2)  AS profit_margin_pct
        FROM fact_order_line f
        JOIN dim_date d ON f.date_key = d.date_key
        GROUP BY d.year, d.month
    """)

    # Top products by revenue
    cur.execute("""
        CREATE VIEW IF NOT EXISTS v_top_products_by_revenue AS
        SELECT
            f.product_key,
            p.product_id,
            p.product_name,
            p.brand,
            p.subcategory,
            ROUND(SUM(f.net_amount), 2)                AS product_revenue,
            ROUND(SUM(f.profit_amount), 2)             AS product_profit,
            COUNT(DISTINCT f.order_id)                  AS orders_count,
            ROUND(SUM(f.quantity), 2)                   AS units_sold,
            DENSE_RANK() OVER (ORDER BY SUM(f.net_amount) DESC) AS revenue_rank
        FROM fact_order_line f
        JOIN dim_product p ON f.product_key = p.product_key
        GROUP BY f.product_key, p.product_id, p.product_name, p.brand, p.subcategory
    """)

    # Category revenue share
    cur.execute("""
        CREATE VIEW IF NOT EXISTS v_category_revenue_share AS
        SELECT
            c.category_key,
            c.category_name,
            ROUND(SUM(f.net_amount), 2)                                              AS category_revenue,
            ROUND(SUM(f.net_amount) * 100.0 / MAX(SUM(SUM(f.net_amount)) OVER (), 0.01), 2) AS revenue_share_pct,
            DENSE_RANK() OVER (ORDER BY SUM(f.net_amount) DESC)                      AS category_rank
        FROM fact_order_line f
        JOIN dim_category c ON f.category_key = c.category_key
        GROUP BY c.category_key, c.category_name
    """)

    # CLV
    cur.execute("""
        CREATE VIEW IF NOT EXISTS v_customer_lifetime_value AS
        SELECT
            c.customer_key,
            c.customer_id,
            c.customer_name,
            c.customer_segment,
            c.city,
            c.region,
            c.age_group,
            COUNT(DISTINCT f.order_id)                                   AS total_orders,
            ROUND(SUM(f.net_amount), 2)                                  AS lifetime_revenue,
            ROUND(SUM(f.profit_amount), 2)                               AS lifetime_profit,
            ROUND(SUM(f.net_amount) * 1.0 / MAX(COUNT(DISTINCT f.order_id), 1), 2) AS customer_aov,
            NTILE(4) OVER (ORDER BY SUM(f.net_amount) DESC)              AS spending_quartile
        FROM fact_order_line f
        JOIN dim_customer c ON f.customer_key = c.customer_key
        GROUP BY c.customer_key, c.customer_id, c.customer_name, c.customer_segment,
                 c.city, c.region, c.age_group
    """)

    # Repeat purchase rate
    cur.execute("""
        CREATE VIEW IF NOT EXISTS v_repeat_purchase_rate AS
        SELECT
            COUNT(*)                                                        AS total_customers,
            SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END)              AS repeat_customers,
            ROUND(
                SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END) * 100.0
                / MAX(COUNT(*), 1), 2
            ) AS repeat_purchase_rate_pct
        FROM (
            SELECT customer_key, COUNT(DISTINCT order_id) AS order_count
            FROM fact_order_line
            GROUP BY customer_key
        )
    """)

    # Register math.exp for SQLite (needed for exponential recency decay)
    conn.create_function("EXP", 1, math.exp)

    # Recommendation (top 4 per product) — improved scoring:
    #   1. Per-source-product normalization (PARTITION BY source_product_key)
    #   2. COALESCE to handle NULL scores
    #   3. NULL-safe subcategory matching + category hierarchy
    #   4. Exponential recency decay (sharper drop-off)
    #   5. Availability filter (is_active)
    #   6. Rebalanced weights (40/25/10/10/10/5)
    cur.execute("""
        CREATE VIEW IF NOT EXISTS v_recommendation_top4 AS
        WITH order_products AS (
            SELECT DISTINCT f.order_id, f.product_key, d.full_date
            FROM fact_order_line f
            JOIN dim_date d ON f.date_key = d.date_key
        ),
        product_pairs AS (
            SELECT
                op1.product_key AS source_product_key,
                op2.product_key AS candidate_product_key,
                COUNT(*)        AS co_purchase_count,
                MAX(MAX(op1.full_date, op2.full_date)) AS last_together_date
            FROM order_products op1
            JOIN order_products op2
              ON op1.order_id = op2.order_id
             AND op1.product_key < op2.product_key
            GROUP BY op1.product_key, op2.product_key
        ),
        directed_pairs AS (
            SELECT source_product_key, candidate_product_key, co_purchase_count, last_together_date
            FROM product_pairs
            UNION ALL
            SELECT candidate_product_key, source_product_key, co_purchase_count, last_together_date
            FROM product_pairs
        ),
        candidate_popularity AS (
            SELECT product_key, COUNT(DISTINCT order_id) AS product_order_count
            FROM fact_order_line
            GROUP BY product_key
        ),
        candidate_margin AS (
            SELECT product_key,
                   AVG(CASE WHEN net_amount = 0 THEN 0 ELSE profit_amount * 1.0 / net_amount END) AS avg_margin_ratio
            FROM fact_order_line
            GROUP BY product_key
        ),
        scored AS (
            SELECT
                dp.source_product_key,
                dp.candidate_product_key,
                dp.co_purchase_count,
                dp.last_together_date,
                cp.product_order_count,
                cm.avg_margin_ratio,

                -- FIX 3: NULL-safe category hierarchy matching
                CASE
                    WHEN COALESCE(sp.subcategory, '') = COALESCE(cpd.subcategory, '')
                         AND sp.subcategory IS NOT NULL THEN 1.0
                    WHEN sp_cat.parent_category = cp_cat.parent_category
                         AND sp_cat.parent_category IS NOT NULL THEN 0.5
                    ELSE 0
                END AS category_match,

                -- FIX 1: Per-source-product normalization
                dp.co_purchase_count * 1.0 / MAX(
                    MAX(dp.co_purchase_count) OVER (PARTITION BY dp.source_product_key), 1
                ) AS freq_norm,

                -- FIX 4: Exponential decay instead of hyperbolic
                EXP(-(JULIANDAY('now') - JULIANDAY(dp.last_together_date)) / 90.0)
                    / MAX(
                        MAX(EXP(-(JULIANDAY('now') - JULIANDAY(dp.last_together_date)) / 90.0))
                        OVER (PARTITION BY dp.source_product_key), 0.001
                    ) AS recency_norm,

                -- Global normalization OK for popularity and margin
                cp.product_order_count * 1.0 / MAX(MAX(cp.product_order_count) OVER (), 1) AS popularity_norm,
                cm.avg_margin_ratio / MAX(MAX(cm.avg_margin_ratio) OVER (), 0.001) AS margin_norm

            FROM directed_pairs dp
            JOIN dim_product sp  ON dp.source_product_key    = sp.product_key
            JOIN dim_product cpd ON dp.candidate_product_key = cpd.product_key
                -- FIX 5: Only recommend active products
                AND cpd.is_active = 1
            -- Category hierarchy joins
            LEFT JOIN dim_category sp_cat  ON sp.subcategory  = sp_cat.category_name
            LEFT JOIN dim_category cp_cat  ON cpd.subcategory = cp_cat.category_name
            JOIN candidate_popularity cp ON dp.candidate_product_key = cp.product_key
            JOIN candidate_margin     cm ON dp.candidate_product_key = cm.product_key
        ),
        ranked AS (
            SELECT
                s.source_product_key,
                s.candidate_product_key,
                -- FIX 2 + FIX 6: COALESCE + rebalanced weights
                ROUND(
                    100 * (
                        0.40 * COALESCE(s.freq_norm, 0) +
                        0.25 * COALESCE(s.recency_norm, 0) +
                        0.10 * COALESCE(s.category_match, 0) +
                        0.10 * COALESCE(s.popularity_norm, 0) +
                        0.10 * COALESCE(s.margin_norm, 0) +
                        0.05 * 1
                    ), 2
                ) AS recommendation_score,
                ROW_NUMBER() OVER (
                    PARTITION BY s.source_product_key
                    ORDER BY (
                        0.40 * COALESCE(s.freq_norm, 0) +
                        0.25 * COALESCE(s.recency_norm, 0) +
                        0.10 * COALESCE(s.category_match, 0) +
                        0.10 * COALESCE(s.popularity_norm, 0) +
                        0.10 * COALESCE(s.margin_norm, 0) +
                        0.05 * 1
                    ) DESC,
                    s.candidate_product_key
                ) AS recommendation_rank
            FROM scored s
        )
        SELECT
            r.source_product_key,
            sp.product_id   AS source_product_id,
            sp.product_name AS source_product_name,
            r.candidate_product_key,
            cp.product_id   AS candidate_product_id,
            cp.product_name AS candidate_product_name,
            cp.brand        AS candidate_brand,
            cp.subcategory  AS candidate_subcategory,
            cp.unit_price   AS candidate_price,
            r.recommendation_score,
            r.recommendation_rank
        FROM ranked r
        JOIN dim_product sp ON r.source_product_key    = sp.product_key
        JOIN dim_product cp ON r.candidate_product_key = cp.product_key
        WHERE r.recommendation_rank <= 4
    """)

    conn.commit()


# ---------------------------------------------------------------------------
# Convenience query functions for the dashboard
# ---------------------------------------------------------------------------

def get_overview_kpis() -> dict:
    """Return aggregate KPI dict for the entire dataset."""
    row = query_df("""
        SELECT
            ROUND(SUM(net_amount), 2)                                       AS total_revenue,
            ROUND(SUM(profit_amount), 2)                                    AS total_profit,
            COUNT(DISTINCT order_id)                                        AS total_orders,
            COUNT(DISTINCT customer_key)                                    AS total_customers,
            ROUND(SUM(net_amount) * 1.0 / MAX(COUNT(DISTINCT order_id), 1), 2) AS aov,
            ROUND(SUM(profit_amount) * 100.0 / MAX(SUM(net_amount), 0.01), 2)  AS profit_margin_pct,
            ROUND(SUM(quantity), 0)                                         AS units_sold
        FROM fact_order_line
    """).iloc[0]
    return row.to_dict()


def get_monthly_kpis() -> pd.DataFrame:
    return query_df("SELECT * FROM v_monthly_kpis ORDER BY year_num, month_num")


def get_monthly_revenue_growth() -> pd.DataFrame:
    """Monthly revenue with MoM growth, cumulative, and 3-month moving average."""
    df = get_monthly_kpis()
    df["prev_revenue"] = df["revenue"].shift(1)
    df["mom_growth_pct"] = ((df["revenue"] - df["prev_revenue"]) / df["prev_revenue"] * 100).round(2)
    df["cumulative_revenue"] = df["revenue"].cumsum().round(2)
    df["ma_3m"] = df["revenue"].rolling(window=3, min_periods=1).mean().round(2)
    return df


def get_top_products(n: int = 20) -> pd.DataFrame:
    return query_df(
        "SELECT * FROM v_top_products_by_revenue ORDER BY revenue_rank LIMIT ?", (n,)
    )


def get_category_share() -> pd.DataFrame:
    return query_df("SELECT * FROM v_category_revenue_share ORDER BY category_rank")


def get_clv() -> pd.DataFrame:
    return query_df("SELECT * FROM v_customer_lifetime_value ORDER BY lifetime_revenue DESC")


def get_repeat_rate() -> dict:
    row = query_df("SELECT * FROM v_repeat_purchase_rate").iloc[0]
    return row.to_dict()


def get_customer_segments() -> pd.DataFrame:
    return query_df("""
        SELECT customer_segment, COUNT(*) AS count,
               ROUND(AVG(lifetime_revenue), 2) AS avg_revenue,
               ROUND(AVG(lifetime_profit), 2)  AS avg_profit,
               ROUND(AVG(total_orders), 1)      AS avg_orders
        FROM v_customer_lifetime_value
        GROUP BY customer_segment
        ORDER BY avg_revenue DESC
    """)


def get_recommendations_for(product_key: int) -> pd.DataFrame:
    return query_df(
        "SELECT * FROM v_recommendation_top4 WHERE source_product_key = ? ORDER BY recommendation_rank",
        (product_key,),
    )


def get_product_list() -> pd.DataFrame:
    """All active products for the recommendation dropdown."""
    return query_df(
        "SELECT product_key, product_id, product_name, brand, subcategory, unit_price "
        "FROM dim_product WHERE is_active = 1 ORDER BY product_name"
    )


# ---------------------------------------------------------------------------
#  Quick self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    conn = get_connection()
    for tbl in ["dim_date", "dim_customer", "dim_category", "dim_product",
                 "dim_payment", "dim_shipping", "fact_order_line"]:
        cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"{tbl:25s} {cnt:>6d} rows")
    print()
    print("Overview KPIs:", get_overview_kpis())
    print("Repeat rate:  ", get_repeat_rate())
