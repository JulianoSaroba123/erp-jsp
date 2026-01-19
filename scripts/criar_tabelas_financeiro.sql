-- ============================================================================
-- Script SQL para criar tabelas do módulo financeiro no Render
-- ============================================================================
-- Execute este script no PostgreSQL do Render via pgAdmin ou psql
-- ============================================================================

-- TABELA: contas_bancarias
-- ============================================================================
CREATE TABLE IF NOT EXISTS contas_bancarias (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    banco VARCHAR(100) NOT NULL,
    agencia VARCHAR(20),
    numero_conta VARCHAR(30) NOT NULL,
    tipo_conta VARCHAR(20) DEFAULT 'corrente',
    saldo NUMERIC(12, 2) DEFAULT 0.00,
    saldo_inicial NUMERIC(12, 2) DEFAULT 0.00,
    limite_credito NUMERIC(12, 2) DEFAULT 0.00,
    gerente VARCHAR(100),
    telefone_banco VARCHAR(20),
    observacoes TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_contas_bancarias_ativo ON contas_bancarias(ativo);
CREATE INDEX IF NOT EXISTS idx_contas_bancarias_banco ON contas_bancarias(banco);

-- ============================================================================
-- TABELA: centros_custo
-- ============================================================================
CREATE TABLE IF NOT EXISTS centros_custo (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    centro_custo_pai_id INTEGER REFERENCES centros_custo(id),
    tipo VARCHAR(50),
    orcamento_mensal NUMERIC(12, 2) DEFAULT 0.00,
    responsavel VARCHAR(100),
    departamento VARCHAR(100),
    observacoes TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_centros_custo_ativo ON centros_custo(ativo);
CREATE INDEX IF NOT EXISTS idx_centros_custo_codigo ON centros_custo(codigo);
CREATE INDEX IF NOT EXISTS idx_centros_custo_pai ON centros_custo(centro_custo_pai_id);

-- ============================================================================
-- TABELA: extratos_bancarios
-- ============================================================================
CREATE TABLE IF NOT EXISTS extratos_bancarios (
    id SERIAL PRIMARY KEY,
    conta_bancaria_id INTEGER NOT NULL REFERENCES contas_bancarias(id),
    data_movimento DATE NOT NULL,
    descricao VARCHAR(255) NOT NULL,
    documento VARCHAR(50),
    valor NUMERIC(12, 2) NOT NULL,
    tipo_movimento VARCHAR(10) NOT NULL,
    saldo NUMERIC(12, 2),
    conciliado BOOLEAN DEFAULT FALSE,
    data_conciliacao TIMESTAMP,
    lancamento_id INTEGER REFERENCES lancamentos_financeiros(id),
    arquivo_origem VARCHAR(255),
    data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    observacoes TEXT,
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_extratos_conta ON extratos_bancarios(conta_bancaria_id);
CREATE INDEX IF NOT EXISTS idx_extratos_conciliado ON extratos_bancarios(conciliado);
CREATE INDEX IF NOT EXISTS idx_extratos_data ON extratos_bancarios(data_movimento);
CREATE INDEX IF NOT EXISTS idx_extratos_lancamento ON extratos_bancarios(lancamento_id);

-- ============================================================================
-- Adicionar colunas na tabela lancamentos_financeiros (se não existirem)
-- ============================================================================
DO $$ 
BEGIN
    -- Adicionar conta_bancaria_id
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'lancamentos_financeiros' 
        AND column_name = 'conta_bancaria_id'
    ) THEN
        ALTER TABLE lancamentos_financeiros 
        ADD COLUMN conta_bancaria_id INTEGER REFERENCES contas_bancarias(id);
        CREATE INDEX idx_lancamentos_conta ON lancamentos_financeiros(conta_bancaria_id);
    END IF;

    -- Adicionar centro_custo_id
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'lancamentos_financeiros' 
        AND column_name = 'centro_custo_id'
    ) THEN
        ALTER TABLE lancamentos_financeiros 
        ADD COLUMN centro_custo_id INTEGER REFERENCES centros_custo(id);
        CREATE INDEX idx_lancamentos_centro ON lancamentos_financeiros(centro_custo_id);
    END IF;
END $$;

-- ============================================================================
-- Dados iniciais (opcional)
-- ============================================================================

-- Inserir uma conta bancária padrão
INSERT INTO contas_bancarias (nome, banco, agencia, numero_conta, tipo_conta, saldo, saldo_inicial)
VALUES ('Caixa Geral', 'Caixa Interno', '0001', '0000001-0', 'caixa', 0.00, 0.00)
ON CONFLICT DO NOTHING;

-- Inserir um centro de custo padrão
INSERT INTO centros_custo (codigo, nome, descricao, tipo)
VALUES ('GERAL', 'Geral', 'Centro de custo geral', 'operacional')
ON CONFLICT (codigo) DO NOTHING;

-- ============================================================================
-- Verificação final
-- ============================================================================
SELECT 'Tabelas criadas com sucesso!' AS status;

SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('contas_bancarias', 'centros_custo', 'extratos_bancarios')
ORDER BY table_name;
