-- ============================================================
-- Mexora BI Project
-- Schéma transactionnel OLTP MySQL
-- Base: mexora_oltp
-- ============================================================

CREATE DATABASE IF NOT EXISTS mexora_oltp
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE mexora_oltp;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `returns`;
DROP TABLE IF EXISTS `deliveries`;
DROP TABLE IF EXISTS `payments`;
DROP TABLE IF EXISTS `order_items`;
DROP TABLE IF EXISTS `orders`;
DROP TABLE IF EXISTS `products`;
DROP TABLE IF EXISTS `customers`;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE `customers` (
    `customer_id`        INT PRIMARY KEY,
    `full_name`          VARCHAR(150) NOT NULL,
    `email`              VARCHAR(150),
    `phone`              VARCHAR(30),
    `city`               VARCHAR(80),
    `region`             VARCHAR(120),
    `registration_date`  DATE,
    `gender`             VARCHAR(20),
    `birth_date`         DATE,
    INDEX `idx_customers_city_region` (`city`, `region`),
    INDEX `idx_customers_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `products` (
    `product_id`     INT PRIMARY KEY,
    `product_name`   VARCHAR(180) NOT NULL,
    `category`       VARCHAR(60) NOT NULL,
    `sub_category`   VARCHAR(80) NOT NULL,
    `brand`          VARCHAR(80),
    `supplier`       VARCHAR(100),
    `price`          DECIMAL(10,2),
    `created_at`     DATE,
    INDEX `idx_products_category` (`category`, `sub_category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `orders` (
    `order_id`      INT PRIMARY KEY,
    `customer_id`   INT NOT NULL,
    `order_date`    DATE,
    `order_status`  VARCHAR(30) NOT NULL,
    `total_amount`  DECIMAL(12,2) DEFAULT 0,
    CONSTRAINT `fk_orders_customer`
      FOREIGN KEY (`customer_id`) REFERENCES `customers`(`customer_id`),
    INDEX `idx_orders_customer` (`customer_id`),
    INDEX `idx_orders_order_date` (`order_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `order_items` (
    `order_item_id`  INT PRIMARY KEY,
    `order_id`       INT NOT NULL,
    `product_id`     INT NOT NULL,
    `quantity`       INT,
    `unit_price`     DECIMAL(10,2),
    `discount_rate`  DECIMAL(5,4) DEFAULT 0,
    CONSTRAINT `fk_items_order`
      FOREIGN KEY (`order_id`) REFERENCES `orders`(`order_id`),
    CONSTRAINT `fk_items_product`
      FOREIGN KEY (`product_id`) REFERENCES `products`(`product_id`),
    INDEX `idx_items_order` (`order_id`),
    INDEX `idx_items_product` (`product_id`),
    INDEX `idx_items_order_product` (`order_id`, `product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `payments` (
    `payment_id`      INT PRIMARY KEY,
    `order_id`        INT NOT NULL,
    `payment_method`  VARCHAR(50) NOT NULL,
    `payment_status`  VARCHAR(40),
    `payment_date`    DATE,
    `amount_paid`     DECIMAL(12,2),
    CONSTRAINT `fk_payments_order`
      FOREIGN KEY (`order_id`) REFERENCES `orders`(`order_id`),
    INDEX `idx_payments_order` (`order_id`),
    INDEX `idx_payments_method_status` (`payment_method`, `payment_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `deliveries` (
    `delivery_id`       INT PRIMARY KEY,
    `order_id`          INT NOT NULL,
    `delivery_city`     VARCHAR(80),
    `delivery_region`   VARCHAR(120),
    `delivery_status`   VARCHAR(40),
    `shipping_company`  VARCHAR(80),
    `shipped_date`      DATE,
    `delivered_date`    DATE,
    CONSTRAINT `fk_deliveries_order`
      FOREIGN KEY (`order_id`) REFERENCES `orders`(`order_id`),
    INDEX `idx_deliveries_order` (`order_id`),
    INDEX `idx_deliveries_region` (`delivery_city`, `delivery_region`),
    INDEX `idx_deliveries_status_company` (`delivery_status`, `shipping_company`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `returns` (
    `return_id`      INT PRIMARY KEY,
    `order_id`       INT NOT NULL,
    `product_id`     INT NOT NULL,
    `return_reason`  VARCHAR(120),
    `return_date`    DATE,
    `refund_amount`  DECIMAL(12,2),
    CONSTRAINT `fk_returns_order`
      FOREIGN KEY (`order_id`) REFERENCES `orders`(`order_id`),
    CONSTRAINT `fk_returns_product`
      FOREIGN KEY (`product_id`) REFERENCES `products`(`product_id`),
    INDEX `idx_returns_order` (`order_id`),
    INDEX `idx_returns_product` (`product_id`),
    INDEX `idx_returns_order_product` (`order_id`, `product_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
