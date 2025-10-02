#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testar o módulo completo de fornecedores
com todos os novos campos implementados.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aplicacao import create_app
from aplicacao.extensoes import db
from aplicacao.fornecedor.fornecedor_model import Fornecedor
import datetime

def test_fornecedor_complete():
    """Testa se o modelo de fornecedor está funcionando corretamente com todos os campos"""
    app = create_app()
    
    with app.app_context():
        print("=== TESTE COMPLETO DO MODELO FORNECEDOR ===\n")
        
        # 1. Teste de criação com todos os campos
        print("1. Testando criação de fornecedor com todos os campos...")
        fornecedor = Fornecedor(
            nome="Empresa Teste Completa LTDA",
            cpf_cnpj="12.345.678/0001-95",
            email="contato@empresateste.com.br",
            telefone="(11) 99999-9999",
            endereco="Rua das Flores, 123",
            numero="123",
            complemento="Sala 456",
            bairro="Centro",
            cidade="São Paulo",
            uf="SP",
            cep="01234-567",
            pais="Brasil",
            inscricao_estadual="123.456.789.012",
            inscricao_municipal="987.654.321",
            observacoes="Fornecedor de teste completo com todos os campos",
            ativo=True,
            nome_fantasia="Empresa Teste",
            apelido="EmpTeste"
        )
        
        try:
            db.session.add(fornecedor)
            db.session.commit()
            print("✅ Fornecedor criado com sucesso!")
            print(f"   ID: {fornecedor.id}")
            print(f"   Nome: {fornecedor.nome}")
            print(f"   CNPJ: {fornecedor.cpf_cnpj}")
            print(f"   Email: {fornecedor.email}")
            print(f"   Data de cadastro: {fornecedor.data_cadastro}")
        except Exception as e:
            print(f"❌ Erro ao criar fornecedor: {e}")
            return False
        
        # 2. Teste de busca
        print("\n2. Testando busca de fornecedor...")
        fornecedor_busca = Fornecedor.query.filter_by(nome="Empresa Teste Completa LTDA").first()
        if fornecedor_busca:
            print("✅ Fornecedor encontrado!")
            print(f"   Nome Fantasia: {fornecedor_busca.nome_fantasia}")
            print(f"   Apelido: {fornecedor_busca.apelido}")
            print(f"   Status: {'Ativo' if fornecedor_busca.ativo else 'Inativo'}")
        else:
            print("❌ Fornecedor não encontrado!")
            return False
        
        # 3. Teste do método to_dict
        print("\n3. Testando método to_dict...")
        try:
            fornecedor_dict = fornecedor_busca.to_dict()
            campos_esperados = [
                'id', 'nome', 'cpf_cnpj', 'email', 'telefone', 
                'endereco', 'numero', 'complemento', 'bairro', 
                'cidade', 'uf', 'cep', 'pais', 'inscricao_estadual',
                'inscricao_municipal', 'observacoes', 'ativo', 
                'nome_fantasia', 'apelido', 'data_cadastro'
            ]
            
            campos_presentes = list(fornecedor_dict.keys())
            campos_faltando = [c for c in campos_esperados if c not in campos_presentes]
            
            if not campos_faltando:
                print("✅ Método to_dict funciona corretamente!")
                print(f"   Campos retornados: {len(campos_presentes)}")
            else:
                print(f"❌ Campos ausentes no to_dict: {campos_faltando}")
                return False
        except Exception as e:
            print(f"❌ Erro no método to_dict: {e}")
            return False
        
        # 4. Teste de atualização
        print("\n4. Testando atualização de fornecedor...")
        try:
            fornecedor_busca.telefone = "(11) 88888-8888"
            fornecedor_busca.observacoes = "Fornecedor atualizado com sucesso!"
            db.session.commit()
            print("✅ Fornecedor atualizado com sucesso!")
            print(f"   Novo telefone: {fornecedor_busca.telefone}")
        except Exception as e:
            print(f"❌ Erro ao atualizar fornecedor: {e}")
            return False
        
        # 5. Teste de limpeza (remover fornecedor de teste)
        print("\n5. Limpando dados de teste...")
        try:
            db.session.delete(fornecedor_busca)
            db.session.commit()
            print("✅ Fornecedor de teste removido com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao remover fornecedor: {e}")
            return False
        
        print("\n=== TODOS OS TESTES PASSARAM! ===")
        print("✅ O modelo de fornecedor está funcionando corretamente")
        print("✅ Todos os novos campos estão implementados")
        print("✅ Métodos de CRUD funcionam perfeitamente")
        return True

if __name__ == "__main__":
    success = test_fornecedor_complete()
    if success:
        print("\n🎉 Sistema de fornecedores pronto para uso!")
    else:
        print("\n❌ Há problemas que precisam ser corrigidos.")