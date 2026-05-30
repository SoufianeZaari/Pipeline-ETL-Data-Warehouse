-- ============================================================
-- Mexora BI Project
-- Données de démonstration minimales pour le schéma OLTP
-- Les volumes complets sont générés par scripts/generate_data.py.
-- ============================================================

USE mexora_oltp;

INSERT INTO customers
  (customer_id, full_name, email, phone, city, region, registration_date, gender, birth_date)
VALUES
  (1, 'Sara El Amrani', 'sara.elamrani@example.com', '0600000001', 'Tanger', 'Tanger-Tétouan-Al Hoceïma', '2025-05-11', 'Female', '1995-02-20'),
  (2, 'Yassine Bennani', 'yassine.bennani@example.com', '0600000002', 'Casablanca', 'Casablanca-Settat', '2025-06-02', 'Male', '1990-09-13'),
  (3, 'Imane Tahiri', 'imane.tahiri@example.com', '0600000003', 'Rabat', 'Rabat-Salé-Kénitra', '2025-07-18', 'Female', '1988-12-01');

INSERT INTO products
  (product_id, product_name, category, sub_category, brand, supplier, price, created_at)
VALUES
  (1, 'Atlas Smartphone X1', 'Electronics', 'Smartphones', 'AtlasTech', 'MediSupplier', 3499.00, '2025-01-01'),
  (2, 'Babouche Premium', 'Fashion', 'Traditional Clothes', 'MedinaWear', 'TangerStyle', 449.00, '2025-01-01'),
  (3, 'Dattes Majhoul 1kg', 'Food', 'Dates', 'SaharaTaste', 'AgriMaroc', 129.00, '2025-01-01');

INSERT INTO `orders`
  (order_id, customer_id, order_date, order_status, total_amount)
VALUES
  (1001, 1, '2026-02-22', 'completed', 3374.04),
  (1002, 2, '2026-03-05', 'completed', 258.00),
  (1003, 3, '2026-04-10', 'pending', 449.00);

INSERT INTO `order_items`
  (order_item_id, order_id, product_id, quantity, unit_price, discount_rate)
VALUES
  (1, 1001, 1, 1, 3499.00, 0.05),
  (2, 1001, 3, 1, 129.00, 0.00),
  (3, 1002, 3, 2, 129.00, 0.00),
  (4, 1003, 2, 1, 449.00, 0.00);

INSERT INTO payments
  (payment_id, order_id, payment_method, payment_status, payment_date, amount_paid)
VALUES
  (1, 1001, 'Credit Card', 'paid', '2026-02-22', 3453.05),
  (2, 1002, 'Cash on Delivery', 'paid', '2026-03-07', 258.00),
  (3, 1003, 'Wallet', 'pending', '2026-04-10', 0.00);

INSERT INTO deliveries
  (delivery_id, order_id, delivery_city, delivery_region, delivery_status, shipping_company, shipped_date, delivered_date)
VALUES
  (1, 1001, 'Tanger', 'Tanger-Tétouan-Al Hoceïma', 'delivered', 'Amana Express', '2026-02-23', '2026-02-25'),
  (2, 1002, 'Casablanca', 'Casablanca-Settat', 'delivered', 'Barid Logistics', '2026-03-06', '2026-03-08'),
  (3, 1003, 'Rabat', 'Rabat-Salé-Kénitra', 'in_transit', 'Jibli', '2026-04-11', NULL);

INSERT INTO `returns`
  (return_id, order_id, product_id, return_reason, return_date, refund_amount)
VALUES
  (1, 1001, 3, 'Damaged product', '2026-02-28', 129.00);
