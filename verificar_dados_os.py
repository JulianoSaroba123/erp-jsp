#!/usr/bin/env python3
from aplicacao.extensoes import db
from aplicacao.ordem_servico.os_model import OrdemServico
from aplicacao import create_app
import json

app = create_app()

with app.app_context():
    print('Verificando dados de produtos e serviços nas OS...')
    ordens = OrdemServico.query.all()
    
    for ordem in ordens:
        print(f'\n--- OS {ordem.id}: {ordem.codigo} ---')
        
        if ordem.servicos_dados:
            try:
                servicos = json.loads(ordem.servicos_dados)
                print(f'Serviços: {len(servicos)} items')
                for i, s in enumerate(servicos[:2]):  # Mostrar apenas 2
                    print(f'  {i+1}. {s.get("nome", "N/A")} - {s.get("valor_total", 0)}')
            except:
                print('Serviços: Erro ao carregar JSON')
        else:
            print('Serviços: Nenhum dado')
            
        if ordem.produtos_dados:
            try:
                produtos = json.loads(ordem.produtos_dados)
                print(f'Produtos: {len(produtos)} items')
                for i, p in enumerate(produtos[:2]):  # Mostrar apenas 2
                    print(f'  {i+1}. {p.get("nome", "N/A")} - {p.get("valor_total", 0)}')
            except:
                print('Produtos: Erro ao carregar JSON')
        else:
            print('Produtos: Nenhum dado')