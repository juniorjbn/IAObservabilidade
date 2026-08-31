-- Esquema mínimo da loja de demonstração.
-- Duas tabelas: o estoque, que é o recurso disputado, e os pedidos.

CREATE TABLE IF NOT EXISTS inventory (
    sku        TEXT PRIMARY KEY,
    disponivel INTEGER NOT NULL,
    reservado  INTEGER NOT NULL DEFAULT 0,
    conferido_em TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS orders (
    id        BIGSERIAL PRIMARY KEY,
    sku       TEXT NOT NULL,
    qtd       INTEGER NOT NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Poucos SKUs, de propósito: o worker e o checkout precisam disputar as
-- MESMAS linhas para o incidente ser determinístico.
INSERT INTO inventory (sku, disponivel) VALUES
    ('SKU-0001', 100000),
    ('SKU-0002', 100000),
    ('SKU-0003', 100000),
    ('SKU-0004', 100000),
    ('SKU-0005', 100000)
ON CONFLICT (sku) DO NOTHING;
