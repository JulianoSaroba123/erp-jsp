#!/usr/bin/env python3
"""Script para adicionar markup aos produtos existentes."""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from aplicacao.extensoes import db
from aplicacao import create_app
from aplicacao.produto.produto_model import Produto

def atualizar_produtos_com_markup():
    app = create_app()
    with app.app_context():
        try:
            produtos = Produto.query.all()
            print(f"Encontrados {len(produtos)} produtos")
            
            for produto in produtos:
                if produto.custo and produto.preco and float(produto.custo) > 0:
                    # Calcular markup baseado no preço e custo existentes
                    markup_calculado = produto.calcular_markup_por_preco()
                    produto.markup = markup_calculado
                    print(f"{produto.nome}: Custo R$ {produto.custo}, Preço R$ {produto.preco}, Markup {markup_calculado:.1f}%")
                else:
                    # Definir markup padrão de 30%
                    produto.markup = 30.00
                    print(f"{produto.nome}: Markup padrão 30%")
            
            db.session.commit()
            print("\n✓ Produtos atualizados com markup!")
            
        except Exception as e:
            print(f"Erro ao atualizar produtos: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    atualizar_produtos_com_markup()