#!/usr/bin/env python3
from aplicacao.extensoes import db
from aplicacao.ordem_servico.os_model import OrdemServico
from aplicacao import create_app

app = create_app()

with app.app_context():
    print('Total de OS:', OrdemServico.query.count())
    ordens = OrdemServico.query.limit(5).all()
    
    if ordens:
        for o in ordens:
            cliente_nome = o.cliente.nome if o.cliente else "N/A"
            print(f'OS {o.id}: {o.codigo} - Cliente: {cliente_nome}')
    else:
        print("Nenhuma OS encontrada.")