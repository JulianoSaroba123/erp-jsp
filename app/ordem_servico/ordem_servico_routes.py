# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Routes de Ordem de Serviço
=========================================

Rotas para gerenciamento de ordens de serviço.
CRUD completo com controle de status.

Autor: JSP Soluções
Data: 2025
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, make_response
from app.extensoes import db
from app.ordem_servico.ordem_servico_model import (
    OrdemServico, OrdemServicoItem, OrdemServicoProduto, OrdemServicoParcela, OrdemServicoAnexo
)
from app.cliente.cliente_model import Cliente
from app.produto.produto_model import Produto
from decimal import Decimal
import decimal
import os
from datetime import datetime, time, date
from werkzeug.utils import secure_filename
import uuid

# Configurações de upload
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads', 'ordem_servico', 'anexos')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size(file):
    """Obtém o tamanho do arquivo"""
    file.seek(0, 2)  # Move para o final
    size = file.tell()
    file.seek(0)  # Volta para o início
    return size

def generate_unique_filename(original_filename):
    """Gera nome único para o arquivo"""
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    unique_name = str(uuid.uuid4())
    return f"{unique_name}.{ext}" if ext else unique_name

# Função auxiliar para conversão segura de inteiros
def safe_int_convert(value, default=None):
    """
    Converte string para int de forma segura.
    
    Args:
        value: Valor a ser convertido
        default: Valor padrão se conversão falhar
        
    Returns:
        int ou None/default
    """
    if not value:
        return default
        
    if isinstance(value, str):
        value = value.strip()
        if not value or not value.isdigit():
            return default
    
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_decimal_convert(value, default=0):
    """
    Converte string para Decimal de forma segura.
    
    Args:
        value: Valor a ser convertido  
        default: Valor padrão se conversão falhar
        
    Returns:
        Decimal
    """
    if not value or (isinstance(value, str) and value.strip() == ''):
        return Decimal(str(default))
        
    try:
        # Remove formatação brasileira e caracteres inválidos
        clean_value = str(value).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
        if clean_value == '' or clean_value == '.':
            return Decimal(str(default))
        return Decimal(clean_value)
    except (ValueError, TypeError, decimal.InvalidOperation):
        return Decimal(str(default))

from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import re
import os
import uuid
from datetime import datetime, date, time
import tempfile
import base64

# Cria o blueprint
ordem_servico_bp = Blueprint('ordem_servico', __name__, template_folder='templates')

# Configurações de upload
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'app', 'static', 'uploads')
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar'
}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def get_logo_base64():
    """Retorna a logo JSP.jpg em base64 para o PDF"""
    try:
        # Caminho para a logo JSP
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'img', 'JSP.jpg')
        
        # Lê o arquivo da imagem e converte para base64
        with open(logo_path, 'rb') as img_file:
            img_data = img_file.read()
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            return f"data:image/jpeg;base64,{img_base64}"
    except FileNotFoundError:
        # Fallback para SVG se a imagem não for encontrada
        svg_logo = '''<svg width="120" height="60" viewBox="0 0 120 60" xmlns="http://www.w3.org/2000/svg">
            <rect width="120" height="60" fill="#002755" rx="5"/>
            <text x="60" y="20" font-family="Arial, sans-serif" font-size="16" font-weight="bold" text-anchor="middle" fill="#f49d16">JSP</text>
            <text x="60" y="40" font-family="Arial, sans-serif" font-size="10" text-anchor="middle" fill="white">SOLUÇÕES</text>
            <text x="60" y="52" font-family="Arial, sans-serif" font-size="8" text-anchor="middle" fill="#f49d16">TECNOLÓGICAS</text>
        </svg>'''
        svg_base64 = base64.b64encode(svg_logo.encode('utf-8')).decode('utf-8')
        return f"data:image/svg+xml;base64,{svg_base64}"

def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size(file):
    """Obtém o tamanho do arquivo em bytes."""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size

def generate_unique_filename(filename):
    """Gera um nome único para o arquivo."""
    name, ext = os.path.splitext(secure_filename(filename))
    unique_name = f"{uuid.uuid4().hex}_{name}{ext}"
    return unique_name

@ordem_servico_bp.route('/')
@ordem_servico_bp.route('/listar')
def listar():
    """
    Lista todas as ordens de serviço ativas.
    
    Suporte para busca por número, cliente ou status.
    """
    # Parâmetros de busca
    busca = request.args.get('busca', '').strip()
    status = request.args.get('status', '').strip()
    prioridade = request.args.get('prioridade', '').strip()
    cliente_id = request.args.get('cliente_id', '').strip()
    
    # Query base
    query = OrdemServico.query.filter_by(ativo=True)
    
    # Aplica filtros se houver busca
    if busca:
        # Busca em múltiplos campos
        query = query.join(Cliente).filter(
            db.or_(
                OrdemServico.numero.ilike(f'%{busca}%'),
                OrdemServico.titulo.ilike(f'%{busca}%'),
                OrdemServico.equipamento.ilike(f'%{busca}%'),
                Cliente.nome.ilike(f'%{busca}%')
            )
        )
    
    # Filtro por status
    if status:
        query = query.filter(OrdemServico.status == status)
    
    # Filtro por prioridade
    if prioridade:
        query = query.filter(OrdemServico.prioridade == prioridade)
    
    # Filtro por cliente
    if cliente_id:
        try:
            query = query.filter(OrdemServico.cliente_id == int(cliente_id))
        except ValueError:
            pass
    
    # Ordena por data de abertura (mais recentes primeiro)
    ordens = query.order_by(OrdemServico.data_abertura.desc()).all()
    
    # Lista de clientes para filtro
    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
    
    # Estatísticas
    stats = OrdemServico.estatisticas_dashboard()
    
    return render_template('os/listar.html', 
                         ordens=ordens, 
                         clientes=clientes,
                         stats=stats,
                         busca=busca,
                         status_filtro=status,
                         prioridade_filtro=prioridade,
                         cliente_filtro=cliente_id)

@ordem_servico_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    """
    Cria uma nova ordem de serviço.
    
    GET: Exibe formulário
    POST: Processa criação
    """
    if request.method == 'POST':
        try:
            # Converte valores
            valor_servico = safe_decimal_convert(request.form.get('valor_servico', '0'), 0)
            valor_pecas = safe_decimal_convert(request.form.get('valor_pecas', '0'), 0)
            valor_desconto = safe_decimal_convert(request.form.get('valor_desconto', '0'), 0)
            
            # Converte datas
            data_prevista = None
            if request.form.get('data_prevista'):
                data_prevista = datetime.strptime(request.form.get('data_prevista'), '%Y-%m-%d').date()
            
            # Converte horas
            hora_inicial = None
            hora_final = None
            
            if request.form.get('hora_inicial'):
                hora_inicial = datetime.strptime(request.form.get('hora_inicial'), '%H:%M').time()
            if request.form.get('hora_final'):
                hora_final = datetime.strptime(request.form.get('hora_final'), '%H:%M').time()
            
            # Cria ordem de serviço
            ordem = OrdemServico(
                numero=OrdemServico.gerar_proximo_numero(),
                cliente_id=int(request.form.get('cliente_id')),
                titulo=request.form.get('titulo', '').strip(),
                descricao=request.form.get('descricao', '').strip(),
                observacoes=request.form.get('observacoes', '').strip(),
                # Novos campos de solicitação
                solicitante=request.form.get('solicitante', '').strip(),
                descricao_problema=request.form.get('descricao_problema', '').strip(),
                status=request.form.get('status', 'aberta'),
                prioridade=request.form.get('prioridade', 'normal'),
                data_prevista=data_prevista,
                tecnico_responsavel=request.form.get('tecnico_responsavel', '').strip(),
                valor_servico=Decimal(valor_servico) if valor_servico else 0,
                valor_pecas=Decimal(valor_pecas) if valor_pecas else 0,
                valor_desconto=Decimal(valor_desconto) if valor_desconto else 0,
                prazo_garantia=int(request.form.get('prazo_garantia', 0)),
                equipamento=request.form.get('equipamento', '').strip(),
                marca_modelo=request.form.get('marca_modelo', '').strip(),
                numero_serie=request.form.get('numero_serie', '').strip(),
                defeito_relatado=request.form.get('defeito_relatado', '').strip(),
                diagnostico=request.form.get('diagnostico', '').strip(),
                solucao=request.form.get('solucao', '').strip(),
                # Novos campos - Tratamento seguro
                km_inicial=safe_int_convert(request.form.get('km_inicial', '')),
                km_final=safe_int_convert(request.form.get('km_final', '')),
                hora_inicial=hora_inicial,
                hora_final=hora_final,
                condicao_pagamento=request.form.get('condicao_pagamento', 'a_vista'),
                numero_parcelas=safe_int_convert(request.form.get('numero_parcelas', '1'), default=1),
                # Novos campos para anexos e descrição de pagamento
                descricao_pagamento=request.form.get('descricao_pagamento', '').strip(),
                observacoes_anexos=request.form.get('observacoes_anexos', '').strip()
            )
            
            # Validações
            if not ordem.titulo:
                flash('Título é obrigatório!', 'error')
                clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
                numero_os = OrdemServico.gerar_proximo_numero()
                return render_template('os/form.html', ordem=None, clientes=clientes, numero_os=numero_os, today=date.today())
            
            if not ordem.cliente_id:
                flash('Cliente é obrigatório!', 'error')
                clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
                numero_os = OrdemServico.gerar_proximo_numero()
                return render_template('os/form.html', ordem=None, clientes=clientes, numero_os=numero_os, today=date.today())
            
            # Salva ordem
            ordem.save()
            
            # Processa itens de serviço
            servicos_desc = request.form.getlist('servico_descricao[]')
            servicos_horas = request.form.getlist('servico_horas[]')
            servicos_valor = request.form.getlist('servico_valor[]')
            
            for i, desc in enumerate(servicos_desc):
                if desc.strip():
                    item = OrdemServicoItem(
                        ordem_servico_id=ordem.id,
                        descricao=desc.strip(),
                        quantidade_horas=Decimal(servicos_horas[i].replace(',', '.')) if i < len(servicos_horas) and servicos_horas[i] else 0,
                        valor_hora=Decimal(servicos_valor[i].replace(',', '.')) if i < len(servicos_valor) and servicos_valor[i] else 0
                    )
                    item.calcular_total()
                    item.save()
            
            # Processa produtos utilizados
            produtos_desc = request.form.getlist('produto_descricao[]')
            produtos_qtd = request.form.getlist('produto_quantidade[]')
            produtos_valor = request.form.getlist('produto_valor[]')
            
            for i, desc in enumerate(produtos_desc):
                if desc.strip():
                    produto = OrdemServicoProduto(
                        ordem_servico_id=ordem.id,
                        descricao=desc.strip(),
                        quantidade=Decimal(produtos_qtd[i].replace(',', '.')) if i < len(produtos_qtd) and produtos_qtd[i] else 1,
                        valor_unitario=Decimal(produtos_valor[i].replace(',', '.')) if i < len(produtos_valor) and produtos_valor[i] else 0
                    )
                    produto.calcular_total()
                    produto.save()
            
            # Processa parcelas se parcelado
            if ordem.condicao_pagamento == 'parcelado' and ordem.numero_parcelas > 1:
                valor_parcela = ordem.valor_total / ordem.numero_parcelas
                data_primeira = date.today()
                
                for i in range(ordem.numero_parcelas):
                    parcela = OrdemServicoParcela(
                        ordem_servico_id=ordem.id,
                        numero_parcela=i + 1,
                        data_vencimento=data_primeira.replace(month=data_primeira.month + i) if data_primeira.month + i <= 12 else data_primeira.replace(year=data_primeira.year + 1, month=(data_primeira.month + i) - 12),
                        valor=Decimal(str(valor_parcela))
                    )
                    parcela.save()
            
            # Processa arquivos anexados
            if 'anexos' in request.files:
                files = request.files.getlist('anexos')
                for file in files:
                    if file and file.filename and allowed_file(file.filename):
                        try:
                            # Verifica tamanho
                            if get_file_size(file) > MAX_FILE_SIZE:
                                flash(f'Arquivo {file.filename} é muito grande (máximo 16MB)', 'warning')
                                continue
                                
                            # Gera nome único
                            filename = generate_unique_filename(file.filename)
                            filepath = os.path.join(UPLOAD_FOLDER, filename)
                            
                            # Cria diretório se não existe
                            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                            
                            # Salva arquivo
                            file.save(filepath)
                            
                            # Cria registro no banco
                            anexo = OrdemServicoAnexo(
                                ordem_servico_id=ordem.id,
                                nome_original=file.filename,
                                nome_arquivo=filename,
                                tipo_arquivo=file.content_type or 'application/octet-stream',
                                tamanho=get_file_size(file)
                            )
                            anexo.save()
                            
                        except Exception as e:
                            flash(f'Erro ao salvar arquivo {file.filename}: {str(e)}', 'warning')
                    elif file and file.filename and not allowed_file(file.filename):
                        flash(f'Tipo de arquivo não permitido: {file.filename}', 'warning')
            
            # Recalcula valor total considerando itens
            ordem.valor_total = ordem.valor_total_calculado_novo
            ordem.save()
            
            flash(f'Ordem de Serviço "{ordem.numero}" criada com sucesso!', 'success')
            return redirect(url_for('ordem_servico.visualizar', id=ordem.id))
            
        except Exception as e:
            flash(f'Erro ao criar ordem de serviço: {str(e)}', 'error')
            clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
            numero_os = OrdemServico.gerar_proximo_numero()
            return render_template('os/form.html', ordem=None, clientes=clientes, numero_os=numero_os, today=date.today())
    
    # GET - exibe formulário vazio
    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
    numero_os = OrdemServico.gerar_proximo_numero()
    return render_template('os/form.html', ordem=None, clientes=clientes, numero_os=numero_os, today=date.today())

@ordem_servico_bp.route('/<int:id>')
def visualizar(id):
    """
    Visualiza detalhes de uma ordem de serviço.
    
    Args:
        id: ID da ordem de serviço
    """
    ordem = OrdemServico.get_by_id(id)
    if not ordem:
        flash('Ordem de serviço não encontrada!', 'error')
        return redirect(url_for('ordem_servico.listar'))
    
    return render_template('os/visualizar.html', ordem=ordem)

@ordem_servico_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    """
    Edita uma ordem de serviço existente.
    
    Args:
        id: ID da ordem de serviço
    """
    print(f"🔍 DEBUG: Iniciando edição para ID {id}")
    
    ordem = OrdemServico.get_by_id(id)
    if not ordem:
        print(f"❌ DEBUG: Ordem com ID {id} não encontrada")
        flash('Ordem de serviço não encontrada!', 'error')
        return redirect(url_for('ordem_servico.listar'))
    
    print(f"✅ DEBUG: Ordem encontrada: {ordem.numero}")
    
    if request.method == 'POST':
        try:
            print(f"🔍 DEBUG: Processando POST para ordem {id}")
            print(f"🔍 DEBUG: Form data keys: {list(request.form.keys())}")
            
            # Debug específico para serviços e produtos
            servicos_desc = request.form.getlist('servico_descricao[]')
            produtos_desc = request.form.getlist('produto_descricao[]')
            print(f"🔍 DEBUG: Serviços encontrados: {len(servicos_desc)} - {servicos_desc}")
            print(f"🔍 DEBUG: Produtos encontrados: {len(produtos_desc)} - {produtos_desc}")
            
            # Converte valores
            valor_servico = safe_decimal_convert(request.form.get('valor_servico', '0'), 0)
            valor_pecas = safe_decimal_convert(request.form.get('valor_pecas', '0'), 0)
            valor_desconto = safe_decimal_convert(request.form.get('valor_desconto', '0'), 0)
            
            # Converte datas
            data_prevista = None
            if request.form.get('data_prevista'):
                data_prevista = datetime.strptime(request.form.get('data_prevista'), '%Y-%m-%d').date()
            
            # Atualiza dados
            ordem.cliente_id = int(request.form.get('cliente_id'))
            ordem.titulo = request.form.get('titulo', '').strip()
            ordem.descricao = request.form.get('descricao', '').strip()
            ordem.observacoes = request.form.get('observacoes', '').strip()
            # Novos campos de solicitação
            ordem.solicitante = request.form.get('solicitante', '').strip()
            ordem.descricao_problema = request.form.get('descricao_problema', '').strip()
            
            # Controla mudança de status
            novo_status = request.form.get('status', 'aberta')
            if novo_status != ordem.status:
                if novo_status == 'em_andamento' and ordem.status == 'aberta':
                    ordem.data_inicio = datetime.now()
                elif novo_status == 'concluida' and ordem.status != 'concluida':
                    ordem.data_conclusao = datetime.now()
            ordem.status = novo_status
            
            ordem.prioridade = request.form.get('prioridade', 'normal')
            ordem.data_prevista = data_prevista
            ordem.tecnico_responsavel = request.form.get('tecnico_responsavel', '').strip()
            ordem.valor_servico = valor_servico
            ordem.valor_pecas = valor_pecas
            ordem.valor_desconto = valor_desconto
            ordem.prazo_garantia = int(request.form.get('prazo_garantia', 0))
            ordem.equipamento = request.form.get('equipamento', '').strip()
            ordem.marca_modelo = request.form.get('marca_modelo', '').strip()
            ordem.numero_serie = request.form.get('numero_serie', '').strip()
            ordem.defeito_relatado = request.form.get('defeito_relatado', '').strip()
            ordem.diagnostico = request.form.get('diagnostico', '').strip()
            ordem.solucao = request.form.get('solucao', '').strip()
            
            # Controle de KM e Tempo - Tratamento seguro de conversão
            ordem.km_inicial = safe_int_convert(request.form.get('km_inicial', ''))
            ordem.km_final = safe_int_convert(request.form.get('km_final', ''))
            
            # Processa horários
            hora_inicial = None
            hora_final = None
            
            if request.form.get('hora_inicial'):
                hora_inicial = datetime.strptime(request.form.get('hora_inicial'), '%H:%M').time()
            if request.form.get('hora_final'):
                hora_final = datetime.strptime(request.form.get('hora_final'), '%H:%M').time()
            
            ordem.hora_inicial = hora_inicial
            ordem.hora_final = hora_final
            
            # Condições de Pagamento
            ordem.condicao_pagamento = request.form.get('condicao_pagamento', 'a_vista')
            ordem.numero_parcelas = int(request.form.get('numero_parcelas', 1)) if request.form.get('numero_parcelas') else 1
            ordem.descricao_pagamento = request.form.get('descricao_pagamento', '').strip()
            ordem.observacoes_anexos = request.form.get('observacoes_anexos', '').strip()
            
            # Validações
            if not ordem.titulo:
                flash('Título é obrigatório!', 'error')
                clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
                return render_template('os/form.html', ordem=ordem, clientes=clientes, today=date.today())
            
            # Processa itens de serviço (CORRIGIDO - estava faltando!)
            # Remove serviços existentes para recriar
            print(f"🔍 DEBUG: Removendo {len(ordem.servicos)} serviços existentes")
            for item_existente in ordem.servicos:
                item_existente.delete()
            
            servicos_desc = request.form.getlist('servico_descricao[]')
            servicos_horas = request.form.getlist('servico_horas[]')
            servicos_valor = request.form.getlist('servico_valor[]')
            
            print(f"🔍 DEBUG: Processando {len(servicos_desc)} serviços novos")
            for i, desc in enumerate(servicos_desc):
                if desc.strip():
                    horas_value = servicos_horas[i] if i < len(servicos_horas) else ''
                    valor_value = servicos_valor[i] if i < len(servicos_valor) else ''
                    
                    print(f"  → Serviço {i+1}: {desc} | Horas: {horas_value} | Valor: {valor_value}")
                    
                    item = OrdemServicoItem(
                        ordem_servico_id=ordem.id,
                        descricao=desc.strip(),
                        quantidade_horas=safe_decimal_convert(horas_value, 0),
                        valor_hora=safe_decimal_convert(valor_value, 0)
                    )
                    item.calcular_total()
                    item.save()
                    print(f"  ✅ Serviço salvo com ID: {item.id}")
            
            # Processa produtos utilizados (CORRIGIDO - estava faltando!)
            # Remove produtos existentes para recriar
            print(f"🔍 DEBUG: Removendo {len(ordem.produtos_utilizados)} produtos existentes")
            for produto_existente in ordem.produtos_utilizados:
                produto_existente.delete()
            
            produtos_desc = request.form.getlist('produto_descricao[]')
            produtos_qtd = request.form.getlist('produto_quantidade[]')
            produtos_valor = request.form.getlist('produto_valor[]')
            
            print(f"🔍 DEBUG: Processando {len(produtos_desc)} produtos novos")
            for i, desc in enumerate(produtos_desc):
                if desc.strip():
                    qtd_value = produtos_qtd[i] if i < len(produtos_qtd) else ''
                    valor_value = produtos_valor[i] if i < len(produtos_valor) else ''
                    
                    print(f"  → Produto {i+1}: {desc} | Qtd: {qtd_value} | Valor: {valor_value}")
                    
                    produto = OrdemServicoProduto(
                        ordem_servico_id=ordem.id,
                        descricao=desc.strip(),
                        quantidade=safe_decimal_convert(qtd_value, 1),
                        valor_unitario=safe_decimal_convert(valor_value, 0)
                    )
                    produto.calcular_total()
                    produto.save()
                    print(f"  ✅ Produto salvo com ID: {produto.id}")
            
            # Calcula valor total
            ordem.valor_total = ordem.valor_total_calculado
            print(f"🧮 DEBUG: Valor total calculado: R$ {ordem.valor_total}")
            
            # Processa arquivos anexados
            if 'anexos' in request.files:
                files = request.files.getlist('anexos')
                for file in files:
                    if file and file.filename and allowed_file(file.filename):
                        try:
                            # Verifica tamanho
                            if get_file_size(file) > MAX_FILE_SIZE:
                                flash(f'Arquivo {file.filename} é muito grande (máximo 16MB)', 'warning')
                                continue
                                
                            # Gera nome único
                            filename = generate_unique_filename(file.filename)
                            filepath = os.path.join(UPLOAD_FOLDER, filename)
                            
                            # Cria diretório se não existe
                            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                            
                            # Salva arquivo
                            file.save(filepath)
                            
                            # Cria registro no banco
                            anexo = OrdemServicoAnexo(
                                ordem_servico_id=ordem.id,
                                nome_original=file.filename,
                                nome_arquivo=filename,
                                tipo_arquivo=file.content_type or 'application/octet-stream',
                                tamanho=get_file_size(file)
                            )
                            anexo.save()
                            
                        except Exception as e:
                            flash(f'Erro ao salvar arquivo {file.filename}: {str(e)}', 'warning')
                    elif file and file.filename and not allowed_file(file.filename):
                        flash(f'Tipo de arquivo não permitido: {file.filename}', 'warning')
            
            # Salva alterações
            ordem.save()
            print(f"🏁 DEBUG: Ordem de Serviço salva com sucesso! Total final: R$ {ordem.valor_total}")
            
            flash(f'Ordem de Serviço "{ordem.numero}" atualizada com sucesso!', 'success')
            return redirect(url_for('ordem_servico.visualizar', id=ordem.id))
            
        except Exception as e:
            flash(f'Erro ao atualizar ordem de serviço: {str(e)}', 'error')
            clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
            return render_template('os/form.html', ordem=ordem, clientes=clientes, today=date.today())
    
    # GET - exibe formulário preenchido
    print("🔍 DEBUG: Buscando clientes...")
    try:
        clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
        print(f"✅ DEBUG: {len(clientes)} clientes encontrados")
    except Exception as e:
        print(f"❌ DEBUG: Erro ao buscar clientes: {e}")
        clientes = []
    
    print("🔍 DEBUG: Renderizando template...")
    try:
        return render_template('os/form.html', 
                             ordem=ordem, 
                             clientes=clientes or [], 
                             today=date.today())
    except Exception as e:
        print(f"❌ DEBUG: Erro ao renderizar template: {e}")
        import traceback
        traceback.print_exc()
        raise

@ordem_servico_bp.route('/<int:id>/excluir', methods=['GET', 'POST'])
def excluir(id):
    """
    Exclui (desativa) uma ordem de serviço.
    
    Args:
        id: ID da ordem de serviço
    """
    ordem = OrdemServico.get_by_id(id)
    if not ordem:
        flash('Ordem de serviço não encontrada!', 'error')
        return redirect(url_for('ordem_servico.listar'))
    
    if request.method == 'GET':
        # Exibe página de confirmação
        return render_template('ordem_servico/confirmar_exclusao.html', ordem=ordem)
    
    try:
        # Soft delete
        ordem.delete()
        flash(f'Ordem de Serviço "{ordem.numero}" excluída com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir ordem de serviço: {str(e)}', 'error')
    
    return redirect(url_for('ordem_servico.listar'))

@ordem_servico_bp.route('/<int:id>/iniciar', methods=['POST'])
def iniciar_servico(id):
    """
    Inicia o serviço (muda status para em_andamento).
    
    Args:
        id: ID da ordem de serviço
    """
    ordem = OrdemServico.get_by_id(id)
    if not ordem:
        flash('Ordem de serviço não encontrada!', 'error')
        return redirect(url_for('ordem_servico.listar'))
    
    try:
        ordem.iniciar_servico()
        flash(f'Serviço da OS "{ordem.numero}" iniciado!', 'success')
    except Exception as e:
        flash(f'Erro ao iniciar serviço: {str(e)}', 'error')
    
    return redirect(url_for('ordem_servico.visualizar', id=id))

@ordem_servico_bp.route('/<int:id>/concluir', methods=['POST'])
def concluir_servico(id):
    """
    Conclui o serviço (muda status para concluida).
    
    Args:
        id: ID da ordem de serviço
    """
    ordem = OrdemServico.get_by_id(id)
    if not ordem:
        flash('Ordem de serviço não encontrada!', 'error')
        return redirect(url_for('ordem_servico.listar'))
    
    try:
        ordem.concluir_servico()
        flash(f'Serviço da OS "{ordem.numero}" concluído!', 'success')
    except Exception as e:
        flash(f'Erro ao concluir serviço: {str(e)}', 'error')
    
    return redirect(url_for('ordem_servico.visualizar', id=id))

@ordem_servico_bp.route('/<int:id>/cancelar', methods=['POST'])
def cancelar_servico(id):
    """
    Cancela o serviço (muda status para cancelada).
    
    Args:
        id: ID da ordem de serviço
    """
    ordem = OrdemServico.get_by_id(id)
    if not ordem:
        flash('Ordem de serviço não encontrada!', 'error')
        return redirect(url_for('ordem_servico.listar'))
    
    try:
        ordem.cancelar_servico()
        flash(f'Serviço da OS "{ordem.numero}" cancelado!', 'warning')
    except Exception as e:
        flash(f'Erro ao cancelar serviço: {str(e)}', 'error')
    
    return redirect(url_for('ordem_servico.visualizar', id=id))

@ordem_servico_bp.route('/api/buscar')
def api_buscar():
    """
    API para busca de ordens de serviço via AJAX.
    
    Parâmetros:
        q: termo de busca
        status: filtro por status
        cliente_id: filtro por cliente
    """
    try:
        termo = request.args.get('q', '').strip()
        status = request.args.get('status', '').strip()
        cliente_id = request.args.get('cliente_id', '').strip()
        
        query = OrdemServico.query.filter_by(ativo=True)
        
        if termo:
            query = query.join(Cliente).filter(
                db.or_(
                    OrdemServico.numero.ilike(f'%{termo}%'),
                    OrdemServico.titulo.ilike(f'%{termo}%'),
                    Cliente.nome.ilike(f'%{termo}%')
                )
            )
        
        if status:
            query = query.filter(OrdemServico.status == status)
        
        if cliente_id:
            query = query.filter(OrdemServico.cliente_id == int(cliente_id))
        
        ordens = query.limit(20).all()
        
        resultado = []
        for ordem in ordens:
            resultado.append({
                'id': ordem.id,
                'numero': ordem.numero,
                'titulo': ordem.titulo,
                'cliente': ordem.cliente.nome if ordem.cliente else '',
                'status': ordem.status_formatado,
                'status_cor': ordem.status_cor,
                'valor_total': f"R$ {ordem.valor_total:.2f}".replace('.', ','),
                'data_abertura': ordem.data_abertura.strftime('%d/%m/%Y')
            })
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@ordem_servico_bp.route('/anexo/<int:anexo_id>')
def baixar_anexo(anexo_id):
    """
    Serve um arquivo anexado à ordem de serviço.
    
    Args:
        anexo_id: ID do anexo
    """
    anexo = OrdemServicoAnexo.query.get_or_404(anexo_id)
    
    try:
        return send_from_directory(
            UPLOAD_FOLDER,
            anexo.nome_arquivo,
            as_attachment=True,
            download_name=anexo.nome_original
        )
    except FileNotFoundError:
        flash('Arquivo não encontrado!', 'error')
        return redirect(url_for('ordem_servico.visualizar', id=anexo.ordem_servico_id))

@ordem_servico_bp.route('/anexo/<int:anexo_id>/visualizar')
def visualizar_anexo(anexo_id):
    """
    Visualiza um arquivo anexado (para imagens principalmente).
    
    Args:
        anexo_id: ID do anexo
    """
    anexo = OrdemServicoAnexo.query.get_or_404(anexo_id)
    
    try:
        return send_from_directory(
            UPLOAD_FOLDER,
            anexo.nome_arquivo,
            as_attachment=False
        )
    except FileNotFoundError:
        flash('Arquivo não encontrado!', 'error')
        return redirect(url_for('ordem_servico.visualizar', id=anexo.ordem_servico_id))

@ordem_servico_bp.route('/anexo/<int:anexo_id>/excluir', methods=['POST'])
def excluir_anexo(anexo_id):
    """
    Exclui um anexo da ordem de serviço.
    
    Args:
        anexo_id: ID do anexo
    """
    anexo = OrdemServicoAnexo.query.get_or_404(anexo_id)
    ordem_id = anexo.ordem_servico_id
    
    try:
        # Remove arquivo físico
        filepath = os.path.join(UPLOAD_FOLDER, anexo.nome_arquivo)
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Remove registro do banco
        anexo.delete()
        
        flash('Anexo excluído com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir anexo: {str(e)}', 'error')
    
    return redirect(url_for('ordem_servico.visualizar', id=ordem_id))

@ordem_servico_bp.route('/<int:id>/anexos')
def listar_anexos(id):
    """
    Lista anexos de uma ordem de serviço em formato JSON.
    
    Args:
        id: ID da ordem de serviço
    """
    ordem = OrdemServico.query.get_or_404(id)
    anexos = OrdemServicoAnexo.query.filter_by(ordem_servico_id=id).all()
    
    resultado = []
    for anexo in anexos:
        resultado.append({
            'id': anexo.id,
            'nome_original': anexo.nome_original,
            'tipo_arquivo': anexo.tipo_arquivo,
            'tamanho': anexo.tamanho,
            'data_upload': anexo.data_upload.strftime('%d/%m/%Y %H:%M') if anexo.data_upload else ''
        })
    
    return jsonify(resultado)

@ordem_servico_bp.route('/anexo/<int:anexo_id>/download')
def download_anexo(anexo_id):
    """
    Faz download de um arquivo anexado.
    
    Args:
        anexo_id: ID do anexo
    """
    anexo = OrdemServicoAnexo.query.get_or_404(anexo_id)
    
    try:
        return send_from_directory(
            UPLOAD_FOLDER,
            anexo.nome_arquivo,
            as_attachment=True,
            download_name=anexo.nome_original
        )
    except FileNotFoundError:
        flash('Arquivo não encontrado!', 'error')
        return redirect(url_for('ordem_servico.visualizar', id=anexo.ordem_servico_id))

@ordem_servico_bp.route('/<int:id>/relatorio-pdf')
def gerar_relatorio_pdf(id):
    """
    Gera relatório em PDF da ordem de serviço.
    
    Args:
        id: ID da ordem de serviço
        
    Returns:
        PDF file: Relatório da ordem de serviço em PDF
    """
    try:
        # Busca a ordem de serviço
        ordem = OrdemServico.query.get_or_404(id)
        
        # Calcula totais se necessário
        if not ordem.valor_servico:
            total_servicos = sum(item.valor_total for item in ordem.servicos) if hasattr(ordem, 'servicos') and ordem.servicos else 0
            ordem.valor_servico = total_servicos
            
        if not ordem.valor_pecas:
            total_produtos = sum(produto.valor_total for produto in ordem.produtos) if hasattr(ordem, 'produtos') and ordem.produtos else 0
            ordem.valor_pecas = total_produtos
            
        if not ordem.valor_total:
            ordem.valor_total = (ordem.valor_servico or 0) + (ordem.valor_pecas or 0) - (ordem.valor_desconto or 0)
        
        # Importar configurações da empresa
        from app.configuracao.configuracao_utils import get_config
        config = get_config()
        
        # Renderiza o template HTML
        html_content = render_template(
            'os/pdf_ordem_servico.html',
            ordem=ordem,
            now=datetime.now,
            logo_base64=get_logo_base64(),  # Função para obter logo em base64
            config=config  # Adicionar configurações
        )
        
        # Configurações do WeasyPrint
        base_url = request.url_root
        css_string = '''
            @page {
                size: A4;
                margin: 1cm;
            }
            body {
                font-family: Arial, sans-serif;
                font-size: 12px;
                line-height: 1.4;
            }
        '''
        
        # Gera o PDF
        try:
            import weasyprint
            pdf_file = weasyprint.HTML(
                string=html_content, 
                base_url=base_url
            ).write_pdf(
                stylesheets=[weasyprint.CSS(string=css_string)]
            )
            
            # Cria resposta HTTP
            response = make_response(pdf_file)
            response.headers['Content-Type'] = 'application/pdf'
            # Headers anti-cache para forçar refresh
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            # Removendo Content-Disposition para forçar abertura inline no navegador
            
            return response
            
        except ImportError:
            # Se WeasyPrint não estiver disponível, retorna HTML
            flash('WeasyPrint não disponível. Exibindo relatório em HTML.', 'warning')
            return render_template(
                'os/relatorios/relatorio_pdf.html',
                ordem=ordem,
                now=datetime.now(),
                config=config
            )
        
        except Exception as pdf_error:
            # Se houver erro na geração do PDF, retorna HTML
            flash(f'Erro na geração PDF: {str(pdf_error)}. Exibindo relatório em HTML.', 'warning')
            return render_template(
                'os/relatorios/relatorio_pdf.html',
                ordem=ordem,
                now=datetime.now(),
                config=config
            )
        
    except Exception as e:
        flash(f'Erro ao gerar relatório PDF: {str(e)}', 'error')
        return redirect(url_for('ordem_servico.visualizar', id=id))