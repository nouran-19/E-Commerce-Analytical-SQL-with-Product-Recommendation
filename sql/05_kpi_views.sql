-- KPI and business-analysis views
-- Run after: 03_seed_fact_order_lines.sql

USE ecommerce_dw;

-- Safe rerun: drop existing views in dependency order
DROP VIEW IF EXISTS v_monthly_revenue_growth;
DROP VIEW IF EXISTS v_top_products_by_revenue;
DROP VIEW IF EXISTS v_category_revenue_share;
DROP VIEW IF EXISTS v_customer_lifetime_value;
DROP VIEW IF EXISTS v_repeat_purchase_rate;
DROP VIEW IF EXISTS v_monthly_kpis;

-- =========================
-- 1) Monthly KPI summary
-- =========================
CREATE VIEW v_monthly_kpis AS
SELECT
  YEAR(d.full_date) AS year_num,
  MONTH(d.full_date) AS month_num,
  DATE_FORMAT(d.full_date, '%Y-%m') AS ym_label,
  COUNT(*) AS order_lines,
  COUNT(DISTINCT f.order_id) AS total_orders,
  COUNT(DISTINCT f.customer_key) AS unique_customers,
  ROUND(SUM(f.net_amount), 2) AS revenue,
  ROUND(SUM(f.profit_amount), 2) AS gross_profit,
  ROUND(SUM(f.quantity), 2) AS units_sold,
  ROUND(SUM(f.net_amount) / NULLIF(COUNT(DISTINCT f.order_id), 0), 2) AS aov,
  ROUND((SUM(f.profit_amount) / NULLIF(SUM(f.net_amount), 0)) * 100, 2) AS profit_margin_pct
FROM fact_order_line f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY YEAR(d.full_date), MONTH(d.full_date), DATE_FORMAT(d.full_date, '%Y-%m');

-- =========================
-- 2) Monthly revenue growth
-- =========================
CREATE VIEW v_monthly_revenue_growth AS
SELECT
  year_num,
  month_num,
  ym_label,
  revenue,
  LAG(revenue) OVER (ORDER BY year_num, month_num) AS previous_month_revenue,
  ROUND(
    ((revenue - LAG(revenue) OVER (ORDER BY year_num, month_num))
      / NULLIF(LAG(revenue) OVER (ORDER BY year_num, month_num), 0)) * 100,
    2
  ) AS mom_growth_pct
FROM v_monthly_kpis;

-- =========================
-- 3) Top products by revenue
-- =========================
CREATE VIEW v_top_products_by_revenue AS
SELECT
  f.product_key,
  p.product_id,
  p.product_name,
  p.brand,
  p.subcategory,
  ROUND(SUM(f.net_amount), 2) AS product_revenue,
  ROUND(SUM(f.profit_amount), 2) AS product_profit,
  COUNT(DISTINCT f.order_id) AS orders_count,
  ROUND(SUM(f.quantity), 2) AS units_sold,
  DENSE_RANK() OVER (ORDER BY SUM(f.net_amount) DESC) AS revenue_rank
FROM fact_order_line f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY f.product_key, p.product_id, p.product_name, p.brand, p.subcategory;

-- =========================
-- 4) Category revenue contribution
-- =========================
CREATE VIEW v_category_revenue_share AS
SELECT
  c.category_key,
  c.category_name,
  ROUND(SUM(f.net_amount), 2) AS category_revenue,
  ROUND((SUM(f.net_amount) / NULLIF(SUM(SUM(f.net_amount)) OVER (), 0)) * 100, 2) AS revenue_share_pct,
  DENSE_RANK() OVER (ORDER BY SUM(f.net_amount) DESC) AS category_rank
FROM fact_order_line f
JOIN dim_category c ON f.category_key = c.category_key
GROUP BY c.category_key, c.category_name;

-- =========================
-- 5) Customer lifetime value summary
-- =========================
CREATE VIEW v_customer_lifetime_value AS
SELECT
  c.customer_key,
  c.customer_id,
  c.customer_name,
  c.customer_segment,
  COUNT(DISTINCT f.order_id) AS total_orders,
  ROUND(SUM(f.net_amount), 2) AS lifetime_revenue,
  ROUND(SUM(f.profit_amount), 2) AS lifetime_profit,
  ROUND(SUM(f.net_amount) / NULLIF(COUNT(DISTINCT f.order_id), 0), 2) AS customer_aov,
  NTILE(4) OVER (ORDER BY SUM(f.net_amount) DESC) AS spending_quartile
FROM fact_order_line f
JOIN dim_customer c ON f.customer_key = c.customer_key
GROUP BY c.customer_key, c.customer_id, c.customer_name, c.customer_segment;

-- =========================
-- 6) Repeat purchase rate
-- =========================
CREATE VIEW v_repeat_purchase_rate AS
WITH customer_orders AS (
  SELECT
    customer_key,
    COUNT(DISTINCT order_id) AS order_count
  FROM fact_order_line
  GROUP BY customer_key
)
SELECT
  COUNT(*) AS total_customers,
  SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END) AS repeat_customers,
  ROUND(
    (SUM(CASE WHEN order_count > 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)) * 100,
    2
  ) AS repeat_purchase_rate_pct
FROM customer_orders;

-- =========================
-- Quick checks
-- =========================
SELECT * FROM v_monthly_kpis ORDER BY year_num, month_num LIMIT 12;
SELECT * FROM v_monthly_revenue_growth ORDER BY year_num, month_num LIMIT 12;
SELECT * FROM v_top_products_by_revenue ORDER BY revenue_rank, product_key LIMIT 20;
SELECT * FROM v_category_revenue_share ORDER BY category_rank;
SELECT * FROM v_customer_lifetime_value ORDER BY lifetime_revenue DESC LIMIT 20;
SELECT * FROM v_repeat_purchase_rate;
