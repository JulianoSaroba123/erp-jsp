#!/usr/bin/env python3
"""
Verificar dados da OS0351 diretamente no banco
"""

import os
import sys
sys.path.append('.')

from aplicacao import criar_app
from aplicacao.ordem_servico.ordem_servico_model import OrdemServico

def verificar_os():
    app = criar_app()
    
    with app.app_context():
        # Buscar a OS com ID 2 (OS0351)
        os = OrdemServico.query.filter_by(id=2).first()
        
        if os:
            print(f"=== DADOS ATUAIS DA OS0351 ===")
            print(f"ID: {os.id}")
            print(f"Código: {os.codigo}")
            print(f"Cliente ID: {os.cliente_id}")
            print(f"Cliente: {os.cliente.nome if os.cliente else 'N/A'}")
            print(f"Solicitante: {os.solicitante}")
            print(f"Contato: {os.contato}")
            print(f"Status: {os.status}")
            print(f"Prioridade: {os.prioridade}")
            print(f"Tipo Serviço: {os.tipo_servico}")
            print(f"Equipamento Nome: {os.equipamento_nome}")
            print(f"Descrição Problema: {os.descricao_problema}")
            print(f"Valor Total: {os.valor_total}")
            print(f"Data Atualização: {os.data_atualizacao}")
            print(f"Ativo: {os.ativo}")
        else:
            print("OS0351 não encontrada!")

if __name__ == "__main__":
    verificar_os()