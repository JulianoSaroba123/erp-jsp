# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Routes de Cliente com APIs Completas
===================================================

Rotas para gerenciamento de clientes incluindo consultas automáticas.
CRUD completo com validações e APIs de CNPJ/CEP.

Autor: JSP Soluções
Data: 2025
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import requests
import re
from datetime import datetime
from app.extensoes import db
from app.cliente.cliente_model import Cliente

# Cria o blueprint
cliente_bp = Blueprint('cliente', __name__, template_folder='templates')

@cliente_bp.route('/')
@cliente_bp.route('/listar')
def listar():
    """Lista todos os clientes ativos."""
    busca = request.args.get('busca', '').strip()
    
    if busca:
        clientes = Cliente.query.filter(
            db.or_(
                Cliente.nome.ilike(f'%{busca}%'),
                Cliente.cpf_cnpj.ilike(f'%{busca}%')
            ),
            Cliente.ativo == True
        ).order_by(Cliente.nome).all()
    else:
        clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
    
    return render_template('cliente/listar.html', clientes=clientes, busca=busca)

@cliente_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    """Cria um novo cliente."""
    if request.method == 'POST':
        try:
            # Validar se CPF/CNPJ já existe
            cpf_cnpj = request.form.get('cpf_cnpj')
            if cpf_cnpj:
                cliente_existente = Cliente.query.filter(
                    Cliente.cpf_cnpj == cpf_cnpj,
                    Cliente.ativo == True
                ).first()
                
                if cliente_existente:
                    flash(f'CPF/CNPJ {cpf_cnpj} já está sendo usado pelo cliente: {cliente_existente.nome}', 'error')
                    return render_template('cliente/form.html')
            
            cliente = Cliente(
                # Dados principais
                nome=request.form.get('nome'),
                nome_fantasia=request.form.get('nome_fantasia'),
                razao_social=request.form.get('razao_social'),
                tipo=request.form.get('tipo'),
                
                # Documentos
                cpf_cnpj=cpf_cnpj,
                rg_ie=request.form.get('rg_ie'),
                im=request.form.get('im'),
                
                # Contato principal
                email=request.form.get('email'),
                email_financeiro=request.form.get('email_financeiro'),
                telefone=request.form.get('telefone'),
                celular=request.form.get('celular'),
                whatsapp=request.form.get('whatsapp'),
                site=request.form.get('site'),
                
                # Contato comercial
                contato_nome=request.form.get('contato_nome'),
                contato_cargo=request.form.get('contato_cargo'),
                contato_telefone=request.form.get('contato_telefone'),
                contato_email=request.form.get('contato_email'),
                
                # Endereço
                cep=request.form.get('cep'),
                endereco=request.form.get('endereco'),
                numero=request.form.get('numero'),
                complemento=request.form.get('complemento'),
                bairro=request.form.get('bairro'),
                cidade=request.form.get('cidade'),
                estado=request.form.get('estado'),
                pais=request.form.get('pais'),
                
                # Dados comerciais
                segmento=request.form.get('segmento'),
                porte_empresa=request.form.get('porte_empresa'),
                origem=request.form.get('origem'),
                classificacao=request.form.get('classificacao', 'A'),
                
                # Configurações financeiras
                limite_credito=float(request.form.get('limite_credito', 0) or 0),
                forma_pagamento_padrao=request.form.get('forma_pagamento_padrao'),
                prazo_pagamento_padrao=int(request.form.get('prazo_pagamento_padrao', 30) or 30),
                desconto_padrao=float(request.form.get('desconto_padrao', 0) or 0),
                
                # Informações extras
                data_nascimento=datetime.strptime(request.form.get('data_nascimento'), '%Y-%m-%d').date() if request.form.get('data_nascimento') else None,
                data_fundacao=datetime.strptime(request.form.get('data_fundacao'), '%Y-%m-%d').date() if request.form.get('data_fundacao') else None,
                genero=request.form.get('genero'),
                estado_civil=request.form.get('estado_civil'),
                profissao=request.form.get('profissao'),
                
                # Observações
                observacoes=request.form.get('observacoes'),
                observacoes_internas=request.form.get('observacoes_internas'),
                
                # Status
                status=request.form.get('status', 'ativo'),
                motivo_bloqueio=request.form.get('motivo_bloqueio') if request.form.get('status') == 'bloqueado' else None
            )
            
            db.session.add(cliente)
            db.session.commit()
            
            flash(f'Cliente {cliente.nome} criado com sucesso!', 'success')
            return redirect(url_for('cliente.listar'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar cliente: {str(e)}', 'error')
    
    cliente = Cliente()
    return render_template('cliente/form.html', cliente=cliente)

@cliente_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    """Edita um cliente existente."""
    cliente = Cliente.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Validar se CPF/CNPJ já existe (exceto o próprio cliente)
            novo_cpf_cnpj = request.form.get('cpf_cnpj')
            if novo_cpf_cnpj:
                cliente_existente = Cliente.query.filter(
                    Cliente.cpf_cnpj == novo_cpf_cnpj,
                    Cliente.id != id,
                    Cliente.ativo == True
                ).first()
                
                if cliente_existente:
                    flash(f'CPF/CNPJ {novo_cpf_cnpj} já está sendo usado pelo cliente: {cliente_existente.nome}', 'error')
                    return render_template('cliente/form.html', cliente=cliente)
            
            # Atualiza todos os campos do cliente
            # Dados principais
            cliente.nome = request.form.get('nome')
            cliente.nome_fantasia = request.form.get('nome_fantasia')
            cliente.razao_social = request.form.get('razao_social')
            cliente.tipo = request.form.get('tipo')
            
            # Documentos
            cliente.cpf_cnpj = novo_cpf_cnpj
            cliente.rg_ie = request.form.get('rg_ie')
            cliente.im = request.form.get('im')
            
            # Contato principal
            cliente.email = request.form.get('email')
            cliente.email_financeiro = request.form.get('email_financeiro')
            cliente.telefone = request.form.get('telefone')
            cliente.celular = request.form.get('celular')
            cliente.whatsapp = request.form.get('whatsapp')
            cliente.site = request.form.get('site')
            
            # Contato comercial
            cliente.contato_nome = request.form.get('contato_nome')
            cliente.contato_cargo = request.form.get('contato_cargo')
            cliente.contato_telefone = request.form.get('contato_telefone')
            cliente.contato_email = request.form.get('contato_email')
            
            # Endereço
            cliente.cep = request.form.get('cep')
            cliente.endereco = request.form.get('endereco')
            cliente.numero = request.form.get('numero')
            cliente.complemento = request.form.get('complemento')
            cliente.bairro = request.form.get('bairro')
            cliente.cidade = request.form.get('cidade')
            cliente.estado = request.form.get('estado')
            cliente.pais = request.form.get('pais')
            
            # Dados comerciais
            cliente.segmento = request.form.get('segmento')
            cliente.porte_empresa = request.form.get('porte_empresa')
            cliente.origem = request.form.get('origem')
            cliente.classificacao = request.form.get('classificacao')
            
            # Configurações financeiras
            cliente.limite_credito = float(request.form.get('limite_credito', 0) or 0)
            cliente.forma_pagamento_padrao = request.form.get('forma_pagamento_padrao')
            cliente.prazo_pagamento_padrao = int(request.form.get('prazo_pagamento_padrao', 30) or 30)
            cliente.desconto_padrao = float(request.form.get('desconto_padrao', 0) or 0)
            
            # Informações extras
            if request.form.get('data_nascimento'):
                cliente.data_nascimento = datetime.strptime(request.form.get('data_nascimento'), '%Y-%m-%d').date()
            if request.form.get('data_fundacao'):
                cliente.data_fundacao = datetime.strptime(request.form.get('data_fundacao'), '%Y-%m-%d').date()
            
            cliente.genero = request.form.get('genero')
            cliente.estado_civil = request.form.get('estado_civil')
            cliente.profissao = request.form.get('profissao')
            
            # Observações
            cliente.observacoes = request.form.get('observacoes')
            cliente.observacoes_internas = request.form.get('observacoes_internas')
            
            # Status
            cliente.status = request.form.get('status')
            if request.form.get('status') == 'bloqueado':
                cliente.motivo_bloqueio = request.form.get('motivo_bloqueio')
            else:
                cliente.motivo_bloqueio = None
            
            db.session.commit()
            
            flash(f'Cliente {cliente.nome} atualizado com sucesso!', 'success')
            return redirect(url_for('cliente.listar'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar cliente: {str(e)}', 'error')
    
    return render_template('cliente/form.html', cliente=cliente)

@cliente_bp.route('/<int:id>')
def visualizar(id):
    """Visualiza um cliente específico."""
    cliente = Cliente.query.get_or_404(id)
    return render_template('cliente/visualizar.html', cliente=cliente)

@cliente_bp.route('/<int:id>/excluir', methods=['GET', 'POST'])
def excluir(id):
    """Exclui (desativa) um cliente."""
    cliente = Cliente.query.get_or_404(id)
    
    if request.method == 'GET':
        # Mostrar página de confirmação
        return render_template('cliente/confirmar_exclusao.html', cliente=cliente)
    
    # POST - realizar exclusão
    try:
        cliente.ativo = False
        db.session.commit()
        
        flash(f'Cliente {cliente.nome} excluído com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir cliente: {str(e)}', 'error')
    
    return redirect(url_for('cliente.listar'))

@cliente_bp.route('/api/buscar')
def api_buscar():
    """API para busca de clientes via AJAX."""
    termo = request.args.get('q', '').strip()
    
    if not termo or len(termo) < 2:
        return jsonify([])
    
    clientes = Cliente.query.filter(
        db.or_(
            Cliente.nome.ilike(f'%{termo}%'),
            Cliente.cpf_cnpj.ilike(f'%{termo}%')
        ),
        Cliente.ativo == True
    ).limit(10).all()

    resultado = []
    for cliente in clientes:
        resultado.append({
            'id': cliente.id,
            'nome': cliente.nome,
            'documento': cliente.documento_formatado,
            'email': cliente.email or '',
            'texto': f'{cliente.nome} - {cliente.documento_formatado}'     
        })

    return jsonify(resultado)


# === NOVAS ROTAS PARA CONSULTA AUTOMÁTICA ===

@cliente_bp.route('/api/consultar-cnpj/<cnpj>')
def consultar_cnpj(cnpj):
    """Consulta dados da empresa via CNPJ usando múltiplas APIs."""
    try:
        # Remove formatação do CNPJ
        cnpj_limpo = re.sub(r'[^0-9]', '', cnpj)
        
        if len(cnpj_limpo) != 14:
            return jsonify({'success': False, 'error': 'CNPJ deve ter 14 dígitos'}), 400
        
        # Tenta primeira API - ReceitaWS
        try:
            print(f"🔍 Consultando CNPJ {cnpj_limpo} na ReceitaWS...")
            url = f'https://www.receitaws.com.br/v1/cnpj/{cnpj_limpo}'
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') != 'ERROR':
                    # Formata os dados para retornar
                    resultado = {
                        'success': True,
                        'data': {
                            'nome': data.get('nome', ''),  # Razão Social
                            'fantasia': data.get('fantasia', ''),  # Nome Fantasia
                            'cnpj': data.get('cnpj', ''),
                            'situacao': data.get('situacao', ''),
                            'email': data.get('email', ''),
                            'telefone': data.get('telefone', ''),
                            'atividade_principal': data.get('atividade_principal', [{}])[0].get('text', '') if data.get('atividade_principal') else '',
                            'endereco': {
                                'logradouro': data.get('logradouro', ''),
                                'numero': data.get('numero', ''),
                                'complemento': data.get('complemento', ''),
                                'bairro': data.get('bairro', ''),
                                'cidade': data.get('municipio', ''),
                                'uf': data.get('uf', ''),
                                'cep': data.get('cep', '')
                            }
                        }
                    }
                    print(f"✅ Dados encontrados na ReceitaWS!")
                    return jsonify(resultado)
        
        except Exception as e:
            print(f"⚠️  ReceitaWS falhou: {e}")
        
        # Se chegou aqui, tenta segunda API - BrasilAPI  
        try:
            print(f"🔍 Tentando BrasilAPI...")
            url = f'https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}'
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                resultado = {
                    'success': True,
                    'data': {
                        'nome': data.get('legal_name', ''),  # Razão Social  
                        'fantasia': data.get('trade_name', ''),  # Nome Fantasia
                        'cnpj': data.get('cnpj', ''),
                        'situacao': data.get('registration_status', ''),
                        'email': data.get('email', ''),
                        'telefone': '',  # BrasilAPI não tem telefone
                        'atividade_principal': data.get('main_activity', {}).get('text', ''),
                        'endereco': {
                            'logradouro': data.get('address', {}).get('street', ''),
                            'numero': data.get('address', {}).get('number', ''),
                            'complemento': data.get('address', {}).get('details', ''),
                            'bairro': data.get('address', {}).get('district', ''),
                            'cidade': data.get('address', {}).get('city', ''),
                            'uf': data.get('address', {}).get('state', ''),
                            'cep': data.get('address', {}).get('zip_code', '')
                        }
                    }
                }
                print(f"✅ Dados encontrados na BrasilAPI!")
                return jsonify(resultado)
                
        except Exception as e:
            print(f"⚠️  BrasilAPI falhou: {e}")
        
        # Se ambas falharam
        return jsonify({
            'success': False, 
            'error': 'CNPJ não encontrado ou serviços temporariamente indisponíveis. Tente novamente em alguns instantes.'
        }), 404
        
    except Exception as e:
        print(f"❌ Erro geral na consulta CNPJ: {e}")
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500


@cliente_bp.route('/api/consultar-cep/<cep>')
def consultar_cep(cep):
    """Consulta endereço via CEP usando a API ViaCEP."""
    try:
        # Remove formatação do CEP
        cep_limpo = re.sub(r'[^0-9]', '', cep)
        
        if len(cep_limpo) != 8:
            return jsonify({'success': False, 'error': 'CEP deve ter 8 dígitos'}), 400
        
        # Consulta API ViaCEP
        url = f'https://viacep.com.br/ws/{cep_limpo}/json/'
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return jsonify({'success': False, 'error': 'Erro ao consultar CEP'}), 500
        
        data = response.json()
        
        if data.get('erro'):
            return jsonify({'success': False, 'error': 'CEP não encontrado'}), 404
        
        # Formata os dados para retornar
        resultado = {
            'success': True,
            'data': {
                'cep': data.get('cep', ''),
                'logradouro': data.get('logradouro', ''),
                'complemento': data.get('complemento', ''),
                'bairro': data.get('bairro', ''),
                'cidade': data.get('localidade', ''),
                'uf': data.get('uf', '')
            }
        }
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500