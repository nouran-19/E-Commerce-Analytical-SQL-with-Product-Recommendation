-- Validation checks for schema + synthetic load
-- Run after: 03_seed_fact_order_lines.sql

USE ecommerce_dw;

-- =========================
-- 1) Row-count checks
-- =========================
SELECT 'dim_date' AS table_name, COUNT(*) AS row_count FROM dim_date
UNION ALL SELECT 'dim_customer', COUNT(*) FROM dim_customer
UNION ALL SELECT 'dim_category', COUNT(*) FROM dim_category
UNION ALL SELECT 'dim_product', COUNT(*) FROM dim_product
UNION ALL SELECT 'dim_payment', COUNT(*) FROM dim_payment
UNION ALL SELECT 'dim_shipping', COUNT(*) FROM dim_shipping
UNION ALL SELECT 'fact_order_line', COUNT(*) FROM fact_order_line;

-- =========================
-- 2) Orphan FK checks (should be 0)
-- =========================
SELECT 'missing_date' AS check_name, COUNT(*) AS issue_count
FROM fact_order_line f LEFT JOIN dim_date d ON f.date_key = d.date_key
WHERE d.date_key IS NULL
UNION ALL
SELECT 'missing_customer', COUNT(*)
FROM fact_order_line f LEFT JOIN dim_customer c ON f.customer_key = c.customer_key
WHERE c.customer_key IS NULL
UNION ALL
SELECT 'missing_product', COUNT(*)
FROM fact_order_line f LEFT JOIN dim_product p ON f.product_key = p.product_key
WHERE p.product_key IS NULL
UNION ALL
SELECT 'missing_category', COUNT(*)
FROM fact_order_line f LEFT JOIN dim_category cat ON f.category_key = cat.category_key
WHERE cat.category_key IS NULL
UNION ALL
SELECT 'missing_payment', COUNT(*)
FROM fact_order_line f LEFT JOIN dim_payment pay ON f.payment_key = pay.payment_key
WHERE pay.payment_key IS NULL
UNION ALL
SELECT 'missing_shipping', COUNT(*)
FROM fact_order_line f LEFT JOIN dim_shipping s ON f.shipping_key = s.shipping_key
WHERE s.shipping_key IS NULL;

-- =========================
-- 3) Arithmetic checks with tolerance (should be 0)
-- =========================
SELECT 'invalid_net_formula' AS check_name, COUNT(*) AS issue_count
FROM fact_order_line
WHERE ABS(net_amount - (gross_amount - discount_amount)) > 0.02
UNION ALL
SELECT 'invalid_profit_formula', COUNT(*)
FROM fact_order_line
WHERE ABS(profit_amount - (net_amount - cost_amount)) > 0.02
UNION ALL
SELECT 'invalid_quantity', COUNT(*)
FROM fact_order_line
WHERE quantity <= 0;

-- =========================
-- 4) Analytical sanity checks
-- =========================
SELECT
  SUM(net_amount) AS total_revenue,
  COUNT(DISTINCT order_id) AS total_orders,
  ROUND(SUM(net_amount) / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS avg_order_value
FROM fact_order_line;

SELECT
  d.year,
  d.month,
  COUNT(*) AS order_lines,
  ROUND(SUM(f.net_amount), 2) AS monthly_revenue
FROM fact_order_line f
JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.year, d.month
ORDER BY d.year, d.month;
