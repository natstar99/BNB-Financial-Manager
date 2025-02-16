-- File: schema.sql

CREATE TABLE IF NOT EXISTS categories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    parent_id TEXT,
    category_type TEXT NOT NULL DEFAULT 'transaction',  -- 'asset_class', 'group', or 'transaction'
    tax_type TEXT,               -- Only applicable for transaction categories
    is_bank_account BOOLEAN DEFAULT 0,  -- Flag for bank account categories
    FOREIGN KEY (parent_id) REFERENCES categories (id)
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    account TEXT NOT NULL,
    description TEXT,
    withdrawal REAL,
    deposit REAL,
    category_id TEXT,
    tax_type TEXT,
    is_tax_deductible BOOLEAN,
    is_hidden BOOLEAN DEFAULT 0,
    is_matched BOOLEAN DEFAULT 0,
    is_internal_transfer BOOLEAN DEFAULT 0,
    FOREIGN KEY (category_id) REFERENCES categories (id)
);

CREATE INDEX IF NOT EXISTS idx_transactions_category 
ON transactions(category_id);

CREATE INDEX IF NOT EXISTS idx_transactions_date 
ON transactions(date);

CREATE TABLE IF NOT EXISTS auto_categorisation_rules (
    id INTEGER PRIMARY KEY,
    category_id TEXT NOT NULL,
    description_text TEXT,
    description_case_sensitive BOOLEAN,
    amount_operator TEXT,
    amount_value REAL,
    amount_value2 REAL,
    account_text TEXT,
    date_range TEXT,
    apply_future BOOLEAN,
    FOREIGN KEY (category_id) REFERENCES categories (id)
);

CREATE TABLE IF NOT EXISTS bank_accounts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    account_number TEXT NOT NULL,
    bsb TEXT NOT NULL,
    bank_name TEXT NOT NULL,
    current_balance DECIMAL(15,2) NOT NULL DEFAULT 0.00,
    last_import_date TEXT,
    notes TEXT,
    UNIQUE(bsb, account_number),
    FOREIGN KEY (id) REFERENCES categories (id)
);