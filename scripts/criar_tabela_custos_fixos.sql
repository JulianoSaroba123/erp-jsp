-- Script para criar tabela custos_fixos no PostgreSQL (Render)
-- Execute este script no console do PostgreSQL do Render

-- Criar tabela custos_fixos
CREATE TABLE IF NOT EXISTS custos_fixos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    valor_mensal NUMERIC(10, 2) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    tipo VARCHAR(20) NOT NULL DEFAULT 'DESPESA',
    dia_vencimento INTEGER NOT NULL,
    gerar_automaticamente BOOLEAN DEFAULT TRUE,
    data_inicio DATE NOT NULL,
    data_fim DATE,
    conta_bancaria_id INTEGER REFERENCES contas_bancarias(id),
    centro_custo_id INTEGER REFERENCES centros_custo(id),
    ativo BOOLEAN DEFAULT TRUE,
    ultimo_mes_gerado VARCHAR(7),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Criar índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_custos_fixos_ativo ON custos_fixos(ativo);
CREATE INDEX IF NOT EXISTS idx_custos_fixos_categoria ON custos_fixos(categoria);
CREATE INDEX IF NOT EXISTS idx_custos_fixos_conta ON custos_fixos(conta_bancaria_id);
CREATE INDEX IF NOT EXISTS idx_custos_fixos_centro ON custos_fixos(centro_custo_id);
CREATE INDEX IF NOT EXISTS idx_custos_fixos_vencimento ON custos_fixos(dia_vencimento);

-- Adicionar coluna origem em lancamentos_financeiros (se não existir)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'lancamentos_financeiros' 
        AND column_name = 'origem'
    ) THEN
        ALTER TABLE lancamentos_financeiros 
        ADD COLUMN origem VARCHAR(20);
        
        COMMENT ON COLUMN lancamentos_financeiros.origem IS 'Origem do lançamento: MANUAL, CUSTO_FIXO, IMPORTACAO, etc';
    END IF;
END $$;

-- Verificar se tabela foi criada
SELECT 
    COUNT(*) as total_custos_fixos,
    'Tabela custos_fixos criada com sucesso!' as mensagem
FROM custos_fixos;

-- Mostrar estrutura da tabela
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'custos_fixos'
ORDER BY ordinal_position;
