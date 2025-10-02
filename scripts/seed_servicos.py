#!/usr/bin/env python3
"""Script para adicionar serviços de exemplo"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aplicacao import create_app
from aplicacao.extensoes import db
from aplicacao.servico.servico_model import Servico

def criar_servicos_exemplo():
    """Criar alguns serviços de exemplo"""
    app = create_app()
    
    with app.app_context():
        # Criar tabela se não existir
        db.create_all()
        print("✅ Tabelas verificadas/criadas")
        
        # Verificar se já existem serviços
        try:
            if Servico.query.count() > 0:
                print("✅ Serviços já existem no banco de dados")
                return
        except:
            print("⚠️ Tabela de serviços não existe, criando...")
            db.create_all()
        
        servicos_exemplo = [
            {
                'codigo': 'SRV0001',
                'nome': 'Instalação de Sistema',
                'descricao': 'Instalação completa de sistema operacional e softwares básicos',
                'unidade': 'H',
                'preco_custo': 50.0,
                'markup_percentual': 100.0,
                'preco_venda': 100.0,
                'valor': 100.0
            },
            {
                'codigo': 'SRV0002', 
                'nome': 'Manutenção Preventiva',
                'descricao': 'Limpeza e verificação geral do equipamento',
                'unidade': 'H',
                'preco_custo': 30.0,
                'markup_percentual': 66.67,
                'preco_venda': 50.0,
                'valor': 50.0
            },
            {
                'codigo': 'SRV0003',
                'nome': 'Recuperação de Dados',
                'descricao': 'Serviço especializado de recuperação de arquivos perdidos',
                'unidade': 'UN',
                'preco_custo': 100.0,
                'markup_percentual': 200.0,
                'preco_venda': 300.0,
                'valor': 300.0
            },
            {
                'codigo': 'SRV0004',
                'nome': 'Configuração de Rede',
                'descricao': 'Instalação e configuração de rede local',
                'unidade': 'UN',
                'preco_custo': 80.0,
                'markup_percentual': 87.5,
                'preco_venda': 150.0,
                'valor': 150.0
            },
            {
                'codigo': 'SRV0005',
                'nome': 'Consultoria Técnica',
                'descricao': 'Consultoria especializada em TI',
                'unidade': 'H',
                'preco_custo': 60.0,
                'markup_percentual': 150.0,
                'preco_venda': 150.0,
                'valor': 150.0
            }
        ]
        
        for servico_data in servicos_exemplo:
            servico = Servico(**servico_data)
            db.session.add(servico)
        
        try:
            db.session.commit()
            print(f"✅ Criados {len(servicos_exemplo)} serviços de exemplo")
            
            # Verificar se foram criados
            total = Servico.query.count()
            print(f"📊 Total de serviços no banco: {total}")
            
        except Exception as e:
            print(f"❌ Erro ao criar serviços: {e}")
            db.session.rollback()

if __name__ == '__main__':
    criar_servicos_exemplo()