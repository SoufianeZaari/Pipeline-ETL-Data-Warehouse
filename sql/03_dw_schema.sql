-- ============================================================
-- Mexora BI Project
-- Data Warehouse MySQL en schéma en étoile
-- Base: mexora_dw
-- ============================================================

CREATE DATABASE IF NOT EXISTS mexora_dw
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE mexora_dw;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `fact_sales`;
DROP TABLE IF EXISTS `quality_issues`;
DROP TABLE IF EXISTS `dim_delivery`;
DROP TABLE IF EXISTS `dim_payment`;
DROP TABLE IF EXISTS `dim_region`;
DROP TABLE IF EXISTS `dim_date`;
DROP TABLE IF EXISTS `dim_product`;
DROP TABLE IF EXISTS `dim_customer`;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE `dim_customer` (
    `customer_key`       INT PRIMARY KEY AUTO_INCREMENT,
    `customer_id`        INT NOT NULL UNIQUE,
    `full_name`          VARCHAR(150) NOT NULL,
    `gender`             VARCHAR(20),
    `age_group`          VARCHAR(20),
    `city`               VARCHAR(80),
    `region`             VARCHAR(120),
    `segment_client`     VARCHAR(20) NOT NULL DEFAULT 'Bronze',
    `registration_date`  DATE,
    `date_debut`         DATE NOT NULL DEFAULT '2025-01-01',
    `date_fin`           DATE NOT NULL DEFAULT '9999-12-31',
    `est_actif`          TINYINT(1) NOT NULL DEFAULT 1,
    CONSTRAINT `chk_dim_customer_segment`
      CHECK (`segment_client` IN ('Gold', 'Silver', 'Bronze')),
    INDEX `idx_dim_customer_city_region` (`city`, `region`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `dim_product` (
    `product_key`   INT PRIMARY KEY AUTO_INCREMENT,
    `product_id`    INT NOT NULL UNIQUE,
    `product_name`  VARCHAR(180) NOT NULL,
    `category`      VARCHAR(60) NOT NULL,
    `sub_category`  VARCHAR(80) NOT NULL,
    `brand`         VARCHAR(80),
    `supplier`      VARCHAR(100),
    `date_debut`    DATE NOT NULL DEFAULT '2025-01-01',
    `date_fin`      DATE NOT NULL DEFAULT '9999-12-31',
    `est_actif`     TINYINT(1) NOT NULL DEFAULT 1,
    INDEX `idx_dim_product_category` (`category`, `sub_category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `dim_date` (
    `date_key`    INT PRIMARY KEY,
    `full_date`   DATE NOT NULL UNIQUE,
    `day`         TINYINT NOT NULL,
    `month`       TINYINT NOT NULL,
    `month_name`  VARCHAR(20) NOT NULL,
    `quarter`     TINYINT NOT NULL,
    `year`        SMALLINT NOT NULL,
    `is_weekend`  TINYINT(1) NOT NULL,
    `is_ramadan`  TINYINT(1) NOT NULL,
    INDEX `idx_dim_date_year_month` (`year`, `month`),
    INDEX `idx_dim_date_ramadan` (`is_ramadan`, `year`, `month`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `dim_region` (
    `region_key`  INT PRIMARY KEY AUTO_INCREMENT,
    `city`        VARCHAR(80) NOT NULL,
    `region`      VARCHAR(120) NOT NULL,
    `country`     VARCHAR(50) NOT NULL DEFAULT 'Maroc',
    UNIQUE KEY `uq_dim_region_city_region` (`city`, `region`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `dim_payment` (
    `payment_key`     INT PRIMARY KEY AUTO_INCREMENT,
    `payment_method`  VARCHAR(50) NOT NULL,
    `payment_status`  VARCHAR(40) NOT NULL,
    UNIQUE KEY `uq_dim_payment_method_status` (`payment_method`, `payment_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `dim_delivery` (
    `delivery_key`      INT PRIMARY KEY AUTO_INCREMENT,
    `delivery_status`   VARCHAR(40) NOT NULL,
    `shipping_company`  VARCHAR(80) NOT NULL,
    `delivery_city`     VARCHAR(80) NOT NULL,
    `delivery_region`   VARCHAR(120) NOT NULL,
    UNIQUE KEY `uq_dim_delivery` (`delivery_status`, `shipping_company`, `delivery_city`, `delivery_region`),
    INDEX `idx_dim_delivery_company` (`shipping_company`),
    INDEX `idx_dim_delivery_region` (`delivery_city`, `delivery_region`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `quality_issues` (
    `issue_key`   BIGINT PRIMARY KEY AUTO_INCREMENT,
    `table_name`  VARCHAR(80) NOT NULL,
    `record_id`   VARCHAR(80),
    `issue_type`  VARCHAR(100) NOT NULL,
    `action`      VARCHAR(30) NOT NULL,
    `details`     VARCHAR(255),
    INDEX `idx_quality_issue_type` (`issue_type`),
    INDEX `idx_quality_action` (`action`),
    INDEX `idx_quality_table` (`table_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `fact_sales` (
    `sales_key`            BIGINT PRIMARY KEY AUTO_INCREMENT,
    `order_id`             INT NOT NULL,
    `order_item_id`        INT NOT NULL UNIQUE,
    `customer_key`         INT NOT NULL,
    `product_key`          INT NOT NULL,
    `date_key`             INT NOT NULL,
    `region_key`           INT NOT NULL,
    `payment_key`          INT NOT NULL,
    `delivery_key`         INT NOT NULL,
    `quantity`             INT NOT NULL,
    `unit_price`           DECIMAL(10,2) NOT NULL,
    `discount_rate`        DECIMAL(5,4) NOT NULL DEFAULT 0,
    `total_amount`         DECIMAL(12,2) NOT NULL,
    `amount_paid`          DECIMAL(12,2) NOT NULL,
    `is_returned`          TINYINT(1) NOT NULL DEFAULT 0,
    `refund_amount`        DECIMAL(12,2) NOT NULL DEFAULT 0,
    `delivery_delay_days`  DECIMAL(8,2),
    `order_status`         VARCHAR(30) NOT NULL,
    `return_reason`        VARCHAR(120),
    CONSTRAINT `fk_fact_customer`
      FOREIGN KEY (`customer_key`) REFERENCES `dim_customer`(`customer_key`),
    CONSTRAINT `fk_fact_product`
      FOREIGN KEY (`product_key`) REFERENCES `dim_product`(`product_key`),
    CONSTRAINT `fk_fact_date`
      FOREIGN KEY (`date_key`) REFERENCES `dim_date`(`date_key`),
    CONSTRAINT `fk_fact_region`
      FOREIGN KEY (`region_key`) REFERENCES `dim_region`(`region_key`),
    CONSTRAINT `fk_fact_payment`
      FOREIGN KEY (`payment_key`) REFERENCES `dim_payment`(`payment_key`),
    CONSTRAINT `fk_fact_delivery`
      FOREIGN KEY (`delivery_key`) REFERENCES `dim_delivery`(`delivery_key`),
    INDEX `idx_fact_sales_order` (`order_id`),
    INDEX `idx_fact_sales_date` (`date_key`),
    INDEX `idx_fact_sales_customer` (`customer_key`),
    INDEX `idx_fact_sales_product` (`product_key`),
    INDEX `idx_fact_sales_region` (`region_key`),
    INDEX `idx_fact_sales_payment` (`payment_key`),
    INDEX `idx_fact_sales_delivery` (`delivery_key`),
    INDEX `idx_fact_sales_status` (`order_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
