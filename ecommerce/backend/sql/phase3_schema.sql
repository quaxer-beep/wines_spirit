-- ============================================================
-- Phase 3: Head Office Management & Business Intelligence
-- PostgreSQL Schema
-- ============================================================

-- Suppliers
CREATE TABLE IF NOT EXISTS suppliers (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    contact_person  VARCHAR(255),
    phone           VARCHAR(50),
    email           VARCHAR(255),
    physical_address TEXT,
    tax_info        VARCHAR(255),
    rating          FLOAT DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_suppliers_name ON suppliers(name);
CREATE INDEX idx_suppliers_phone ON suppliers(phone);
CREATE INDEX idx_suppliers_active ON suppliers(is_active);

-- Supplier Ratings
CREATE TABLE IF NOT EXISTS supplier_ratings (
    id                  SERIAL PRIMARY KEY,
    supplier_id         INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    delivery_accuracy   FLOAT,
    delivery_timeliness FLOAT,
    product_quality     FLOAT,
    order_fulfillment_rate FLOAT,
    overall_score       FLOAT,
    notes               TEXT,
    rated_by            INTEGER,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_supplier_ratings_supplier ON supplier_ratings(supplier_id);

-- Purchase Orders
CREATE TABLE IF NOT EXISTS purchase_orders (
    id                    SERIAL PRIMARY KEY,
    po_number             VARCHAR(50) NOT NULL UNIQUE,
    supplier_id           INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE RESTRICT,
    branch_id             INTEGER,
    ordered_by            INTEGER,
    approved_by           INTEGER,
    status                VARCHAR(30) NOT NULL DEFAULT 'draft',
    subtotal              FLOAT NOT NULL DEFAULT 0,
    tax                   FLOAT NOT NULL DEFAULT 0,
    grand_total           FLOAT NOT NULL DEFAULT 0,
    notes                 TEXT,
    expected_delivery_date DATE,
    actual_delivery_date   DATE,
    created_at            TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at            TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved_at           TIMESTAMP WITH TIME ZONE,
    received_at           TIMESTAMP WITH TIME ZONE
);
CREATE INDEX idx_po_number ON purchase_orders(po_number);
CREATE INDEX idx_po_supplier ON purchase_orders(supplier_id);
CREATE INDEX idx_po_status ON purchase_orders(status);
CREATE INDEX idx_po_branch ON purchase_orders(branch_id);
CREATE INDEX idx_po_created ON purchase_orders(created_at);

-- Purchase Order Items
CREATE TABLE IF NOT EXISTS purchase_order_items (
    id                  SERIAL PRIMARY KEY,
    purchase_order_id   INTEGER NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    product_id          INTEGER,
    product_name        VARCHAR(255) NOT NULL,
    quantity_ordered    FLOAT NOT NULL,
    quantity_received   FLOAT NOT NULL DEFAULT 0,
    unit_price          FLOAT NOT NULL,
    subtotal            FLOAT NOT NULL,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_poi_order ON purchase_order_items(purchase_order_id);
CREATE INDEX idx_poi_product ON purchase_order_items(product_id);

-- Goods Received Notes
CREATE TABLE IF NOT EXISTS goods_received_notes (
    id                  SERIAL PRIMARY KEY,
    grn_number          VARCHAR(50) NOT NULL UNIQUE,
    purchase_order_id   INTEGER NOT NULL REFERENCES purchase_orders(id) ON DELETE RESTRICT,
    supplier_id         INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE RESTRICT,
    branch_id           INTEGER,
    received_by         INTEGER,
    delivery_note_number VARCHAR(100),
    invoice_reference   VARCHAR(100),
    status              VARCHAR(20) NOT NULL DEFAULT 'pending',
    notes               TEXT,
    received_at         TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_grn_number ON goods_received_notes(grn_number);
CREATE INDEX idx_grn_po ON goods_received_notes(purchase_order_id);
CREATE INDEX idx_grn_supplier ON goods_received_notes(supplier_id);
CREATE INDEX idx_grn_branch ON goods_received_notes(branch_id);

-- Goods Received Items
CREATE TABLE IF NOT EXISTS goods_received_items (
    id                SERIAL PRIMARY KEY,
    grn_id            INTEGER NOT NULL REFERENCES goods_received_notes(id) ON DELETE CASCADE,
    product_id        INTEGER,
    product_name      VARCHAR(255) NOT NULL,
    quantity_received FLOAT NOT NULL,
    unit_cost         FLOAT NOT NULL,
    total_cost        FLOAT NOT NULL,
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Stock Transfers
CREATE TABLE IF NOT EXISTS stock_transfers (
    id                SERIAL PRIMARY KEY,
    transfer_number   VARCHAR(50) NOT NULL UNIQUE,
    from_branch_id    INTEGER NOT NULL,
    to_branch_id      INTEGER NOT NULL,
    requested_by      INTEGER,
    approved_by       INTEGER,
    dispatched_by     INTEGER,
    received_by       INTEGER,
    status            VARCHAR(30) NOT NULL DEFAULT 'requested',
    notes             TEXT,
    rejection_reason  TEXT,
    requested_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved_at       TIMESTAMP WITH TIME ZONE,
    dispatched_at     TIMESTAMP WITH TIME ZONE,
    received_at       TIMESTAMP WITH TIME ZONE,
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_st_transfer_number ON stock_transfers(transfer_number);
CREATE INDEX idx_st_from_branch ON stock_transfers(from_branch_id);
CREATE INDEX idx_st_to_branch ON stock_transfers(to_branch_id);
CREATE INDEX idx_st_status ON stock_transfers(status);
CREATE INDEX idx_st_requested ON stock_transfers(requested_at);

-- Stock Transfer Items
CREATE TABLE IF NOT EXISTS stock_transfer_items (
    id                  SERIAL PRIMARY KEY,
    stock_transfer_id   INTEGER NOT NULL REFERENCES stock_transfers(id) ON DELETE CASCADE,
    product_id          INTEGER NOT NULL,
    product_name        VARCHAR(255) NOT NULL,
    quantity            FLOAT NOT NULL,
    unit_cost           FLOAT,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_sti_transfer ON stock_transfer_items(stock_transfer_id);
CREATE INDEX idx_sti_product ON stock_transfer_items(product_id);

-- Analytics Snapshots (Data Warehouse)
CREATE TABLE IF NOT EXISTS analytics_snapshots (
    id              SERIAL PRIMARY KEY,
    snapshot_date   DATE NOT NULL,
    branch_id       INTEGER,
    total_sales     FLOAT NOT NULL DEFAULT 0,
    total_orders    INTEGER NOT NULL DEFAULT 0,
    total_cost      FLOAT NOT NULL DEFAULT 0,
    gross_profit    FLOAT NOT NULL DEFAULT 0,
    total_expenses  FLOAT NOT NULL DEFAULT 0,
    net_profit      FLOAT NOT NULL DEFAULT 0,
    inventory_value FLOAT NOT NULL DEFAULT 0,
    customer_count  INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(snapshot_date, branch_id)
);
CREATE INDEX idx_snapshots_date ON analytics_snapshots(snapshot_date);
CREATE INDEX idx_snapshots_branch ON analytics_snapshots(branch_id);

-- Forecasts
CREATE TABLE IF NOT EXISTS forecasts (
    id                SERIAL PRIMARY KEY,
    forecast_date     DATE NOT NULL,
    branch_id         INTEGER,
    product_id        INTEGER,
    forecast_type     VARCHAR(50) NOT NULL,
    predicted_value   FLOAT NOT NULL,
    confidence_lower  FLOAT,
    confidence_upper  FLOAT,
    actual_value      FLOAT,
    model_used        VARCHAR(100),
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_forecasts_date ON forecasts(forecast_date);
CREATE INDEX idx_forecasts_branch ON forecasts(branch_id);
CREATE INDEX idx_forecasts_product ON forecasts(product_id);
CREATE INDEX idx_forecasts_type ON forecasts(forecast_type);

-- Executive Reports
CREATE TABLE IF NOT EXISTS executive_reports (
    id                  SERIAL PRIMARY KEY,
    report_type         VARCHAR(50) NOT NULL,
    period_start        DATE NOT NULL,
    period_end          DATE NOT NULL,
    total_revenue       FLOAT NOT NULL DEFAULT 0,
    gross_profit        FLOAT NOT NULL DEFAULT 0,
    net_profit          FLOAT NOT NULL DEFAULT 0,
    operating_expenses  FLOAT NOT NULL DEFAULT 0,
    inventory_value     FLOAT NOT NULL DEFAULT 0,
    customer_growth     FLOAT NOT NULL DEFAULT 0,
    online_sales_growth FLOAT NOT NULL DEFAULT 0,
    report_data         TEXT,
    generated_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_exec_reports_type ON executive_reports(report_type);
CREATE INDEX idx_exec_reports_period ON executive_reports(period_start, period_end);

-- Audit Events
CREATE TABLE IF NOT EXISTS audit_events (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER,
    branch_id     INTEGER,
    event_type    VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id   INTEGER,
    description   TEXT NOT NULL,
    changes       TEXT,
    ip_address    VARCHAR(50),
    user_agent    VARCHAR(500),
    created_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_audit_events_type ON audit_events(event_type);
CREATE INDEX idx_audit_events_resource ON audit_events(resource_type, resource_id);
CREATE INDEX idx_audit_events_user ON audit_events(user_id);
CREATE INDEX idx_audit_events_branch ON audit_events(branch_id);
CREATE INDEX idx_audit_events_created ON audit_events(created_at);

-- Alerts
CREATE TABLE IF NOT EXISTS alerts (
    id            SERIAL PRIMARY KEY,
    branch_id     INTEGER,
    alert_type    VARCHAR(50) NOT NULL,
    severity      VARCHAR(20) NOT NULL DEFAULT 'info',
    title         VARCHAR(255) NOT NULL,
    message       TEXT NOT NULL,
    resource_type VARCHAR(50),
    resource_id   INTEGER,
    is_read       BOOLEAN DEFAULT FALSE,
    is_resolved   BOOLEAN DEFAULT FALSE,
    resolved_at   TIMESTAMP WITH TIME ZONE,
    created_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_alerts_type ON alerts(alert_type);
CREATE INDEX idx_alerts_branch ON alerts(branch_id);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_alerts_created ON alerts(created_at);
CREATE INDEX idx_alerts_read ON alerts(is_read);

-- Materialized Views for Analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_sales AS
SELECT
    DATE(s.created_at) AS sale_date,
    s.branch_id,
    COUNT(DISTINCT s.id) AS order_count,
    COUNT(DISTINCT s.user_id) AS cashier_count,
    SUM(s.grand_total) AS total_sales,
    SUM(s.subtotal) AS total_subtotal,
    SUM(s.discount) AS total_discount,
    SUM(s.tax) AS total_tax,
    SUM(si.quantity) AS total_items,
    SUM(si.quantity * p.cost_price) AS total_cost
FROM sales s
JOIN sale_items si ON si.sale_id = s.id
JOIN products p ON p.id = si.product_id
WHERE s.status = 'COMPLETED'
GROUP BY DATE(s.created_at), s.branch_id;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_daily_sales
ON mv_daily_sales(sale_date, branch_id);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_branch_performance AS
SELECT
    b.id AS branch_id,
    b.name AS branch_name,
    b.code AS branch_code,
    COALESCE(SUM(s.grand_total), 0) AS total_sales,
    COUNT(DISTINCT s.id) AS total_orders,
    COALESCE(SUM(si.quantity * p.cost_price), 0) AS total_cost,
    COALESCE(SUM(s.grand_total) - SUM(si.quantity * p.cost_price), 0) AS gross_profit,
    CASE WHEN COALESCE(SUM(s.grand_total), 0) > 0
         THEN (COALESCE(SUM(s.grand_total) - SUM(si.quantity * p.cost_price), 0) / SUM(s.grand_total)) * 100
         ELSE 0 END AS profit_margin_pct
FROM branches b
LEFT JOIN sales s ON s.branch_id = b.id AND s.status = 'COMPLETED'
LEFT JOIN sale_items si ON si.sale_id = s.id
LEFT JOIN products p ON p.id = si.product_id
GROUP BY b.id, b.name, b.code;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_branch_performance
ON mv_branch_performance(branch_id);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_product_performance AS
SELECT
    p.id AS product_id,
    p.name AS product_name,
    p.brand,
    c.name AS category,
    COUNT(DISTINCT s.id) AS times_sold,
    SUM(si.quantity) AS total_quantity,
    SUM(si.subtotal) AS total_revenue,
    SUM(si.quantity * p.cost_price) AS total_cost,
    SUM(si.subtotal) - SUM(si.quantity * p.cost_price) AS gross_profit,
    CASE WHEN SUM(si.subtotal) > 0
         THEN (SUM(si.subtotal) - SUM(si.quantity * p.cost_price)) / SUM(si.subtotal) * 100
         ELSE 0 END AS profit_margin_pct
FROM products p
LEFT JOIN categories c ON c.id = p.category_id
LEFT JOIN sale_items si ON si.product_id = p.id
LEFT JOIN sales s ON s.id = si.sale_id AND s.status = 'COMPLETED'
GROUP BY p.id, p.name, p.brand, c.name;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_product_performance
ON mv_product_performance(product_id);

-- Trigger: updated_at auto-update
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_suppliers_updated_at
    BEFORE UPDATE ON suppliers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_purchase_orders_updated_at
    BEFORE UPDATE ON purchase_orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_stock_transfers_updated_at
    BEFORE UPDATE ON stock_transfers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
