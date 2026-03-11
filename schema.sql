-- PostgreSQL schema for StockMarketDB
-- Run against your Render PostgreSQL database

CREATE TABLE IF NOT EXISTS userbase (

    -- 1. Primary Identification
    id                  BIGSERIAL PRIMARY KEY,
    uuid                VARCHAR(50),
    referral_code       VARCHAR(20),
    referred_by         BIGINT,

    -- 2. Basic Profile Information
    full_name           VARCHAR(100)    NOT NULL,
    email               VARCHAR(150)    NOT NULL UNIQUE,
    phone               VARCHAR(20)     UNIQUE,
    password            VARCHAR(255)    NOT NULL,
    profile_photo       VARCHAR(255),
    date_of_birth       DATE,
    gender              VARCHAR(10)     CHECK (gender IN ('male', 'female', 'other')),

    -- 3. Address Details
    address_line1       VARCHAR(200),
    address_line2       VARCHAR(200),
    city                VARCHAR(100),
    state               VARCHAR(100),
    country             VARCHAR(100),
    pincode             VARCHAR(10),

    -- 4. KYC Verification
    pan_number          VARCHAR(20),
    aadhaar_number      VARCHAR(20),
    pan_verified        SMALLINT        DEFAULT 0,
    aadhaar_verified    SMALLINT        DEFAULT 0,
    kyc_status          VARCHAR(10)     DEFAULT 'pending' CHECK (kyc_status IN ('pending', 'verified', 'rejected')),

    -- 5. Trading Account Details
    demat_account       VARCHAR(50),
    broker_name         VARCHAR(100),
    trading_enabled     SMALLINT        DEFAULT 0,
    risk_profile        VARCHAR(10)     CHECK (risk_profile IN ('low', 'medium', 'high')),

    -- 6. Wallet / Balance
    wallet_balance      DECIMAL(12, 2)  DEFAULT 0.00,
    invested_amount     DECIMAL(12, 2)  DEFAULT 0.00,
    profit_loss         DECIMAL(12, 2)  DEFAULT 0.00,

    -- 7. Security
    mpin                VARCHAR(10),
    otp                 VARCHAR(10),
    otp_expiry          TIMESTAMP,
    two_factor_enabled  SMALLINT        DEFAULT 0,

    -- 8. App Status
    account_status      VARCHAR(10)     DEFAULT 'active' CHECK (account_status IN ('active', 'suspended', 'blocked')),
    email_verified      SMALLINT        DEFAULT 0,
    phone_verified      SMALLINT        DEFAULT 0,

    -- 9. Device Information
    device_token        VARCHAR(255),
    device_type         VARCHAR(10)     CHECK (device_type IN ('android', 'ios', 'web')),
    last_login          TIMESTAMP,
    ip_address          VARCHAR(45),

    -- 10. Timestamps
    created_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);
