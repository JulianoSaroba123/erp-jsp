-- =========================================================================
-- TESTE DE INTEGRIDADE - INSERT Real após Correção
-- =========================================================================
-- Execute APÓS o script de correção
-- Testa se a estrutura está funcionando corretamente
-- =========================================================================

\echo '========================================================================='
\echo 'TESTE DE INTEGRIDADE - PostgreSQL'
\echo '========================================================================='

BEGIN;

-- Criar cliente de teste
INSERT INTO clientes (
    nome, tipo, cpf_cnpj, telefone, email, 
    endereco, cidade, estado, cep, ativo,
    criado_em, atualizado_em
) VALUES (
    'Cliente Teste Integridade',
    'PJ',
    '12345678000199',
    '(14) 99999-9999',
    'teste@integridade.com',
    'Rua Teste, 123',
    'Botucatu',
    'SP',
    '18600-000',
    TRUE,
    NOW(),
    NOW()
) RETURNING id, nome;

-- Armazenar ID do cliente criado
\set cliente_id `echo "SELECT id FROM clientes WHERE cpf_cnpj = '12345678000199'"`

-- Criar proposta de teste vinculada ao cliente
INSERT INTO propostas (
    codigo, cliente_id, titulo, descricao,
    status, data_emissao, validade, data_validade,
    valor_produtos, valor_servicos, desconto, valor_total,
    ativo, criado_em, atualizado_em
) VALUES (
    'PROP-TEST-001',
    (SELECT id FROM clientes WHERE cpf_cnpj = '12345678000199'),
    'Proposta Teste de Integridade',
    'Proposta criada para validar integridade referencial',
    'rascunho',
    CURRENT_DATE,
    30,
    CURRENT_DATE + INTERVAL '30 days',
    1000.00,
    500.00,
    5.00,
    1425.00,
    TRUE,
    NOW(),
    NOW()
) RETURNING id, codigo;

-- Armazenar ID da proposta criada
\set proposta_id `echo "SELECT id FROM propostas WHERE codigo = 'PROP-TEST-001'"`

-- Criar ordem de serviço vinculada ao cliente E à proposta
INSERT INTO ordem_servico (
    numero, cliente_id, proposta_id, titulo, descricao,
    status, prioridade, data_abertura,
    valor_servico, valor_pecas, valor_total,
    ativo, criado_em, atualizado_em
) VALUES (
    'OS-TEST-001',
    (SELECT id FROM clientes WHERE cpf_cnpj = '12345678000199'),
    (SELECT id FROM propostas WHERE codigo = 'PROP-TEST-001'),
    'OS Teste de Integridade',
    'Ordem de serviço criada para validar integridade referencial',
    'pendente',
    'normal',
    CURRENT_DATE,
    1000.00,
    425.00,
    1425.00,
    TRUE,
    NOW(),
    NOW()
) RETURNING id, numero;

ROLLBACK; -- Remove os testes após validação

\echo ''
\echo '========================================================================='
\echo 'RESULTADO DO TESTE:'
\echo '========================================================================='
\echo 'Se não houve erro SQL, a estrutura está íntegra!'
\echo ''
\echo 'Verificações realizadas:'
\echo '✅ INSERT em clientes'
\echo '✅ INSERT em propostas com FK para clientes'
\echo '✅ INSERT em ordem_servico com FKs para clientes E propostas'
\echo '✅ ROLLBACK automático (dados não foram persistidos)'
\echo ''
\echo 'Se algum erro ocorreu:'
\echo '❌ Verifique as mensagens de erro acima'
\echo '❌ Execute novamente o script de correção'
\echo '========================================================================='

-- =========================================================================
-- CONSULTAS DE VALIDAÇÃO (SOMENTE LEITURA)
-- =========================================================================

\echo ''
\echo '========================================================================='
\echo 'CONSULTAS DE VALIDAÇÃO'
\echo '========================================================================='

-- 1. Estrutura das foreign keys
\echo 'Foreign Keys de ordem_servico:'
SELECT
    kcu.column_name,
    ccu.table_name AS foreign_table,
    ccu.column_name AS foreign_column
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'ordem_servico'
  AND tc.constraint_type = 'FOREIGN KEY'
ORDER BY kcu.column_name;

\echo ''
\echo 'Foreign Keys de propostas:'
SELECT
    kcu.column_name,
    ccu.table_name AS foreign_table,
    ccu.column_name AS foreign_column
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'propostas'
  AND tc.constraint_type = 'FOREIGN KEY'
ORDER BY kcu.column_name;

-- 2. Verificar órfãos
\echo ''
\echo 'Verificação de Órfãos:'
SELECT 
    'OS com proposta inválida' as tipo,
    COUNT(*) as quantidade
FROM ordem_servico
WHERE proposta_id IS NOT NULL
  AND proposta_id NOT IN (SELECT id FROM propostas)
UNION ALL
SELECT 
    'OS com cliente inválido',
    COUNT(*)
FROM ordem_servico
WHERE cliente_id NOT IN (SELECT id FROM clientes)
UNION ALL
SELECT 
    'Propostas com cliente inválido',
    COUNT(*)
FROM propostas
WHERE cliente_id NOT IN (SELECT id FROM clientes);

-- 3. Contagem geral
\echo ''
\echo 'Contagens Gerais:'
SELECT 
    'Clientes' as entidade,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE ativo = TRUE) as ativos
FROM clientes
UNION ALL
SELECT 'Propostas', COUNT(*), COUNT(*) FILTER (WHERE ativo = TRUE)
FROM propostas
UNION ALL
SELECT 'Ordens de Serviço', COUNT(*), COUNT(*) FILTER (WHERE ativo = TRUE)
FROM ordem_servico
ORDER BY entidade;

\echo ''
\echo '========================================================================='
\echo 'FIM DO TESTE'
\echo '========================================================================='
