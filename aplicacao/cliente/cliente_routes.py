# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Routes de Cliente com APIs Completas
===================================================

Rotas para gerenciamento de clientes incluindo consultas automáticas.
CRUD completo com validações e APIs de CNPJ/CEP.

Versão: 3.0.1 - Corrigido tratamento de erros 404/500
Autor: JSP Soluções
Data: 2025
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
import requests
import re
from datetime import datetime
from sqlalchemy import inspect
from aplicacao.extensoes import db
from aplicacao.cliente.cliente_model import Cliente

# Cria o blueprint
cliente_bp = Blueprint('cliente', __name__, template_folder='templates')


def _get_clientes_column_limits():
    """Lê limites de colunas VARCHAR de clientes no banco atual."""
    limits = {}
    try:
        db_inspector = inspect(db.engine)
        for col in db_inspector.get_columns('clientes'):
            col_type = col.get('type')
            length = getattr(col_type, 'length', None)
            if isinstance(length, int) and length > 0:
                limits[col.get('name')] = length
    except Exception:
        pass

    if not limits:
        for col in Cliente.__table__.columns:
            length = getattr(col.type, 'length', None)
            if isinstance(length, int) and length > 0:
                limits[col.name] = length

    return limits


def _sanitize_text(field_name, value, limits, truncated_fields):
    if value is None:
        return None
    text_value = str(value).strip()
    if text_value == '':
        return None

    max_len = limits.get(field_name)
    if isinstance(max_len, int) and max_len > 0 and len(text_value) > max_len:
        truncated_fields.append(field_name)
        return text_value[:max_len]

    return text_value


def _safe_float(value, default_value=0.0):
    try:
        if value is None or str(value).strip() == '':
            return float(default_value)
        return float(value)
    except Exception:
        return float(default_value)


def _safe_int(value, default_value=0):
    try:
        if value is None or str(value).strip() == '':
            return int(default_value)
        return int(value)
    except Exception:
        return int(default_value)


def _flash_truncation_warning(truncated_fields):
    if not truncated_fields:
        return
    fields = ', '.join(sorted(set(truncated_fields)))
    flash(
        f'Alguns campos excediam o tamanho permitido e foram ajustados automaticamente: {fields}.',
        'warning'
    )

# Handler de erros para o blueprint
@cliente_bp.errorhandler(404)
def cliente_nao_encontrado(e):
    """Handler para erro 404 no módulo de clientes."""
    flash('Cliente não encontrado.', 'error')
    return redirect(url_for('cliente.listar'))

@cliente_bp.errorhandler(500)
def erro_interno_cliente(e):
    """Handler para erro 500 no módulo de clientes."""
    import traceback
    print(f"❌ Erro 500 no módulo cliente:")
    print(traceback.format_exc())
    flash(f'Erro interno ao processar cliente: {str(e)}', 'error')
    return redirect(url_for('cliente.listar'))

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
    
    # Debug: verificar se Cliente 11 está na lista
    cliente11_na_lista = any(c.id == 11 for c in clientes)
    print(f"DEBUG LISTAGEM: {len(clientes)} clientes encontrados")
    print(f"DEBUG: Cliente 11 na lista: {cliente11_na_lista}")
    if not cliente11_na_lista:
        cliente11_direto = Cliente.query.filter_by(id=11).first()
        if cliente11_direto:
            print(f"DEBUG: Cliente 11 existe no banco - Nome: {cliente11_direto.nome}, Ativo: {cliente11_direto.ativo}")
    
    return render_template('cliente/listar.html', clientes=clientes, busca=busca)

@cliente_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    """Cria um novo cliente."""
    if request.method == 'POST':
        print(f"\n{'='*60}")
        print(f"🆕 NOVO CLIENTE - POST RECEBIDO")
        print(f"{'='*60}")
        print(f"📋 Form data keys: {list(request.form.keys())}")
        print(f"📝 Nome: {request.form.get('nome')}")
        print(f"🏢 Tipo: {request.form.get('tipo')}")
        print(f"📄 CPF/CNPJ: {request.form.get('cpf_cnpj')}")
        print(f"{'='*60}\n")
        try:
            limits = _get_clientes_column_limits()
            truncated_fields = []
            # Validar se CPF/CNPJ já existe (incluindo clientes inativos)
            cpf_cnpj = _sanitize_text('cpf_cnpj', request.form.get('cpf_cnpj'), limits, truncated_fields)
            if cpf_cnpj:
                cliente_existente = Cliente.query.filter(
                    Cliente.cpf_cnpj == cpf_cnpj
                ).first()
                
                if cliente_existente:
                    if not cliente_existente.ativo:
                        # Cliente inativo encontrado - oferecer reativação
                        flash(f'Cliente {cliente_existente.nome} com CPF/CNPJ {cpf_cnpj} existe mas está inativo. Reativando...', 'info')
                        
                        # Reativar e atualizar dados do cliente existente
                        cliente_existente.ativo = True
                        cliente_existente.nome = _sanitize_text('nome', request.form.get('nome'), limits, truncated_fields) or cliente_existente.nome
                        cliente_existente.nome_fantasia = _sanitize_text('nome_fantasia', request.form.get('nome_fantasia'), limits, truncated_fields) or cliente_existente.nome_fantasia
                        cliente_existente.razao_social = _sanitize_text('razao_social', request.form.get('razao_social'), limits, truncated_fields) or cliente_existente.razao_social
                        cliente_existente.tipo = _sanitize_text('tipo', request.form.get('tipo'), limits, truncated_fields) or cliente_existente.tipo
                        cliente_existente.email = _sanitize_text('email', request.form.get('email'), limits, truncated_fields) or cliente_existente.email
                        cliente_existente.telefone = _sanitize_text('telefone', request.form.get('telefone'), limits, truncated_fields) or cliente_existente.telefone
                        cliente_existente.endereco = _sanitize_text('endereco', request.form.get('endereco'), limits, truncated_fields) or cliente_existente.endereco
                        cliente_existente.cidade = _sanitize_text('cidade', request.form.get('cidade'), limits, truncated_fields) or cliente_existente.cidade
                        cliente_existente.estado = _sanitize_text('estado', request.form.get('estado'), limits, truncated_fields) or cliente_existente.estado
                        cliente_existente.cep = _sanitize_text('cep', request.form.get('cep'), limits, truncated_fields) or cliente_existente.cep
                        
                        try:
                            db.session.commit()
                            _flash_truncation_warning(truncated_fields)
                            flash(f'Cliente {cliente_existente.nome} reativado e atualizado com sucesso!', 'success')
                            return redirect(url_for('cliente.listar'))
                        except Exception as e:
                            db.session.rollback()
                            flash(f'Erro ao reativar cliente: {str(e)}', 'error')
                            return render_template('cliente/form.html')
                    else:
                        # Cliente ativo - erro
                        print(f"⚠️ VALIDAÇÃO: CPF/CNPJ {cpf_cnpj} já existe (cliente ativo)")
                        flash(f'CPF/CNPJ {cpf_cnpj} já está sendo usado pelo cliente ativo: {cliente_existente.nome}', 'error')
                        # Criar objeto com dados do form para não perder
                        cliente = Cliente(**{k: v for k, v in request.form.items() if hasattr(Cliente, k)})
                        return render_template('cliente/form.html', cliente=cliente)
            
            # Validar campos obrigatórios
            tipo = (_sanitize_text('tipo', request.form.get('tipo', ''), limits, truncated_fields) or '').strip()
            nome = (_sanitize_text('nome', request.form.get('nome', ''), limits, truncated_fields) or '').strip()
            nome_fantasia = (_sanitize_text('nome_fantasia', request.form.get('nome_fantasia', ''), limits, truncated_fields) or '').strip()
            
            # Para PJ, se nome está vazio mas tem nome_fantasia, usa nome_fantasia como nome
            if tipo.upper() == 'PJ' and not nome and nome_fantasia:
                nome = nome_fantasia
                print(f"✅ PJ: Usando nome_fantasia como nome: {nome}")
            
            if not nome:
                print("⚠️ VALIDAÇÃO: Nome é obrigatório!")
                if tipo.upper() == 'PJ':
                    flash('Nome Fantasia é obrigatório para Pessoa Jurídica!', 'error')
                else:
                    flash('Nome é obrigatório!', 'error')
                # Criar objeto com dados do form para não perder
                cliente = Cliente(**{k: v for k, v in request.form.items() if hasattr(Cliente, k)})
                return render_template('cliente/form.html', cliente=cliente)
                
            if not tipo:
                print("⚠️ VALIDAÇÃO: Tipo é obrigatório!")
                flash('Tipo de cliente (PF/PJ) é obrigatório!', 'error')
                # Criar objeto com dados do form para não perder
                cliente = Cliente(**{k: v for k, v in request.form.items() if hasattr(Cliente, k)})
                return render_template('cliente/form.html', cliente=cliente)
            
            cliente = Cliente(
                # Dados principais
                nome=nome,
                nome_fantasia=_sanitize_text('nome_fantasia', request.form.get('nome_fantasia'), limits, truncated_fields),
                razao_social=_sanitize_text('razao_social', request.form.get('razao_social'), limits, truncated_fields),
                tipo=_sanitize_text('tipo', request.form.get('tipo'), limits, truncated_fields),
                
                # Documentos
                cpf_cnpj=cpf_cnpj,
                rg_ie=_sanitize_text('rg_ie', request.form.get('rg_ie'), limits, truncated_fields),
                im=_sanitize_text('im', request.form.get('im'), limits, truncated_fields),
                
                # Contato principal
                email=_sanitize_text('email', request.form.get('email'), limits, truncated_fields),
                email_financeiro=_sanitize_text('email_financeiro', request.form.get('email_financeiro'), limits, truncated_fields),
                telefone=_sanitize_text('telefone', request.form.get('telefone'), limits, truncated_fields),
                celular=_sanitize_text('celular', request.form.get('celular'), limits, truncated_fields),
                whatsapp=_sanitize_text('whatsapp', request.form.get('whatsapp'), limits, truncated_fields),
                site=_sanitize_text('site', request.form.get('site'), limits, truncated_fields),
                
                # Contato comercial
                contato_nome=_sanitize_text('contato_nome', request.form.get('contato_nome'), limits, truncated_fields),
                contato_cargo=_sanitize_text('contato_cargo', request.form.get('contato_cargo'), limits, truncated_fields),
                contato_telefone=_sanitize_text('contato_telefone', request.form.get('contato_telefone'), limits, truncated_fields),
                contato_email=_sanitize_text('contato_email', request.form.get('contato_email'), limits, truncated_fields),
                
                # Endereço
                cep=_sanitize_text('cep', request.form.get('cep'), limits, truncated_fields),
                endereco=_sanitize_text('endereco', request.form.get('endereco'), limits, truncated_fields),
                numero=_sanitize_text('numero', request.form.get('numero'), limits, truncated_fields),
                complemento=_sanitize_text('complemento', request.form.get('complemento'), limits, truncated_fields),
                bairro=_sanitize_text('bairro', request.form.get('bairro'), limits, truncated_fields),
                cidade=_sanitize_text('cidade', request.form.get('cidade'), limits, truncated_fields),
                estado=_sanitize_text('estado', request.form.get('estado'), limits, truncated_fields),
                pais=_sanitize_text('pais', request.form.get('pais'), limits, truncated_fields),
                
                # Dados comerciais
                segmento=_sanitize_text('segmento', request.form.get('segmento'), limits, truncated_fields),
                porte_empresa=_sanitize_text('porte_empresa', request.form.get('porte_empresa'), limits, truncated_fields),
                origem=_sanitize_text('origem', request.form.get('origem'), limits, truncated_fields),
                classificacao=_sanitize_text('classificacao', request.form.get('classificacao', 'A'), limits, truncated_fields),
                
                # Configurações financeiras
                limite_credito=_safe_float(request.form.get('limite_credito', 0), 0.0),
                forma_pagamento_padrao=_sanitize_text('forma_pagamento_padrao', request.form.get('forma_pagamento_padrao'), limits, truncated_fields),
                prazo_pagamento_padrao=_safe_int(request.form.get('prazo_pagamento_padrao', 30), 30),
                desconto_padrao=_safe_float(request.form.get('desconto_padrao', 0), 0.0),
                
                # Informações extras
                data_nascimento=datetime.strptime(request.form.get('data_nascimento'), '%Y-%m-%d').date() if request.form.get('data_nascimento') else None,
                data_fundacao=datetime.strptime(request.form.get('data_fundacao'), '%Y-%m-%d').date() if request.form.get('data_fundacao') else None,
                genero=_sanitize_text('genero', request.form.get('genero'), limits, truncated_fields),
                estado_civil=_sanitize_text('estado_civil', request.form.get('estado_civil'), limits, truncated_fields),
                profissao=_sanitize_text('profissao', request.form.get('profissao'), limits, truncated_fields),
                
                # Observações
                observacoes=request.form.get('observacoes'),
                observacoes_internas=request.form.get('observacoes_internas'),
                
                # Status
                status=_sanitize_text('status', request.form.get('status', 'ativo'), limits, truncated_fields),
                motivo_bloqueio=_sanitize_text('motivo_bloqueio', request.form.get('motivo_bloqueio'), limits, truncated_fields) if request.form.get('status') == 'bloqueado' else None,
                
                # Garantir que o cliente esteja ativo
                ativo=True
            )
            
            db.session.add(cliente)
            print(f"DEBUG: Cliente adicionado à sessão - Nome: {cliente.nome}, CPF/CNPJ: {cliente.cpf_cnpj}")
            
            db.session.flush()  # Força persistência antes do commit
            print(f"DEBUG: Flush executado - ID gerado: {cliente.id}")
            
            db.session.commit()
            print(f"DEBUG: Commit executado com sucesso - Cliente ID {cliente.id} salvo!")
            _flash_truncation_warning(truncated_fields)
            
            flash(f'Cliente {cliente.nome} criado com sucesso!', 'success')
            return redirect(url_for('cliente.listar'))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ ERRO ao criar cliente: {str(e)}")
            import traceback
            traceback.print_exc()
            error_msg = str(e)
            if "StringDataRightTruncation" in error_msg or "value too long for type character varying" in error_msg.lower():
                flash('Um ou mais campos ultrapassam o limite permitido pelo banco de dados. Revise os textos e tente novamente.', 'error')
            else:
                flash('Não foi possível criar o cliente. Tente novamente em instantes.', 'error')
            # Criar objeto com dados do form para não perder
            cliente = Cliente(**{k: v for k, v in request.form.items() if hasattr(Cliente, k)})
            return render_template('cliente/form.html', cliente=cliente)
    
    # GET - formulário vazio
    cliente = Cliente()
    return render_template('cliente/form.html', cliente=cliente)

@cliente_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    """Edita um cliente existente."""
    cliente = Cliente.query.filter_by(id=id).first()
    
    if cliente is None:
        flash(f'Cliente #{id} não encontrado.', 'error')
        return redirect(url_for('cliente.listar'))
    
    if request.method == 'POST':
        try:
            limits = _get_clientes_column_limits()
            truncated_fields = []
            # Validar se CPF/CNPJ já existe (exceto o próprio cliente, incluindo inativos)
            novo_cpf_cnpj = _sanitize_text('cpf_cnpj', request.form.get('cpf_cnpj'), limits, truncated_fields)
            if novo_cpf_cnpj:
                cliente_existente = Cliente.query.filter(
                    Cliente.cpf_cnpj == novo_cpf_cnpj,
                    Cliente.id != id
                ).first()
                
                if cliente_existente:
                    status_texto = "ativo" if cliente_existente.ativo else "inativo"
                    flash(f'CPF/CNPJ {novo_cpf_cnpj} já está sendo usado pelo cliente: {cliente_existente.nome} ({status_texto})', 'error')
                    return render_template('cliente/form.html', cliente=cliente)
            
            # Validar campos obrigatórios
            nome = (_sanitize_text('nome', request.form.get('nome', ''), limits, truncated_fields) or '').strip()
            tipo = (_sanitize_text('tipo', request.form.get('tipo', ''), limits, truncated_fields) or '')
            
            if not nome:
                flash('Nome é obrigatório!', 'error')
                return render_template('cliente/form.html', cliente=cliente)
                
            if not tipo:
                flash('Tipo de cliente (PF/PJ) é obrigatório!', 'error')
                return render_template('cliente/form.html', cliente=cliente)
            
            # Atualiza todos os campos do cliente
            # Dados principais
            cliente.nome = nome
            cliente.nome_fantasia = _sanitize_text('nome_fantasia', request.form.get('nome_fantasia'), limits, truncated_fields)
            cliente.razao_social = _sanitize_text('razao_social', request.form.get('razao_social'), limits, truncated_fields)
            cliente.tipo = tipo
            
            # Documentos
            cliente.cpf_cnpj = novo_cpf_cnpj
            cliente.rg_ie = _sanitize_text('rg_ie', request.form.get('rg_ie'), limits, truncated_fields)
            cliente.im = _sanitize_text('im', request.form.get('im'), limits, truncated_fields)
            
            # Contato principal
            cliente.email = _sanitize_text('email', request.form.get('email'), limits, truncated_fields)
            cliente.email_financeiro = _sanitize_text('email_financeiro', request.form.get('email_financeiro'), limits, truncated_fields)
            cliente.telefone = _sanitize_text('telefone', request.form.get('telefone'), limits, truncated_fields)
            cliente.celular = _sanitize_text('celular', request.form.get('celular'), limits, truncated_fields)
            cliente.whatsapp = _sanitize_text('whatsapp', request.form.get('whatsapp'), limits, truncated_fields)
            cliente.site = _sanitize_text('site', request.form.get('site'), limits, truncated_fields)
            
            # Contato comercial
            cliente.contato_nome = _sanitize_text('contato_nome', request.form.get('contato_nome'), limits, truncated_fields)
            cliente.contato_cargo = _sanitize_text('contato_cargo', request.form.get('contato_cargo'), limits, truncated_fields)
            cliente.contato_telefone = _sanitize_text('contato_telefone', request.form.get('contato_telefone'), limits, truncated_fields)
            cliente.contato_email = _sanitize_text('contato_email', request.form.get('contato_email'), limits, truncated_fields)
            
            # Endereço
            cliente.cep = _sanitize_text('cep', request.form.get('cep'), limits, truncated_fields)
            cliente.endereco = _sanitize_text('endereco', request.form.get('endereco'), limits, truncated_fields)
            cliente.numero = _sanitize_text('numero', request.form.get('numero'), limits, truncated_fields)
            cliente.complemento = _sanitize_text('complemento', request.form.get('complemento'), limits, truncated_fields)
            cliente.bairro = _sanitize_text('bairro', request.form.get('bairro'), limits, truncated_fields)
            cliente.cidade = _sanitize_text('cidade', request.form.get('cidade'), limits, truncated_fields)
            cliente.estado = _sanitize_text('estado', request.form.get('estado'), limits, truncated_fields)
            cliente.pais = _sanitize_text('pais', request.form.get('pais'), limits, truncated_fields)
            
            # Dados comerciais
            cliente.segmento = _sanitize_text('segmento', request.form.get('segmento'), limits, truncated_fields)
            cliente.porte_empresa = _sanitize_text('porte_empresa', request.form.get('porte_empresa'), limits, truncated_fields)
            cliente.origem = _sanitize_text('origem', request.form.get('origem'), limits, truncated_fields)
            cliente.classificacao = _sanitize_text('classificacao', request.form.get('classificacao'), limits, truncated_fields)
            
            # Configurações financeiras
            cliente.limite_credito = _safe_float(request.form.get('limite_credito', 0), 0.0)
            cliente.forma_pagamento_padrao = _sanitize_text('forma_pagamento_padrao', request.form.get('forma_pagamento_padrao'), limits, truncated_fields)
            cliente.prazo_pagamento_padrao = _safe_int(request.form.get('prazo_pagamento_padrao', 30), 30)
            cliente.desconto_padrao = _safe_float(request.form.get('desconto_padrao', 0), 0.0)
            
            # Informações extras
            if request.form.get('data_nascimento'):
                cliente.data_nascimento = datetime.strptime(request.form.get('data_nascimento'), '%Y-%m-%d').date()
            if request.form.get('data_fundacao'):
                cliente.data_fundacao = datetime.strptime(request.form.get('data_fundacao'), '%Y-%m-%d').date()
            
            cliente.genero = _sanitize_text('genero', request.form.get('genero'), limits, truncated_fields)
            cliente.estado_civil = _sanitize_text('estado_civil', request.form.get('estado_civil'), limits, truncated_fields)
            cliente.profissao = _sanitize_text('profissao', request.form.get('profissao'), limits, truncated_fields)
            
            # Observações
            cliente.observacoes = request.form.get('observacoes')
            cliente.observacoes_internas = request.form.get('observacoes_internas')
            
            # Status
            cliente.status = _sanitize_text('status', request.form.get('status'), limits, truncated_fields)
            if request.form.get('status') == 'bloqueado':
                cliente.motivo_bloqueio = _sanitize_text('motivo_bloqueio', request.form.get('motivo_bloqueio'), limits, truncated_fields)
                cliente.ativo = False  # Bloquear = inativo
            else:
                cliente.motivo_bloqueio = None
                cliente.ativo = True  # Garantir que fique ativo
            
            print(f"DEBUG: Preparando commit - Cliente ID {cliente.id}, Nome: {cliente.nome}")
            
            db.session.flush()  # Força persistência antes do commit
            print(f"DEBUG: Flush executado - Alterações aplicadas")
            
            db.session.commit()
            print(f"DEBUG: Commit executado com sucesso - Cliente ID {cliente.id} atualizado!")
            _flash_truncation_warning(truncated_fields)
            
            flash(f'Cliente {cliente.nome} atualizado com sucesso!', 'success')
            return redirect(url_for('cliente.listar'))
            
        except Exception as e:
            db.session.rollback()
            print(f"ERRO ao atualizar cliente: {str(e)}")
            import traceback
            traceback.print_exc()
            error_msg = str(e)
            if "StringDataRightTruncation" in error_msg or "value too long for type character varying" in error_msg.lower():
                flash('Um ou mais campos ultrapassam o limite permitido pelo banco de dados. Revise os textos e tente novamente.', 'error')
            else:
                flash('Não foi possível atualizar o cliente. Tente novamente em instantes.', 'error')
    
    return render_template('cliente/form.html', cliente=cliente)

@cliente_bp.route('/<int:id>')
def visualizar(id):
    """Visualiza um cliente específico."""
    cliente = Cliente.query.filter_by(id=id, ativo=True).first()
    
    if cliente is None:
        flash(f'Cliente #{id} não encontrado ou foi excluído.', 'error')
        return redirect(url_for('cliente.listar'))
    
    return render_template('cliente/visualizar.html', cliente=cliente)

@cliente_bp.route('/<int:id>/excluir', methods=['GET', 'POST'])
def excluir(id):
    """Exclui (desativa) um cliente."""
    cliente = Cliente.query.filter_by(id=id, ativo=True).first()
    
    if cliente is None:
        flash(f'Cliente #{id} não encontrado ou já foi excluído.', 'error')
        return redirect(url_for('cliente.listar'))
    
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
            print(f"Consultando CNPJ {cnpj_limpo} na ReceitaWS...")
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
                    print(f" Dados encontrados na ReceitaWS!")
                    return jsonify(resultado)
        
        except Exception as e:
            print(f"⚠️  ReceitaWS falhou: {e}")
        
        # Se chegou aqui, tenta segunda API - BrasilAPI  
        try:
            print(f"Tentando BrasilAPI...")
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
                print(f" Dados encontrados na BrasilAPI!")
                return jsonify(resultado)
                
        except Exception as e:
            print(f"⚠️  BrasilAPI falhou: {e}")
        
        # Se ambas falharam
        return jsonify({
            'success': False, 
            'error': 'CNPJ não encontrado ou serviços temporariamente indisponíveis. Tente novamente em alguns instantes.'
        }), 404
        
    except Exception as e:
        print(f" Erro geral na consulta CNPJ: {e}")
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