-- =========================================================================
-- VERIFICAÇÃO PÓS-MIGRAÇÃO - PostgreSQL ONLY
-- =========================================================================
-- Execute após a migração para garantir integridade dos dados
-- =========================================================================

-- 1. VERIFICAR QUANTIDADES
-- -------------------------------------------------------------------------
SELECT 'Clientes' as tabela, COUNT(*) as total, COUNT(*) FILTER (WHERE ativo = TRUE) as ativos
FROM clientes
UNION ALL
SELECT 'Propostas', COUNT(*), COUNT(*) FILTER (WHERE ativo = TRUE)
FROM propostas
UNION ALL
SELECT 'Ordem Serviço', COUNT(*), COUNT(*) FILTER (WHERE ativo = TRUE)
FROM ordem_servico;


-- 2. VERIFICAR INTEGRIDADE REFERENCIAL
-- -------------------------------------------------------------------------

-- 2.1 OS sem cliente válido (deve ser 0)
SELECT COUNT(*) as os_sem_cliente
FROM ordem_servico os
WHERE NOT EXISTS (SELECT 1 FROM clientes c WHERE c.id = os.cliente_id);

-- 2.2 OS com proposta inválida (deve ser 0)
SELECT COUNT(*) as os_proposta_invalida
FROM ordem_servico os
WHERE os.proposta_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM propostas p WHERE p.id = os.proposta_id);

-- 2.3 Propostas sem cliente válido (deve ser 0)
SELECT COUNT(*) as propostas_sem_cliente
FROM propostas p
WHERE NOT EXISTS (SELECT 1 FROM clientes c WHERE c.id = p.cliente_id);


-- 3. VERIFICAR DUPLICATAS
-- -------------------------------------------------------------------------

-- 3.1 Clientes duplicados por CPF/CNPJ
SELECT cpf_cnpj, COUNT(*) as qtd
FROM clientes
WHERE cpf_cnpj IS NOT NULL
GROUP BY cpf_cnpj
HAVING COUNT(*) > 1;

-- 3.2 Propostas duplicadas por código
SELECT codigo, COUNT(*) as qtd
FROM propostas
GROUP BY codigo
HAVING COUNT(*) > 1;

-- 3.3 OS duplicadas por número
SELECT numero, COUNT(*) as qtd
FROM ordem_servico
GROUP BY numero
HAVING COUNT(*) > 1;


-- 4. VERIFICAR CAMPOS OBRIGATÓRIOS
-- -------------------------------------------------------------------------

-- 4.1 Clientes sem CPF/CNPJ
SELECT COUNT(*) as clientes_sem_cpf
FROM clientes
WHERE ativo = TRUE AND (cpf_cnpj IS NULL OR cpf_cnpj = '');

-- 4.2 Propostas sem código
SELECT COUNT(*) as propostas_sem_codigo
FROM propostas
WHERE ativo = TRUE AND (codigo IS NULL OR codigo = '');

-- 4.3 OS sem número
SELECT COUNT(*) as os_sem_numero
FROM ordem_servico
WHERE ativo = TRUE AND (numero IS NULL OR numero = '');


-- 5. LISTAR ÚLTIMOS REGISTROS IMPORTADOS
-- -------------------------------------------------------------------------

SELECT 'Cliente' as tipo, id, nome as descricao, created_at
FROM clientes
WHERE ativo = TRUE
ORDER BY id DESC
LIMIT 5;

SELECT 'Proposta' as tipo, id, codigo as descricao, data_proposta as created_at
FROM propostas
WHERE ativo = TRUE
ORDER BY id DESC
LIMIT 5;

SELECT 'OS' as tipo, id, numero as descricao, data_abertura as created_at
FROM ordem_servico
WHERE ativo = TRUE
ORDER BY id DESC
LIMIT 5;


-- 6. VERIFICAR SEQUENCES
-- -------------------------------------------------------------------------
SELECT 
    'clientes' as tabela,
    last_value as ultimo_id,
    (SELECT MAX(id) FROM clientes) as max_id_tabela,
    last_value >= (SELECT MAX(id) FROM clientes) as sequence_ok
FROM clientes_id_seq;

SELECT 
    'propostas' as tabela,
    last_value as ultimo_id,
    (SELECT MAX(id) FROM propostas) as max_id_tabela,
    last_value >= (SELECT MAX(id) FROM propostas) as sequence_ok
FROM propostas_id_seq;

SELECT 
    'ordem_servico' as tabela,
    last_value as ultimo_id,
    (SELECT MAX(id) FROM ordem_servico) as max_id_tabela,
    last_value >= (SELECT MAX(id) FROM ordem_servico) as sequence_ok
FROM ordem_servico_id_seq;


-- 7. RELATÓRIO FINAL (RESUMO)
-- -------------------------------------------------------------------------
SELECT 
    'VERIFICAÇÃO CONCLUÍDA' as status,
    CASE 
        WHEN (SELECT COUNT(*) FROM ordem_servico WHERE NOT EXISTS (SELECT 1 FROM clientes WHERE id = ordem_servico.cliente_id)) = 0
         AND (SELECT COUNT(*) FROM propostas WHERE NOT EXISTS (SELECT 1 FROM clientes WHERE id = propostas.cliente_id)) = 0
         AND (SELECT COUNT(*) FROM clientes WHERE cpf_cnpj IS NULL OR cpf_cnpj = '') = 0
        THEN '✅ SUCESSO - Dados íntegros'
        ELSE '❌ FALHA - Corrija os problemas acima'
    END as resultado;
