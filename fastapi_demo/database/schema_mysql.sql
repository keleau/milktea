-- ============================================================
-- 四猫茶学园 · MySQL 8.0 建库建表脚本
-- 对应文档：docs/data-dictionary.md
-- 使用：mysql -u root -p < fastapi_demo/database/schema_mysql.sql
-- 说明：金额单位元，时间统一为 Unix 毫秒时间戳，图片存相对路径
-- ============================================================

CREATE DATABASE IF NOT EXISTS milktea
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE milktea;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS idempotency_keys;
DROP TABLE IF EXISTS order_item_toppings;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS favorites;
DROP TABLE IF EXISTS addresses;
DROP TABLE IF EXISTS user_coupons;
DROP TABLE IF EXISTS points_logs;
DROP TABLE IF EXISTS exchange_items;
DROP TABLE IF EXISTS coupon_templates;
DROP TABLE IF EXISTS stores;
DROP TABLE IF EXISTS toppings;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS product_lines;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS member_levels;

SET FOREIGN_KEY_CHECKS = 1;

-- ------------------------------------------------------------
-- 1. 会员等级
-- ------------------------------------------------------------
CREATE TABLE member_levels (
    code       VARCHAR(8) NOT NULL,
    name       VARCHAR(32) NOT NULL,
    min_points INT NOT NULL DEFAULT 0,
    sort_order INT NOT NULL DEFAULT 0,
    PRIMARY KEY (code),
    CONSTRAINT ck_member_levels_min_points CHECK (min_points >= 0)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '会员等级';

-- ------------------------------------------------------------
-- 2. 用户
-- ------------------------------------------------------------
CREATE TABLE users (
    id          INT NOT NULL AUTO_INCREMENT,
    openid      VARCHAR(64) NOT NULL,
    nickname    VARCHAR(20) NOT NULL DEFAULT '猫友1234',
    avatar_path VARCHAR(255) NOT NULL DEFAULT '/static/images/avatar.jpg',
    level_code  VARCHAR(8) NOT NULL DEFAULT 'V1',
    points      INT NOT NULL DEFAULT 0,
    growth      INT NOT NULL DEFAULT 0,
    balance     DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    created_at  BIGINT NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_openid (openid),
    KEY idx_users_level (level_code),
    CONSTRAINT fk_users_level FOREIGN KEY (level_code)
        REFERENCES member_levels (code)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT ck_users_points CHECK (points >= 0),
    CONSTRAINT ck_users_balance CHECK (balance >= 0)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  AUTO_INCREMENT = 1001 COMMENT = '用户';

-- ------------------------------------------------------------
-- 3. 产品线
-- ------------------------------------------------------------
CREATE TABLE product_lines (
    id          VARCHAR(32) NOT NULL,
    name        VARCHAR(64) NOT NULL,
    tag         VARCHAR(16) NOT NULL,
    en          VARCHAR(100) NOT NULL,
    description VARCHAR(255) NOT NULL DEFAULT '',
    color       CHAR(7) NOT NULL DEFAULT '#8B5E3C',
    bg          CHAR(7) NOT NULL DEFAULT '#F3EAE0',
    sort_order  INT NOT NULL DEFAULT 0,
    PRIMARY KEY (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '产品线';

-- ------------------------------------------------------------
-- 4. 饮品
-- ------------------------------------------------------------
CREATE TABLE products (
    id          INT NOT NULL AUTO_INCREMENT,
    line_id     VARCHAR(32) NOT NULL,
    name        VARCHAR(64) NOT NULL,
    price       DECIMAL(10, 2) NOT NULL,
    orig_price  DECIMAL(10, 2) NULL,
    paws        INT NOT NULL DEFAULT 3,
    is_hot      TINYINT(1) NOT NULL DEFAULT 0,
    is_new      TINYINT(1) NOT NULL DEFAULT 0,
    description VARCHAR(255) NOT NULL DEFAULT '',
    image_path  VARCHAR(255) NOT NULL,
    stock       INT NOT NULL DEFAULT 0,
    on_sale     TINYINT(1) NOT NULL DEFAULT 1,
    sort_order  INT NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    KEY idx_products_line (line_id),
    KEY idx_products_on_sale (on_sale, sort_order),
    CONSTRAINT fk_products_line FOREIGN KEY (line_id)
        REFERENCES product_lines (id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT ck_products_price CHECK (price >= 0),
    CONSTRAINT ck_products_orig_price CHECK (orig_price IS NULL OR orig_price >= 0),
    CONSTRAINT ck_products_paws CHECK (paws BETWEEN 1 AND 5),
    CONSTRAINT ck_products_is_hot CHECK (is_hot IN (0, 1)),
    CONSTRAINT ck_products_is_new CHECK (is_new IN (0, 1)),
    CONSTRAINT ck_products_stock CHECK (stock >= 0),
    CONSTRAINT ck_products_on_sale CHECK (on_sale IN (0, 1))
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '饮品';

-- ------------------------------------------------------------
-- 5. 小料
-- ------------------------------------------------------------
CREATE TABLE toppings (
    id         INT NOT NULL AUTO_INCREMENT,
    name       VARCHAR(32) NOT NULL,
    price      DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    sort_order INT NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    CONSTRAINT ck_toppings_price CHECK (price >= 0)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '小料';

-- ------------------------------------------------------------
-- 6. 门店
-- ------------------------------------------------------------
CREATE TABLE stores (
    id             INT NOT NULL AUTO_INCREMENT,
    name           VARCHAR(64) NOT NULL,
    area           VARCHAR(64) NOT NULL,
    address        VARCHAR(255) NOT NULL,
    lat            DOUBLE NOT NULL,
    lng            DOUBLE NOT NULL,
    distance       INT NOT NULL DEFAULT 0,
    status         VARCHAR(16) NOT NULL DEFAULT 'open',
    business_hours VARCHAR(32) NOT NULL DEFAULT '10:00-22:00',
    making_cups    INT NOT NULL DEFAULT 0,
    pack_fee       DECIMAL(10, 2) NOT NULL DEFAULT 1.00,
    delivery_fee   DECIMAL(10, 2) NOT NULL DEFAULT 4.00,
    sort_order     INT NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    CONSTRAINT ck_stores_lat CHECK (lat BETWEEN -90 AND 90),
    CONSTRAINT ck_stores_lng CHECK (lng BETWEEN -180 AND 180),
    CONSTRAINT ck_stores_distance CHECK (distance >= 0),
    CONSTRAINT ck_stores_status CHECK (status IN ('open', 'resting', 'closed')),
    CONSTRAINT ck_stores_making_cups CHECK (making_cups >= 0),
    CONSTRAINT ck_stores_pack_fee CHECK (pack_fee >= 0),
    CONSTRAINT ck_stores_delivery_fee CHECK (delivery_fee >= 0)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '门店';

-- ------------------------------------------------------------
-- 7. 优惠券模板
-- ------------------------------------------------------------
CREATE TABLE coupon_templates (
    id          INT NOT NULL AUTO_INCREMENT,
    title       VARCHAR(64) NOT NULL,
    description VARCHAR(128) NOT NULL DEFAULT '',
    cut         DECIMAL(10, 2) NOT NULL,
    min_amount  DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    valid_days  INT NOT NULL DEFAULT 30,
    sort_order  INT NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    CONSTRAINT ck_coupon_templates_cut CHECK (cut > 0),
    CONSTRAINT ck_coupon_templates_min_amount CHECK (min_amount >= 0),
    CONSTRAINT ck_coupon_templates_valid_days CHECK (valid_days > 0)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '优惠券模板';

-- ------------------------------------------------------------
-- 8. 用户优惠券
-- ------------------------------------------------------------
CREATE TABLE user_coupons (
    id          INT NOT NULL AUTO_INCREMENT,
    user_id     INT NOT NULL,
    template_id INT NOT NULL,
    title       VARCHAR(64) NOT NULL,
    description VARCHAR(128) NOT NULL DEFAULT '',
    cut         DECIMAL(10, 2) NOT NULL,
    min_amount  DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    status      VARCHAR(16) NOT NULL DEFAULT 'unused',
    expire_at   BIGINT NOT NULL,
    locked_by   VARCHAR(32) NULL,
    created_at  BIGINT NOT NULL,
    PRIMARY KEY (id),
    KEY idx_coupons_user_status (user_id, status, expire_at),
    KEY idx_coupons_locked_by (locked_by),
    CONSTRAINT fk_coupons_user FOREIGN KEY (user_id)
        REFERENCES users (id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_coupons_template FOREIGN KEY (template_id)
        REFERENCES coupon_templates (id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT ck_user_coupons_cut CHECK (cut > 0),
    CONSTRAINT ck_user_coupons_min_amount CHECK (min_amount >= 0),
    CONSTRAINT ck_user_coupons_status CHECK (status IN ('unused', 'used', 'expired'))
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci
  AUTO_INCREMENT = 501 COMMENT = '用户优惠券';

-- ------------------------------------------------------------
-- 9. 收货地址
-- ------------------------------------------------------------
CREATE TABLE addresses (
    id         INT NOT NULL AUTO_INCREMENT,
    user_id    INT NOT NULL,
    name       VARCHAR(20) NOT NULL,
    phone      VARCHAR(20) NOT NULL,
    detail     VARCHAR(120) NOT NULL,
    is_default TINYINT(1) NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    KEY idx_addresses_user (user_id),
    CONSTRAINT fk_addresses_user FOREIGN KEY (user_id)
        REFERENCES users (id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT ck_addresses_is_default CHECK (is_default IN (0, 1))
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '收货地址';

-- ------------------------------------------------------------
-- 10. 收藏
-- ------------------------------------------------------------
CREATE TABLE favorites (
    user_id    INT NOT NULL,
    product_id INT NOT NULL,
    created_at BIGINT NOT NULL,
    PRIMARY KEY (user_id, product_id),
    KEY idx_favorites_product (product_id),
    CONSTRAINT fk_favorites_user FOREIGN KEY (user_id)
        REFERENCES users (id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_favorites_product FOREIGN KEY (product_id)
        REFERENCES products (id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '收藏';

-- ------------------------------------------------------------
-- 11. 订单主表
-- ------------------------------------------------------------
CREATE TABLE orders (
    out_trade_no       VARCHAR(32) NOT NULL,
    user_id            INT NOT NULL,
    state              VARCHAR(16) NOT NULL DEFAULT 'pending_pay',
    stock_reserved     TINYINT(1) NOT NULL DEFAULT 0,
    store_id           INT NOT NULL,
    store_name         VARCHAR(64) NOT NULL,
    mode               VARCHAR(16) NOT NULL,
    subtotal           DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    pack_fee           DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    coupon_id          INT NULL,
    coupon_cut         DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    total              DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    pick_code          VARCHAR(16) NULL,
    table_no           VARCHAR(8) NULL,
    address_id         INT NULL,
    address_name       VARCHAR(20) NULL,
    address_phone      VARCHAR(20) NULL,
    address_detail     VARCHAR(120) NULL,
    address_is_default TINYINT(1) NULL,
    remark             VARCHAR(100) NOT NULL DEFAULT '',
    create_time        BIGINT NOT NULL,
    pay_time           BIGINT NULL,
    finish_time        BIGINT NULL,
    review_rating      TINYINT NULL,
    review_content     VARCHAR(200) NULL,
    review_created_at  BIGINT NULL,
    earning_points     INT NOT NULL DEFAULT 0,
    transaction_id     VARCHAR(64) NULL,
    PRIMARY KEY (out_trade_no),
    KEY idx_orders_user_state (user_id, state, create_time),
    KEY idx_orders_create_time (create_time),
    KEY idx_orders_store (store_id),
    KEY idx_orders_coupon (coupon_id),
    KEY idx_orders_address (address_id),
    CONSTRAINT fk_orders_user FOREIGN KEY (user_id)
        REFERENCES users (id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_orders_store FOREIGN KEY (store_id)
        REFERENCES stores (id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_orders_coupon FOREIGN KEY (coupon_id)
        REFERENCES user_coupons (id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_orders_address FOREIGN KEY (address_id)
        REFERENCES addresses (id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT ck_orders_state CHECK (state IN ('pending_pay', 'making', 'completed', 'cancelled')),
    CONSTRAINT ck_orders_mode CHECK (mode IN ('pickup', 'delivery')),
    CONSTRAINT ck_orders_subtotal CHECK (subtotal >= 0),
    CONSTRAINT ck_orders_pack_fee CHECK (pack_fee >= 0),
    CONSTRAINT ck_orders_coupon_cut CHECK (coupon_cut >= 0),
    CONSTRAINT ck_orders_total CHECK (total >= 0),
    CONSTRAINT ck_orders_earning_points CHECK (earning_points >= 0),
    CONSTRAINT ck_orders_address_is_default CHECK (address_is_default IN (0, 1) OR address_is_default IS NULL),
    CONSTRAINT ck_orders_review_rating CHECK (review_rating BETWEEN 1 AND 5)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '订单';

-- ------------------------------------------------------------
-- 12. 订单明细快照
-- ------------------------------------------------------------
CREATE TABLE order_items (
    id         INT NOT NULL AUTO_INCREMENT,
    order_no   VARCHAR(32) NOT NULL,
    product_id INT NOT NULL,
    name       VARCHAR(64) NOT NULL,
    image_path VARCHAR(255) NOT NULL,
    line_id    VARCHAR(32) NOT NULL,
    ice        VARCHAR(16) NOT NULL,
    sugar      VARCHAR(16) NOT NULL,
    count      INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    amount     DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    sort_order INT NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    KEY idx_order_items_order (order_no),
    CONSTRAINT fk_order_items_order FOREIGN KEY (order_no)
        REFERENCES orders (out_trade_no)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT ck_order_items_count CHECK (count BETWEEN 1 AND 99),
    CONSTRAINT ck_order_items_unit_price CHECK (unit_price >= 0),
    CONSTRAINT ck_order_items_amount CHECK (amount >= 0)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '订单明细';

-- ------------------------------------------------------------
-- 13. 订单明细小料快照
-- ------------------------------------------------------------
CREATE TABLE order_item_toppings (
    id            INT NOT NULL AUTO_INCREMENT,
    order_item_id INT NOT NULL,
    topping_id    INT NOT NULL,
    name          VARCHAR(32) NOT NULL,
    price         DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    sort_order    INT NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE KEY uq_item_topping (order_item_id, topping_id),
    CONSTRAINT fk_item_toppings_item FOREIGN KEY (order_item_id)
        REFERENCES order_items (id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT ck_item_toppings_price CHECK (price >= 0)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '订单明细小料';

-- ------------------------------------------------------------
-- 14. 积分流水
-- ------------------------------------------------------------
CREATE TABLE points_logs (
    id         INT NOT NULL AUTO_INCREMENT,
    user_id    INT NOT NULL,
    title      VARCHAR(64) NOT NULL,
    points     INT NOT NULL,
    type       VARCHAR(16) NOT NULL,
    created_at BIGINT NOT NULL,
    PRIMARY KEY (id),
    KEY idx_points_logs_user_time (user_id, created_at DESC),
    CONSTRAINT fk_points_logs_user FOREIGN KEY (user_id)
        REFERENCES users (id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT ck_points_logs_type CHECK (type IN ('order', 'refund', 'exchange', 'history'))
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '积分流水';

-- ------------------------------------------------------------
-- 15. 积分兑换商品
-- ------------------------------------------------------------
CREATE TABLE exchange_items (
    id          INT NOT NULL AUTO_INCREMENT,
    title       VARCHAR(64) NOT NULL,
    cost        INT NOT NULL,
    item_type   VARCHAR(16) NOT NULL DEFAULT 'coupon',
    template_id INT NULL,
    sort_order  INT NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    CONSTRAINT fk_exchange_template FOREIGN KEY (template_id)
        REFERENCES coupon_templates (id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT ck_exchange_cost CHECK (cost > 0),
    CONSTRAINT ck_exchange_item_type CHECK (item_type IN ('coupon')),
    CONSTRAINT ck_exchange_template CHECK (item_type <> 'coupon' OR template_id IS NOT NULL)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '积分兑换商品';

-- ------------------------------------------------------------
-- 16. 下单幂等
-- ------------------------------------------------------------
CREATE TABLE idempotency_keys (
    user_id    INT NOT NULL,
    idem_key   VARCHAR(128) NOT NULL,
    order_no   VARCHAR(32) NOT NULL,
    expires_at BIGINT NOT NULL,
    PRIMARY KEY (user_id, idem_key),
    KEY idx_idem_expires (expires_at),
    CONSTRAINT fk_idem_user FOREIGN KEY (user_id)
        REFERENCES users (id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_idem_order FOREIGN KEY (order_no)
        REFERENCES orders (out_trade_no)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '下单幂等';

-- ============================================================
-- 种子数据
-- ============================================================

INSERT IGNORE INTO member_levels (code, name, min_points, sort_order) VALUES
    ('V1', '见习猫评员', 0,    1),
    ('V2', '银牌猫评员', 200,  2),
    ('V3', '金牌猫评员', 800,  3),
    ('V4', '黑金猫评员', 2000, 4);

INSERT IGNORE INTO users
    (id, openid, nickname, avatar_path, level_code, points, growth, balance, created_at)
VALUES
    (1001, 'mock-openid-demo', '猫友1234', '/static/images/avatar.jpg', 'V2', 320, 320, 8.50, 1788220800000);

INSERT IGNORE INTO product_lines (id, name, tag, en, description, color, bg, sort_order) VALUES
    ('buchi',    '布奇·醇厚系列', '醇厚', 'Buchi''s Rich Collection',  '厚乳打底，浓郁治愈',   '#8B5E3C', '#F3EAE0', 1),
    ('sakamoto', '坂本·纯选系列', '纯选', 'Sakamoto''s Pure Selection', '原叶直萃，低糖轻负担', '#5A5A5A', '#EFEFEF', 2),
    ('tom',      '汤姆·甜心角落', '甜心', 'Tom''s Sweet Corner',        '布丁芋泥，甜蜜暴击',   '#D9737F', '#FAEBED', 3),
    ('tama',     '玉·清爽系列',   '清爽', 'Tama''s Refresh Line',       '冷萃鲜果，一口回魂',   '#5C9E6E', '#EAF3EC', 4);

INSERT IGNORE INTO products
    (id, line_id, name, price, orig_price, paws, is_hot, is_new, description, image_path, stock, on_sale, sort_order)
VALUES
    (1,  'buchi',    '黑糖波波厚奶茶',   14.00, 17.00, 5, 1, 0, '手熬黑糖挂壁，波波Q弹，厚乳香浓', '/static/images/drink_1.jpg',  50, 1, 1),
    (2,  'buchi',    '经典原味厚乳奶茶', 12.00, 15.00, 4, 1, 0, '锡兰红茶配厚牛乳，经典不翻车',   '/static/images/drink_2.jpg',  45, 1, 2),
    (3,  'buchi',    '提拉米苏厚乳茶',   16.00, NULL,  4, 0, 1, '可可粉轻撒，奶油顶配厚乳茶底',   '/static/images/drink_3.jpg',  30, 1, 3),
    (4,  'sakamoto', '茉莉初雪轻乳茶',   12.00, NULL,  4, 0, 0, '茉莉雪芽打底，轻薄乳盖',         '/static/images/drink_4.jpg',  40, 1, 4),
    (5,  'sakamoto', '四季春原叶纯茶',    9.00, NULL,  4, 0, 0, '原叶冷萃，零奶零糖也回甘',       '/static/images/drink_5.jpg',  60, 1, 5),
    (6,  'sakamoto', '轻乳乌龙茶',       11.00, NULL,  3, 0, 1, '三分甜轻负担，乌龙回香',         '/static/images/drink_6.jpg',  35, 1, 6),
    (7,  'tom',      '布丁可可萌宠杯',   15.00, 18.00, 4, 1, 0, '整颗焦糖布丁沉底，可可香浓',     '/static/images/drink_7.jpg',  25, 1, 7),
    (8,  'tom',      '芋泥啵啵鲜奶茶',   15.00, NULL,  5, 0, 0, '手捣芋泥厚挂壁，芋圆软糯',       '/static/images/drink_8.jpg',  25, 1, 8),
    (9,  'tom',      '草莓芝士奶盖',     16.00, NULL,  4, 0, 1, '鲜草莓果肉，咸香芝士奶盖',       '/static/images/drink_9.jpg',  20, 1, 9),
    (10, 'tama',     '满杯百香果茶',     12.00, NULL,  5, 0, 0, '整颗百香果，冰爽维C满格',        '/static/images/drink_10.jpg', 40, 1, 10),
    (11, 'tama',     '手打香水柠檬茶',   11.00, NULL,  5, 0, 0, '现捶香水柠檬，酸爽解腻',         '/static/images/drink_11.jpg', 40, 1, 11),
    (12, 'tama',     '冷萃乌龙青提茶',   14.00, NULL,  4, 0, 1, '冷萃乌龙配青提，低糖果香',       '/static/images/drink_12.jpg', 30, 1, 12);

INSERT IGNORE INTO toppings (id, name, price, sort_order) VALUES
    (1, '珍珠',     1.00, 1),
    (2, '椰果',     1.00, 2),
    (3, '布丁',     2.00, 3),
    (4, '芋圆',     2.00, 4),
    (5, '芝士奶盖', 3.00, 5);

INSERT IGNORE INTO stores
    (id, name, area, address, lat, lng, distance, status, business_hours, making_cups, pack_fee, delivery_fee, sort_order)
VALUES
    (1, '四猫茶学园·星悦广场店', '星悦广场 1F',     '浦东新区世纪大道 100 号', 31.2320, 121.4750, 205,  'resting', '10:00-22:00', 4, 1.00, 4.00, 1),
    (2, '四猫茶学园·万象城店',   '万象城 L2',       '闵行区吴中路 1599 号',   31.2250, 121.4650, 1200, 'open',    '10:00-22:00', 6, 1.00, 5.00, 2),
    (3, '四猫茶学园·大学城店',   '大学城美食街 B1', '松江区文汇路 800 号',     31.2000, 121.4300, 2400, 'open',    '09:30-21:30', 2, 1.00, 3.00, 3);

INSERT IGNORE INTO coupon_templates (id, title, description, cut, min_amount, valid_days, sort_order) VALUES
    (1, '新猫见面礼', '满15减3', 3.00, 15.00, 30, 1),
    (2, '周二会员日', '满25减5', 5.00, 25.00, 30, 2);

INSERT IGNORE INTO user_coupons
    (id, user_id, template_id, title, description, cut, min_amount, status, expire_at, locked_by, created_at)
VALUES
    (501, 1001, 1, '新猫见面礼', '满15减3', 3.00, 15.00, 'unused', 1893456000000, NULL, 1788220800000),
    (502, 1001, 2, '周二会员日', '满25减5', 5.00, 25.00, 'unused', 1893456000000, NULL, 1788220800000);

INSERT IGNORE INTO addresses (id, user_id, name, phone, detail, is_default) VALUES
    (1, 1001, '张女士', '13800008888', '星悦广场 3 栋 502', 1);

INSERT IGNORE INTO favorites (user_id, product_id, created_at) VALUES
    (1001, 1, 1788220800000),
    (1001, 8, 1788220800000);

INSERT IGNORE INTO points_logs (id, user_id, title, points, type, created_at) VALUES
    (1, 1001, '历史积分', 320, 'history', 1788220800000);

INSERT IGNORE INTO exchange_items (id, title, cost, item_type, template_id, sort_order) VALUES
    (1, '¥3 优惠券', 100, 'coupon', 1, 1),
    (2, '¥5 优惠券', 200, 'coupon', 2, 2);
