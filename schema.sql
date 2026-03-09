-- Create and select database
CREATE DATABASE IF NOT EXISTS StockMarketDB;
USE StockMarketDB;

-- Create userbase table
CREATE TABLE IF NOT EXISTS userbase (

    -- 1. Primary Identification
    id                  BIGINT AUTO_INCREMENT PRIMARY KEY,
    uuid                VARCHAR(50),
    referral_code       VARCHAR(20),
    referred_by         BIGINT,

    -- 2. Basic Profile Information
    full_name           VARCHAR(100)                        NOT NULL,
    email               VARCHAR(150)                        NOT NULL UNIQUE,
    phone               VARCHAR(20)                         UNIQUE,
    password            VARCHAR(255)                        NOT NULL,
    profile_photo       VARCHAR(255),
    date_of_birth       DATE,
    gender              ENUM('male', 'female', 'other'),

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
    pan_verified        TINYINT(1)                          DEFAULT 0,
    aadhaar_verified    TINYINT(1)                          DEFAULT 0,
    kyc_status          ENUM('pending', 'verified', 'rejected') DEFAULT 'pending',

    -- 5. Trading Account Details
    demat_account       VARCHAR(50),
    broker_name         VARCHAR(100),
    trading_enabled     TINYINT(1)                          DEFAULT 0,
    risk_profile        ENUM('low', 'medium', 'high'),

    -- 6. Wallet / Balance
    wallet_balance      DECIMAL(12, 2)                      DEFAULT 0.00,
    invested_amount     DECIMAL(12, 2)                      DEFAULT 0.00,
    profit_loss         DECIMAL(12, 2)                      DEFAULT 0.00,

    -- 7. Security
    mpin                VARCHAR(10),
    otp                 VARCHAR(10),
    otp_expiry          DATETIME,
    two_factor_enabled  TINYINT(1)                          DEFAULT 0,

    -- 8. App Status
    account_status      ENUM('active', 'suspended', 'blocked') DEFAULT 'active',
    email_verified      TINYINT(1)                          DEFAULT 0,
    phone_verified      TINYINT(1)                          DEFAULT 0,

    -- 9. Device Information
    device_token        VARCHAR(255),
    device_type         ENUM('android', 'ios', 'web'),
    last_login          DATETIME,
    ip_address          VARCHAR(45),

    -- 10. Timestamps
    created_at          TIMESTAMP                           DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP                           DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
