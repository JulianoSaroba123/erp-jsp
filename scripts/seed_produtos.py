#!/usr/bin/env python3
"""Script para adicionar dados de teste."""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from aplicacao.extensoes import db
from aplicacao import create_app
from aplicacao.fornecedor.fornecedor_model import Fornecedor
from aplicacao.produto.produto_model import Produto
from datetime import datetime

def adicionar_dados_teste():
    app = create_app()
    with app.app_context():
        try:
            # Adicionar fornecedores
            if not Fornecedor.query.first():
                fornecedores = [
                    Fornecedor(
                        codigo="FOR001",
                        nome="TechSupplies LTDA",
                        cnpj="12.345.678/0001-90",
                        telefone="(11) 1234-5678",
                        endereco="Rua das Tecnologias, 123",
                        cidade="São Paulo",
                        cep="01234-567"
                    ),
                    Fornecedor(
                        codigo="FOR002", 
                        nome="MegaDistribuidora S.A.",
                        cnpj="98.765.432/0001-10",
                        telefone="(21) 9876-5432",
                        endereco="Av. das Indústrias, 456",
                        cidade="Rio de Janeiro",
                        cep="20000-000"
                    ),
                    Fornecedor(
                        codigo="FOR003",
                        nome="Global Components",
                        telefone="(11) 5555-1234",
                        endereco="Rua dos Componentes, 789",
                        cidade="São Paulo",
                        cep="04567-890"
                    )
                ]
                
                for f in fornecedores:
                    db.session.add(f)
                    
                db.session.commit()
                print("✓ Fornecedores criados")
                
            # Adicionar produtos
            if not Produto.query.first():
                fornecedor1 = Fornecedor.query.filter_by(codigo="FOR001").first()
                fornecedor2 = Fornecedor.query.filter_by(codigo="FOR002").first()
                fornecedor3 = Fornecedor.query.filter_by(codigo="FOR003").first()
                
                produtos = [
                    Produto(
                        codigo="PRD001",
                        nome="Notebook Gamer RGB",
                        sku="NBG-RGB-001",
                        fornecedor_id=fornecedor1.id if fornecedor1 else None,
                        preco=2500.00,
                        custo=2000.00,
                        estoque=15,
                        unidade="UN",
                        categoria="Informática",
                        descricao="Notebook gamer com RGB e alta performance",
                        ativo=True
                    ),
                    Produto(
                        codigo="PRD002",
                        nome="Mouse Wireless Pro",
                        sku="MWP-2024",
                        fornecedor_id=fornecedor2.id if fornecedor2 else None,
                        preco=150.00,
                        custo=100.00,
                        estoque=50,
                        unidade="UN",
                        categoria="Periféricos",
                        descricao="Mouse wireless profissional de alta precisão",
                        ativo=True
                    ),
                    Produto(
                        codigo="PRD003",
                        nome="Teclado Mecânico LED",
                        sku="TML-LED-001",
                        fornecedor_id=fornecedor3.id if fornecedor3 else None,
                        preco=300.00,
                        custo=220.00,
                        estoque=25,
                        unidade="UN",
                        categoria="Periféricos",
                        descricao="Teclado mecânico com iluminação LED customizável",
                        ativo=True
                    ),
                    Produto(
                        codigo="PRD004",
                        nome="Monitor Ultrawide 34\"",
                        sku="MUW-34-2024",
                        fornecedor_id=fornecedor1.id if fornecedor1 else None,
                        preco=1200.00,
                        custo=900.00,
                        estoque=8,
                        unidade="UN",
                        categoria="Monitores",
                        descricao="Monitor ultrawide 34 polegadas para produtividade",
                        ativo=True
                    ),
                    Produto(
                        codigo="PRD005",
                        nome="Headset Gamer 7.1",
                        sku="HG-71-PRO",
                        fornecedor_id=fornecedor2.id if fornecedor2 else None,
                        preco=250.00,
                        custo=180.00,
                        estoque=30,
                        unidade="UN",
                        categoria="Áudio",
                        descricao="Headset gamer com som surround 7.1",
                        ativo=True
                    )
                ]
                
                for p in produtos:
                    db.session.add(p)
                    
                db.session.commit()
                print("✓ Produtos criados")
                
            print(f"\nTotal de fornecedores: {Fornecedor.query.count()}")
            print(f"Total de produtos: {Produto.query.count()}")
                
        except Exception as e:
            print(f"Erro ao adicionar dados: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    adicionar_dados_teste()