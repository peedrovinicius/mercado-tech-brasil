CREATE TABLE IF NOT EXISTS dim_periodo (
    competencia DATE PRIMARY KEY,
    ano SMALLINT NOT NULL,
    mes SMALLINT NOT NULL CHECK (mes BETWEEN 1 AND 12)
);

CREATE TABLE IF NOT EXISTS dim_ocupacao (
    cbo_codigo VARCHAR(10) PRIMARY KEY,
    cbo_familia VARCHAR(4) NOT NULL,
    titulo TEXT,
    is_tech BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS dim_municipio (
    municipio_codigo VARCHAR(7) PRIMARY KEY,
    municipio_nome TEXT NOT NULL,
    uf CHAR(2) NOT NULL,
    regiao TEXT
);

CREATE TABLE IF NOT EXISTS fact_mercado_mensal (
    competencia DATE NOT NULL REFERENCES dim_periodo(competencia),
    municipio_codigo VARCHAR(7) NOT NULL REFERENCES dim_municipio(municipio_codigo),
    cbo_codigo VARCHAR(10) NOT NULL REFERENCES dim_ocupacao(cbo_codigo),
    admissoes INTEGER NOT NULL CHECK (admissoes >= 0),
    desligamentos INTEGER NOT NULL CHECK (desligamentos >= 0),
    saldo INTEGER NOT NULL,
    salario_medio_admissao NUMERIC(14,2),
    salario_mediano_admissao NUMERIC(14,2),
    PRIMARY KEY (competencia, municipio_codigo, cbo_codigo)
);

CREATE INDEX IF NOT EXISTS idx_fact_mercado_uf_periodo
ON fact_mercado_mensal (competencia, municipio_codigo);

CREATE INDEX IF NOT EXISTS idx_fact_mercado_cbo_periodo
ON fact_mercado_mensal (competencia, cbo_codigo);
