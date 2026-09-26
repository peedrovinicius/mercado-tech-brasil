CREATE TABLE IF NOT EXISTS dataset_release (
    competence DATE PRIMARY KEY,
    source VARCHAR(80) NOT NULL,
    source_sha256 VARCHAR(64) NOT NULL,
    publishable BOOLEAN NOT NULL,
    admissions INTEGER NOT NULL CHECK (admissions >= 0),
    dismissals INTEGER NOT NULL CHECK (dismissals >= 0),
    balance INTEGER NOT NULL,
    records_tech INTEGER NOT NULL CHECK (records_tech >= 0),
    salary_mean_admissions NUMERIC(14,2),
    salary_median_admissions NUMERIC(14,2),
    valid_rate NUMERIC(8,6) NOT NULL,
    loaded_at_utc TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_market_uf (
    competence DATE NOT NULL REFERENCES dataset_release(competence) ON DELETE CASCADE,
    uf CHAR(2) NOT NULL,
    admissions INTEGER NOT NULL CHECK (admissions >= 0),
    dismissals INTEGER NOT NULL CHECK (dismissals >= 0),
    balance INTEGER NOT NULL,
    salary_median_admissions NUMERIC(14,2),
    PRIMARY KEY (competence, uf)
);

CREATE TABLE IF NOT EXISTS fact_market_occupation (
    competence DATE NOT NULL REFERENCES dataset_release(competence) ON DELETE CASCADE,
    cbo_family VARCHAR(4) NOT NULL,
    cbo_code VARCHAR(10) NOT NULL,
    admissions INTEGER NOT NULL CHECK (admissions >= 0),
    dismissals INTEGER NOT NULL CHECK (dismissals >= 0),
    balance INTEGER NOT NULL,
    salary_median_admissions NUMERIC(14,2),
    PRIMARY KEY (competence, cbo_family, cbo_code)
);

CREATE INDEX IF NOT EXISTS idx_market_uf_admissions
ON fact_market_uf (competence, admissions DESC);

CREATE INDEX IF NOT EXISTS idx_market_occupation_admissions
ON fact_market_occupation (competence, admissions DESC);
