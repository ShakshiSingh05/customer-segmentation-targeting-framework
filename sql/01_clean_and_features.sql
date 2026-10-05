-- 1. Clean transactions: drop duplicates and invalid (non-positive) amounts
DROP TABLE IF EXISTS txn_clean;
CREATE TABLE txn_clean AS
SELECT DISTINCT txn_id, customer_id, txn_date, category, amount
FROM transactions
WHERE amount > 0 AND customer_id IS NOT NULL;

-- 2. Customer-level behavioural features (spend, frequency, recency, tenure)
DROP TABLE IF EXISTS cust_features;
CREATE TABLE cust_features AS
SELECT c.customer_id, c.age_band, c.region, c.card_tier, c.tenure_months,
       COUNT(t.txn_id)                              AS txn_count,
       ROUND(SUM(t.amount),2)                       AS total_spend,
       ROUND(AVG(t.amount),2)                       AS avg_ticket,
       COUNT(DISTINCT t.category)                   AS categories_used,
       CAST(julianday('2026-09-30') - julianday(MAX(t.txn_date)) AS INT) AS recency_days
FROM customers c
JOIN txn_clean t ON t.customer_id = c.customer_id
GROUP BY c.customer_id;

-- 3. Category share of spend per customer
DROP TABLE IF EXISTS cust_category_share;
CREATE TABLE cust_category_share AS
SELECT t.customer_id, t.category,
       ROUND(SUM(t.amount) * 1.0 / f.total_spend, 4) AS spend_share
FROM txn_clean t JOIN cust_features f USING (customer_id)
GROUP BY t.customer_id, t.category;

-- 4. Data-quality audit (rows removed)
SELECT (SELECT COUNT(*) FROM transactions) AS raw_rows,
       (SELECT COUNT(*) FROM txn_clean)   AS clean_rows;
