-- ============================================================
-- 四猫茶学园 · SQLite 建表脚本
-- 对应文档：docs/data-dictionary.md
-- 生成数据库：python database/build_sqlite.py
-- 说明：金额单位元，时间统一为 Unix 毫秒时间戳，图片存相对路径
-- ============================================================

PRAGMA foreign_keys = OFF;

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

PRAGMA foreign_keys = ON;
BEGIN TRANSACTION;

-- ------------------------------------------------------------
-- 1. 会员等级
-- ------------------------------------------------------------
CREATE TABLE member_levels (
    code       TEXT    PRIMARY KEY,
    name       TEXT    NOT NULL,
    min_points INTEGER NOT NULL DEFAULT 0 CHECK (min_points >= 0),
    sort_order INTEGER NOT NULL DEFAULT 0
);

-- ------------------------------------------------------------
-- 2. 用户
-- ------------------------------------------------------------
CREATE TABLE users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    openid      TEXT    NOT NULL UNIQUE,
    nickname    TEXT    NOT NULL DEFAULT '猫友1234',
    avatar_path TEXT    NOT NULL DEFAULT '/static/images/avatar.jpg',
    level_code  TEXT    NOT NULL DEFAULT 'V1',
    points      INTEGER NOT NULL DEFAULT 0 CHECK (points >= 0),
    growth      INTEGER NOT NULL DEFAULT 0 CHECK (growth >= 0),
    balance     NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (balance >= 0),
    created_at  INTEGER NOT NULL,
    CONSTRAINT fk_users_level FOREIGN KEY (level_code) REFERENCES member_levels (code)
        ON UPDATE CASCADE ON DELETE RESTRICT
);
CREATE INDEX idx_users_level ON users (level_code);

-- ------------------------------------------------------------
-- 3. 产品线
-- ------------------------------------------------------------
CREATE TABLE product_lines (
    id          TEXT    PRIMARY KEY,
    name        TEXT    NOT NULL,
    tag         TEXT    NOT NULL,
    en          TEXT    NOT NULL,
    description TEXT    NOT NULL DEFAULT '',
    color       TEXT    NOT NULL DEFAULT '#8B5E3C',
    bg          TEXT    NOT NULL DEFAULT '#F3EAE0',
    sort_order  INTEGER NOT NULL DEFAULT 0
);

-- ------------------------------------------------------------
-- 4. 饮品
-- ------------------------------------------------------------
CREATE TABLE products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    line_id     TEXT    NOT NULL,
    name        TEXT    NOT NULL,
    price       NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    orig_price  NUMERIC(10, 2) CHECK (orig_price IS NULL OR orig_price >= 0),
    paws        INTEGER NOT NULL DEFAULT 3 CHECK (paws BETWEEN 1 AND 5),
    is_hot      INTEGER NOT NULL DEFAULT 0 CHECK (is_hot IN (0, 1)),
    is_new      INTEGER NOT NULL DEFAULT 0 CHECK (is_new IN (0, 1)),
    description TEXT    NOT NULL DEFAULT '',
    image_path  TEXT    NOT NULL,
    stock       INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    on_sale     INTEGER NOT NULL DEFAULT 1 CHECK (on_sale IN (0, 1)),
    sort_order  INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT fk_products_line FOREIGN KEY (line_id) REFERENCES product_lines (id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);
CREATE INDEX idx_products_line ON products (line_id);
CREATE INDEX idx_products_on_sale ON products (on_sale, sort_order);

-- ------------------------------------------------------------
-- 5. 小料
-- ------------------------------------------------------------
CREATE TABLE toppings (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    price      NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (price >= 0),
    sort_order INTEGER NOT NULL DEFAULT 0
);

-- ------------------------------------------------------------
-- 6. 门店
-- ------------------------------------------------------------
CREATE TABLE stores (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL,
    area           TEXT    NOT NULL,
    address        TEXT    NOT NULL,
    lat            REAL    NOT NULL CHECK (lat BETWEEN -90 AND 90),
    lng            REAL    NOT NULL CHECK (lng BETWEEN -180 AND 180),
    distance       INTEGER NOT NULL DEFAULT 0 CHECK (distance >= 0),
    status         TEXT    NOT NULL DEFAULT 'open'
                   CHECK (status IN ('open', 'resting', 'closed')),
    business_hours TEXT    NOT NULL DEFAULT '10:00-22:00',
    making_cups    INTEGER NOT NULL DEFAULT 0 CHECK (making_cups >= 0),
    pack_fee       NUMERIC(10, 2) NOT NULL DEFAULT 1.00 CHECK (pack_fee >= 0),
    delivery_fee   NUMERIC(10, 2) NOT NULL DEFAULT 4.00 CHECK (delivery_fee >= 0),
    sort_order     INTEGER NOT NULL DEFAULT 0
);

-- ------------------------------------------------------------
-- 7. 优惠券模板
-- ------------------------------------------------------------
CREATE TABLE coupon_templates (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    description TEXT    NOT NULL DEFAULT '',
    cut         NUMERIC(10, 2) NOT NULL CHECK (cut > 0),
    min_amount  NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (min_amount >= 0),
    valid_days  INTEGER NOT NULL DEFAULT 30 CHECK (valid_days > 0),
    sort_order  INTEGER NOT NULL DEFAULT 0
);

-- ------------------------------------------------------------
-- 8. 用户优惠券
-- ------------------------------------------------------------
CREATE TABLE user_coupons (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    template_id INTEGER NOT NULL,
    title       TEXT    NOT NULL,
    description TEXT    NOT NULL DEFAULT '',
    cut         NUMERIC(10, 2) NOT NULL CHECK (cut > 0),
    min_amount  NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (min_amount >= 0),
    status      TEXT    NOT NULL DEFAULT 'unused'
                CHECK (status IN ('unused', 'used', 'expired')),
    expire_at   INTEGER NOT NULL,
    locked_by   TEXT,
    created_at  INTEGER NOT NULL,
    CONSTRAINT fk_coupons_user FOREIGN KEY (user_id) REFERENCES users (id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_coupons_template FOREIGN KEY (template_id) REFERENCES coupon_templates (id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);
CREATE INDEX idx_coupons_user_status ON user_coupons (user_id, status, expire_at);
CREATE INDEX idx_coupons_locked_by ON user_coupons (locked_by);

-- ------------------------------------------------------------
-- 9. 收货地址
-- ------------------------------------------------------------
CREATE TABLE addresses (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    name       TEXT    NOT NULL,
    phone      TEXT    NOT NULL,
    detail     TEXT    NOT NULL,
    is_default INTEGER NOT NULL DEFAULT 0 CHECK (is_default IN (0, 1)),
    CONSTRAINT fk_addresses_user FOREIGN KEY (user_id) REFERENCES users (id)
        ON UPDATE CASCADE ON DELETE CASCADE
);
CREATE INDEX idx_addresses_user ON addresses (user_id);

-- ------------------------------------------------------------
-- 10. 收藏
-- ------------------------------------------------------------
CREATE TABLE favorites (
    user_id    INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    PRIMARY KEY (user_id, product_id),
    CONSTRAINT fk_favorites_user FOREIGN KEY (user_id) REFERENCES users (id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_favorites_product FOREIGN KEY (product_id) REFERENCES products (id)
        ON UPDATE CASCADE ON DELETE CASCADE
);
CREATE INDEX idx_favorites_product ON favorites (product_id);

-- ------------------------------------------------------------
-- 11. 订单主表
-- ------------------------------------------------------------
CREATE TABLE orders (
    out_trade_no      TEXT    PRIMARY KEY,
    user_id           INTEGER NOT NULL,
    state             TEXT    NOT NULL DEFAULT 'pending_pay'
                      CHECK (state IN ('pending_pay', 'making', 'completed', 'cancelled')),
    stock_reserved    INTEGER NOT NULL DEFAULT 0 CHECK (stock_reserved IN (0, 1)),
    store_id          INTEGER NOT NULL,
    store_name        TEXT    NOT NULL,
    mode              TEXT    NOT NULL CHECK (mode IN ('pickup', 'delivery')),
    subtotal          NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (subtotal >= 0),
    pack_fee          NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (pack_fee >= 0),
    coupon_id         INTEGER,
    coupon_cut        NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (coupon_cut >= 0),
    total             NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (total >= 0),
    pick_code         TEXT,
    table_no          TEXT,
    address_id        INTEGER,
    address_name      TEXT,
    address_phone     TEXT,
    address_detail    TEXT,
    address_is_default INTEGER CHECK (address_is_default IN (0, 1) OR address_is_default IS NULL),
    remark            TEXT    NOT NULL DEFAULT '',
    create_time       INTEGER NOT NULL,
    pay_time          INTEGER,
    finish_time       INTEGER,
    review_rating     INTEGER CHECK (review_rating BETWEEN 1 AND 5),
    review_content    TEXT,
    review_created_at INTEGER,
    earning_points    INTEGER NOT NULL DEFAULT 0 CHECK (earning_points >= 0),
    transaction_id    TEXT,
    CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users (id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_orders_store FOREIGN KEY (store_id) REFERENCES stores (id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_orders_coupon FOREIGN KEY (coupon_id) REFERENCES user_coupons (id)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_orders_address FOREIGN KEY (address_id) REFERENCES addresses (id)
        ON UPDATE CASCADE ON DELETE SET NULL
);
CREATE INDEX idx_orders_user_state ON orders (user_id, state, create_time);
CREATE INDEX idx_orders_create_time ON orders (create_time);
CREATE INDEX idx_orders_store ON orders (store_id);
CREATE INDEX idx_orders_coupon ON orders (coupon_id);
CREATE INDEX idx_orders_address ON orders (address_id);

-- ------------------------------------------------------------
-- 12. 订单明细快照
-- ------------------------------------------------------------
CREATE TABLE order_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no    TEXT    NOT NULL,
    product_id  INTEGER NOT NULL,
    name        TEXT    NOT NULL,
    image_path  TEXT    NOT NULL,
    line_id     TEXT    NOT NULL,
    ice         TEXT    NOT NULL,
    sugar       TEXT    NOT NULL,
    count       INTEGER NOT NULL CHECK (count BETWEEN 1 AND 99),
    unit_price  NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (unit_price >= 0),
    amount      NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (amount >= 0),
    sort_order  INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT fk_order_items_order FOREIGN KEY (order_no) REFERENCES orders (out_trade_no)
        ON UPDATE CASCADE ON DELETE CASCADE
);
CREATE INDEX idx_order_items_order ON order_items (order_no);

-- ------------------------------------------------------------
-- 13. 订单明细小料快照
-- ------------------------------------------------------------
CREATE TABLE order_item_toppings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    order_item_id INTEGER NOT NULL,
    topping_id    INTEGER NOT NULL,
    name          TEXT    NOT NULL,
    price         NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (price >= 0),
    sort_order    INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT fk_item_toppings_item FOREIGN KEY (order_item_id) REFERENCES order_items (id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT uq_item_topping UNIQUE (order_item_id, topping_id)
);

-- ------------------------------------------------------------
-- 14. 积分流水
-- ------------------------------------------------------------
CREATE TABLE points_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    title      TEXT    NOT NULL,
    points     INTEGER NOT NULL,
    type       TEXT    NOT NULL CHECK (type IN ('order', 'refund', 'exchange', 'history')),
    created_at INTEGER NOT NULL,
    CONSTRAINT fk_points_logs_user FOREIGN KEY (user_id) REFERENCES users (id)
        ON UPDATE CASCADE ON DELETE CASCADE
);
CREATE INDEX idx_points_logs_user_time ON points_logs (user_id, created_at DESC);

-- ------------------------------------------------------------
-- 15. 积分兑换商品
-- ------------------------------------------------------------
CREATE TABLE exchange_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    cost        INTEGER NOT NULL CHECK (cost > 0),
    item_type   TEXT    NOT NULL DEFAULT 'coupon' CHECK (item_type IN ('coupon')),
    template_id INTEGER,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT fk_exchange_template FOREIGN KEY (template_id) REFERENCES coupon_templates (id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT ck_exchange_template CHECK (item_type <> 'coupon' OR template_id IS NOT NULL)
);

-- ------------------------------------------------------------
-- 16. 下单幂等
-- ------------------------------------------------------------
CREATE TABLE idempotency_keys (
    user_id    INTEGER NOT NULL,
    idem_key   TEXT    NOT NULL,
    order_no   TEXT    NOT NULL,
    expires_at INTEGER NOT NULL,
    PRIMARY KEY (user_id, idem_key),
    CONSTRAINT fk_idem_user FOREIGN KEY (user_id) REFERENCES users (id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_idem_order FOREIGN KEY (order_no) REFERENCES orders (out_trade_no)
        ON UPDATE CASCADE ON DELETE CASCADE
);
CREATE INDEX idx_idem_expires ON idempotency_keys (expires_at);

-- ============================================================
-- 种子数据
-- ============================================================

-- 会员等级
INSERT OR IGNORE INTO member_levels (code, name, min_points, sort_order) VALUES
    ('V1', '见习猫评员', 0,    1),
    ('V2', '银牌猫评员', 200,  2),
    ('V3', '金牌猫评员', 800,  3),
    ('V4', '黑金猫评员', 2000, 4);

-- 用户（演示账号）
INSERT OR IGNORE INTO users
    (id, openid, nickname, avatar_path, level_code, points, growth, balance, created_at)
VALUES
    (1001, 'mock-openid-demo', '猫友1234', '/static/images/avatar.jpg', 'V2', 320, 320, 8.50, 1788220800000);

-- 产品线
INSERT OR IGNORE INTO product_lines (id, name, tag, en, description, color, bg, sort_order) VALUES
    ('buchi',    '布奇·醇厚系列',  '醇厚', 'Buchi''s Rich Collection',  '厚乳打底，浓郁治愈',   '#8B5E3C', '#F3EAE0', 1),
    ('sakamoto', '坂本·纯选系列',  '纯选', 'Sakamoto''s Pure Selection', '原叶直萃，低糖轻负担', '#5A5A5A', '#EFEFEF', 2),
    ('tom',      '汤姆·甜心角落',  '甜心', 'Tom''s Sweet Corner',        '布丁芋泥，甜蜜暴击',   '#D9737F', '#FAEBED', 3),
    ('tama',     '玉·清爽系列',    '清爽', 'Tama''s Refresh Line',       '冷萃鲜果，一口回魂',   '#5C9E6E', '#EAF3EC', 4);

-- 饮品
INSERT OR IGNORE INTO products
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

-- 小料
INSERT OR IGNORE INTO toppings (id, name, price, sort_order) VALUES
    (1, '珍珠',     1.00, 1),
    (2, '椰果',     1.00, 2),
    (3, '布丁',     2.00, 3),
    (4, '芋圆',     2.00, 4),
    (5, '芝士奶盖', 3.00, 5);

-- 门店
INSERT OR IGNORE INTO stores
    (id, name, area, address, lat, lng, distance, status, business_hours, making_cups, pack_fee, delivery_fee, sort_order)
VALUES
    (1, '四猫茶学园·星悦广场店', '星悦广场 1F',     '浦东新区世纪大道 100 号', 31.2320, 121.4750, 205,  'resting', '10:00-22:00', 4, 1.00, 4.00, 1),
    (2, '四猫茶学园·万象城店',   '万象城 L2',       '闵行区吴中路 1599 号',   31.2250, 121.4650, 1200, 'open',    '10:00-22:00', 6, 1.00, 5.00, 2),
    (3, '四猫茶学园·大学城店',   '大学城美食街 B1', '松江区文汇路 800 号',     31.2000, 121.4300, 2400, 'open',    '09:30-21:30', 2, 1.00, 3.00, 3);

-- 优惠券模板
INSERT OR IGNORE INTO coupon_templates (id, title, description, cut, min_amount, valid_days, sort_order) VALUES
    (1, '新猫见面礼', '满15减3', 3.00, 15.00, 30, 1),
    (2, '周二会员日', '满25减5', 5.00, 25.00, 30, 2);

-- 演示用户的优惠券
INSERT OR IGNORE INTO user_coupons
    (id, user_id, template_id, title, description, cut, min_amount, status, expire_at, locked_by, created_at)
VALUES
    (501, 1001, 1, '新猫见面礼', '满15减3', 3.00, 15.00, 'unused', 1893456000000, NULL, 1788220800000),
    (502, 1001, 2, '周二会员日', '满25减5', 5.00, 25.00, 'unused', 1893456000000, NULL, 1788220800000);

-- 收货地址
INSERT OR IGNORE INTO addresses (id, user_id, name, phone, detail, is_default) VALUES
    (1, 1001, '张女士', '13800008888', '星悦广场 3 栋 502', 1);

-- 收藏
INSERT OR IGNORE INTO favorites (user_id, product_id, created_at) VALUES
    (1001, 1, 1788220800000),
    (1001, 8, 1788220800000);

-- 积分流水
INSERT OR IGNORE INTO points_logs (id, user_id, title, points, type, created_at) VALUES
    (1, 1001, '历史积分', 320, 'history', 1788220800000);

-- 积分兑换商品
INSERT OR IGNORE INTO exchange_items (id, title, cost, item_type, template_id, sort_order) VALUES
    (1, '¥3 优惠券', 100, 'coupon', 1, 1),
    (2, '¥5 优惠券', 200, 'coupon', 2, 2);

COMMIT;
