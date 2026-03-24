-- E-Commerce Data Warehouse Schema (MySQL 8.0)
-- Purpose: Create database + 6 dimensions + 1 fact table

CREATE DATABASE IF NOT EXISTS ecommerce_dw
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE ecommerce_dw;

-- Strict mode helps catch bad data early.
SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- =========================
-- Dimension tables
-- =========================

CREATE TABLE IF NOT EXISTS dim_date (
  date_key INT PRIMARY KEY COMMENT 'YYYYMMDD, e.g. 20260324',
  full_date DATE NOT NULL UNIQUE,
  day_of_week TINYINT NOT NULL COMMENT '1=Monday ... 7=Sunday',
  day_name VARCHAR(10) NOT NULL,
  day_of_month TINYINT NOT NULL,
  day_of_year SMALLINT NOT NULL,
  week_number TINYINT NOT NULL,
  month TINYINT NOT NULL,
  month_name VARCHAR(10) NOT NULL,
  quarter TINYINT NOT NULL,
  year SMALLINT NOT NULL,
  is_weekend BOOLEAN NOT NULL DEFAULT FALSE,
  is_holiday BOOLEAN NOT NULL DEFAULT FALSE,
  INDEX idx_dim_date_year_month (year, month),
  INDEX idx_dim_date_full_date (full_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dim_customer (
  customer_key INT PRIMARY KEY AUTO_INCREMENT,
  customer_id VARCHAR(50) NOT NULL UNIQUE,
  customer_name VARCHAR(100) NOT NULL,
  email VARCHAR(100),
  gender ENUM('Male', 'Female', 'Other', 'Prefer not to say') DEFAULT 'Prefer not to say',
  age_group VARCHAR(20),
  city VARCHAR(50),
  region VARCHAR(50),
  country VARCHAR(50) DEFAULT 'Egypt',
  registration_date DATE NOT NULL,
  customer_segment VARCHAR(20),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_dim_customer_segment (customer_segment),
  INDEX idx_dim_customer_region (region)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dim_category (
  category_key INT PRIMARY KEY AUTO_INCREMENT,
  category_id VARCHAR(50) NOT NULL UNIQUE,
  category_name VARCHAR(100) NOT NULL,
  parent_category VARCHAR(100),
  seasonal_flag BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_dim_category_parent (parent_category)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dim_product (
  product_key INT PRIMARY KEY AUTO_INCREMENT,
  product_id VARCHAR(50) NOT NULL UNIQUE,
  product_name VARCHAR(200) NOT NULL,
  brand VARCHAR(100),
  subcategory VARCHAR(50),
  unit_price DECIMAL(10,2),
  cost_price DECIMAL(10,2),
  launch_date DATE,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_dim_product_brand (brand),
  INDEX idx_dim_product_subcategory (subcategory),
  INDEX idx_dim_product_is_active (is_active)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dim_payment (
  payment_key INT PRIMARY KEY AUTO_INCREMENT,
  payment_id VARCHAR(50) NOT NULL UNIQUE,
  payment_method VARCHAR(50) NOT NULL,
  payment_provider VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_dim_payment_method (payment_method)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dim_shipping (
  shipping_key INT PRIMARY KEY AUTO_INCREMENT,
  shipping_id VARCHAR(50) NOT NULL UNIQUE,
  shipping_type VARCHAR(50) NOT NULL,
  carrier VARCHAR(50),
  delivery_days INT,
  shipping_cost DECIMAL(10,2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_dim_shipping_type (shipping_type)
) ENGINE=InnoDB;

-- =========================
-- Fact table
-- =========================

CREATE TABLE IF NOT EXISTS fact_order_line (
  order_line_key BIGINT PRIMARY KEY AUTO_INCREMENT,

  -- Dimension foreign keys
  date_key INT NOT NULL,
  customer_key INT NOT NULL,
  product_key INT NOT NULL,
  category_key INT NOT NULL,
  payment_key INT NOT NULL,
  shipping_key INT NOT NULL,

  -- Degenerate dimension
  order_id VARCHAR(50) NOT NULL,

  -- Measures
  quantity DECIMAL(10,2) NOT NULL,
  gross_amount DECIMAL(10,2) NOT NULL,
  discount_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
  net_amount DECIMAL(10,2) NOT NULL,
  cost_amount DECIMAL(10,2) NOT NULL,
  profit_amount DECIMAL(10,2) NOT NULL,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  INDEX idx_fact_date (date_key),
  INDEX idx_fact_customer (customer_key),
  INDEX idx_fact_product (product_key),
  INDEX idx_fact_category (category_key),
  INDEX idx_fact_order (order_id),
  INDEX idx_fact_date_customer (date_key, customer_key),
  INDEX idx_fact_date_product (date_key, product_key),

  CONSTRAINT fk_fact_date
    FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
  CONSTRAINT fk_fact_customer
    FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
  CONSTRAINT fk_fact_product
    FOREIGN KEY (product_key) REFERENCES dim_product(product_key),
  CONSTRAINT fk_fact_category
    FOREIGN KEY (category_key) REFERENCES dim_category(category_key),
  CONSTRAINT fk_fact_payment
    FOREIGN KEY (payment_key) REFERENCES dim_payment(payment_key),
  CONSTRAINT fk_fact_shipping
    FOREIGN KEY (shipping_key) REFERENCES dim_shipping(shipping_key)
) ENGINE=InnoDB;

-- =========================
-- Quick verification
-- =========================

SHOW DATABASES LIKE 'ecommerce_dw';
SHOW TABLES;

SELECT
  table_name,
  engine,
  table_rows
FROM information_schema.tables
WHERE table_schema = 'ecommerce_dw'
ORDER BY table_name;

SELECT
  table_name,
  constraint_name,
  referenced_table_name
FROM information_schema.key_column_usage
WHERE table_schema = 'ecommerce_dw'
  AND referenced_table_name IS NOT NULL
ORDER BY table_name, constraint_name;
