#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de teste para visualização de proposta.
Testa se todas as propriedades necessárias estão disponíveis.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.extensoes import db
from app.proposta.proposta_model import Proposta
from app.cliente.cliente_model import Cliente

def testar_proposta():
    """Testa a visualização de uma proposta."""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("🔍 TESTE DE VISUALIZAÇÃO DE PROPOSTA")
        print("=" * 60)
        
        # Buscar primeira proposta ativa
        proposta = Proposta.query.filter_by(ativo=True).first()
        
        if not proposta:
            print("\n❌ NENHUMA PROPOSTA ENCONTRADA NO BANCO!")
            print("\nCriando proposta de teste...")
            
            # Buscar ou criar cliente
            cliente = Cliente.query.filter_by(ativo=True).first()
            if not cliente:
                cliente = Cliente(
                    nome="Cliente Teste",
                    email="teste@teste.com",
                    telefone="123456789",
                    ativo=True
                )
                db.session.add(cliente)
                db.session.commit()
                print(f"✅ Cliente criado: {cliente.nome}")
            
            # Criar proposta de teste
            proposta = Proposta(
                cliente_id=cliente.id,
                titulo="Proposta de Teste",
                descricao="Proposta criada para teste de visualização",
                status="pendente",
                vendedor="Vendedor Teste",
                prioridade="normal",
                valor_total=1000.00,
                ativo=True
            )
            db.session.add(proposta)
            db.session.commit()
            print(f"✅ Proposta criada: {proposta.codigo}")
        
        print(f"\n📋 Testando Proposta: {proposta.codigo}")
        print(f"   Título: {proposta.titulo}")
        print(f"   Cliente: {proposta.cliente.nome if proposta.cliente else 'N/A'}")
        
        # Testar propriedades usadas no template
        print("\n" + "=" * 60)
        print("🔍 TESTANDO PROPRIEDADES DO TEMPLATE")
        print("=" * 60)
        
        testes = [
            ('codigo', lambda: proposta.codigo),
            ('status_formatado', lambda: proposta.status_formatado),
            ('status_cor', lambda: proposta.status_cor),
            ('prioridade_formatada', lambda: proposta.prioridade_formatada),
            ('prioridade_cor', lambda: proposta.prioridade_cor),
            ('vencida', lambda: proposta.vencida),
            ('dias_para_vencimento', lambda: proposta.dias_para_vencimento),
            ('criado_em', lambda: proposta.criado_em),
            ('valida_ate', lambda: proposta.valida_ate),
            ('pode_converter', lambda: proposta.pode_converter),
            ('valor_total', lambda: proposta.valor_total),
            ('valor_servicos', lambda: proposta.valor_servicos),
            ('valor_produtos', lambda: proposta.valor_produtos),
            ('condicao_pagamento', lambda: proposta.condicao_pagamento),
            ('forma_pagamento', lambda: proposta.forma_pagamento),
        ]
        
        erros = []
        sucesso = 0
        
        for nome, teste in testes:
            try:
                valor = teste()
                print(f"   ✅ {nome:30s} = {valor}")
                sucesso += 1
            except Exception as e:
                print(f"   ❌ {nome:30s} - ERRO: {e}")
                erros.append((nome, e))
        
        print("\n" + "=" * 60)
        print("📊 RESULTADO DO TESTE")
        print("=" * 60)
        print(f"   ✅ Sucesso: {sucesso}/{len(testes)}")
        print(f"   ❌ Erros: {len(erros)}/{len(testes)}")
        
        if erros:
            print("\n⚠️  ERROS ENCONTRADOS:")
            for nome, erro in erros:
                print(f"   • {nome}: {erro}")
            return False
        else:
            print("\n🎉 TODOS OS TESTES PASSARAM!")
            print(f"\n✅ A proposta {proposta.codigo} pode ser visualizada sem erros.")
            return True

if __name__ == '__main__':
    resultado = testar_proposta()
    sys.exit(0 if resultado else 1)
