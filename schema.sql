-- ============================================================
-- Wines & Spirits POS - SQLite Schema
-- ============================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 5000;
PRAGMA cache_size = -64000;
PRAGMA synchronous = NORMAL;
PRAGMA temp_store = MEMORY;
PRAGMA mmap_size = 268435456;

-- ============================================================
-- LOOKUP / REFERENCE TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS branches (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    code        TEXT    NOT NULL UNIQUE,
    location    TEXT,
    phone       TEXT,
    email       TEXT,
    tax_reg_no  TEXT,
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
    updated_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))
);

CREATE TABLE IF NOT EXISTS roles (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    description TEXT,
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))
);

CREATE TABLE IF NOT EXISTS permissions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id     INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    resource    TEXT    NOT NULL,
    can_create  INTEGER NOT NULL DEFAULT 0,
    can_read    INTEGER NOT NULL DEFAULT 0,
    can_update  INTEGER NOT NULL DEFAULT 0,
    can_delete  INTEGER NOT NULL DEFAULT 0,
    UNIQUE(role_id, resource)
);

CREATE TABLE IF NOT EXISTS users (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id    INTEGER REFERENCES branches(id) ON DELETE SET NULL,
    role_id      INTEGER NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    username     TEXT    NOT NULL UNIQUE,
    password_hash TEXT   NOT NULL,
    full_name    TEXT    NOT NULL,
    email        TEXT,
    phone        TEXT,
    is_active    INTEGER NOT NULL DEFAULT 1,
    last_login   TEXT,
    created_at   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
    updated_at   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))
);

CREATE TABLE IF NOT EXISTS categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    description TEXT,
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
    updated_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))
);

-- ============================================================
-- PRODUCT & INVENTORY TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS products (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    barcode       TEXT    UNIQUE,
    name          TEXT    NOT NULL,
    brand         TEXT,
    category_id   INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    cost_price    REAL    NOT NULL DEFAULT 0,
    selling_price REAL    NOT NULL DEFAULT 0,
    unit          TEXT    NOT NULL DEFAULT 'pcs',
    reorder_level REAL    NOT NULL DEFAULT 0,
    is_active     INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
    updated_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))
);

CREATE TABLE IF NOT EXISTS inventory (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id       INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    branch_id        INTEGER NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
    quantity_on_hand REAL    NOT NULL DEFAULT 0,
    last_count_date  TEXT,
    created_at       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
    updated_at       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
    UNIQUE(product_id, branch_id)
);

CREATE TABLE IF NOT EXISTS stock_movements (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id     INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    branch_id      INTEGER NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
    movement_type  TEXT    NOT NULL CHECK (movement_type IN ('IN', 'OUT', 'ADJUSTMENT', 'TRANSFER')),
    quantity       REAL    NOT NULL,
    reference_type TEXT,
    reference_id   INTEGER,
    notes          TEXT,
    created_by     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))
);

-- ============================================================
-- SALES & PAYMENT TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS sales (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_number  TEXT    NOT NULL UNIQUE,
    branch_id       INTEGER NOT NULL REFERENCES branches(id) ON DELETE RESTRICT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    subtotal        REAL    NOT NULL DEFAULT 0,
    discount        REAL    NOT NULL DEFAULT 0,
    tax             REAL    NOT NULL DEFAULT 0,
    grand_total     REAL    NOT NULL DEFAULT 0,
    payment_method  TEXT,
    status          TEXT    NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'COMPLETED', 'REFUNDED', 'CANCELLED')),
    voided          INTEGER NOT NULL DEFAULT 0,
    void_reason     TEXT,
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))
);

CREATE TABLE IF NOT EXISTS sale_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id     INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    product_id  INTEGER NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    quantity    REAL    NOT NULL,
    unit_price  REAL    NOT NULL,
    subtotal    REAL    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))
);

CREATE TABLE IF NOT EXISTS payments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id     INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    method      TEXT    NOT NULL CHECK (method IN ('CASH', 'MPESA', 'CARD', 'BANK_TRANSFER', 'CREDIT')),
    amount      REAL    NOT NULL,
    reference   TEXT,
    mpesa_code  TEXT,
    status      TEXT    NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'COMPLETED', 'FAILED', 'REFUNDED')),
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))
);

-- ============================================================
-- MPESA & EXPENSE TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS mpesa_transactions (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    checkout_request_id   TEXT,
    merchant_request_id   TEXT,
    transaction_code      TEXT UNIQUE,
    amount                REAL    NOT NULL,
    phone_number          TEXT,
    status                TEXT    NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'SUCCESS', 'FAILED', 'CANCELLED')),
    result_desc           TEXT,
    created_at            TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
    updated_at            TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))
);

CREATE TABLE IF NOT EXISTS expenses (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id     INTEGER NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
    category      TEXT    NOT NULL,
    description   TEXT,
    amount        REAL    NOT NULL,
    expense_date  TEXT    NOT NULL,
    recorded_by   INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))
);

-- ============================================================
-- SYSTEM TABLES
-- ============================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    branch_id   INTEGER REFERENCES branches(id) ON DELETE SET NULL,
    action      TEXT    NOT NULL,
    resource    TEXT    NOT NULL,
    resource_id INTEGER,
    details     TEXT,
    ip_address  TEXT,
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))
);

CREATE TABLE IF NOT EXISTS sync_queue (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id     INTEGER REFERENCES branches(id) ON DELETE CASCADE,
    table_name    TEXT    NOT NULL,
    record_id     INTEGER NOT NULL,
    action        TEXT    NOT NULL CHECK (action IN ('CREATE', 'UPDATE', 'DELETE')),
    payload       TEXT,
    status        TEXT    NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'SYNCED', 'FAILED')),
    error_message TEXT,
    created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
    synced_at     TEXT
);

CREATE TABLE IF NOT EXISTS etims_invoices (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id              INTEGER NOT NULL UNIQUE REFERENCES sales(id) ON DELETE CASCADE,
    invoice_number       TEXT    UNIQUE,
    control_number       TEXT,
    qr_code              TEXT,
    submission_status    TEXT    NOT NULL DEFAULT 'PENDING' CHECK (submission_status IN ('PENDING', 'SUBMITTED', 'FAILED', 'CANCELLED')),
    submission_response  TEXT,
    created_at           TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
    submitted_at         TEXT
);

-- ============================================================
-- INDEXES
-- ============================================================

-- Branches
CREATE INDEX IF NOT EXISTS idx_branches_code       ON branches(code);
CREATE INDEX IF NOT EXISTS idx_branches_is_active  ON branches(is_active);

-- Permissions
CREATE INDEX IF NOT EXISTS idx_permissions_role_id ON permissions(role_id);
CREATE INDEX IF NOT EXISTS idx_permissions_resource ON permissions(resource);

-- Users
CREATE INDEX IF NOT EXISTS idx_users_branch_id  ON users(branch_id);
CREATE INDEX IF NOT EXISTS idx_users_role_id    ON users(role_id);
CREATE INDEX IF NOT EXISTS idx_users_username   ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_is_active  ON users(is_active);

-- Categories
CREATE INDEX IF NOT EXISTS idx_categories_name  ON categories(name);

-- Products
CREATE INDEX IF NOT EXISTS idx_products_barcode     ON products(barcode);
CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_name        ON products(name);
CREATE INDEX IF NOT EXISTS idx_products_is_active   ON products(is_active);

-- Inventory
CREATE INDEX IF NOT EXISTS idx_inventory_product_id ON inventory(product_id);
CREATE INDEX IF NOT EXISTS idx_inventory_branch_id  ON inventory(branch_id);

-- Stock Movements
CREATE INDEX IF NOT EXISTS idx_stock_movements_product_id ON stock_movements(product_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_branch_id  ON stock_movements(branch_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_type       ON stock_movements(movement_type);
CREATE INDEX IF NOT EXISTS idx_stock_movements_created    ON stock_movements(created_at);

-- Sales
CREATE INDEX IF NOT EXISTS idx_sales_receipt_number ON sales(receipt_number);
CREATE INDEX IF NOT EXISTS idx_sales_branch_id      ON sales(branch_id);
CREATE INDEX IF NOT EXISTS idx_sales_user_id        ON sales(user_id);
CREATE INDEX IF NOT EXISTS idx_sales_status         ON sales(status);
CREATE INDEX IF NOT EXISTS idx_sales_created_at     ON sales(created_at);

-- Sale Items
CREATE INDEX IF NOT EXISTS idx_sale_items_sale_id    ON sale_items(sale_id);
CREATE INDEX IF NOT EXISTS idx_sale_items_product_id ON sale_items(product_id);

-- Payments
CREATE INDEX IF NOT EXISTS idx_payments_sale_id ON payments(sale_id);
CREATE INDEX IF NOT EXISTS idx_payments_method  ON payments(method);
CREATE INDEX IF NOT EXISTS idx_payments_status  ON payments(status);

-- M-PESA
CREATE INDEX IF NOT EXISTS idx_mpesa_checkout_request_id ON mpesa_transactions(checkout_request_id);
CREATE INDEX IF NOT EXISTS idx_mpesa_transaction_code    ON mpesa_transactions(transaction_code);
CREATE INDEX IF NOT EXISTS idx_mpesa_status              ON mpesa_transactions(status);

-- Expenses
CREATE INDEX IF NOT EXISTS idx_expenses_branch_id  ON expenses(branch_id);
CREATE INDEX IF NOT EXISTS idx_expenses_category   ON expenses(category);
CREATE INDEX IF NOT EXISTS idx_expenses_date       ON expenses(expense_date);

-- Audit Logs
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id   ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_branch_id ON audit_logs(branch_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action    ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource  ON audit_logs(resource);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created   ON audit_logs(created_at);

-- Sync Queue
CREATE INDEX IF NOT EXISTS idx_sync_queue_branch_id  ON sync_queue(branch_id);
CREATE INDEX IF NOT EXISTS idx_sync_queue_status     ON sync_queue(status);
CREATE INDEX IF NOT EXISTS idx_sync_queue_table_name ON sync_queue(table_name);

-- eTIMS
CREATE INDEX IF NOT EXISTS idx_etims_sale_id          ON etims_invoices(sale_id);
CREATE INDEX IF NOT EXISTS idx_etims_invoice_number   ON etims_invoices(invoice_number);
CREATE INDEX IF NOT EXISTS idx_etims_submission_status ON etims_invoices(submission_status);

-- ============================================================
-- TRIGGERS: updated_at auto-update
-- ============================================================

CREATE TRIGGER IF NOT EXISTS trg_branches_updated_at
    AFTER UPDATE ON branches
    FOR EACH ROW
BEGIN
    UPDATE branches SET updated_at = strftime('%Y-%m-%d %H:%M:%f', 'now') WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_users_updated_at
    AFTER UPDATE ON users
    FOR EACH ROW
BEGIN
    UPDATE users SET updated_at = strftime('%Y-%m-%d %H:%M:%f', 'now') WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_categories_updated_at
    AFTER UPDATE ON categories
    FOR EACH ROW
BEGIN
    UPDATE categories SET updated_at = strftime('%Y-%m-%d %H:%M:%f', 'now') WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_products_updated_at
    AFTER UPDATE ON products
    FOR EACH ROW
BEGIN
    UPDATE products SET updated_at = strftime('%Y-%m-%d %H:%M:%f', 'now') WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_inventory_updated_at
    AFTER UPDATE ON inventory
    FOR EACH ROW
BEGIN
    UPDATE inventory SET updated_at = strftime('%Y-%m-%d %H:%M:%f', 'now') WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_mpesa_transactions_updated_at
    AFTER UPDATE ON mpesa_transactions
    FOR EACH ROW
BEGIN
    UPDATE mpesa_transactions SET updated_at = strftime('%Y-%m-%d %H:%M:%f', 'now') WHERE id = OLD.id;
END;

-- ============================================================
-- TRIGGERS: stock movement → inventory
-- ============================================================

CREATE TRIGGER IF NOT EXISTS trg_stock_movement_insert_in
    AFTER INSERT ON stock_movements
    WHEN NEW.movement_type = 'IN'
BEGIN
    INSERT INTO inventory (product_id, branch_id, quantity_on_hand, last_count_date)
        VALUES (NEW.product_id, NEW.branch_id, NEW.quantity, strftime('%Y-%m-%d %H:%M:%f', 'now'))
    ON CONFLICT(product_id, branch_id) DO UPDATE SET
        quantity_on_hand = quantity_on_hand + NEW.quantity,
        last_count_date  = strftime('%Y-%m-%d %H:%M:%f', 'now');
END;

CREATE TRIGGER IF NOT EXISTS trg_stock_movement_insert_out
    AFTER INSERT ON stock_movements
    WHEN NEW.movement_type = 'OUT'
BEGIN
    INSERT INTO inventory (product_id, branch_id, quantity_on_hand, last_count_date)
        VALUES (NEW.product_id, NEW.branch_id, -NEW.quantity, strftime('%Y-%m-%d %H:%M:%f', 'now'))
    ON CONFLICT(product_id, branch_id) DO UPDATE SET
        quantity_on_hand = quantity_on_hand - NEW.quantity,
        last_count_date  = strftime('%Y-%m-%d %H:%M:%f', 'now');
END;

CREATE TRIGGER IF NOT EXISTS trg_stock_movement_insert_adjustment
    AFTER INSERT ON stock_movements
    WHEN NEW.movement_type = 'ADJUSTMENT'
BEGIN
    INSERT INTO inventory (product_id, branch_id, quantity_on_hand, last_count_date)
        VALUES (NEW.product_id, NEW.branch_id, NEW.quantity, strftime('%Y-%m-%d %H:%M:%f', 'now'))
    ON CONFLICT(product_id, branch_id) DO UPDATE SET
        quantity_on_hand = NEW.quantity,
        last_count_date  = strftime('%Y-%m-%d %H:%M:%f', 'now');
END;

CREATE TRIGGER IF NOT EXISTS trg_stock_movement_insert_transfer_out
    AFTER INSERT ON stock_movements
    WHEN NEW.movement_type = 'TRANSFER' AND NEW.quantity < 0
BEGIN
    INSERT INTO inventory (product_id, branch_id, quantity_on_hand, last_count_date)
        VALUES (NEW.product_id, NEW.branch_id, NEW.quantity, strftime('%Y-%m-%d %H:%M:%f', 'now'))
    ON CONFLICT(product_id, branch_id) DO UPDATE SET
        quantity_on_hand = quantity_on_hand + NEW.quantity,
        last_count_date  = strftime('%Y-%m-%d %H:%M:%f', 'now');
END;

CREATE TRIGGER IF NOT EXISTS trg_stock_movement_insert_transfer_in
    AFTER INSERT ON stock_movements
    WHEN NEW.movement_type = 'TRANSFER' AND NEW.quantity > 0
BEGIN
    INSERT INTO inventory (product_id, branch_id, quantity_on_hand, last_count_date)
        VALUES (NEW.product_id, NEW.branch_id, NEW.quantity, strftime('%Y-%m-%d %H:%M:%f', 'now'))
    ON CONFLICT(product_id, branch_id) DO UPDATE SET
        quantity_on_hand = quantity_on_hand + NEW.quantity,
        last_count_date  = strftime('%Y-%m-%d %H:%M:%f', 'now');
END;

-- ============================================================
-- DEFAULT SEED DATA
-- ============================================================

INSERT OR IGNORE INTO roles (id, name, description) VALUES
    (1, 'Admin',   'Full system access'),
    (2, 'Manager', 'Branch-level management access'),
    (3, 'Cashier', 'Point of sale operations only');

-- Admin gets all permissions on all resources
INSERT OR IGNORE INTO permissions (role_id, resource, can_create, can_read, can_update, can_delete)
SELECT 1, r.resource, 1, 1, 1, 1
FROM (
    SELECT 'branches' AS resource UNION SELECT 'users' UNION SELECT 'roles' UNION
    SELECT 'permissions' UNION SELECT 'categories' UNION SELECT 'products' UNION
    SELECT 'inventory' UNION SELECT 'stock_movements' UNION SELECT 'sales' UNION
    SELECT 'sale_items' UNION SELECT 'payments' UNION SELECT 'mpesa_transactions' UNION
    SELECT 'expenses' UNION SELECT 'audit_logs' UNION SELECT 'sync_queue' UNION
    SELECT 'etims_invoices' UNION SELECT 'settings' UNION SELECT 'reports' UNION
    SELECT 'dashboard'
) r;

-- Manager: full CRUD on operational resources; read-only on admin resources
INSERT OR IGNORE INTO permissions (role_id, resource, can_create, can_read, can_update, can_delete)
SELECT 2, r.resource, r.can_create, r.can_read, r.can_update, r.can_delete
FROM (
    SELECT 'branches'        AS resource, 0 AS can_create, 1 AS can_read, 0 AS can_update, 0 AS can_delete UNION
    SELECT 'users',       1, 1, 1, 0 UNION
    SELECT 'roles',       0, 1, 0, 0 UNION
    SELECT 'permissions', 0, 1, 0, 0 UNION
    SELECT 'categories',  1, 1, 1, 1 UNION
    SELECT 'products',    1, 1, 1, 1 UNION
    SELECT 'inventory',   0, 1, 1, 0 UNION
    SELECT 'stock_movements', 1, 1, 0, 0 UNION
    SELECT 'sales',       1, 1, 1, 0 UNION
    SELECT 'sale_items',  1, 1, 1, 0 UNION
    SELECT 'payments',    1, 1, 1, 0 UNION
    SELECT 'mpesa_transactions', 0, 1, 0, 0 UNION
    SELECT 'expenses',    1, 1, 1, 1 UNION
    SELECT 'audit_logs',  0, 1, 0, 0 UNION
    SELECT 'sync_queue',  0, 1, 0, 0 UNION
    SELECT 'etims_invoices', 0, 1, 0, 0 UNION
    SELECT 'settings',    0, 1, 0, 0 UNION
    SELECT 'reports',     0, 1, 0, 0 UNION
    SELECT 'dashboard',   0, 1, 0, 0
) r;

-- Cashier: minimal permissions — POS and lookup only
INSERT OR IGNORE INTO permissions (role_id, resource, can_create, can_read, can_update, can_delete)
SELECT 3, r.resource, r.can_create, r.can_read, r.can_update, r.can_delete
FROM (
    SELECT 'categories'   AS resource, 0 AS can_create, 1 AS can_read, 0 AS can_update, 0 AS can_delete UNION
    SELECT 'products',    0, 1, 0, 0 UNION
    SELECT 'inventory',   0, 1, 0, 0 UNION
    SELECT 'stock_movements', 0, 1, 0, 0 UNION
    SELECT 'sales',       1, 1, 0, 0 UNION
    SELECT 'sale_items',  1, 1, 0, 0 UNION
    SELECT 'payments',    1, 1, 0, 0 UNION
    SELECT 'mpesa_transactions', 0, 1, 0, 0 UNION
    SELECT 'expenses',    1, 1, 0, 0 UNION
    SELECT 'dashboard',   0, 1, 0, 0
) r;

-- Default categories
INSERT OR IGNORE INTO categories (id, name, description) VALUES
    (1,  'Wines',      'Red, white, rosé, sparkling wines'),
    (2,  'Spirits',    'General spirits and liquors'),
    (3,  'Beer',       'Beer, ale, lager, stout'),
    (4,  'Soft Drinks','Non-alcoholic carbonated and still drinks'),
    (5,  'Whisky',     'Whisky and whiskey'),
    (6,  'Vodka',      'Vodka'),
    (7,  'Gin',        'Gin'),
    (8,  'Rum',        'Rum'),
    (9,  'Liqueur',    'Liqueurs and cordials'),
    (10, 'Cognac',     'Cognac and brandy'),
    (11, 'Water',      'Bottled and still water');
