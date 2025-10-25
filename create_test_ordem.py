"""
Cria uma ordem de serviço de exemplo para testar parágrafos no PDF
"""
import sqlite3
import os
from datetime import datetime

def create_test_ordem():
    """Cria ordem de serviço de teste com quebras de linha"""
    
    db_path = "database/database.db"
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Texto com quebras de linha para testar
        descricao_problema = """Equipamento apresentando falhas intermitentes.

Cliente reportou que a máquina para de funcionar aleatoriamente.

Necessário diagnóstico completo do sistema elétrico."""

        descricao_servico = """Realizado reaperto das conexões das resistências e relé de estado sólido.

Feito testes e medições de corrente elétrica das resistências, possível defeito intermitente no relé de estado sólido.

Após reaperto voltou a operar normalmente."""

        observacoes = """IMPORTANTE: Equipamento requer monitoramento.

Recomendações:
- Verificar conexões semanalmente
- Realizar limpeza preventiva mensalmente  
- Substituir relé em 30 dias

Garantia: 90 dias para serviços realizados."""
        
        # Insere dados da ordem de serviço
        dados_ordem = (
            "OS-2024-001",  # numero
            "TESTE PARAGRAFOS",  # titulo
            "Cliente Teste Ltda",  # cliente_nome
            "12.345.678/0001-90",  # cliente_cnpj
            "João da Silva",  # cliente_contato
            "(11) 99999-9999",  # cliente_telefone
            "joao@teste.com",  # cliente_email
            "Rua Teste, 123",  # cliente_endereco
            "São Paulo",  # cliente_cidade
            "SP",  # cliente_estado
            "01234-567",  # cliente_cep
            "ELÉTRICO INDUSTRIAL",  # tipo_servico
            descricao_problema,  # descricao_problema
            descricao_servico,  # descricao
            "Painel Elétrico XYZ",  # equipamento_tipo
            "Industrial 2024",  # equipamento_modelo
            "IE-789456",  # equipamento_serie
            "220V Trifásico",  # equipamento_voltagem
            "50HP",  # equipamento_potencia
            datetime.now(),  # data_abertura
            "em_andamento",  # status
            "normal",  # prioridade
            2500.00,  # valor_total
            "30 dias",  # prazo_entrega
            "50% entrada, 50% na entrega",  # condicoes_pagamento
            observacoes,  # observacoes
            datetime.now(),  # data_criacao
            datetime.now()   # data_atualizacao
        )
        
        sql_insert = """
        INSERT OR REPLACE INTO ordem_servico (
            numero, titulo, cliente_nome, cliente_cnpj, cliente_contato,
            cliente_telefone, cliente_email, cliente_endereco, cliente_cidade,
            cliente_estado, cliente_cep, tipo_servico, descricao_problema,
            descricao, equipamento_tipo, equipamento_modelo, equipamento_serie,
            equipamento_voltagem, equipamento_potencia, data_abertura, status,
            prioridade, valor_total, prazo_entrega, condicoes_pagamento,
            observacoes, data_criacao, data_atualizacao
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """
        
        cursor.execute(sql_insert, dados_ordem)
        
        # Pega o ID da ordem inserida
        ordem_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        print(f"✅ Ordem de serviço criada com ID: {ordem_id}")
        print("📝 Dados inseridos com quebras de linha nos campos:")
        print("   - Descrição do Problema")
        print("   - Descrição do Serviço")
        print("   - Observações")
        print(f"\n🌐 Teste o PDF em: http://localhost:5001/ordem_servico/pdf/{ordem_id}")
        
        return ordem_id
        
    except Exception as e:
        print(f"❌ Erro ao criar ordem: {e}")
        return None

if __name__ == "__main__":
    create_test_ordem()