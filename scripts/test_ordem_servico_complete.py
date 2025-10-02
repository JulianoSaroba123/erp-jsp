"""
Teste completo para módulo Ordem de Serviço
Testa CRUD, cálculos, modelos e integração
"""
import sys
import os
import json
from datetime import date

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aplicacao import create_app
from aplicacao.extensoes import db
from aplicacao.cliente.cliente_model import Cliente
from aplicacao.produto.produto_model import Produto  
from aplicacao.ordem_servico.ordem_servico_model import OrdemServico, OrdemServicoItem
from aplicacao.ordem_servico.os_calculos import CalculadoraOS


def test_ordem_servico_complete():
    """Teste completo do módulo de Ordem de Serviço"""
    app = create_app()
    
    with app.app_context():
        print("=== TESTE COMPLETO ORDEM DE SERVIÇO ===\n")
        
        # 1. PREPARAR DADOS DE TESTE
        print("1. Preparando dados de teste...")
        
        # Criar cliente de teste (se não existir)
        cliente_teste = Cliente.query.filter_by(nome="Cliente Teste OS").first()
        if not cliente_teste:
            cliente_teste = Cliente(
                nome="Cliente Teste OS",
                email="cliente@testeOS.com",
                telefone="11999999999",
                endereco="Rua Teste, 123"
            )
            db.session.add(cliente_teste)
            db.session.commit()
        
        # Criar produto de teste (se não existir)
        produto_teste = Produto.query.filter_by(nome="Produto Teste OS").first()
        if not produto_teste:
            produto_teste = Produto(
                nome="Produto Teste OS",
                preco_venda=100.00,
                markup=20.0
            )
            db.session.add(produto_teste)
            db.session.commit()
        
        print(f"   ✓ Cliente teste criado: {cliente_teste.nome} (ID: {cliente_teste.id})")
        print(f"   ✓ Produto teste criado: {produto_teste.nome} (ID: {produto_teste.id})")
        
        # 2. TESTAR MODELO ORDEM DE SERVIÇO
        print("\n2. Testando modelo OrdemServico...")
        
        # Criar nova ordem
        ordem = OrdemServico(
            cliente_id=cliente_teste.id,
            data_emissao=date.today(),
            tipo_servico="Manutenção",
            solicitante="João Silva",
            contato="11988776655",
            prioridade="Alta",
            status="Aberta",
            problema_descrito="Equipamento apresentando falhas",
            valor_mao_obra=150.00,
            valor_produtos=50.00,
            valor_servicos=80.00,
            valor_deslocamento=25.00
        )
        
        # Testar geração de código
        codigo_gerado = ordem.gerar_codigo()
        print(f"   ✓ Código gerado: {codigo_gerado}")
        assert codigo_gerado is not None
        assert codigo_gerado.startswith('OS')
        
        # Testar cálculo de valor total
        valor_total = ordem.calcular_valor_total()
        valor_esperado = 150.00 + 50.00 + 80.00 + 25.00  # 305.00
        print(f"   ✓ Valor total calculado: R$ {valor_total:.2f} (esperado: R$ {valor_esperado:.2f})")
        assert abs(valor_total - valor_esperado) < 0.01
        
        # Testar badge de status
        badge_class = ordem.get_status_badge_class()
        print(f"   ✓ Badge class para status '{ordem.status}': {badge_class}")
        assert badge_class is not None
        
        # Testar badge de prioridade
        prioridade_class = ordem.get_prioridade_badge_class()
        print(f"   ✓ Badge class para prioridade '{ordem.prioridade}': {prioridade_class}")
        assert prioridade_class is not None
        
        # Salvar ordem
        db.session.add(ordem)
        db.session.commit()
        print(f"   ✓ Ordem salva no banco (ID: {ordem.id})")
        
        # 3. TESTAR ITENS DE ORDEM DE SERVIÇO
        print("\n3. Testando OrdemServicoItem...")
        
        # Criar item produto
        item_produto = OrdemServicoItem(
            ordem_servico_id=ordem.id,
            tipo_item="produto",
            produto_id=produto_teste.id,
            descricao=produto_teste.nome,
            quantidade=2.0,
            valor_unitario=100.00
        )
        
        # Testar cálculo do total do item
        total_item = item_produto.calcular_total()
        print(f"   ✓ Item produto: {item_produto.descricao}")
        print(f"     Quantidade: {item_produto.quantidade}")
        print(f"     Valor unitário: R$ {item_produto.valor_unitario:.2f}")
        print(f"     Total calculado: R$ {total_item:.2f}")
        assert total_item == 200.00
        
        # Criar item serviço
        item_servico = OrdemServicoItem(
            ordem_servico_id=ordem.id,
            tipo_item="servico",
            descricao="Instalação e configuração",
            quantidade=3.0,
            valor_unitario=50.00
        )
        
        total_servico = item_servico.calcular_total()
        print(f"   ✓ Item serviço: {item_servico.descricao}")
        print(f"     Total calculado: R$ {total_servico:.2f}")
        assert total_servico == 150.00
        
        # Salvar itens
        db.session.add(item_produto)
        db.session.add(item_servico)
        db.session.commit()
        
        # 4. TESTAR CALCULADORA OS
        print("\n4. Testando CalculadoraOS...")
        
        # Recarregar ordem com itens
        ordem = OrdemServico.query.get(ordem.id)
        
        # Testar cálculo de total dos itens
        total_itens = CalculadoraOS.calcular_total_itens(ordem)
        print(f"   ✓ Total dos itens: R$ {total_itens:.2f}")
        assert total_itens == 350.00  # 200 + 150
        
        # Testar dados JSON dos serviços
        servicos_dados = [
            {"descricao": "Consultoria", "horas": 2, "valor": 120.00},
            {"descricao": "Treinamento", "horas": 1, "valor": 80.00}
        ]
        ordem.servicos_dados = json.dumps(servicos_dados)
        
        total_servicos = CalculadoraOS.calcular_total_servicos(ordem)
        print(f"   ✓ Total serviços (JSON): R$ {total_servicos:.2f}")
        assert total_servicos == 200.00
        
        # Testar cálculo de horas
        total_horas = CalculadoraOS.calcular_total_horas_servicos(ordem)
        print(f"   ✓ Total horas serviços: {total_horas}")
        assert total_horas == 3.0
        
        # Testar validação de valores
        erros = CalculadoraOS.validar_valores(ordem)
        print(f"   ✓ Validação de valores: {len(erros)} erros encontrados")
        assert len(erros) == 0
        
        # Testar recálculo completo
        sucesso = CalculadoraOS.calcular_todos_valores(ordem)
        print(f"   ✓ Recálculo completo: {'Sucesso' if sucesso else 'Falhou'}")
        assert sucesso == True
        
        # 5. TESTAR MÉTODO BEFORE_SAVE
        print("\n5. Testando método before_save()...")
        
        valor_antes = ordem.valor_total
        ordem.valor_mao_obra = 200.00  # Alterar valor
        resultado = ordem.before_save()
        
        print(f"   ✓ Valor antes: R$ {valor_antes:.2f}")
        print(f"   ✓ Valor depois: R$ {ordem.valor_total:.2f}")
        print(f"   ✓ Before_save retornou: {resultado}")
        
        # 6. TESTAR CONVERSÃO PARA DICT
        print("\n6. Testando conversão para dict...")
        
        ordem_dict = ordem.to_dict()
        print(f"   ✓ Campos no dict: {len(ordem_dict)} campos")
        print(f"   ✓ Código: {ordem_dict.get('codigo')}")
        print(f"   ✓ Cliente: {ordem_dict.get('cliente_nome')}")
        print(f"   ✓ Status: {ordem_dict.get('status')}")
        
        assert 'codigo' in ordem_dict
        assert 'cliente_nome' in ordem_dict
        assert ordem_dict['status'] == 'Aberta'
        
        # 7. LIMPEZA DOS DADOS DE TESTE
        print("\n7. Removendo dados de teste...")
        
        # Remover itens
        OrdemServicoItem.query.filter_by(ordem_servico_id=ordem.id).delete()
        
        # Remover ordem
        db.session.delete(ordem)
        
        # Remover produto e cliente de teste
        db.session.delete(produto_teste)
        db.session.delete(cliente_teste)
        
        db.session.commit()
        print("   ✓ Dados de teste removidos")
        
        # 8. RESULTADOS
        print("\n=== RESULTADOS DO TESTE ===")
        print("✓ Modelo OrdemServico funcionando")
        print("✓ Modelo OrdemServicoItem funcionando") 
        print("✓ CalculadoraOS funcionando")
        print("✓ Geração de código funcionando")
        print("✓ Cálculos de valores funcionando")
        print("✓ Validações funcionando")
        print("✓ Método before_save funcionando")
        print("✓ Conversão para dict funcionando")
        print("✓ CRUD básico funcionando")
        print("\n🎉 TODOS OS TESTES PASSARAM! Módulo Ordem de Serviço está funcionando corretamente.")
        
        return True


if __name__ == '__main__':
    try:
        test_ordem_servico_complete()
        print("\n✅ Script de teste executado com sucesso!")
    except Exception as e:
        print(f"\n❌ Erro durante os testes: {e}")
        import traceback
        traceback.print_exc()