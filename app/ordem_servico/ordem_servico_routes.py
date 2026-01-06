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
import base64
from datetime import datetime as dt, datetime, time, date, timedelta
from werkzeug.utils import secure_filename
import uuid

# === FUNÇÃO UTILITÁRIA PARA BUSCAR CLIENTES ===
def buscar_clientes_ativos():
    """
    Função simples e confiável para buscar clientes ativos.
    Retorna APENAS clientes ativos com nome válido.
    Garante consistência entre todos os módulos.
    """
    try:
        # Busca básica e segura
        clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
        
        # Filtrar em Python para evitar problemas de SQL
        clientes_validos = []
        for cliente in clientes:
            if cliente and cliente.nome and cliente.nome.strip():
                clientes_validos.append(cliente)
        
        return clientes_validos
        
    except Exception as e:
        print(f"❌ ERRO na busca de clientes: {e}")
        return []

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
        s = str(value).strip()
        # Remove currency symbol and spaces
        s = s.replace('R$', '').replace(' ', '')

        # Se contém vírgula, assumimos formato brasileiro: pontos como milhares e vírgula como decimal
        if ',' in s:
            # Remover pontos (separadores de milhares) e trocar vírgula por ponto
            clean_value = s.replace('.', '').replace(',', '.')
        else:
            # Não há vírgula. Pode ser `1.23` (ponto decimal) ou `1.000` (milhares) dependendo do contexto.
            # Neste caso, NÃO removemos pontos automaticamente — assumimos que ponto é separador decimal.
            clean_value = s

        if clean_value == '' or clean_value == '.':
            return Decimal(str(default))
        return Decimal(clean_value)
    except (ValueError, TypeError, decimal.InvalidOperation):
        return Decimal(str(default))

from werkzeug.utils import secure_filename
import re
import os
import uuid
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
    """Retorna o logo configurado no sistema em base64 para o PDF"""
    try:
        from app.configuracao.configuracao_model import Configuracao
        import base64
        
        # Busca a configuração do sistema
        config = Configuracao.get_solo()
        
        # Se há logo em base64 armazenado no banco (para cloud/Render), usa ele primeiro
        if config and config.logo_base64:
            return config.logo_base64
        
        # Se há logo configurado como arquivo, usa ele
        if config and config.logo:
            # Verifica se é caminho absoluto ou relativo
            if os.path.isabs(config.logo):
                logo_path = config.logo
            else:
                # Caminho relativo ao diretório static
                logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'uploads', config.logo)
            
            # Lê o arquivo da imagem e converte para base64
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as img_file:
                    img_data = img_file.read()
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    # Detecta o tipo da imagem pela extensão
                    ext = os.path.splitext(logo_path)[1].lower()
                    if ext in ['.jpg', '.jpeg']:
                        return img_base64
                    elif ext in ['.png']:
                        return img_base64
                    elif ext in ['.gif']:
                        return img_base64
                    else:
                        return img_base64
        
        # Fallback: tenta usar a logo padrão JSP.jpg
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'img', 'JSP.jpg')
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as img_file:
                img_data = img_file.read()
                img_base64 = base64.b64encode(img_data).decode('utf-8')
                return img_base64
                
    except Exception as e:
        print(f"Erro ao carregar logo: {e}")
    
    # Fallback final: SVG padrão
    svg_logo = '''<svg width="80" height="80" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
        <rect width="80" height="80" fill="#007bff" rx="8"/>
        <text x="40" y="30" font-family="Arial, sans-serif" font-size="16" font-weight="bold" text-anchor="middle" fill="white">JSP</text>
        <text x="40" y="50" font-family="Arial, sans-serif" font-size="10" text-anchor="middle" fill="white">ELÉTRICA</text>
        <text x="40" y="65" font-family="Arial, sans-serif" font-size="8" text-anchor="middle" fill="white">INDUSTRIAL</text>
    </svg>'''
    svg_base64 = base64.b64encode(svg_logo.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{svg_base64}"

@ordem_servico_bp.route('/teste_os')
def teste_os():
    """Endpoint de teste para verificar se as OS estão acessíveis"""
    from app.ordem_servico.ordem_servico_model import OrdemServico
    
    todas = OrdemServico.query.all()
    ativas = OrdemServico.query.filter_by(ativo=True).all()
    
    resultado = {
        'total_os': len(todas),
        'os_ativas': len(ativas),
        'lista_os': [{'numero': os.numero, 'titulo': os.titulo, 'ativo': os.ativo} for os in todas]
    }
    
    return jsonify(resultado)

@ordem_servico_bp.route('/debug_banco')
def debug_banco():
    """🔍 Endpoint de DEBUG - Verifica banco de dados"""
    from sqlalchemy import text, inspect
    from app.extensoes import db
    import os
    
    resultado = {
        'status': 'iniciando',
        'erros': [],
        'dados': {}
    }
    
    try:
        # 1. Conexão
        resultado['dados']['database_url_exists'] = bool(os.getenv('DATABASE_URL'))
        resultado['dados']['sqlalchemy_uri'] = str(db.engine.url)[:80]
        
        # 2. Tabelas
        inspector = inspect(db.engine)
        tabelas = inspector.get_table_names()
        resultado['dados']['total_tabelas'] = len(tabelas)
        resultado['dados']['ordem_servico_existe'] = 'ordem_servico' in tabelas
        resultado['dados']['lista_tabelas'] = tabelas
        
        # 3. Schema
        try:
            schema_result = db.session.execute(text("SELECT current_schema()"))
            resultado['dados']['schema_atual'] = schema_result.scalar()
        except:
            resultado['dados']['schema_atual'] = 'N/A (SQLite)'
        
        # 4. Query SQL direta
        sql_result = db.session.execute(text("SELECT COUNT(*) FROM ordem_servico"))
        resultado['dados']['count_sql'] = sql_result.scalar()
        
        # 4.1 Status SQL direta
        sql_status = db.session.execute(text("SELECT status, COUNT(*) FROM ordem_servico GROUP BY status"))
        resultado['dados']['status_sql'] = {row[0]: row[1] for row in sql_status.fetchall()}
        
        # 4.2 Campo ativo SQL direta
        sql_ativo = db.session.execute(text("SELECT ativo, COUNT(*) FROM ordem_servico GROUP BY ativo"))
        resultado['dados']['ativo_sql'] = {str(row[0]): row[1] for row in sql_ativo.fetchall()}
        
        if resultado['dados']['count_sql'] > 0:
            sql_result2 = db.session.execute(text("SELECT id, numero, titulo, status, ativo FROM ordem_servico LIMIT 5"))
            resultado['dados']['primeiras_os_sql'] = [
                {'id': row[0], 'numero': row[1], 'titulo': row[2], 'status': row[3], 'ativo': row[4]} 
                for row in sql_result2.fetchall()
            ]
        
        # 5. Query ORM
        total_orm = OrdemServico.query.count()
        total_orm_ativas = OrdemServico.query.filter(OrdemServico.ativo == True).count()
        resultado['dados']['count_orm'] = total_orm
        resultado['dados']['count_orm_ativas'] = total_orm_ativas
        resultado['dados']['model_tablename'] = OrdemServico.__tablename__
        
        if total_orm > 0:
            primeiras_orm = OrdemServico.query.limit(5).all()
            resultado['dados']['primeiras_os_orm'] = [
                {'id': os.id, 'numero': os.numero, 'titulo': os.titulo, 'status': os.status, 'ativo': os.ativo}
                for os in primeiras_orm
            ]
        
        resultado['status'] = 'sucesso'
        
    except Exception as e:
        resultado['status'] = 'erro'
        resultado['erros'].append(str(e))
        import traceback
        resultado['traceback'] = traceback.format_exc()
    
    return jsonify(resultado)

@ordem_servico_bp.route('/')
@ordem_servico_bp.route('/listar')
def listar():
    """
    Lista todas as ordens de serviço ativas.
    
    Suporte para busca por número, cliente ou status.
    """
    # DEBUG: Log de início
    print("=" * 80)
    print("🔍 DEBUG ROTA /listar")
    print("=" * 80)
    
    # DEBUG: Verificar TODAS as OS no banco
    total_os = OrdemServico.query.count()
    print(f"🔍 Total de OS no banco (SEM filtro): {total_os}")
    
    if total_os > 0:
        print(f"🔍 Primeiras 5 OS no banco:")
        primeiras = OrdemServico.query.limit(5).all()
        for os in primeiras:
            print(f"   ID={os.id}, numero={os.numero}, ativo={os.ativo} (tipo: {type(os.ativo)}), titulo={os.titulo}")
    
    # Parâmetros de busca
    busca = request.args.get('busca', '').strip()
    status = request.args.get('status', '').strip()
    prioridade = request.args.get('prioridade', '').strip()
    cliente_id = request.args.get('cliente_id', '').strip()
    
    print(f"\n📊 Parâmetros recebidos:")
    print(f"   busca: '{busca}'")
    print(f"   status: '{status}'")
    print(f"   prioridade: '{prioridade}'")
    print(f"   cliente_id: '{cliente_id}'")
    
    # ============================================================
    # QUERY COM FILTRO EXPLÍCITO - ativo=True
    # ============================================================
    
    # Log de diagnóstico
    total_geral = OrdemServico.query.count()
    total_ativas = OrdemServico.query.filter(OrdemServico.ativo == True).count()
    print(f"\n📊 DIAGNÓSTICO:")
    print(f"   Total de OS (sem filtro): {total_geral}")
    print(f"   Total de OS ativas: {total_ativas}")
    
    # Query principal
    query = OrdemServico.query.filter(OrdemServico.ativo == True)
    
    # Aplica filtros de busca se houver
    if busca:
        query = query.join(Cliente).filter(
            db.or_(
                OrdemServico.numero.ilike(f'%{busca}%'),
                OrdemServico.titulo.ilike(f'%{busca}%'),
                OrdemServico.equipamento.ilike(f'%{busca}%'),
                Cliente.nome.ilike(f'%{busca}%')
            )
        )
    
    if status:
        query = query.filter(OrdemServico.status == status)
    
    if prioridade:
        query = query.filter(OrdemServico.prioridade == prioridade)
    
    if cliente_id:
        try:
            query = query.filter(OrdemServico.cliente_id == int(cliente_id))
        except ValueError:
            pass
    
    ordens = query.order_by(OrdemServico.data_abertura.desc()).all()
    
    print(f"\n📋 Resultado da query:")
    print(f"   Total de OS encontradas: {len(ordens)}")
    if ordens:
        print(f"   Primeiras 5 OS:")
        for os in ordens[:5]:
            print(f"   - {os.numero} | {os.titulo} | Status: {os.status}")
    else:
        print("   ⚠️ NENHUMA OS ENCONTRADA COM OS FILTROS APLICADOS")
    
    # Lista de clientes para filtro
    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
    print(f"\n👥 Clientes ativos: {len(clientes)}")
    
    # Estatísticas
    stats = OrdemServico.estatisticas_dashboard()
    print(f"\n📊 Estatísticas: {stats}")
    print("=" * 80)
    
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
            print("🔍 DEBUG: Iniciando processamento POST...")
            
            # Converte valores
            print("🔍 DEBUG: Convertendo valores...")
            valor_servico = safe_decimal_convert(request.form.get('valor_servico', '0'), 0)
            valor_pecas = safe_decimal_convert(request.form.get('valor_pecas', '0'), 0)
            valor_desconto = safe_decimal_convert(request.form.get('valor_desconto', '0'), 0)
            valor_entrada = safe_decimal_convert(request.form.get('valor_entrada', '0'), 0)
            
            print("🔍 DEBUG: Convertendo datas...")
            # Converte datas
            data_prevista = None
            data_primeira_parcela = None
            data_vencimento_pagamento = None
            if request.form.get('data_prevista'):
                data_prevista = datetime.strptime(request.form.get('data_prevista'), '%Y-%m-%d').date()
            if request.form.get('data_primeira_parcela'):
                data_primeira_parcela = datetime.strptime(request.form.get('data_primeira_parcela'), '%Y-%m-%d').date()
            if request.form.get('data_vencimento_pagamento'):
                data_vencimento_pagamento = datetime.strptime(request.form.get('data_vencimento_pagamento'), '%Y-%m-%d').date()
            
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
                titulo=request.form.get('titulo', request.form.get('equipamento', 'OS sem título')).strip(),
                descricao=request.form.get('descricao', '').strip(),
                observacoes=request.form.get('observacoes', '').strip(),
                # Novos campos de solicitação
                solicitante=request.form.get('solicitante', '').strip(),
                descricao_problema=request.form.get('descricao_problema', '').strip(),
                status=request.form.get('status', 'aberta'),
                prioridade=request.form.get('prioridade', 'normal'),
                data_prevista=data_prevista,
                # Data de abertura (editável)
                data_abertura=(datetime.strptime(request.form.get('data_abertura'), '%Y-%m-%d').date() if request.form.get('data_abertura') else date.today()),
                # Data de início (editável)
                data_inicio=(datetime.strptime(request.form.get('data_inicio'), '%Y-%m-%dT%H:%M') if request.form.get('data_inicio') else None),
                # Data de conclusão (editável)
                data_conclusao=(datetime.strptime(request.form.get('data_conclusao'), '%Y-%m-%dT%H:%M') if request.form.get('data_conclusao') else None),
                # Data de vencimento do pagamento (editável)
                data_vencimento_pagamento=(datetime.strptime(request.form.get('data_vencimento_pagamento'), '%Y-%m-%d').date() if request.form.get('data_vencimento_pagamento') else None),
                tecnico_responsavel=request.form.get('tecnico_responsavel', '').strip(),
                valor_servico=Decimal(str(valor_servico)) if valor_servico else Decimal('0'),
                valor_pecas=Decimal(str(valor_pecas)) if valor_pecas else Decimal('0'),
                valor_desconto=Decimal(str(valor_desconto)) if valor_desconto else Decimal('0'),
                prazo_garantia=int(request.form.get('prazo_garantia', 0)),
                equipamento=request.form.get('equipamento', '').strip(),
                marca_modelo=request.form.get('marca_modelo', '').strip(),
                numero_serie=request.form.get('numero_serie', '').strip(),
                diagnostico=request.form.get('diagnostico', '').strip(),
                diagnostico_tecnico=request.form.get('diagnostico_tecnico', '').strip(),
                solucao=request.form.get('solucao', '').strip(),
                # Novos campos - Tratamento seguro
                km_inicial=safe_int_convert(request.form.get('km_inicial', '')),
                km_final=safe_int_convert(request.form.get('km_final', '')),
                total_km=request.form.get('total_km', '').strip(),
                hora_inicial=hora_inicial,
                hora_final=hora_final,
                total_horas=request.form.get('total_horas', '').strip(),
                condicao_pagamento=request.form.get('condicao_pagamento', 'a_vista'),
                status_pagamento=request.form.get('status_pagamento', 'pendente'),
                numero_parcelas=safe_int_convert(request.form.get('numero_parcelas', '1'), default=1),
                valor_entrada=Decimal(str(valor_entrada)) if valor_entrada else Decimal('0'),
                data_primeira_parcela=data_primeira_parcela,
                # Novos campos para anexos e descrição de pagamento
                descricao_pagamento=request.form.get('descricao_pagamento', '').strip(),
                observacoes_anexos=request.form.get('observacoes_anexos', '').strip()
            )
            
            # Validações
            print(f"DEBUG: Validando título: '{ordem.titulo}'")
            if not ordem.titulo or ordem.titulo == 'OS sem título':
                # Se não há título, usar equipamento como referência
                if request.form.get('equipamento', '').strip():
                    ordem.titulo = f"OS - {request.form.get('equipamento', '').strip()}"
                else:
                    ordem.titulo = f"OS #{ordem.numero}"
            
            print(f"DEBUG: Validando cliente_id: '{ordem.cliente_id}'")
            if not ordem.cliente_id:
                flash('Cliente é obrigatório!', 'error')
                print(" DEBUG: Cliente é obrigatório")
                clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
                numero_os = OrdemServico.gerar_proximo_numero()
                return render_template('os/form.html', ordem=None, clientes=clientes, numero_os=numero_os, today=date.today())
            
            # Adiciona ordem à sessão (transação será confirmada no final)
            try:
                print("🔍 DEBUG: Iniciando processo de adicionar ordem...")
                db.session.add(ordem)
                # Flush para garantir que ordem.id seja populado antes de criar os itens
                print("🔍 DEBUG: Fazendo flush da ordem...")
                db.session.flush()
                print(f"✅ DEBUG: Ordem adicionada com sucesso, ID: {ordem.id}")
            except Exception as e:
                print(f"❌ DEBUG: Erro ao adicionar ordem: {e}")
                db.session.rollback()
                flash(f'Erro ao criar ordem: {str(e)}', 'error')
                clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
                numero_os = OrdemServico.gerar_proximo_numero()
                return render_template('os/form.html', ordem=None, clientes=clientes, numero_os=numero_os, today=date.today())
            
            # Processa itens de serviço
            print("🔍 DEBUG: Processando itens de serviço com nova estrutura de tipos")
            
            # Primeiro tenta coletar dados da estrutura de arrays simples (nova)
            print("🔍 DEBUG: Coletando dados de serviços...")
            servicos_desc_array = request.form.getlist('servico_descricao[]')
            servicos_tipo_array = request.form.getlist('servico_tipo[]')
            servicos_quantidade_array = request.form.getlist('servico_quantidade[]')
            servicos_valor_array = request.form.getlist('servico_valor[]')
            
            print(f"DEBUG: Arrays simples encontrados - desc: {len(servicos_desc_array)}, tipo: {len(servicos_tipo_array)}, qtd: {len(servicos_quantidade_array)}, valor: {len(servicos_valor_array)}")
            
            # Se encontrou arrays simples, usa essa estrutura
            servicos_data = []
            if servicos_desc_array:
                print("DEBUG: Usando estrutura de arrays simples para serviços (novo)")
                for i, desc in enumerate(servicos_desc_array):
                    if desc and desc.strip():
                        tipo = servicos_tipo_array[i] if i < len(servicos_tipo_array) else 'Serviço Fechado'
                        quantidade = servicos_quantidade_array[i] if i < len(servicos_quantidade_array) else '1'
                        valor_unitario = servicos_valor_array[i] if i < len(servicos_valor_array) else '0'
                        
                        servicos_data.append({
                            'descricao': desc.strip(),
                            'tipo': tipo,
                            'quantidade': float(safe_decimal_convert(quantidade, 1.0)),
                            'valor_unitario': float(safe_decimal_convert(valor_unitario, 0.0))
                        })
            else:
                # Fallback para estrutura indexada (antiga)
                print("DEBUG: Usando estrutura indexada para serviços (fallback)")
                index = 0
                while True:
                    desc_key = f'servicos[{index}][descricao]'
                    if desc_key not in request.form:
                        break
                        
                    tipo_key = f'servicos[{index}][tipo]'
                    quantidade_key = f'servicos[{index}][quantidade]'
                    valor_key = f'servicos[{index}][valor_unitario]'
                    
                    desc = request.form.get(desc_key, '').strip()
                    if desc:
                        tipo = request.form.get(tipo_key, 'Serviço Fechado')
                        quantidade = request.form.get(quantidade_key, '1')
                        valor_unitario = request.form.get(valor_key, '0')
                        
                        servicos_data.append({
                            'descricao': desc,
                            'tipo': tipo,
                            'quantidade': float(safe_decimal_convert(quantidade, 1.0)),
                            'valor_unitario': float(safe_decimal_convert(valor_unitario, 0.0))
                        })
                        
                    index += 1
            
            print(f"🔍 DEBUG: Coletados {len(servicos_data)} serviços: {servicos_data}")
            
            # Criar itens de serviço
            print("🔍 DEBUG: Criando itens de serviço...")
            for servico_data in servicos_data:
                item = OrdemServicoItem(
                    ordem_servico_id=ordem.id,
                    descricao=servico_data['descricao'],
                    tipo_servico=servico_data['tipo'],
                    quantidade=Decimal(str(servico_data['quantidade'])),
                    valor_unitario=Decimal(str(servico_data['valor_unitario']))
                )
                item.calcular_total()
                db.session.add(item)
                print(f"➕ Serviço adicionado: {item.descricao} - {item.quantidade} {item.tipo_servico} = R$ {item.valor_total}")
            
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
                    db.session.add(produto)
            
            # Recalcula valores principais considerando itens (DEPOIS que todos os itens foram criados)
            # Garante consistência entre telas e PDF
            ordem.valor_servico = ordem.valor_total_servicos
            ordem.valor_pecas = ordem.valor_total_produtos
            ordem.valor_total = ordem.valor_total_calculado_novo
            
            # NOTE: parcelas processing moved to after total calculation (see below)

            # Preferência: incluir imagens no relatório
            ordem.incluir_imagens_relatorio = True if request.form.get('incluir_imagens_relatorio') in ('1', 'on', 'true') else False
            
            # Processa arquivos anexados
            if 'anexos' in request.files or 'anexos[]' in request.files:
                # Pega os arquivos usando o nome correto
                if 'anexos' in request.files:
                    files = request.files.getlist('anexos')
                else:
                    files = request.files.getlist('anexos[]')
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
                            
                            # Lê o conteúdo do arquivo para salvar no banco (Render precisa)
                            file.seek(0)  # Volta ao início do arquivo
                            file_content = file.read()
                            file.seek(0)  # Volta novamente para salvar em disco
                            
                            # Salva arquivo em disco também (para desenvolvimento local)
                            file.save(filepath)
                            
                            # Detecta tipo do arquivo
                            content_type = file.content_type or 'application/octet-stream'
                            tipo_arquivo = 'image' if content_type.startswith('image/') else 'document'
                            
                            # Cria registro no banco (com conteúdo em BLOB para Render)
                            try:
                                anexo = OrdemServicoAnexo(
                                    ordem_servico_id=ordem.id,
                                    nome_original=file.filename,
                                    nome_arquivo=filename,
                                    tipo_arquivo=tipo_arquivo,
                                    mime_type=content_type,
                                    tamanho=len(file_content),
                                    caminho=filepath,
                                    conteudo=file_content  # Salva no banco para persistir no Render
                                )
                            except TypeError:
                                # Se a coluna conteudo não existir ainda, cria sem ela
                                print(f"⚠️ Coluna 'conteudo' não existe, criando anexo sem BLOB")
                                anexo = OrdemServicoAnexo(
                                    ordem_servico_id=ordem.id,
                                    nome_original=file.filename,
                                    nome_arquivo=filename,
                                    tipo_arquivo=tipo_arquivo,
                                    mime_type=content_type,
                                    tamanho=len(file_content),
                                    caminho=filepath
                                )
                            db.session.add(anexo)
                            
                        except Exception as e:
                            flash(f'Erro ao salvar arquivo {file.filename}: {str(e)}', 'warning')
                    elif file and file.filename and not allowed_file(file.filename):
                        flash(f'Tipo de arquivo não permitido: {file.filename}', 'warning')
            
            # Processa parcelas (validação + criação)
            if ordem.condicao_pagamento == 'parcelado' and ordem.numero_parcelas and ordem.numero_parcelas > 0:
                entrada = safe_decimal_convert(request.form.get('valor_entrada', '0'), 0)
                parcelas_datas = request.form.getlist('parcela_data[]')
                parcelas_valores = request.form.getlist('parcela_valor[]')

                base_date = date.today()
                # Usar data_primeira_parcela se fornecida
                if request.form.get('data_primeira_parcela'):
                    try:
                        base_date = datetime.strptime(request.form.get('data_primeira_parcela'), '%Y-%m-%d').date()
                    except Exception:
                        base_date = date.today()
                elif request.form.get('data_prevista'):
                    try:
                        base_date = datetime.strptime(request.form.get('data_prevista'), '%Y-%m-%d').date()
                    except Exception:
                        base_date = date.today()
                elif request.form.get('data_abertura'):
                    try:
                        base_date = datetime.strptime(request.form.get('data_abertura'), '%Y-%m-%d').date()
                    except Exception:
                        base_date = date.today()

                # Tolerância para diferenças pequenas (centavos)
                tolerancia = Decimal('0.02')

                # Se o usuário forneceu parcelas manualmente, validar soma
                if parcelas_valores and any(v.strip() for v in parcelas_valores):
                    soma_parcelas = Decimal('0')
                    parsed_parcelas = []
                    for idx, val in enumerate(parcelas_valores):
                        try:
                            valor_parcela = safe_decimal_convert(val, 0)
                            soma_parcelas += valor_parcela
                            data_venc = None
                            if idx < len(parcelas_datas) and parcelas_datas[idx]:
                                try:
                                    data_venc = datetime.strptime(parcelas_datas[idx], '%Y-%m-%d').date()
                                except Exception:
                                    data_venc = base_date
                            else:
                                data_venc = base_date
                            parsed_parcelas.append((idx + 1, data_venc, valor_parcela))
                        except Exception:
                            continue

                    total_form = entrada + soma_parcelas
                    if abs(total_form - Decimal(str(ordem.valor_total))) > tolerancia:
                        # Não criar parcelas se soma não bater com o total
                        flash('Soma das parcelas + entrada não corresponde ao valor total. Verifique os valores inseridos.', 'error')
                        clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
                        numero_os = OrdemServico.gerar_proximo_numero()
                        # Não persistir alterações de parcelas neste fluxo; deixa o usuário corrigir
                        return render_template('os/form.html', ordem=ordem, clientes=clientes, numero_os=numero_os, today=date.today())

                    # Apaga possíveis parcelas pré-existentes (não deveria haver em novo, mas seguro)
                    for p in list(ordem.parcelas):
                        # remover via sessão (evita commits intermediários)
                        db.session.delete(p)

                    # Salva parcelas conforme fornecido
                    for numero, data_venc, valor_parcela in parsed_parcelas:
                        parcela = OrdemServicoParcela(
                            ordem_servico_id=ordem.id,
                            numero_parcela=numero,
                            data_vencimento=data_venc,
                            valor=Decimal(str(valor_parcela)).quantize(Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)
                        )
                        db.session.add(parcela)

                else:
                    # Distribuição automática:.garante soma exata distribuindo resto na última parcela
                    restante = Decimal(str(ordem.valor_total)) - entrada
                    if restante < 0:
                        restante = Decimal('0')

                    created = 0
                    if entrada and entrada > 0:
                        # cria parcela de entrada
                        parcela = OrdemServicoParcela(
                            ordem_servico_id=ordem.id,
                            numero_parcela=1,
                            data_vencimento=base_date,
                            valor=Decimal(str(entrada)).quantize(Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)
                        )
                        db.session.add(parcela)
                        created = 1

                    parcelas_a_distribuir = ordem.numero_parcelas - created
                    if parcelas_a_distribuir <= 0:
                        parcelas_a_distribuir = 1

                    # Calcula valor por parcela com quantize e ajusta última parcela com o restante
                    if parcelas_a_distribuir > 0:
                        valor_por_parcela = (restante / parcelas_a_distribuir)
                        valor_por_parcela_q = valor_por_parcela.quantize(Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)
                        soma_parcels = valor_por_parcela_q * parcelas_a_distribuir
                        diferenca = restante - soma_parcels

                        for i in range(parcelas_a_distribuir):
                            numero = created + i + 1
                            try:
                                mes = base_date.month + i + 1
                                ano = base_date.year + ((mes - 1) // 12)
                                mes = ((mes - 1) % 12) + 1
                                dia = min(base_date.day, 28)
                                data_venc = date(ano, mes, dia)
                            except Exception:
                                data_venc = base_date

                            # para a última parcela, adiciona a diferença (pode ser negativa/positiva devido ao arredondamento)
                            if i == parcelas_a_distribuir - 1:
                                valor_final = (valor_por_parcela_q + diferenca).quantize(Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)
                            else:
                                valor_final = valor_por_parcela_q

                            parcela = OrdemServicoParcela(
                                ordem_servico_id=ordem.id,
                                numero_parcela=numero,
                                data_vencimento=data_venc,
                                valor=valor_final
                            )
                            db.session.add(parcela)

            # Recalcula e atualiza valores antes de confirmar transação
            ordem.valor_servico = ordem.valor_total_servicos
            ordem.valor_pecas = ordem.valor_total_produtos
            ordem.valor_total = ordem.valor_total_calculado_novo
            print(f"DEBUG: Totais calculados → Serviços: R$ {ordem.valor_servico} | Peças: R$ {ordem.valor_pecas} | Total: R$ {ordem.valor_total}")

            try:
                print("DEBUG: Tentando fazer commit da ordem...")
                db.session.commit()
                print(" DEBUG: Commit realizado com sucesso!")
                
                # === INTEGRAÇÃO FINANCEIRA ===
                try:
                    from app.financeiro.financeiro_utils import gerar_lancamento_ordem_servico
                    print("DEBUG: Gerando lançamento financeiro...")
                    gerar_lancamento_ordem_servico(ordem)
                    print(" DEBUG: Integração financeira concluída!")
                except Exception as financeiro_error:
                    print(f"⚠️ DEBUG: Erro na integração financeira: {financeiro_error}")
                    # Não interrompe o fluxo - ordem já foi criada
                
            except Exception as commit_error:
                print(f" DEBUG: Erro no commit: {commit_error}")
                db.session.rollback()
                raise

            flash(f'Ordem de Serviço {ordem.numero} criada com sucesso! Você pode visualizar, editar ou gerar o PDF.', 'success')
            return redirect(url_for('ordem_servico.visualizar', id=ordem.id))
            
        except Exception as e:
            # Em caso de erro, desfaz qualquer alteração pendente na sessão
            try:
                db.session.rollback()
            except Exception:
                pass
            flash(f'Erro ao criar ordem de serviço: {str(e)}', 'error')
            clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
            numero_os = OrdemServico.gerar_proximo_numero()
            return render_template('os/form.html', ordem=None, clientes=clientes, numero_os=numero_os, today=date.today())
    
    # GET - exibe formulário vazio
    clientes = buscar_clientes_ativos()
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
    print(f"DEBUG: Iniciando edição para ID {id}")
    
    ordem = OrdemServico.get_by_id(id)
    if not ordem:
        print(f" DEBUG: Ordem com ID {id} não encontrada")
        flash('Ordem de serviço não encontrada!', 'error')
        return redirect(url_for('ordem_servico.listar'))
    
    print(f" DEBUG: Ordem encontrada: {ordem.numero}")
    
    if request.method == 'POST':
        try:
            print(f"DEBUG: Processando POST para ordem {id}")
            print(f"DEBUG: Form data keys: {list(request.form.keys())}")
            
            # Debug específico para serviços e produtos
            servicos_desc = request.form.getlist('servico_descricao[]')
            produtos_desc = request.form.getlist('produto_descricao[]')
            print(f"DEBUG: Serviços encontrados: {len(servicos_desc)} - {servicos_desc}")
            print(f"DEBUG: Produtos encontrados: {len(produtos_desc)} - {produtos_desc}")
            
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
            ordem.titulo = request.form.get('titulo', request.form.get('equipamento', ordem.titulo or 'OS sem título')).strip()
            ordem.descricao = request.form.get('descricao', '').strip()
            ordem.observacoes = request.form.get('observacoes', '').strip()
            # Novos campos de solicitação
            ordem.solicitante = request.form.get('solicitante', '').strip()
            ordem.descricao_problema = request.form.get('descricao_problema', '').strip()
            
            # Controla mudança de status
            novo_status = request.form.get('status', 'aberta')
            # Permite sobrescrever data_abertura e data_conclusao manualmente
            if request.form.get('data_abertura'):
                try:
                    ordem.data_abertura = datetime.strptime(request.form.get('data_abertura'), '%Y-%m-%d').date()
                except Exception:
                    pass

            if request.form.get('data_conclusao'):
                try:
                    ordem.data_conclusao = datetime.strptime(request.form.get('data_conclusao'), '%Y-%m-%dT%H:%M').replace(tzinfo=None)
                except Exception:
                    # aceitar também formato YYYY-MM-DD
                    try:
                        ordem.data_conclusao = datetime.strptime(request.form.get('data_conclusao'), '%Y-%m-%d')
                    except Exception:
                        pass

            # Permite sobrescrever data_inicio manualmente
            if request.form.get('data_inicio'):
                try:
                    ordem.data_inicio = datetime.strptime(request.form.get('data_inicio'), '%Y-%m-%dT%H:%M').replace(tzinfo=None)
                except Exception:
                    # aceitar também formato YYYY-MM-DD
                    try:
                        ordem.data_inicio = datetime.strptime(request.form.get('data_inicio'), '%Y-%m-%d')
                    except Exception:
                        pass

            # Permite definir data de vencimento do pagamento
            if request.form.get('data_vencimento_pagamento'):
                try:
                    ordem.data_vencimento_pagamento = datetime.strptime(request.form.get('data_vencimento_pagamento'), '%Y-%m-%d').date()
                except Exception:
                    pass

            if novo_status != ordem.status:
                if novo_status == 'em_andamento' and ordem.status == 'aberta':
                    ordem.data_inicio = dt.now()
                elif novo_status == 'concluida' and ordem.status != 'concluida' and not ordem.data_conclusao:
                    ordem.data_conclusao = dt.now()
            ordem.status = novo_status
            
            ordem.prioridade = request.form.get('prioridade', 'normal')
            ordem.data_prevista = data_prevista
            ordem.tecnico_responsavel = request.form.get('tecnico_responsavel', '').strip()
            # valor_servico e valor_pecas serão recalculados após processar itens
            ordem.valor_desconto = safe_decimal_convert(request.form.get('valor_desconto', '0'), 0)
            ordem.prazo_garantia = int(request.form.get('prazo_garantia', 0))
            ordem.equipamento = request.form.get('equipamento', '').strip()
            ordem.marca_modelo = request.form.get('marca_modelo', '').strip()
            ordem.numero_serie = request.form.get('numero_serie', '').strip()
            ordem.diagnostico = request.form.get('diagnostico', '').strip()
            ordem.diagnostico_tecnico = request.form.get('diagnostico_tecnico', '').strip()
            ordem.solucao = request.form.get('solucao', '').strip()
            
            # Controle de KM e Tempo - Tratamento seguro de conversão
            ordem.km_inicial = safe_int_convert(request.form.get('km_inicial', ''))
            ordem.km_final = safe_int_convert(request.form.get('km_final', ''))
            ordem.total_km = request.form.get('total_km', '').strip()
            
            # Processa horários
            hora_inicial = None
            hora_final = None
            
            if request.form.get('hora_inicial'):
                hora_inicial = datetime.strptime(request.form.get('hora_inicial'), '%H:%M').time()
            if request.form.get('hora_final'):
                hora_final = datetime.strptime(request.form.get('hora_final'), '%H:%M').time()
            
            ordem.hora_inicial = hora_inicial
            ordem.hora_final = hora_final
            ordem.total_horas = request.form.get('total_horas', '').strip()
            
            # Condições de Pagamento
            ordem.condicao_pagamento = request.form.get('condicao_pagamento', 'a_vista')
            ordem.status_pagamento = request.form.get('status_pagamento', 'pendente')
            ordem.numero_parcelas = int(request.form.get('numero_parcelas', 1)) if request.form.get('numero_parcelas') else 1
            ordem.valor_entrada = safe_decimal_convert(request.form.get('valor_entrada', '0'), 0)
            
            # Data da primeira parcela
            if request.form.get('data_primeira_parcela'):
                try:
                    ordem.data_primeira_parcela = datetime.strptime(request.form.get('data_primeira_parcela'), '%Y-%m-%d').date()
                except Exception:
                    pass
            
            # Data de vencimento do pagamento
            if request.form.get('data_vencimento_pagamento'):
                try:
                    ordem.data_vencimento_pagamento = datetime.strptime(request.form.get('data_vencimento_pagamento'), '%Y-%m-%d').date()
                except Exception:
                    pass
            
            ordem.descricao_pagamento = request.form.get('descricao_pagamento', '').strip()
            ordem.observacoes_anexos = request.form.get('observacoes_anexos', '').strip()
            
            # Validações
            if not ordem.titulo or ordem.titulo == 'OS sem título':
                # Se não há título, usar equipamento como referência
                if request.form.get('equipamento', '').strip():
                    ordem.titulo = f"OS - {request.form.get('equipamento', '').strip()}"
                else:
                    ordem.titulo = f"OS #{ordem.numero}"
            
            # Processa itens de serviço - Remove antigos e adiciona novos
            print(f"DEBUG: Removendo {len(ordem.servicos)} serviços antigos via loop delete")
            servicos_removidos = 0
            for item_existente in list(ordem.servicos):
                print(f"  🗑️ Removendo serviço: {item_existente.descricao}")
                db.session.delete(item_existente)
                servicos_removidos += 1
            print(f" {servicos_removidos} serviços removidos")
            
            # Processa itens de serviço com nova estrutura de tipos
            print("DEBUG: Processando itens de serviço com nova estrutura de tipos (edição)")
            
            # Primeiro tenta coletar dados da estrutura de arrays simples (nova)
            servicos_desc_array = request.form.getlist('servico_descricao[]')
            servicos_tipo_array = request.form.getlist('servico_tipo[]')
            servicos_quantidade_array = request.form.getlist('servico_quantidade[]')
            servicos_valor_array = request.form.getlist('servico_valor[]')
            
            print(f"DEBUG: Arrays simples encontrados - desc: {len(servicos_desc_array)}, tipo: {len(servicos_tipo_array)}, qtd: {len(servicos_quantidade_array)}, valor: {len(servicos_valor_array)}")
            
            # Se encontrou arrays simples, usa essa estrutura
            servicos_data = []
            if servicos_desc_array:
                print("DEBUG: Usando estrutura de arrays simples para serviços")
                for i, desc in enumerate(servicos_desc_array):
                    if desc and desc.strip():
                        tipo = servicos_tipo_array[i] if i < len(servicos_tipo_array) else 'Serviço Fechado'
                        quantidade = servicos_quantidade_array[i] if i < len(servicos_quantidade_array) else '1'
                        valor_unitario = servicos_valor_array[i] if i < len(servicos_valor_array) else '0'
                        
                        servicos_data.append({
                            'descricao': desc.strip(),
                            'tipo': tipo,
                            'quantidade': float(safe_decimal_convert(quantidade, 1.0)),
                            'valor_unitario': float(safe_decimal_convert(valor_unitario, 0.0))
                        })
            else:
                # Fallback para estrutura indexada (antiga)
                print("DEBUG: Usando estrutura indexada para serviços (fallback)")
                index = 0
                while True:
                    desc_key = f'servicos[{index}][descricao]'
                    if desc_key not in request.form:
                        break
                        
                    tipo_key = f'servicos[{index}][tipo]'
                    quantidade_key = f'servicos[{index}][quantidade]'
                    valor_key = f'servicos[{index}][valor_unitario]'
                    
                    desc = request.form.get(desc_key, '').strip()
                    if desc:
                        tipo = request.form.get(tipo_key, 'Serviço Fechado')
                        quantidade = request.form.get(quantidade_key, '1')
                        valor_unitario = request.form.get(valor_key, '0')
                        
                        servicos_data.append({
                            'descricao': desc,
                            'tipo': tipo,
                            'quantidade': float(safe_decimal_convert(quantidade, 1.0)),
                            'valor_unitario': float(safe_decimal_convert(valor_unitario, 0.0))
                        })
                        
                    index += 1
            
            print(f"DEBUG: Coletados {len(servicos_data)} serviços para edição: {servicos_data}")

            # Criar novos itens de serviço
            servicos_adicionados = 0
            for servico_data in servicos_data:
                item = OrdemServicoItem(
                    ordem_servico_id=ordem.id,
                    descricao=servico_data['descricao'],
                    tipo_servico=servico_data['tipo'],
                    quantidade=Decimal(str(servico_data['quantidade'])),
                    valor_unitario=Decimal(str(servico_data['valor_unitario']))
                )
                item.calcular_total()
                db.session.add(item)
                servicos_adicionados += 1
                print(f"  ➕ Adicionado serviço: {item.descricao} - {item.quantidade} {item.tipo_servico} = R$ {item.valor_total}")
            print(f" {servicos_adicionados} serviços adicionados")
            
            # Processa produtos utilizados - Remove antigos e adiciona novos
            print(f"DEBUG: Removendo {len(ordem.produtos_utilizados)} produtos antigos via loop delete")
            produtos_removidos = 0
            for produto_existente in list(ordem.produtos_utilizados):
                print(f"  🗑️ Removendo produto: {produto_existente.descricao}")
                db.session.delete(produto_existente)
                produtos_removidos += 1
            print(f" {produtos_removidos} produtos removidos")
            
            produtos_desc = request.form.getlist('produto_descricao[]')
            produtos_qtd = request.form.getlist('produto_quantidade[]')
            produtos_valor = request.form.getlist('produto_valor[]')

            print(f"DEBUG: Processando {len(produtos_desc)} produtos do formulário")
            print(f"  📝 Descrições: {produtos_desc}")
            produtos_adicionados = 0
            for i, desc in enumerate(produtos_desc):
                if desc and desc.strip():
                    qtd_value = produtos_qtd[i] if i < len(produtos_qtd) else ''
                    valor_value = produtos_valor[i] if i < len(produtos_valor) else ''
                    produto = OrdemServicoProduto(
                        ordem_servico_id=ordem.id,
                        descricao=desc.strip(),
                        quantidade=safe_decimal_convert(qtd_value, 1),
                        valor_unitario=safe_decimal_convert(valor_value, 0)
                    )
                    produto.calcular_total()
                    db.session.add(produto)
                    produtos_adicionados += 1
                    print(f"  ➕ Adicionado produto: {desc.strip()}")
            print(f" {produtos_adicionados} produtos adicionados")
            
            # Recalcula valores dos campos principais após adicionar todos os itens
            ordem.valor_servico = ordem.valor_total_servicos
            ordem.valor_pecas = ordem.valor_total_produtos
            ordem.valor_total = ordem.valor_total_calculado_novo
            print(f"🧮 DEBUG: Valor serviço: R$ {ordem.valor_servico} | Valor peças: R$ {ordem.valor_pecas} | Valor total: R$ {ordem.valor_total}")

            # Processa parcelas da ordem: validação e recriação conforme formulário
            try:
                if ordem.condicao_pagamento == 'parcelado' and ordem.numero_parcelas > 0:
                    entrada = safe_decimal_convert(request.form.get('entrada', '0'), 0)
                    parcelas_datas = request.form.getlist('parcela_data[]')
                    parcelas_valores = request.form.getlist('parcela_valor[]')

                    base_date = date.today()
                    if request.form.get('data_prevista'):
                        try:
                            base_date = datetime.strptime(request.form.get('data_prevista'), '%Y-%m-%d').date()
                        except Exception:
                            base_date = date.today()
                    elif request.form.get('data_abertura'):
                        try:
                            base_date = datetime.strptime(request.form.get('data_abertura'), '%Y-%m-%d').date()
                        except Exception:
                            base_date = date.today()

                    tolerancia = Decimal('0.02')

                    # Se parcelas manuais foram enviadas, valida soma antes de destruir existentes
                    if parcelas_valores and any(v.strip() for v in parcelas_valores):
                        soma_parcelas = Decimal('0')
                        parsed_parcelas = []
                        for idx, val in enumerate(parcelas_valores):
                            try:
                                valor_parcela = safe_decimal_convert(val, 0)
                                soma_parcelas += valor_parcela
                                data_venc = None
                                if idx < len(parcelas_datas) and parcelas_datas[idx]:
                                    try:
                                        data_venc = datetime.strptime(parcelas_datas[idx], '%Y-%m-%d').date()
                                    except Exception:
                                        data_venc = base_date
                                else:
                                    data_venc = base_date
                                parsed_parcelas.append((idx + 1, data_venc, valor_parcela))
                            except Exception:
                                continue

                        total_form = entrada + soma_parcelas
                        if abs(total_form - Decimal(str(ordem.valor_total))) > tolerancia:
                            flash('Soma das parcelas + entrada não corresponde ao valor total. Verifique os valores inseridos.', 'error')
                            clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
                            return render_template('os/form.html', ordem=ordem, clientes=clientes, today=date.today())

                        # Limpa existentes e salva as parcelas manuais
                        for p in list(ordem.parcelas):
                            p.delete()

                        for numero, data_venc, valor_parcela in parsed_parcelas:
                            parcela = OrdemServicoParcela(
                                ordem_servico_id=ordem.id,
                                numero_parcela=numero,
                                data_vencimento=data_venc,
                                valor=Decimal(str(valor_parcela)).quantize(Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)
                            )
                            db.session.add(parcela)
                    else:
                        # Distribuição automática: calcula parcelas garantindo soma exata
                        restante = Decimal(str(ordem.valor_total)) - entrada
                        if restante < 0:
                            restante = Decimal('0')

                        created = 0
                        parcelas_a_distribuir = ordem.numero_parcelas
                        if entrada and entrada > 0:
                            created = 1
                            parcelas_a_distribuir = ordem.numero_parcelas - 1
                            if parcelas_a_distribuir <= 0:
                                parcelas_a_distribuir = 1

                        # Calcula valores e prepara lista
                        valores = []
                        if parcelas_a_distribuir > 0:
                            valor_por_parcela = (restante / parcelas_a_distribuir)
                            valor_por_parcela_q = valor_por_parcela.quantize(Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)
                            soma_parcels = valor_por_parcela_q * parcelas_a_distribuir
                            diferenca = restante - soma_parcels

                            for i in range(parcelas_a_distribuir):
                                if i == parcelas_a_distribuir - 1:
                                    valor_final = (valor_por_parcela_q + diferenca).quantize(Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)
                                else:
                                    valor_final = valor_por_parcela_q
                                valores.append(valor_final)

                        # Limpa parcelas existentes e salva nova distribuição
                        for p in list(ordem.parcelas):
                            p.delete()

                        idx_offset = 0
                        if entrada and entrada > 0:
                            parcela = OrdemServicoParcela(
                                ordem_servico_id=ordem.id,
                                numero_parcela=1,
                                data_vencimento=base_date,
                                valor=Decimal(str(entrada)).quantize(Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)
                            )
                            db.session.add(parcela)
                            idx_offset = 1

                        for i, val in enumerate(valores):
                            numero = idx_offset + i + 1
                            try:
                                mes = base_date.month + i + 1
                                ano = base_date.year + ((mes - 1) // 12)
                                mes = ((mes - 1) % 12) + 1
                                dia = min(base_date.day, 28)
                                data_venc = date(ano, mes, dia)
                            except Exception:
                                data_venc = base_date

                            parcela = OrdemServicoParcela(
                                ordem_servico_id=ordem.id,
                                numero_parcela=numero,
                                data_vencimento=data_venc,
                                valor=val
                            )
                            db.session.add(parcela)
            except Exception as e:
                print('Erro ao processar parcelas:', e)
            
            # Processa arquivos anexados
            print(f"🔍 DEBUG ANEXOS EDITAR: Verificando anexos em request.files...")
            print(f"🔍 DEBUG ANEXOS EDITAR: request.files keys: {list(request.files.keys())}")
            print(f"🔍 DEBUG ANEXOS EDITAR: request.form keys: {list(request.form.keys())}")
            print(f"🔍 DEBUG ANEXOS EDITAR: Tem campo 'anexos'? {'anexos' in request.files}")
            print(f"🔍 DEBUG ANEXOS EDITAR: Tem campo 'anexos[]'? {'anexos[]' in request.files}")
            print(f"🔍 DEBUG ANEXOS EDITAR: Valor de request.files.get('anexos'): {request.files.get('anexos')}")
            print(f"🔍 DEBUG ANEXOS EDITAR: Valor de request.files.get('anexos[]'): {request.files.get('anexos[]')}")

            # Atualiza preferência: incluir imagens no PDF
            ordem.incluir_imagens_relatorio = True if request.form.get('incluir_imagens_relatorio') in ('1', 'on', 'true') else False
            
            # Verifica tanto 'anexos' quanto 'anexos[]'
            if 'anexos' in request.files or 'anexos[]' in request.files:
                # Pega os arquivos usando o nome correto
                if 'anexos' in request.files:
                    files = request.files.getlist('anexos')
                    campo_usado = 'anexos'
                else:
                    files = request.files.getlist('anexos[]')
                    campo_usado = 'anexos[]'
                    
                print(f"🔍 DEBUG ANEXOS EDITAR: {len(files)} arquivos encontrados usando campo '{campo_usado}'")
                
                for i, file in enumerate(files):
                    print(f"🔍 DEBUG ANEXOS EDITAR: Arquivo {i+1}: filename='{file.filename}', content_type='{file.content_type}', size={get_file_size(file) if file else 0}")
                    
                    if file and file.filename and allowed_file(file.filename):
                        try:
                            print(f"🔍 DEBUG ANEXOS EDITAR: Processando arquivo válido: {file.filename}")
                            
                            # Verifica tamanho
                            file_size = get_file_size(file)
                            print(f"🔍 DEBUG ANEXOS EDITAR: Tamanho do arquivo: {file_size} bytes")
                            
                            if file_size > MAX_FILE_SIZE:
                                flash(f'Arquivo {file.filename} é muito grande (máximo 16MB)', 'warning')
                                print(f"❌ DEBUG ANEXOS EDITAR: Arquivo muito grande: {file.filename}")
                                continue
                                
                            # Gera nome único
                            filename = generate_unique_filename(file.filename)
                            filepath = os.path.join(UPLOAD_FOLDER, filename)
                            print(f"🔍 DEBUG ANEXOS EDITAR: Salvando em: {filepath}")
                            
                            # Cria diretório se não existe
                            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                            
                            # Lê o conteúdo do arquivo para salvar no banco (Render precisa)
                            file.seek(0)  # Volta ao início do arquivo
                            file_content = file.read()
                            file.seek(0)  # Volta novamente para salvar em disco
                            
                            # Salva arquivo em disco (para desenvolvimento local)
                            file.save(filepath)
                            print(f"✅ DEBUG ANEXOS EDITAR: Arquivo salvo fisicamente: {filepath}")
                            
                            # Detecta tipo do arquivo
                            content_type = file.content_type or 'application/octet-stream'
                            tipo_arquivo = 'image' if content_type.startswith('image/') else 'document'
                            print(f"🔍 DEBUG ANEXOS EDITAR: Tipo detectado: {tipo_arquivo}, MIME: {content_type}")
                            
                            # Cria registro no banco (com conteúdo em BLOB para Render)
                            try:
                                anexo = OrdemServicoAnexo(
                                    ordem_servico_id=ordem.id,
                                    nome_original=file.filename,
                                    nome_arquivo=filename,
                                    tipo_arquivo=tipo_arquivo,
                                    mime_type=content_type,
                                    tamanho=len(file_content),
                                    caminho=filepath,
                                    conteudo=file_content  # Salva no banco para persistir no Render
                                )
                            except TypeError:
                                # Se a coluna conteudo não existir ainda, cria sem ela
                                print(f"⚠️ Coluna 'conteudo' não existe, criando anexo sem BLOB")
                                anexo = OrdemServicoAnexo(
                                    ordem_servico_id=ordem.id,
                                    nome_original=file.filename,
                                    nome_arquivo=filename,
                                    tipo_arquivo=tipo_arquivo,
                                    mime_type=content_type,
                                    tamanho=len(file_content),
                                    caminho=filepath
                                )
                            db.session.add(anexo)
                            print(f"✅ DEBUG ANEXOS EDITAR: Registro criado no banco: {anexo}")
                            
                        except Exception as e:
                            print(f"❌ DEBUG ANEXOS EDITAR: Erro ao processar {file.filename}: {str(e)}")
                            flash(f'Erro ao salvar arquivo {file.filename}: {str(e)}', 'warning')
                    elif file and file.filename and not allowed_file(file.filename):
                        print(f"❌ DEBUG ANEXOS EDITAR: Tipo não permitido: {file.filename}")
                        flash(f'Tipo de arquivo não permitido: {file.filename}', 'warning')
                    elif file and file.filename == '':
                        print(f"🔍 DEBUG ANEXOS EDITAR: Arquivo vazio ignorado")
                    else:
                        print(f"🔍 DEBUG ANEXOS EDITAR: Arquivo inválido: file={file}, filename='{file.filename if file else None}'")
            else:
                print("🔍 DEBUG ANEXOS EDITAR: Nenhum campo 'anexos' encontrado nos arquivos")
            
            # Recalcula valor total novamente antes do commit final
            ordem.valor_total = ordem.valor_total_calculado

            # Commit final: salva novas linhas de serviços/produtos/parcelas/anexos
            try:
                db.session.commit()
                print(f"🏁 DEBUG: Ordem de Serviço salva com sucesso! Total final: R$ {ordem.valor_total}")
                
                # Integração financeira - gerar/atualizar lançamento
                from app.financeiro.financeiro_utils import gerar_lancamento_ordem_servico
                try:
                    gerar_lancamento_ordem_servico(ordem)
                    print(f"💰 DEBUG: Lançamento financeiro atualizado para OS {ordem.numero}")
                except Exception as fin_err:
                    print(f"⚠️ DEBUG: Erro na integração financeira: {fin_err}")
                    # Não falha a operação principal
                    
            except Exception as commit_err:
                try:
                    db.session.rollback()
                except Exception:
                    pass
                raise

            flash(f'Ordem de Serviço {ordem.numero} atualizada com sucesso!', 'success')
            return redirect(url_for('ordem_servico.visualizar', id=ordem.id))
            
        except Exception as e:
            flash(f'Erro ao atualizar ordem de serviço: {str(e)}', 'error')
            # Busca clientes com função robusta
            db.session.rollback()
            clientes = buscar_clientes_ativos()
            return render_template('os/form.html', ordem=ordem, clientes=clientes, today=date.today())
    
    # GET - exibe formulário preenchido
    print("DEBUG: Buscando clientes...")
    clientes = buscar_clientes_ativos()
    
    print("DEBUG: Renderizando template...")
    try:
        return render_template('os/form.html', 
                             ordem=ordem, 
                             clientes=clientes or [], 
                             today=date.today())
    except Exception as e:
        print(f" DEBUG: Erro ao renderizar template: {e}")
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
        
        # Integração financeira - remover/cancelar lançamento
        from app.financeiro.financeiro_utils import cancelar_lancamento_ordem_servico
        try:
            cancelar_lancamento_ordem_servico(ordem)
            print(f"💰 DEBUG: Lançamento financeiro cancelado para OS {ordem.numero}")
        except Exception as fin_err:
            print(f"⚠️ DEBUG: Erro ao cancelar lançamento financeiro: {fin_err}")
            # Não falha a operação principal
            
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
    Serve do BLOB primeiro, depois tenta disco físico.
    
    Args:
        anexo_id: ID do anexo
    """
    from flask import Response
    import io
    
    anexo = OrdemServicoAnexo.query.get_or_404(anexo_id)
    
    # 1. Tenta servir do BLOB (se disponível)
    if hasattr(anexo, 'conteudo') and anexo.conteudo:
        return Response(
            io.BytesIO(anexo.conteudo),
            mimetype=anexo.mime_type,
            headers={'Content-Disposition': f'attachment; filename="{anexo.nome_original}"'}
        )
    
    # 2. Fallback: tenta servir do disco
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
    Serve do BLOB primeiro, depois tenta disco físico.
    
    Args:
        anexo_id: ID do anexo
    """
    from flask import Response
    import io
    
    anexo = OrdemServicoAnexo.query.get_or_404(anexo_id)
    
    # 1. Tenta servir do BLOB (se disponível)
    if hasattr(anexo, 'conteudo') and anexo.conteudo:
        return Response(
            io.BytesIO(anexo.conteudo),
            mimetype=anexo.mime_type,
            headers={'Content-Disposition': f'inline; filename="{anexo.nome_original}"'}
        )
    
    # 2. Fallback: tenta servir do disco
    try:
        return send_from_directory(
            UPLOAD_FOLDER,
            anexo.nome_arquivo,
            as_attachment=False
        )
    except FileNotFoundError:
        # 3. Tenta caminhos alternativos
        possible_paths = [
            os.path.join('app', 'static', 'uploads', anexo.nome_arquivo),
            os.path.join(current_app.root_path, 'static', 'uploads', anexo.nome_arquivo),
            os.path.join('uploads', anexo.nome_arquivo)
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                with open(path, 'rb') as f:
                    return Response(
                        io.BytesIO(f.read()),
                        mimetype=anexo.mime_type,
                        headers={'Content-Disposition': f'inline; filename="{anexo.nome_original}"'}
                    )
        
        # Arquivo não encontrado em lugar nenhum
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
    nome_arquivo = anexo.nome_original
    
    try:
        # Remove arquivo físico (se existir)
        filepath = os.path.join(UPLOAD_FOLDER, anexo.nome_arquivo)
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Remove registro do banco (BLOB também será removido automaticamente)
        anexo.delete()
        
        return jsonify({
            'success': True,
            'message': f'Anexo "{nome_arquivo}" excluído com sucesso!'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao excluir anexo: {str(e)}'
        }), 500

@ordem_servico_bp.route('/<int:id>/anexos')
def listar_anexos(id):
    """
    Lista anexos de uma ordem de serviço em formato JSON.
    
    Args:
        id: ID da ordem de serviço
    """
    ordem = OrdemServico.query.get_or_404(id)
    anexos = OrdemServicoAnexo.query.filter_by(ordem_servico_id=id).order_by(OrdemServicoAnexo.data_upload, OrdemServicoAnexo.id).all()
    
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

@ordem_servico_bp.route('/api/test')
def api_test():
    """Rota de teste básico."""
    return {'message': 'API funcionando!', 'success': True}

@ordem_servico_bp.route('/api/clientes')
def api_clientes():
    """API para buscar clientes ativos (para atualização dinâmica do select)."""
    try:
        print(" API /api/clientes chamada!")
        
        # Usa a função robusta para buscar clientes
        clientes = buscar_clientes_ativos()
        
        # Debug: listar primeiros clientes
        cliente11_encontrado = False
        for i, cliente in enumerate(clientes[:5]):
            print(f"  Cliente {i+1}: ID={cliente.id}, Nome='{cliente.nome}', Ativo={cliente.ativo}")
            if cliente.id == 11:
                cliente11_encontrado = True
        
        # Verificar especificamente Cliente 11
        if not cliente11_encontrado:
            c11_direto = Cliente.query.filter_by(id=11).first()
            if c11_direto:
                print(f"  ⚠️ Cliente 11 existe mas não aparece na lista: Nome='{c11_direto.nome}', Ativo={c11_direto.ativo}")
            else:
                print(f"   Cliente 11 não existe no banco")
        else:
            print(f"   Cliente 11 encontrado na lista!")
        
        # Formato para atualização do select
        clientes_validos = []
        for c in clientes:
            if c.nome and c.nome.strip():  # Mesmo filtro do template
                clientes_validos.append({
                    'id': c.id,
                    'nome': c.nome.strip(),
                    'cpf_cnpj': c.cpf_cnpj or '',
                    'cidade': c.cidade or ''
                })
        
        resultado = {
            'success': True,
            'clientes': clientes_validos,
            'total': len(clientes_validos),
            'debug_info': {
                'total_no_banco': len(clientes),
                'com_nome_valido': len(clientes_validos),
                'timestamp': str(dt.now())
            }
        }
        
        print(f" Retornando {resultado['total']} clientes válidos de {len(clientes)} no banco")
        return jsonify(resultado)
        
    except Exception as e:
        print(f" Erro na API de clientes: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@ordem_servico_bp.route('/api/clientes/test')
def api_clientes_test():
    """Rota de teste para debug."""
    return jsonify({
        'message': 'API de clientes funcionando!',
        'timestamp': str(dt.now()),
        'blueprint': 'ordem_servico',
        'success': True
    })

@ordem_servico_bp.route('/api/clientes/refresh')
def api_clientes_refresh():
    """API para forçar refresh dos clientes com função robusta."""
    try:
        print(" API /api/clientes/refresh chamada - REFRESH FORÇADO!")
        
        # Usar função robusta para buscar clientes
        clientes = buscar_clientes_ativos()
        
        # Debug: listar TODOS os clientes
        print("LISTA COMPLETA DE CLIENTES:")
        for i, cliente in enumerate(clientes):
            print(f"  📝 Cliente {i+1}: ID={cliente.id}, Nome='{cliente.nome}', Ativo={cliente.ativo}")
        
        # Aplicar mesmo filtro do template
        clientes_validos = []
        
        for c in clientes:
            if c.nome and c.nome.strip():  # Mesmo filtro do template
                clientes_validos.append({
                    'id': c.id,
                    'nome': c.nome.strip(),
                    'cpf_cnpj': c.cpf_cnpj or '',
                    'cidade': c.cidade or ''
                })
            else:
                print(f"⚠️ Cliente ignorado: ID={c.id}, Nome='{c.nome or 'SEM_NOME'}'")
        
        print(f" CLIENTES VÁLIDOS: {len(clientes_validos)}")
        
        resultado = {
            'success': True,
            'clientes': clientes_validos,
            'total': len(clientes_validos),
            'debug_info': {
                'total_no_banco': len(clientes),
                'com_nome_valido': len(clientes_validos),
                'timestamp': str(dt.now()),
                'refresh': True
            },
            'message': f'Lista atualizada! {len(clientes_validos)} clientes encontrados.'
        }
        
        print(f" RETORNANDO: {len(clientes_validos)} clientes válidos de {len(clientes)} totais")
        return jsonify(resultado)
        
    except Exception as e:
        print(f" Erro na API de clientes REFRESH: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@ordem_servico_bp.route('/api/equipamentos-cliente/<int:cliente_id>')
def api_equipamentos_cliente(cliente_id):
    """
    API para buscar histórico de equipamentos de um cliente.
    Retorna equipamentos únicos com seus detalhes das OS anteriores.
    """
    try:
        # Busca todas as OS do cliente (ativas, concluídas, etc)
        ordens = OrdemServico.query.filter_by(
            cliente_id=cliente_id,
            ativo=True
        ).order_by(OrdemServico.data_abertura.desc()).all()
        
        # Dicionário para armazenar equipamentos únicos
        # Chave: nome do equipamento (normalizado)
        # Valor: dados completos do equipamento mais recente
        equipamentos_dict = {}
        
        for ordem in ordens:
            if ordem.equipamento and ordem.equipamento.strip():
                # Normaliza o nome para comparação (minúsculas, sem espaços extras)
                nome_normalizado = ordem.equipamento.strip().lower()
                
                # Se ainda não temos este equipamento, ou se esta OS é mais recente
                if nome_normalizado not in equipamentos_dict:
                    equipamentos_dict[nome_normalizado] = {
                        'equipamento': ordem.equipamento.strip(),
                        'modelo': ordem.modelo or '',
                        'marca': ordem.marca or '',
                        'numero_serie': ordem.numero_serie or '',
                        'ultima_os': ordem.numero,
                        'data_ultima_os': ordem.data_abertura.strftime('%d/%m/%Y') if ordem.data_abertura else '',
                        'total_os': 1
                    }
                else:
                    # Incrementa contador de OS para este equipamento
                    equipamentos_dict[nome_normalizado]['total_os'] += 1
        
        # Converte para lista ordenada por nome
        equipamentos_lista = sorted(
            equipamentos_dict.values(),
            key=lambda x: x['equipamento']
        )
        
        return jsonify({
            'success': True,
            'equipamentos': equipamentos_lista,
            'total': len(equipamentos_lista)
        })
        
    except Exception as e:
        print(f"❌ Erro ao buscar equipamentos do cliente: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@ordem_servico_bp.route('/<int:id>/relatorio-pdf')
def gerar_relatorio_pdf(id):
    """
    Gera relatório em PDF da ordem de serviço.
    
    Args:
        id: ID da ordem de serviço
        com_imagens: parâmetro opcional para forçar inclusão/exclusão de imagens (0 ou 1)
        
    Returns:
        PDF file: Relatório da ordem de serviço em PDF
    """
    print(f"DEBUG PDF: Iniciando geração de PDF para OS ID: {id}")
    
    try:
        # Busca a ordem de serviço
        ordem = OrdemServico.query.get_or_404(id)
        print(f" DEBUG PDF: Ordem encontrada: {ordem.numero}")
        
        # Verifica se deve incluir imagens (parâmetro da URL ou configuração da OS)
        com_imagens_param = request.args.get('com_imagens')
        if com_imagens_param is not None:
            # Parâmetro da URL tem prioridade
            incluir_imagens = com_imagens_param == '1'
            print(f"DEBUG PDF: Incluir imagens (via URL): {incluir_imagens}")
        else:
            # Usa configuração salva na OS
            incluir_imagens = ordem.incluir_imagens_relatorio if hasattr(ordem, 'incluir_imagens_relatorio') else False
            print(f"DEBUG PDF: Incluir imagens (via config OS): {incluir_imagens}")
        
        # Temporariamente define o valor para renderização
        ordem_incluir_imagens_original = getattr(ordem, 'incluir_imagens_relatorio', False)
        ordem.incluir_imagens_relatorio = incluir_imagens
        
        # Calcula totais se necessário
        if not ordem.valor_servico:
            total_servicos = sum(item.valor_total for item in ordem.servicos) if hasattr(ordem, 'servicos') and ordem.servicos else 0
            ordem.valor_servico = Decimal(str(total_servicos))
            
        if not ordem.valor_pecas:
            total_produtos = sum(produto.valor_total for produto in ordem.produtos_utilizados) if hasattr(ordem, 'produtos_utilizados') and ordem.produtos_utilizados else 0
            ordem.valor_pecas = Decimal(str(total_produtos))
            
        # Debug dos produtos
        if hasattr(ordem, 'produtos_utilizados') and ordem.produtos_utilizados:
            print(f"DEBUG PDF: Produtos encontrados:")
            for i, produto in enumerate(ordem.produtos_utilizados, 1):
                print(f"  {i}. {produto.descricao}: Qtd={produto.quantidade} x R${produto.valor_unitario} = R${produto.valor_total}")
            print(f"DEBUG PDF: Total calculado: R$ {ordem.valor_pecas}")
        else:
            print(f"⚠️ DEBUG PDF: Nenhum produto encontrado!")
            
        if not ordem.valor_total:
            valor_servico = Decimal(str(ordem.valor_servico or 0))
            valor_pecas = Decimal(str(ordem.valor_pecas or 0))
            valor_desconto = Decimal(str(ordem.valor_desconto or 0))
            ordem.valor_total = valor_servico + valor_pecas - valor_desconto
        
        print(f"DEBUG PDF: Importando configurações...")
        # Importar configurações da empresa
        from app.configuracao.configuracao_utils import get_config
        config = get_config()
        
        print(f"DEBUG PDF: Renderizando template HTML...")
        print(f"🔍 TEMPLATE SENDO USADO: 'os/pdf_ordem_servico.html'")
        print(f"🔍 CAMINHO ABSOLUTO: {os.path.abspath(os.path.join('app', 'ordem_servico', 'templates', 'os', 'pdf_ordem_servico.html'))}")
        
        # Converter imagens anexadas para base64 se incluir_imagens estiver ativo
        anexos_base64 = {}
        if incluir_imagens and hasattr(ordem, 'anexos') and ordem.anexos:
            import base64
            print(f"🖼️ DEBUG PDF: Convertendo {len(ordem.anexos)} anexos para base64...")
            for anexo in ordem.anexos:
                print(f"  📁 Processando: {anexo.nome_original}")
                print(f"     - Tipo: {anexo.tipo_arquivo}")
                print(f"     - MIME: {anexo.mime_type}")
                print(f"     - Caminho salvo: {anexo.caminho}")
                
                if anexo.tipo_arquivo == 'image' or (anexo.mime_type and 'image' in anexo.mime_type):
                    try:
                        # PRIORIDADE 1: Usar conteúdo BLOB salvo no banco (funciona no Render)
                        if hasattr(anexo, 'conteudo') and anexo.conteudo:
                            print(f"     ✅ Usando conteúdo do BLOB no banco ({len(anexo.conteudo)} bytes)")
                            img_base64 = base64.b64encode(anexo.conteudo).decode('utf-8')
                            anexos_base64[str(anexo.id)] = img_base64
                            print(f"     ✅ Convertido do BLOB: {len(img_base64)} chars base64")
                        else:
                            # PRIORIDADE 2: Tentar ler do disco (desenvolvimento local)
                            print(f"     ⚠️ BLOB vazio, tentando ler do disco...")
                            possible_paths = [
                                anexo.caminho,  # Caminho completo salvo no banco
                                os.path.join(UPLOAD_FOLDER, anexo.nome_arquivo),  # Usando UPLOAD_FOLDER
                                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads', 'ordem_servico', 'anexos', anexo.nome_arquivo),
                                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'app', 'static', 'uploads', anexo.nome_arquivo),  # Caminho usado atualmente
                            ]
                            
                            arquivo_encontrado = None
                            for caminho_teste in possible_paths:
                                if os.path.exists(caminho_teste):
                                    arquivo_encontrado = caminho_teste
                                    print(f"     ✅ Arquivo encontrado em: {arquivo_encontrado}")
                                    break
                                else:
                                    print(f"     ❌ Não encontrado em: {caminho_teste}")
                            
                            if arquivo_encontrado:
                                # Lê o arquivo e converte para base64
                                with open(arquivo_encontrado, 'rb') as img_file:
                                    img_data = img_file.read()
                                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                                    anexos_base64[str(anexo.id)] = img_base64
                                    print(f"     ✅ Convertido do disco: {len(img_base64)} chars base64 | {len(img_data)} bytes")
                            else:
                                print(f"     ⚠️ ARQUIVO NÃO ENCONTRADO em nenhum caminho testado!")
                            
                    except Exception as e:
                        print(f"     ⚠️ ERRO ao converter {anexo.nome_original}: {str(e)}")
                        import traceback
                        print(f"     Stack: {traceback.format_exc()}")
            print(f"🖼️ DEBUG PDF: Total de imagens convertidas com sucesso: {len(anexos_base64)}/{len(ordem.anexos)}")
        
        # Renderiza o template HTML com timestamp para evitar cache
        html_content = render_template(
            'os/pdf_ordem_servico.html',
            ordem=ordem,
            now=dt.now,
            logo_base64=get_logo_base64(),  # Função para obter logo em base64
            config=config,  # Adicionar configurações
            timedelta=timedelta,  # Para cálculo de garantia
            timestamp=dt.now().isoformat(),  # Timestamp único para evitar cache
            anexos_base64=anexos_base64  # Imagens em base64
        )
        print(f"🔍 PRIMEIROS 200 CHARS DO HTML: {html_content[:200]}...")
        print(f" DEBUG PDF: Template renderizado com sucesso")
        
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
        
        # Retorna HTML otimizado para impressão com script de auto-download
        print(f"DEBUG PDF: Retornando HTML para impressão com auto-download...")
        
        # Adiciona script para forçar diálogo de impressão (salvar como PDF)
        script_auto_print = '''
        <script>
            window.onload = function() {
                // Abre automaticamente o diálogo de impressão
                window.print();
            };
        </script>
        '''
        
        # Injeta o script antes do </body>
        if '</body>' in html_content:
            html_content = html_content.replace('</body>', f'{script_auto_print}</body>')
        else:
            html_content += script_auto_print
        
        response = make_response(html_content)
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        # Sugere nome do arquivo para quando o usuário escolher "Salvar como PDF"
        response.headers['Content-Disposition'] = f'inline; filename="OS_{ordem.numero}_{dt.now().strftime("%Y%m%d")}.pdf"'
        
        print(f" DEBUG PDF: HTML retornado com sucesso (com auto-print)")
        return response
        
    except Exception as e:
        print(f" DEBUG PDF: Erro geral na geração de PDF: {str(e)}")
        print(f" DEBUG PDF: Tipo do erro geral: {type(e)}")
        import traceback
        print(f" DEBUG PDF: Stack trace: {traceback.format_exc()}")
        flash(f'Erro ao gerar relatório PDF: {str(e)}', 'error')
        return redirect(url_for('ordem_servico.visualizar', id=id))