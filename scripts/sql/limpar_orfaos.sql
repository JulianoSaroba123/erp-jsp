-- =========================================================================
-- LIMPEZA DE REGISTROS ÓRFÃOS - PostgreSQL ONLY
-- =========================================================================
-- Remove registros com referências inválidas antes da importação limpa
-- Execute APENAS no PostgreSQL (Render)
-- =========================================================================

-- 1. IDENTIFICAR ÓRFÃOS
-- -------------------------------------------------------------------------

-- 1.1 Ordens de Serviço sem Cliente válido
SELECT 
    os.id, 
    os.numero, 
    os.cliente_id,
    'Cliente inexistente' as problema
FROM ordem_servico os
LEFT JOIN clientes c ON os.cliente_id = c.id
WHERE c.id IS NULL;

-- 1.2 Ordens de Serviço com Proposta inválida
SELECT 
    os.id, 
    os.numero, 
    os.proposta_id,
    'Proposta inexistente' as problema
FROM ordem_servico os
WHERE os.proposta_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM propostas WHERE id = os.proposta_id);

-- 1.3 Propostas sem Cliente válido
SELECT 
    p.id, 
    p.codigo, 
    p.cliente_id,
    'Cliente inexistente' as problema
FROM propostas p
LEFT JOIN clientes c ON p.cliente_id = c.id
WHERE c.id IS NULL;

-- 1.4 Propostas sem Itens
SELECT 
    p.id, 
    p.codigo,
    'Sem itens' as problema
FROM propostas p
WHERE NOT EXISTS (SELECT 1 FROM proposta_item WHERE proposta_id = p.id);


-- 2. LIMPAR ÓRFÃOS (CUIDADO: IRREVERSÍVEL!)
-- -------------------------------------------------------------------------

-- OPÇÃO A: Remover completamente
BEGIN;

-- Remove OS órfãs (sem cliente)
DELETE FROM ordem_servico 
WHERE cliente_id NOT IN (SELECT id FROM clientes);

-- Remove OS com proposta inválida
DELETE FROM ordem_servico 
WHERE proposta_id IS NOT NULL 
  AND proposta_id NOT IN (SELECT id FROM propostas);

-- Remove propostas órfãs (sem cliente)
DELETE FROM propostas 
WHERE cliente_id NOT IN (SELECT id FROM clientes);

-- Remove clientes de teste/órfãos (sem CPF/CNPJ)
DELETE FROM clientes 
WHERE cpf_cnpj IS NULL OR cpf_cnpj = '';

COMMIT;


-- OPÇÃO B: Desativar órfãos (soft delete - RECOMENDADO)
BEGIN;

-- Desativa OS órfãs
UPDATE ordem_servico 
SET ativo = FALSE 
WHERE cliente_id NOT IN (SELECT id FROM clientes);

-- Desativa OS com proposta inválida
UPDATE ordem_servico 
SET ativo = FALSE 
WHERE proposta_id IS NOT NULL 
  AND proposta_id NOT IN (SELECT id FROM propostas);

-- Desativa propostas órfãs
UPDATE propostas 
SET ativo = FALSE 
WHERE cliente_id NOT IN (SELECT id FROM clientes);

-- Desativa clientes sem CPF/CNPJ
UPDATE clientes 
SET ativo = FALSE 
WHERE cpf_cnpj IS NULL OR cpf_cnpj = '';

COMMIT;


-- 3. RESETAR SEQUENCES (APENAS APÓS LIMPAR)
-- -------------------------------------------------------------------------
SELECT setval(
    pg_get_serial_sequence('clientes', 'id'), 
    COALESCE((SELECT MAX(id) FROM clientes), 1)
);

SELECT setval(
    pg_get_serial_sequence('propostas', 'id'), 
    COALESCE((SELECT MAX(id) FROM propostas), 1)
);

SELECT setval(
    pg_get_serial_sequence('ordem_servico', 'id'), 
    COALESCE((SELECT MAX(id) FROM ordem_servico), 1)
);


-- 4. VERIFICAR INTEGRIDADE FINAL
-- -------------------------------------------------------------------------
-- Deve retornar 0 em todas as queries

SELECT COUNT(*) as os_orfas_cliente 
FROM ordem_servico 
WHERE cliente_id NOT IN (SELECT id FROM clientes);

SELECT COUNT(*) as os_orfas_proposta 
FROM ordem_servico 
WHERE proposta_id IS NOT NULL 
  AND proposta_id NOT IN (SELECT id FROM propostas);

SELECT COUNT(*) as propostas_orfas 
FROM propostas 
WHERE cliente_id NOT IN (SELECT id FROM clientes);

SELECT COUNT(*) as clientes_sem_cpf 
FROM clientes 
WHERE cpf_cnpj IS NULL OR cpf_cnpj = '';
