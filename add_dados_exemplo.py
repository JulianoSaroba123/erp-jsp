#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para adicionar dados de exemplo na ordem de serviço
Para visualizar as tabelas no PDF
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.app import create_app
from app.extensoes import db
from app.ordem_servico.ordem_servico_model import OrdemServico, OrdemServicoItem, OrdemServicoProduto

def main():
    """Adiciona dados de exemplo na ordem de serviço."""
    print("📋 ADICIONANDO DADOS DE EXEMPLO PARA PDF")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        # Buscar a ordem existente
        ordem = OrdemServico.query.get(1)
        
        if not ordem:
            print("❌ Ordem de serviço não encontrada")
            return False
            
        print(f"✅ Ordem encontrada: {ordem.numero}")
        
        # Adicionar serviços de exemplo se não existirem
        if not ordem.servicos or len(ordem.servicos) == 0:
            print("📝 Adicionando serviços de exemplo...")
            
            servicos_exemplo = [
                {
                    'descricao': 'Manutenção preventiva em equipamento',
                    'horas': 2.5,
                    'valor_unitario': 80.00
                },
                {
                    'descricao': 'Limpeza e calibração de sensores',
                    'horas': 1.0,
                    'valor_unitario': 120.00
                },
                {
                    'descricao': 'Atualização de software',
                    'horas': 0.5,
                    'valor_unitario': 100.00
                }
            ]
            
            for servico_data in servicos_exemplo:
                servico = OrdemServicoItem(
                    ordem_servico_id=ordem.id,
                    descricao=servico_data['descricao'],
                    quantidade_horas=servico_data['horas'],
                    valor_hora=servico_data['valor_unitario']
                )
                db.session.add(servico)
                servico.calcular_total()
                print(f"   + {servico_data['descricao']}: {servico_data['horas']}h × R$ {servico_data['valor_unitario']:.2f}")
        
        # Adicionar produtos de exemplo se não existirem
        if not ordem.produtos_utilizados or len(ordem.produtos_utilizados) == 0:
            print("📦 Adicionando produtos de exemplo...")
            
            produtos_exemplo = [
                {
                    'descricao': 'Filtro de ar industrial',
                    'quantidade': 2,
                    'valor_unitario': 45.50
                },
                {
                    'descricao': 'Óleo lubrificante premium',
                    'quantidade': 1,
                    'valor_unitario': 89.90
                },
                {
                    'descricao': 'Kit de vedação',
                    'quantidade': 1,
                    'valor_unitario': 65.00
                }
            ]
            
            for produto_data in produtos_exemplo:
                produto = OrdemServicoProduto(
                    ordem_servico_id=ordem.id,
                    descricao=produto_data['descricao'],
                    quantidade=produto_data['quantidade'],
                    valor_unitario=produto_data['valor_unitario']
                )
                db.session.add(produto)
                print(f"   + {produto_data['descricao']}: {produto_data['quantidade']} × R$ {produto_data['valor_unitario']:.2f}")
        
        # Calcular totais
        valor_servicos = sum((s.quantidade_horas or 0) * (s.valor_hora or 0) for s in ordem.servicos) if ordem.servicos else 0
        valor_produtos = sum((p.quantidade or 0) * (p.valor_unitario or 0) for p in ordem.produtos_utilizados) if ordem.produtos_utilizados else 0
        
        # Atualizar valores na ordem
        ordem.valor_servico = valor_servicos
        ordem.valor_pecas = valor_produtos
        ordem.valor_total = valor_servicos + valor_produtos
        
        # Salvar mudanças
        try:
            db.session.commit()
            print(f"\n💰 RESUMO FINANCEIRO:")
            print(f"   Valor Serviços: R$ {valor_servicos:.2f}")
            print(f"   Valor Produtos: R$ {valor_produtos:.2f}")
            print(f"   Valor Total: R$ {ordem.valor_total:.2f}")
            print(f"\n✅ Dados salvos com sucesso!")
            print(f"📄 Acesse o PDF em: http://localhost:5009/ordem_servico/1/relatorio-pdf")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao salvar: {e}")
            return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)