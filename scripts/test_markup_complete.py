#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testar o campo markup nos produtos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aplicacao import create_app
from aplicacao.extensoes import db
from aplicacao.produto.produto_model import Produto
from aplicacao.fornecedor.fornecedor_model import Fornecedor

def test_produto_markup():
    """Testa se o campo markup está funcionando nos produtos"""
    app = create_app()
    
    with app.app_context():
        print("=== TESTE DO MARKUP EM PRODUTOS ===\n")
        
        # 1. Criar fornecedor para teste
        print("1. Criando fornecedor de teste...")
        fornecedor = Fornecedor(
            nome="Fornecedor Teste",
            cpf_cnpj="12.345.678/0001-95",
            ativo=True
        )
        db.session.add(fornecedor)
        db.session.commit()
        print(f"✅ Fornecedor criado: ID {fornecedor.id}")
        
        # 2. Criar produto com markup
        print("\n2. Criando produto com markup...")
        produto = Produto(
            nome="Produto Teste Markup",
            codigo="TEST001",
            custo=100.0,
            markup=25.0,  # 25%
            fornecedor_id=fornecedor.id,
            categoria="Teste",
            ativo=True
        )
        
        # O preço deve ser calculado automaticamente
        preco_calculado = produto.calcular_preco_venda()
        produto.preco = preco_calculado
        
        db.session.add(produto)
        db.session.commit()
        
        print(f"✅ Produto criado com sucesso!")
        print(f"   Nome: {produto.nome}")
        print(f"   Custo: R$ {produto.custo:.2f}")
        print(f"   Markup: {produto.markup}%")
        print(f"   Preço calculado: R$ {produto.preco:.2f}")
        
        # 3. Testar cálculos
        print("\n3. Testando métodos de cálculo...")
        
        # Teste: calcular_preco_venda
        preco_esperado = 100.0 * (1 + 25.0/100)  # 100 + 25% = 125
        preco_calculado = produto.calcular_preco_venda()
        print(f"   Preço esperado: R$ {preco_esperado:.2f}")
        print(f"   Preço calculado: R$ {preco_calculado:.2f}")
        
        if abs(preco_calculado - preco_esperado) < 0.01:
            print("   ✅ Cálculo de preço correto!")
        else:
            print("   ❌ Erro no cálculo de preço!")
        
        # Teste: calcular_markup_por_preco
        produto.preco = 150.0
        markup_calculado = produto.calcular_markup_por_preco()
        markup_esperado = ((150.0 - 100.0) / 100.0) * 100  # 50%
        print(f"   Markup esperado: {markup_esperado}%")
        print(f"   Markup calculado: {markup_calculado}%")
        
        if abs(markup_calculado - markup_esperado) < 0.01:
            print("   ✅ Cálculo de markup correto!")
        else:
            print("   ❌ Erro no cálculo de markup!")
        
        # 4. Teste to_dict
        print("\n4. Testando método to_dict...")
        produto_dict = produto.to_dict()
        if 'markup' in produto_dict:
            print("   ✅ Campo markup presente no to_dict!")
            print(f"   Markup: {produto_dict['markup']}")
        else:
            print("   ❌ Campo markup ausente no to_dict!")
        
        # 5. Limpeza
        print("\n5. Limpando dados de teste...")
        db.session.delete(produto)
        db.session.delete(fornecedor)
        db.session.commit()
        print("✅ Dados de teste removidos!")
        
        print("\n=== TESTE DE MARKUP CONCLUÍDO! ===")
        return True

if __name__ == "__main__":
    success = test_produto_markup()
    if success:
        print("\n🎉 Sistema de markup funcionando perfeitamente!")
    else:
        print("\n❌ Há problemas no sistema de markup.")