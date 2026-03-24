-- Seed dimension tables for ecommerce_dw
-- Run after: 01_create_dw_schema.sql

USE ecommerce_dw;

-- Optional clean reset for repeatable runs
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE fact_order_line;
TRUNCATE TABLE dim_shipping;
TRUNCATE TABLE dim_payment;
TRUNCATE TABLE dim_product;
TRUNCATE TABLE dim_category;
TRUNCATE TABLE dim_customer;
TRUNCATE TABLE dim_date;
SET FOREIGN_KEY_CHECKS = 1;

-- =========================
-- dim_date (2 years = 730 rows)
-- =========================

INSERT INTO dim_date (
  date_key, full_date, day_of_week, day_name, day_of_month, day_of_year,
  week_number, month, month_name, quarter, year, is_weekend, is_holiday
)
WITH RECURSIVE seq AS (
  SELECT 0 AS n
  UNION ALL
  SELECT n + 1 FROM seq WHERE n < 729
)
SELECT
  DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL (729 - n) DAY), '%Y%m%d') + 0 AS date_key,
  DATE_SUB(CURDATE(), INTERVAL (729 - n) DAY) AS full_date,
  WEEKDAY(DATE_SUB(CURDATE(), INTERVAL (729 - n) DAY)) + 1 AS day_of_week,
  DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL (729 - n) DAY), '%W') AS day_name,
  DAY(DATE_SUB(CURDATE(), INTERVAL (729 - n) DAY)) AS day_of_month,
  DAYOFYEAR(DATE_SUB(CURDATE(), INTERVAL (729 - n) DAY)) AS day_of_year,
  WEEK(DATE_SUB(CURDATE(), INTERVAL (729 - n) DAY), 3) AS week_number,
  MONTH(DATE_SUB(CURDATE(), INTERVAL (729 - n) DAY)) AS month,
  DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL (729 - n) DAY), '%M') AS month_name,
  QUARTER(DATE_SUB(CURDATE(), INTERVAL (729 - n) DAY)) AS quarter,
  YEAR(DATE_SUB(CURDATE(), INTERVAL (729 - n) DAY)) AS year,
  CASE WHEN WEEKDAY(DATE_SUB(CURDATE(), INTERVAL (729 - n) DAY)) IN (5, 6) THEN TRUE ELSE FALSE END AS is_weekend,
  CASE
    WHEN DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL (729 - n) DAY), '%m-%d') IN ('01-01', '04-25', '05-01', '07-23', '10-06')
      THEN TRUE
    ELSE FALSE
  END AS is_holiday
FROM seq;

-- =========================
-- dim_category (12 rows)
-- =========================

INSERT INTO dim_category (category_id, category_name, parent_category, seasonal_flag)
VALUES
  ('CAT001', 'Smartphones', 'Mobile Devices', FALSE),
  ('CAT002', 'Laptops', 'Computing', FALSE),
  ('CAT003', 'Tablets', 'Mobile Devices', FALSE),
  ('CAT004', 'Smartwatches', 'Wearables', FALSE),
  ('CAT005', 'Headphones', 'Audio', FALSE),
  ('CAT006', 'Earbuds', 'Audio', FALSE),
  ('CAT007', 'Gaming Consoles', 'Gaming', FALSE),
  ('CAT008', 'Keyboards', 'Computer Accessories', FALSE),
  ('CAT009', 'Mice', 'Computer Accessories', FALSE),
  ('CAT010', 'Monitors', 'Displays', FALSE),
  ('CAT011', 'Chargers', 'Accessories', FALSE),
  ('CAT012', 'Power Banks', 'Accessories', TRUE);

-- =========================
-- dim_payment (8 rows)
-- =========================

INSERT INTO dim_payment (payment_id, payment_method, payment_provider)
VALUES
  ('PAY001', 'Credit Card', 'Visa'),
  ('PAY002', 'Credit Card', 'Mastercard'),
  ('PAY003', 'Debit Card', 'Visa Electron'),
  ('PAY004', 'Digital Wallet', 'PayPal'),
  ('PAY005', 'Digital Wallet', 'Apple Pay'),
  ('PAY006', 'Digital Wallet', 'Google Pay'),
  ('PAY007', 'Cash on Delivery', 'Courier'),
  ('PAY008', 'Bank Transfer', 'Local Bank');

-- =========================
-- dim_shipping (8 rows)
-- =========================

INSERT INTO dim_shipping (shipping_id, shipping_type, carrier, delivery_days, shipping_cost)
VALUES
  ('SHP001', 'Standard', 'Aramex', 5, 35.00),
  ('SHP002', 'Standard', 'DHL eCommerce', 6, 30.00),
  ('SHP003', 'Express', 'DHL Express', 2, 70.00),
  ('SHP004', 'Express', 'FedEx', 2, 75.00),
  ('SHP005', 'Same-Day', 'Local Courier', 0, 95.00),
  ('SHP006', 'Next-Day', 'Aramex', 1, 55.00),
  ('SHP007', 'Pickup Point', 'Partner Store', 1, 15.00),
  ('SHP008', 'Economy', 'Egypt Post', 8, 20.00);

-- =========================
-- dim_customer (120 rows)
-- =========================

INSERT INTO dim_customer (
  customer_id, customer_name, email, gender, age_group, city, region, country,
  registration_date, customer_segment
)
WITH RECURSIVE seq AS (
  SELECT 1 AS n
  UNION ALL
  SELECT n + 1 FROM seq WHERE n < 120
)
SELECT
  CONCAT('CUST', LPAD(n, 4, '0')) AS customer_id,
  CONCAT('Customer ', LPAD(n, 4, '0')) AS customer_name,
  CONCAT('customer', LPAD(n, 4, '0'), '@example.com') AS email,
  ELT(1 + FLOOR(RAND(n * 17) * 4), 'Male', 'Female', 'Other', 'Prefer not to say') AS gender,
  ELT(1 + FLOOR(RAND(n * 19) * 4), '18-25', '26-35', '36-50', '51+') AS age_group,
  ELT(1 + FLOOR(RAND(n * 23) * 8), 'Cairo', 'Giza', 'Alexandria', 'Mansoura', 'Tanta', 'Asyut', 'Hurghada', 'Suez') AS city,
  ELT(1 + FLOOR(RAND(n * 29) * 5), 'Greater Cairo', 'Delta', 'Alexandria', 'Upper Egypt', 'Canal') AS region,
  'Egypt' AS country,
  DATE_SUB(CURDATE(), INTERVAL FLOOR(RAND(n * 31) * 720) DAY) AS registration_date,
  CASE
    WHEN n % 10 = 0 THEN 'VIP'
    WHEN n % 3 = 0 THEN 'Regular'
    ELSE 'New'
  END AS customer_segment
FROM seq;

-- =========================
-- dim_product (140 rows)
-- =========================

INSERT INTO dim_product (
  product_id, product_name, brand, subcategory, unit_price, cost_price, launch_date, is_active
)
WITH RECURSIVE seq AS (
  SELECT 1 AS n
  UNION ALL
  SELECT n + 1 FROM seq WHERE n < 140
),
base AS (
  SELECT
    n,
    ELT(1 + (n % 12),
      'Smartphones', 'Laptops', 'Tablets', 'Smartwatches', 'Headphones', 'Earbuds',
      'Gaming Consoles', 'Keyboards', 'Mice', 'Monitors', 'Chargers', 'Power Banks'
    ) AS subcategory,
    ELT(1 + FLOOR(RAND(n * 37) * 10),
      'Apple', 'Samsung', 'Xiaomi', 'Sony', 'Lenovo', 'HP', 'Dell', 'Asus', 'Logitech', 'Anker'
    ) AS brand,
    CASE
      WHEN (n % 12) = 1 THEN ROUND(25000 + RAND(n * 41) * 45000, 2)   -- Smartphones
      WHEN (n % 12) = 2 THEN ROUND(28000 + RAND(n * 43) * 70000, 2)   -- Laptops
      WHEN (n % 12) = 3 THEN ROUND(12000 + RAND(n * 47) * 28000, 2)   -- Tablets
      WHEN (n % 12) = 4 THEN ROUND(7000 + RAND(n * 53) * 18000, 2)    -- Smartwatches
      WHEN (n % 12) = 5 THEN ROUND(1800 + RAND(n * 59) * 9000, 2)     -- Headphones
      WHEN (n % 12) = 6 THEN ROUND(1200 + RAND(n * 61) * 6000, 2)     -- Earbuds
      WHEN (n % 12) = 7 THEN ROUND(18000 + RAND(n * 67) * 25000, 2)   -- Consoles
      WHEN (n % 12) = 8 THEN ROUND(450 + RAND(n * 71) * 3500, 2)       -- Keyboards
      WHEN (n % 12) = 9 THEN ROUND(300 + RAND(n * 73) * 2800, 2)       -- Mice
      WHEN (n % 12) = 10 THEN ROUND(4500 + RAND(n * 79) * 30000, 2)    -- Monitors
      WHEN (n % 12) = 11 THEN ROUND(200 + RAND(n * 83) * 1600, 2)      -- Chargers
      ELSE ROUND(350 + RAND(n * 89) * 4200, 2)                         -- Power Banks
    END AS unit_price
  FROM seq
)
SELECT
  CONCAT('PROD', LPAD(n, 4, '0')) AS product_id,
  CONCAT(brand, ' ', subcategory, ' Model ', LPAD(n, 3, '0')) AS product_name,
  brand,
  subcategory,
  unit_price,
  ROUND(unit_price * (0.62 + RAND(n * 97) * 0.22), 2) AS cost_price,
  DATE_SUB(CURDATE(), INTERVAL FLOOR(RAND(n * 101) * 900) DAY) AS launch_date,
  CASE WHEN n % 20 = 0 THEN FALSE ELSE TRUE END AS is_active
FROM base;

-- Quick checks
SELECT 'dim_date' AS table_name, COUNT(*) AS row_count FROM dim_date
UNION ALL SELECT 'dim_customer', COUNT(*) FROM dim_customer
UNION ALL SELECT 'dim_category', COUNT(*) FROM dim_category
UNION ALL SELECT 'dim_product', COUNT(*) FROM dim_product
UNION ALL SELECT 'dim_payment', COUNT(*) FROM dim_payment
UNION ALL SELECT 'dim_shipping', COUNT(*) FROM dim_shipping;
