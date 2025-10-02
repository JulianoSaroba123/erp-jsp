#!/usr/bin/env python3

import sys
import os
from datetime import datetime

# Adicionar o diretório raiz do projeto ao sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aplicacao import app
from aplicacao.proposta.proposta_model import Proposta, PropostaItem
from aplicacao.cliente.cliente_model import Cliente
from aplicacao.extensoes import db

def debug_lista():
    """Debug da lista de propostas"""
    print("🔍 Debugando listagem de propostas...")
    
    with app.app_context():
        try:
            print("\n=== DEBUG QUERY ORIGINAL ===")
            # Query original da rota
            propostas_original = Proposta.query.filter(Proposta.data_exclusao.is_(None)).order_by(Proposta.data_criacao.desc()).all()
            print(f"Query original: {len(propostas_original)} propostas encontradas")
            
            print("\n=== DEBUG TODAS AS PROPOSTAS ===")
            # Todas as propostas (incluindo excluídas)
            todas_propostas = Proposta.query.all()
            print(f"Total no banco: {len(todas_propostas)} propostas")
            
            for proposta in todas_propostas:
                status_exclusao = "EXCLUÍDA" if proposta.data_exclusao else "ATIVA"
                print(f"  - ID: {proposta.id}, Número: {proposta.numero}, Título: {proposta.titulo}, Status: {status_exclusao}")
                if proposta.data_exclusao:
                    print(f"    Data exclusão: {proposta.data_exclusao}")
                    
            print("\n=== DEBUG FILTRO MANUAL ===")
            # Verificar manualmente o filtro
            propostas_ativas = [p for p in todas_propostas if p.data_exclusao is None]
            print(f"Filtro manual: {len(propostas_ativas)} propostas ativas")
            
            for proposta in propostas_ativas:
                print(f"  - ATIVA: ID: {proposta.id}, Número: {proposta.numero}, Título: {proposta.titulo}")
                
            print("\n=== DEBUG QUERY ALTERNATIVA ===")
            # Query alternativa
            propostas_alt = db.session.query(Proposta).filter(Proposta.data_exclusao.is_(None)).all()
            print(f"Query alternativa: {len(propostas_alt)} propostas")
            
            print("\n=== DEBUG ESTRUTURA TABELA ===")
            # Verificar estrutura da tabela
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = inspector.get_columns('propostas')
            print(f"Colunas da tabela 'propostas':")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
                
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
    
    print("🎉 Debug concluído!")

if __name__ == "__main__":
    debug_lista()