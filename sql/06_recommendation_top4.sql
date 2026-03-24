-- Product recommendation ranking (SQL-first)
-- Improvements applied:
--   1. Per-source-product normalization (PARTITION BY source_product_key)
--   2. COALESCE to handle NULL scores
--   3. NULL-safe subcategory matching
--   4. Exponential recency decay (sharper drop-off)
--   5. Availability filter (is_active)
--   6. Rebalanced weights + category hierarchy matching

USE ecommerce_dw;

DROP VIEW IF EXISTS v_recommendation_top4;

CREATE VIEW v_recommendation_top4 AS
WITH order_products AS (
  SELECT DISTINCT
    f.order_id,
    f.product_key,
    d.full_date
  FROM fact_order_line f
  JOIN dim_date d ON f.date_key = d.date_key
),
product_pairs AS (
  SELECT
    op1.product_key AS source_product_key,
    op2.product_key AS candidate_product_key,
    COUNT(*) AS co_purchase_count,
    MAX(GREATEST(op1.full_date, op2.full_date)) AS last_together_date
  FROM order_products op1
  JOIN order_products op2
    ON op1.order_id = op2.order_id
   AND op1.product_key < op2.product_key
  GROUP BY op1.product_key, op2.product_key
),
directed_pairs AS (
  SELECT
    source_product_key,
    candidate_product_key,
    co_purchase_count,
    last_together_date
  FROM product_pairs
  UNION ALL
  SELECT
    candidate_product_key AS source_product_key,
    source_product_key AS candidate_product_key,
    co_purchase_count,
    last_together_date
  FROM product_pairs
),
candidate_popularity AS (
  SELECT
    product_key,
    COUNT(DISTINCT order_id) AS product_order_count
  FROM fact_order_line
  GROUP BY product_key
),
candidate_margin AS (
  SELECT
    product_key,
    AVG(CASE WHEN net_amount = 0 THEN 0 ELSE profit_amount / net_amount END) AS avg_margin_ratio
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
           AND sp.subcategory IS NOT NULL THEN 1.0          -- Same subcategory
      WHEN sp_cat.parent_category = cp_cat.parent_category
           AND sp_cat.parent_category IS NOT NULL THEN 0.5  -- Same parent category
      ELSE 0
    END AS category_match,

    -- FIX 1: Per-source-product normalization (not global)
    dp.co_purchase_count / NULLIF(
      MAX(dp.co_purchase_count) OVER (PARTITION BY dp.source_product_key), 0
    ) AS freq_norm,

    -- FIX 4: Exponential decay instead of hyperbolic
    EXP(-DATEDIFF(CURDATE(), dp.last_together_date) / 90.0)
      / NULLIF(
          MAX(EXP(-DATEDIFF(CURDATE(), dp.last_together_date) / 90.0))
          OVER (PARTITION BY dp.source_product_key), 0
        ) AS recency_norm,

    -- Global normalization is OK for popularity and margin (comparing across all products)
    cp.product_order_count / NULLIF(MAX(cp.product_order_count) OVER (), 0) AS popularity_norm,
    cm.avg_margin_ratio / NULLIF(MAX(cm.avg_margin_ratio) OVER (), 0) AS margin_norm

  FROM directed_pairs dp
  JOIN dim_product sp  ON dp.source_product_key    = sp.product_key
  JOIN dim_product cpd ON dp.candidate_product_key = cpd.product_key
  -- FIX 5: Only recommend active products
  AND cpd.is_active = TRUE
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
        0.05 * 1  -- availability bonus (already filtered to active only)
      ),
      2
    ) AS recommendation_score,
    ROW_NUMBER() OVER (
      PARTITION BY s.source_product_key
      ORDER BY
        (0.40 * COALESCE(s.freq_norm, 0) +
         0.25 * COALESCE(s.recency_norm, 0) +
         0.10 * COALESCE(s.category_match, 0) +
         0.10 * COALESCE(s.popularity_norm, 0) +
         0.10 * COALESCE(s.margin_norm, 0) +
         0.05 * 1) DESC,
        s.candidate_product_key
    ) AS recommendation_rank
  FROM scored s
)
SELECT
  r.source_product_key,
  sp.product_id AS source_product_id,
  sp.product_name AS source_product_name,
  r.candidate_product_key,
  cp.product_id AS candidate_product_id,
  cp.product_name AS candidate_product_name,
  r.recommendation_score,
  r.recommendation_rank
FROM ranked r
JOIN dim_product sp ON r.source_product_key = sp.product_key
JOIN dim_product cp ON r.candidate_product_key = cp.product_key
WHERE r.recommendation_rank <= 4;

-- =========================
-- Validation queries
-- =========================

-- Quick sample
SELECT *
FROM v_recommendation_top4
ORDER BY source_product_key, recommendation_rank
LIMIT 80;

-- Coverage: recommendations per product
SELECT
  source_product_id,
  COUNT(*) AS recommendations_per_product
FROM v_recommendation_top4
GROUP BY source_product_id
ORDER BY recommendations_per_product DESC, source_product_id
LIMIT 20;

-- Check 1: Products with NO recommendations (never co-purchased)
SELECT
  p.product_id,
  p.product_name,
  COUNT(r.candidate_product_key) AS rec_count
FROM dim_product p
LEFT JOIN v_recommendation_top4 r ON p.product_key = r.source_product_key
WHERE p.is_active = TRUE
GROUP BY p.product_id, p.product_name
HAVING rec_count = 0;

-- Check 2: No self-recommendations (should return 0 rows)
SELECT *
FROM v_recommendation_top4
WHERE source_product_key = candidate_product_key;

-- Check 3: Score distribution sanity
SELECT
  MIN(recommendation_score) AS min_score,
  AVG(recommendation_score) AS avg_score,
  MAX(recommendation_score) AS max_score,
  STDDEV(recommendation_score) AS stddev_score
FROM v_recommendation_top4;

-- Check 4: Diversity check (flag if one product dominates recs)
SELECT
  candidate_product_id,
  COUNT(DISTINCT source_product_id) AS appears_in_N_recommendations
FROM v_recommendation_top4
GROUP BY candidate_product_id
ORDER BY appears_in_N_recommendations DESC
LIMIT 10;
