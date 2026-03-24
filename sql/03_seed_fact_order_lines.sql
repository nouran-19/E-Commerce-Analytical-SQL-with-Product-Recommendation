-- Seed fact_order_line with synthetic transactions
-- Run after: 02_seed_dimensions.sql

USE ecommerce_dw;

-- For repeatable reruns during practice
TRUNCATE TABLE fact_order_line;

SET @date_cnt = (SELECT COUNT(*) FROM dim_date);
SET @customer_cnt = (SELECT COUNT(*) FROM dim_customer);
SET @product_cnt = (SELECT COUNT(*) FROM dim_product);
SET @category_cnt = (SELECT COUNT(*) FROM dim_category);
SET @payment_cnt = (SELECT COUNT(*) FROM dim_payment);
SET @shipping_cnt = (SELECT COUNT(*) FROM dim_shipping);

-- 1,000 order lines (enough signal for analytics/recommendation demos)
INSERT INTO fact_order_line (
  date_key,
  customer_key,
  product_key,
  category_key,
  payment_key,
  shipping_key,
  order_id,
  quantity,
  gross_amount,
  discount_amount,
  net_amount,
  cost_amount,
  profit_amount
)
WITH RECURSIVE seq AS (
  SELECT 1 AS n
  UNION ALL
  SELECT n + 1 FROM seq WHERE n < 1000
),
b AS (
  SELECT
    n,
    -- About 2 lines per order on average
    CONCAT('ORD', LPAD(FLOOR((n - 1) / 2) + 1, 6, '0')) AS order_id,

    -- Random dimension links using row-number selection
    (
      SELECT d.date_key
      FROM (
        SELECT date_key, ROW_NUMBER() OVER (ORDER BY date_key) AS rn
        FROM dim_date
      ) d
      WHERE d.rn = 1 + FLOOR(RAND(n * 11) * @date_cnt)
    ) AS date_key,

    1 + FLOOR(RAND(n * 13) * @customer_cnt) AS customer_key,
    1 + FLOOR(RAND(n * 17) * @product_cnt) AS product_key,
    1 + FLOOR(RAND(n * 19) * @category_cnt) AS category_key,
    1 + FLOOR(RAND(n * 23) * @payment_cnt) AS payment_key,
    1 + FLOOR(RAND(n * 29) * @shipping_cnt) AS shipping_key,

    (1 + FLOOR(RAND(n * 31) * 3)) AS qty,

    CASE
      WHEN RAND(n * 37) < 0.25 THEN ROUND(350 + RAND(n * 41) * 2000, 2)
      WHEN RAND(n * 37) < 0.75 THEN ROUND(1800 + RAND(n * 43) * 12000, 2)
      ELSE ROUND(12000 + RAND(n * 47) * 65000, 2)
    END AS unit_price,

    ROUND(
      CASE
        WHEN RAND(n * 53) < 0.50 THEN RAND(n * 59) * 0.05
        WHEN RAND(n * 53) < 0.85 THEN 0.05 + RAND(n * 61) * 0.10
        ELSE 0.15 + RAND(n * 67) * 0.15
      END,
      4
    ) AS discount_pct,

    ROUND(0.62 + RAND(n * 71) * 0.25, 4) AS cost_ratio
  FROM seq
)
SELECT
  date_key,
  customer_key,
  product_key,
  category_key,
  payment_key,
  shipping_key,
  order_id,
  qty AS quantity,
  ROUND(qty * unit_price, 2) AS gross_amount,
  ROUND((qty * unit_price) * discount_pct, 2) AS discount_amount,
  ROUND((qty * unit_price) - ((qty * unit_price) * discount_pct), 2) AS net_amount,
  ROUND(((qty * unit_price) - ((qty * unit_price) * discount_pct)) * cost_ratio, 2) AS cost_amount,
  ROUND(
    ((qty * unit_price) - ((qty * unit_price) * discount_pct))
      - (((qty * unit_price) - ((qty * unit_price) * discount_pct)) * cost_ratio),
    2
  ) AS profit_amount
FROM b;

-- Quick checks
SELECT COUNT(*) AS fact_rows, COUNT(DISTINCT order_id) AS orders FROM fact_order_line;

SELECT
  MIN(net_amount) AS min_net,
  MAX(net_amount) AS max_net,
  AVG(net_amount) AS avg_net
FROM fact_order_line;
