-- ============================================================
-- FIX RÁPIDO: Adiciona TODAS as colunas faltantes
-- Execute este SQL no Render Shell
-- ============================================================

-- TABELA: ordem_servico
-- Colunas de horários que podem estar faltando
ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS intervalo_almoco INTEGER DEFAULT 60;
ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS hora_entrada_manha TIME;
ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS hora_saida_almoco TIME;
ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS hora_retorno_almoco TIME;
ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS hora_saida TIME;
ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS hora_entrada_extra TIME;
ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS hora_saida_extra TIME;
ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS horas_normais NUMERIC(10,2);
ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS horas_extras NUMERIC(10,2);

-- TABELA: ordem_servico_colaborador  
-- Colunas de horários detalhados
ALTER TABLE ordem_servico_colaborador ADD COLUMN IF NOT EXISTS hora_entrada_manha TIME;
ALTER TABLE ordem_servico_colaborador ADD COLUMN IF NOT EXISTS hora_saida_manha TIME;
ALTER TABLE ordem_servico_colaborador ADD COLUMN IF NOT EXISTS hora_entrada_tarde TIME;
ALTER TABLE ordem_servico_colaborador ADD COLUMN IF NOT EXISTS hora_saida_tarde TIME;
ALTER TABLE ordem_servico_colaborador ADD COLUMN IF NOT EXISTS hora_entrada_extra TIME;
ALTER TABLE ordem_servico_colaborador ADD COLUMN IF NOT EXISTS hora_saida_extra TIME;
ALTER TABLE ordem_servico_colaborador ADD COLUMN IF NOT EXISTS horas_normais NUMERIC(10,2);
ALTER TABLE ordem_servico_colaborador ADD COLUMN IF NOT EXISTS horas_extras NUMERIC(10,2);

-- Colunas de KM
ALTER TABLE ordem_servico_colaborador ADD COLUMN IF NOT EXISTS km_inicial INTEGER;
ALTER TABLE ordem_servico_colaborador ADD COLUMN IF NOT EXISTS km_final INTEGER;

-- Verificação final
SELECT 'ordem_servico' as tabela, column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'ordem_servico' 
  AND column_name IN ('intervalo_almoco', 'hora_entrada_manha', 'horas_normais', 'horas_extras')
ORDER BY column_name;

SELECT 'ordem_servico_colaborador' as tabela, column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'ordem_servico_colaborador' 
  AND column_name IN ('hora_entrada_manha', 'hora_saida_manha', 'km_inicial', 'km_final')
ORDER BY column_name;
