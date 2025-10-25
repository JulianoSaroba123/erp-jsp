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
            cliente = Cliente(
                nome=request.form.get('nome'),
                tipo=request.form.get('tipo'),
                cpf_cnpj=request.form.get('cpf_cnpj'),
                rg_ie=request.form.get('rg_ie'),
                email=request.form.get('email'),
                telefone=request.form.get('telefone'),
                celular=request.form.get('celular'),
                cep=request.form.get('cep'),
                endereco=request.form.get('endereco'),
                numero=request.form.get('numero'),
                complemento=request.form.get('complemento'),
                bairro=request.form.get('bairro'),
                cidade=request.form.get('cidade'),
                estado=request.form.get('estado')
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
            cliente.nome = request.form.get('nome')
            cliente.tipo = request.form.get('tipo')
            cliente.cpf_cnpj = request.form.get('cpf_cnpj')
            cliente.rg_ie = request.form.get('rg_ie')
            cliente.email = request.form.get('email')
            cliente.telefone = request.form.get('telefone')
            cliente.celular = request.form.get('celular')
            cliente.cep = request.form.get('cep')
            cliente.endereco = request.form.get('endereco')
            cliente.numero = request.form.get('numero')
            cliente.complemento = request.form.get('complemento')
            cliente.bairro = request.form.get('bairro')
            cliente.cidade = request.form.get('cidade')
            cliente.estado = request.form.get('estado')
            
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
    """Consulta dados da empresa via CNPJ usando a API ReceitaWS."""
    try:
        # Remove formatação do CNPJ
        cnpj_limpo = re.sub(r'[^0-9]', '', cnpj)
        
        if len(cnpj_limpo) != 14:
            return jsonify({'success': False, 'error': 'CNPJ deve ter 14 dígitos'}), 400
        
        # Consulta API ReceitaWS
        url = f'https://www.receitaws.com.br/v1/cnpj/{cnpj_limpo}'
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return jsonify({'success': False, 'error': 'Erro ao consultar CNPJ'}), 500
        
        data = response.json()
        
        if data.get('status') == 'ERROR':
            return jsonify({'success': False, 'error': data.get('message', 'CNPJ não encontrado')}), 404
        
        # Formata os dados para retornar
        resultado = {
            'success': True,
            'data': {
                'nome': data.get('nome', ''),
                'fantasia': data.get('fantasia', ''),
                'cnpj': data.get('cnpj', ''),
                'situacao': data.get('situacao', ''),
                'email': data.get('email', ''),
                'telefone': data.get('telefone', ''),
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
        
        return jsonify(resultado)
        
    except Exception as e:
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