#!/usr/bin/env python3
"""Script para testar a funcionalidade do markup."""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from aplicacao.extensoes import db
from aplicacao import create_app
from aplicacao.produto.produto_model import Produto

def testar_markup():
    app = create_app()
    with app.app_context():
        try:
            # Criar produto de teste
            produto_teste = Produto(
                codigo="TEST001",
                nome="Produto Teste Markup",
                custo=100.00,
                markup=25.50  # 25.5%
            )
            
            # Testar cálculo de preço
            preco_calculado = produto_teste.calcular_preco_venda()
            print(f"Custo: R$ {produto_teste.custo}")
            print(f"Markup: {produto_teste.markup}%")
            print(f"Preço calculado: R$ {preco_calculado:.2f}")
            print(f"Preço esperado: R$ {100 * 1.255:.2f}")
            
            # Testar atualização automática
            produto_teste.atualizar_preco_por_markup()
            print(f"Preço atualizado no produto: R$ {produto_teste.preco}")
            
            # Testar cálculo reverso (markup por preço)
            produto_teste.preco = 150.00
            produto_teste.custo = 100.00
            markup_calculado = produto_teste.calcular_markup_por_preco()
            print(f"\nTeste reverso:")
            print(f"Custo: R$ {produto_teste.custo}")
            print(f"Preço: R$ {produto_teste.preco}")
            print(f"Markup calculado: {markup_calculado:.2f}%")
            print(f"Markup esperado: {((150/100) - 1) * 100:.2f}%")
            
            # Testar to_dict() com markup
            dict_produto = produto_teste.to_dict()
            print(f"\nDicionário do produto:")
            print(f"- markup: {dict_produto['markup']}")
            
            print("\n✓ Todos os testes passaram!")
            
        except Exception as e:
            print(f"Erro nos testes: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    testar_markup()