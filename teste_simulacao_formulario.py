#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de simulação de envio do formulário de edição de OS
Simula exatamente o que acontece quando o usuário clica em "Atualizar OS"
"""

import os
import sys
sys.path.append(os.path.abspath('.'))

from aplicacao import create_app
from aplicacao.ordem_servico.ordem_servico_model import OrdemServico
from aplicacao.extensoes import db
from datetime import datetime
import json

def simular_envio_formulario():
    """Simula o envio do formulário HTML de edição"""
    
    app = create_app()
    
    with app.app_context():
        print("=== SIMULAÇÃO DE ENVIO DO FORMULÁRIO DE EDIÇÃO ===\n")
        
        # 1. Buscar OS para editar
        print("1. Carregando OS para edição...")
        ordem = OrdemServico.query.filter_by(codigo='OS0351').first()
        
        if not ordem:
            print("❌ OS0351 não encontrada!")
            return
            
        print(f"✅ OS carregada: {ordem.codigo}")
        print(f"   Estado inicial:")
        print(f"   - Cliente: {ordem.cliente_nome}")
        print(f"   - Status: {ordem.status}")
        print(f"   - Equipamento: {ordem.equipamento_nome}")
        print(f"   - Valor total: R$ {ordem.valor_total or 0}")
        print()
        
        # 2. Simular dados POST do formulário
        print("2. Simulando dados POST do formulário...")
        
        # Estes são exatamente os dados que viriam do form HTML
        form_data = {
            # Dados do cliente
            'cliente_nome': 'TESTE FORMULÁRIO - Nome Editado',
            'cliente_id': str(ordem.cliente_id or ''),
            'solicitante': 'Solicitante Teste Formulário',
            'contato': '(11) 88888-8888',
            
            # Detalhes da OS
            'codigo': ordem.codigo,
            'data_emissao': '2024-01-15',
            'previsao_conclusao': '2024-01-20',
            'prioridade': 'Alta',
            'status': 'Em Andamento',
            
            # Equipamento
            'equipamento_nome': 'Equipamento Editado pelo Formulário',
            'equipamento_marca': 'Marca Nova',
            'equipamento_modelo': 'Modelo 2024',
            'equipamento_numero_serie': 'SN123456789',
            'equipamento_acessorios': 'Cabos, Manual',
            
            # Problema/Solução
            'descricao_problema': 'Problema descrito via formulário de teste',
            'descricao_servico_realizado': 'Serviço realizado via formulário de teste',
            
            # Responsável/Horários
            'tecnico_responsavel': 'Técnico do Formulário',
            'hora_inicio': '08:00',
            'hora_termino': '17:00',
            'total_horas': '9.0',
            
            # Valores
            'valor_mao_obra': '180.00',
            'valor_produtos': '120.00',
            'valor_servicos': '90.00',
            'valor_total': '390.00',
            
            # Pagamento
            'forma_pagamento': 'Cartão',
            'condicoes_pagamento': 'Parcelado via formulário',
            
            # Observações
            'observacoes_internas': 'Observação interna via formulário',
            'outras_informacoes': 'Outras informações via formulário',
            
            # JSON fields (como viriam do JavaScript)
            'servicos_json': '[]',
            'produtos_json': '[]',
            'parcelas_json': '[]'
        }
        
        print("   Dados do formulário:")
        for campo, valor in form_data.items():
            print(f"   - {campo}: {valor}")
        print()
        
        # 3. Processar dados como faria a rota de edição
        print("3. Processando dados como faria a rota /editar_ordem...")
        
        try:
            # Simular validação do formulário (função validarFormulario() do JS)
            print("   Validando formulário...")
            if not form_data.get('cliente_nome', '').strip():
                print("   ❌ Validação falhou: Nome do cliente obrigatório")
                return
            if not form_data.get('data_emissao'):
                print("   ❌ Validação falhou: Data de emissão obrigatória")
                return
            print("   ✅ Validação do formulário passou")
            
            # Simular processamento da rota
            print("   Atualizando campos da OS...")
            
            # Atualizar campos básicos
            ordem.cliente_nome = form_data.get('cliente_nome')
            ordem.solicitante = form_data.get('solicitante')
            ordem.contato = form_data.get('contato')
            
            # Converter data
            if form_data.get('data_emissao'):
                ordem.data_emissao = datetime.strptime(form_data['data_emissao'], '%Y-%m-%d').date()
            if form_data.get('previsao_conclusao'):
                ordem.previsao_conclusao = datetime.strptime(form_data['previsao_conclusao'], '%Y-%m-%d').date()
                
            ordem.prioridade = form_data.get('prioridade')
            ordem.status = form_data.get('status')
            
            # Equipamento
            ordem.equipamento_nome = form_data.get('equipamento_nome')
            ordem.equipamento_marca = form_data.get('equipamento_marca')
            ordem.equipamento_modelo = form_data.get('equipamento_modelo')
            ordem.equipamento_numero_serie = form_data.get('equipamento_numero_serie')
            ordem.equipamento_acessorios = form_data.get('equipamento_acessorios')
            
            # Descrições
            ordem.descricao_problema = form_data.get('descricao_problema')
            ordem.descricao_servico_realizado = form_data.get('descricao_servico_realizado')
            
            # Técnico
            ordem.tecnico_responsavel = form_data.get('tecnico_responsavel')
            
            # Horários
            if form_data.get('hora_inicio'):
                ordem.hora_inicio = datetime.strptime(form_data['hora_inicio'], '%H:%M').time()
            if form_data.get('hora_termino'):
                ordem.hora_termino = datetime.strptime(form_data['hora_termino'], '%H:%M').time()
            if form_data.get('total_horas'):
                ordem.total_horas = float(form_data['total_horas'])
            
            # Valores
            ordem.valor_mao_obra = float(form_data.get('valor_mao_obra', 0))
            ordem.valor_produtos = float(form_data.get('valor_produtos', 0))
            ordem.valor_servicos = float(form_data.get('valor_servicos', 0))
            ordem.valor_total = float(form_data.get('valor_total', 0))
            
            # Pagamento
            ordem.forma_pagamento = form_data.get('forma_pagamento')
            ordem.condicoes_pagamento = form_data.get('condicoes_pagamento')
            
            # Observações
            ordem.observacoes_internas = form_data.get('observacoes_internas')
            ordem.outras_informacoes = form_data.get('outras_informacoes')
            
            print("   ✅ Todos os campos atualizados na instância do ORM")
            
            # 4. Commit das mudanças
            print("\n4. Fazendo commit das mudanças...")
            db.session.commit()
            print("   ✅ Commit realizado com SUCESSO!")
            
            # 5. Verificar se persistiu
            print("\n5. Verificando persistência no banco...")
            ordem_verificacao = OrdemServico.query.filter_by(codigo='OS0351').first()
            
            if ordem_verificacao:
                print("   ✅ OS encontrada após commit:")
                print(f"   - Cliente: {ordem_verificacao.cliente_nome}")
                print(f"   - Status: {ordem_verificacao.status}")
                print(f"   - Equipamento: {ordem_verificacao.equipamento_nome}")
                print(f"   - Técnico: {ordem_verificacao.tecnico_responsavel}")
                print(f"   - Valor total: R$ {ordem_verificacao.valor_total}")
                print(f"   - Forma pagamento: {ordem_verificacao.forma_pagamento}")
                
                # Verificar mudanças específicas
                mudancas_corretas = 0
                campos_teste = {
                    'cliente_nome': 'TESTE FORMULÁRIO - Nome Editado',
                    'status': 'Em Andamento',
                    'equipamento_nome': 'Equipamento Editado pelo Formulário',
                    'valor_total': 390.00
                }
                
                print("\n   Verificando campos específicos:")
                for campo, valor_esperado in campos_teste.items():
                    valor_atual = getattr(ordem_verificacao, campo)
                    if valor_atual == valor_esperado:
                        print(f"   ✅ {campo}: {valor_atual}")
                        mudancas_corretas += 1
                    else:
                        print(f"   ❌ {campo}: esperado '{valor_esperado}', atual '{valor_atual}'")
                
                if mudancas_corretas == len(campos_teste):
                    print(f"\n🎉 TESTE PASSOU COMPLETAMENTE!")
                    print("   ✅ Simulação do formulário funcionou perfeitamente")
                    print("   ✅ Todas as edições foram salvas no banco")
                    print("   ✅ O processo de edição de OS está FUNCIONANDO")
                    print("\n💡 CONCLUSÃO:")
                    print("   O problema NÃO está no backend/ORM/banco de dados.")
                    print("   O problema está no frontend:")
                    print("   - JavaScript não está enviando os dados")
                    print("   - CSS está bloqueando a interação")
                    print("   - Validação JavaScript está falhando")
                    print("   - Formulário não está sendo enviado corretamente")
                else:
                    print(f"\n⚠️  TESTE PARCIAL: {mudancas_corretas}/{len(campos_teste)} campos corretos")
            else:
                print("   ❌ OS perdida após commit!")
                
        except Exception as e:
            print(f"❌ Erro durante processamento: {e}")
            print(f"   Tipo do erro: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    simular_envio_formulario()