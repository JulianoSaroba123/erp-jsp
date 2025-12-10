-- =========================================================================
-- CORREÇÃO DEFINITIVA - Estrutura de Propostas no PostgreSQL
-- =========================================================================
-- Execute este script no console PSQL do Render
-- Database: erp_jsp_db_iw6v
-- Data: 2025-12-10
-- =========================================================================

-- PROBLEMA IDENTIFICADO:
-- 1. Existem DUAS tabelas: 'proposta' (vazia) e 'propostas' (6 registros)
-- 2. Models Flask usam 'propostas' (correto)
-- 3. FK de ordem_servico aponta para 'propostas' (correto)
-- 4. Tabela 'proposta' é órfã e deve ser removida

-- SOLUÇÃO:
-- 1. Verificar estrutura atual
-- 2. Remover tabela 'proposta' órfã
-- 3. Garantir que todas as FKs apontam para 'propostas'
-- 4. Limpar registros órfãos
-- 5. Validar integridade final

\echo '========================================================================='
\echo 'ETAPA 1: DIAGNÓSTICO INICIAL'
\echo '========================================================================='

-- 1.1 Listar todas as tabelas com 'proposta'
SELECT tablename 
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename LIKE '%proposta%'
ORDER BY tablename;

-- 1.2 Contagens
SELECT 'proposta' as tabela, COUNT(*) as total FROM proposta
UNION ALL
SELECT 'propostas', COUNT(*) FROM propostas
UNION ALL
SELECT 'ordem_servico', COUNT(*) FROM ordem_servico;

\echo ''
\echo '========================================================================='
\echo 'ETAPA 2: VERIFICAR FOREIGN KEYS EXISTENTES'
\echo '========================================================================='

-- 2.1 FKs que referenciam 'proposta' (tabela órfã)
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
  AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
  AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND ccu.table_name = 'proposta'
  AND tc.table_schema = 'public';

-- 2.2 FKs que referenciam 'propostas' (tabela correta)
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
  AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
  AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND ccu.table_name = 'propostas'
  AND tc.table_schema = 'public';

\echo ''
\echo '========================================================================='
\echo 'ETAPA 3: IDENTIFICAR REGISTROS ÓRFÃOS'
\echo '========================================================================='

-- 3.1 Ordem de Serviço com proposta_id inválido (referenciando 'propostas')
SELECT COUNT(*) as os_orfas_propostas
FROM ordem_servico
WHERE proposta_id IS NOT NULL
  AND proposta_id NOT IN (SELECT id FROM propostas);

-- 3.2 Ordem de Serviço com cliente_id inválido
SELECT COUNT(*) as os_orfas_clientes
FROM ordem_servico
WHERE cliente_id NOT IN (SELECT id FROM clientes);

-- 3.3 Propostas com cliente_id inválido
SELECT COUNT(*) as propostas_orfas
FROM propostas
WHERE cliente_id NOT IN (SELECT id FROM clientes);

\echo ''
\echo '========================================================================='
\echo 'ETAPA 4: LISTAR ÓRFÃOS DETALHADOS (se houver)'
\echo '========================================================================='

-- 4.1 OS órfãs (proposta inválida)
SELECT 
    id, 
    numero, 
    proposta_id,
    'Proposta inexistente' as problema
FROM ordem_servico
WHERE proposta_id IS NOT NULL
  AND proposta_id NOT IN (SELECT id FROM propostas)
LIMIT 10;

-- 4.2 OS órfãs (cliente inválido)
SELECT 
    id, 
    numero, 
    cliente_id,
    'Cliente inexistente' as problema
FROM ordem_servico
WHERE cliente_id NOT IN (SELECT id FROM clientes)
LIMIT 10;

\echo ''
\echo '========================================================================='
\echo 'ETAPA 5: CORREÇÃO - REMOVER TABELA ÓRFÃ'
\echo '========================================================================='

-- IMPORTANTE: Esta operação é irreversível!
-- Só execute se confirmou que 'proposta' está vazia e não é usada

BEGIN;

-- 5.1 Verificar se tabela 'proposta' existe e está vazia
DO $$
DECLARE
    v_count INTEGER;
BEGIN
    -- Conta registros na tabela 'proposta'
    SELECT COUNT(*) INTO v_count FROM proposta;
    
    IF v_count > 0 THEN
        RAISE EXCEPTION 'ATENÇÃO: Tabela proposta contém % registros! Não pode ser removida.', v_count;
    ELSE
        RAISE NOTICE 'Tabela proposta está vazia. Pode ser removida.';
    END IF;
END $$;

-- 5.2 Remover foreign keys que referenciam 'proposta' (se houver)
-- Esta query será gerada dinamicamente se necessário
SELECT 'ALTER TABLE ' || tc.table_name || 
       ' DROP CONSTRAINT ' || tc.constraint_name || ';' as comando_drop
FROM information_schema.table_constraints AS tc
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND ccu.table_name = 'proposta'
  AND tc.table_schema = 'public';

-- 5.3 Remover tabela 'proposta' (órfã)
DROP TABLE IF EXISTS proposta CASCADE;

COMMIT;

\echo 'Tabela proposta removida (se existia)'

\echo ''
\echo '========================================================================='
\echo 'ETAPA 6: CORREÇÃO - LIMPAR ÓRFÃOS DE ORDEM_SERVICO'
\echo '========================================================================='

BEGIN;

-- 6.1 Desativar OS com proposta inválida (soft delete)
UPDATE ordem_servico 
SET ativo = FALSE
WHERE proposta_id IS NOT NULL
  AND proposta_id NOT IN (SELECT id FROM propostas);

-- Ou OPÇÃO ALTERNATIVA: Remover FK inválida (recomendado)
UPDATE ordem_servico 
SET proposta_id = NULL
WHERE proposta_id IS NOT NULL
  AND proposta_id NOT IN (SELECT id FROM propostas);

-- 6.2 Desativar OS com cliente inválido
UPDATE ordem_servico 
SET ativo = FALSE
WHERE cliente_id NOT IN (SELECT id FROM clientes);

-- 6.3 Desativar propostas com cliente inválido
UPDATE propostas 
SET ativo = FALSE
WHERE cliente_id NOT IN (SELECT id FROM clientes);

COMMIT;

\echo 'Órfãos corrigidos'

\echo ''
\echo '========================================================================='
\echo 'ETAPA 7: VALIDAÇÃO FINAL'
\echo '========================================================================='

-- 7.1 Verificar se tabela 'proposta' foi removida
SELECT tablename 
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename LIKE '%proposta%'
ORDER BY tablename;

-- 7.2 Verificar órfãos (deve retornar 0 em todos)
SELECT 'OS com proposta inválida' as tipo, COUNT(*) as total
FROM ordem_servico
WHERE proposta_id IS NOT NULL
  AND proposta_id NOT IN (SELECT id FROM propostas)
UNION ALL
SELECT 'OS com cliente inválido', COUNT(*)
FROM ordem_servico
WHERE ativo = TRUE
  AND cliente_id NOT IN (SELECT id FROM clientes)
UNION ALL
SELECT 'Propostas com cliente inválido', COUNT(*)
FROM propostas
WHERE ativo = TRUE
  AND cliente_id NOT IN (SELECT id FROM clientes);

-- 7.3 Verificar FKs finais
SELECT
    tc.table_name AS tabela,
    kcu.column_name AS coluna,
    ccu.table_name AS referencia_tabela,
    ccu.column_name AS referencia_coluna
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND (ccu.table_name IN ('propostas', 'clientes') 
       OR tc.table_name IN ('ordem_servico', 'propostas'))
  AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.column_name;

-- 7.4 Contagens finais
SELECT 'Clientes' as tabela, 
       COUNT(*) as total, 
       COUNT(*) FILTER (WHERE ativo = TRUE) as ativos
FROM clientes
UNION ALL
SELECT 'Propostas', COUNT(*), COUNT(*) FILTER (WHERE ativo = TRUE)
FROM propostas
UNION ALL
SELECT 'Ordem Serviço', COUNT(*), COUNT(*) FILTER (WHERE ativo = TRUE)
FROM ordem_servico;

\echo ''
\echo '========================================================================='
\echo 'RESULTADO ESPERADO:'
\echo '========================================================================='
\echo '✅ Tabela proposta removida'
\echo '✅ Todas as FKs apontam para propostas (não proposta)'
\echo '✅ 0 registros órfãos'
\echo '✅ ordem_servico.proposta_id → propostas.id'
\echo '✅ ordem_servico.cliente_id → clientes.id'
\echo '✅ propostas.cliente_id → clientes.id'
\echo '========================================================================='
