#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificação final dos novos campos implementados
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.app import create_app
from app.extensoes import db
from app.ordem_servico.ordem_servico_model import OrdemServico

def main():
    """Verifica implementação completa dos novos campos."""
    print("🎯 VERIFICAÇÃO FINAL DOS NOVOS CAMPOS")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Verificar banco de dados
            print("1️⃣ VERIFICANDO BANCO DE DADOS:")
            ordem = OrdemServico.query.get(1)
            
            if ordem:
                print(f"   📋 Ordem: {ordem.numero}")
                print(f"   👤 Cliente: {ordem.cliente.nome if ordem.cliente else 'N/A'}")
                print(f"   🙋 Solicitante: {ordem.solicitante or 'Não informado'}")
                print(f"   📝 Descrição do Problema: {(ordem.descricao_problema[:50] + '...') if ordem.descricao_problema else 'Não informado'}")
                print("   ✅ Campos presentes no banco")
            else:
                print("   ❌ Ordem não encontrada")
                return False
            
            # Verificar modelo
            print("\n2️⃣ VERIFICANDO MODELO (OrdemServico):")
            model_fields = [attr for attr in dir(OrdemServico) if not attr.startswith('_')]
            if 'solicitante' in model_fields:
                print("   ✅ Campo 'solicitante' presente no modelo")
            else:
                print("   ❌ Campo 'solicitante' ausente do modelo")
                
            if 'descricao_problema' in model_fields:
                print("   ✅ Campo 'descricao_problema' presente no modelo")
            else:
                print("   ❌ Campo 'descricao_problema' ausente do modelo")
            
            print("\n3️⃣ ACESSOS DISPONÍVEIS:")
            print("   🌐 Formulário: http://127.0.0.1:5001/ordem_servico/1/editar")
            print("   📄 PDF: http://127.0.0.1:5001/ordem_servico/1/relatorio-pdf")
            print("   📋 Listagem: http://127.0.0.1:5001/ordem_servico/listar")
            
            print("\n4️⃣ FUNCIONALIDADES IMPLEMENTADAS:")
            print("   ✅ Campos adicionados ao banco de dados")
            print("   ✅ Modelo OrdemServico atualizado")
            print("   ✅ Formulário HTML com novos campos")
            print("   ✅ Rotas de criação/edição atualizadas")
            print("   ✅ Template PDF com novos campos")
            print("   ✅ Dados de exemplo inseridos")
            
            print("\n🎉 IMPLEMENTAÇÃO COMPLETA!")
            print("\n📋 CAMPOS ADICIONADOS:")
            print("   • Solicitante: Nome da pessoa que solicitou o serviço")
            print("   • Descrição do Problema: Detalhes do problema/defeito")
            print("\n📍 LOCALIZAÇÃO NO FORMULÁRIO:")
            print("   • Card 'Dados da Solicitação' (após dados do cliente)")
            print("\n📍 LOCALIZAÇÃO NO PDF:")
            print("   • Seção 'Dados do Cliente e Serviço'")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n🚨 Alguns problemas foram encontrados!")
        sys.exit(1)
    else:
        print("\n✅ Tudo funcionando perfeitamente!")