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
from datetime import datetime, time, date, timedelta
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
            valor_entrada = safe_decimal_convert(request.form.get('valor_entrada', '0'), 0)
            
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
                numero_parcelas=safe_int_convert(request.form.get('numero_parcelas', '1'), default=1),
                valor_entrada=Decimal(valor_entrada) if valor_entrada else 0,
                data_primeira_parcela=data_primeira_parcela,
                data_vencimento_pagamento=data_vencimento_pagamento,
                # Novos campos para anexos e descrição de pagamento
                descricao_pagamento=request.form.get('descricao_pagamento', '').strip(),
                observacoes_anexos=request.form.get('observacoes_anexos', '').strip()
            )
            
            # Validações
            print(f"🔍 DEBUG: Validando título: '{ordem.titulo}'")
            if not ordem.titulo or ordem.titulo == 'OS sem título':
                # Se não há título, usar equipamento como referência
                if request.form.get('equipamento', '').strip():
                    ordem.titulo = f"OS - {request.form.get('equipamento', '').strip()}"
                else:
                    ordem.titulo = f"OS #{ordem.numero}"
            
            print(f"🔍 DEBUG: Validando cliente_id: '{ordem.cliente_id}'")
            if not ordem.cliente_id:
                flash('Cliente é obrigatório!', 'error')
                print("❌ DEBUG: Cliente é obrigatório")
                clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
                numero_os = OrdemServico.gerar_proximo_numero()
                return render_template('os/form.html', ordem=None, clientes=clientes, numero_os=numero_os, today=date.today())
            
            # Adiciona ordem à sessão (transação será confirmada no final)
            db.session.add(ordem)
            # Flush para garantir que ordem.id seja populado antes de criar os itens
            db.session.flush()
            
            # Processa itens de serviço
            print("🔍 DEBUG: Processando itens de serviço com nova estrutura de tipos")
            
            # Primeiro tenta coletar dados da estrutura de arrays simples (nova)
            servicos_desc_array = request.form.getlist('servico_descricao[]')
            servicos_tipo_array = request.form.getlist('servico_tipo[]')
            servicos_quantidade_array = request.form.getlist('servico_quantidade[]')
            servicos_valor_array = request.form.getlist('servico_valor[]')
            
            print(f"🔍 DEBUG: Arrays simples encontrados - desc: {len(servicos_desc_array)}, tipo: {len(servicos_tipo_array)}, qtd: {len(servicos_quantidade_array)}, valor: {len(servicos_valor_array)}")
            
            # Se encontrou arrays simples, usa essa estrutura
            servicos_data = []
            if servicos_desc_array:
                print("🔍 DEBUG: Usando estrutura de arrays simples para serviços (novo)")
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
                print("🔍 DEBUG: Usando estrutura indexada para serviços (fallback)")
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
            
            # NOTE: parcelas processing moved to after total calculation (see below)
            
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
                            db.session.add(anexo)
                            
                        except Exception as e:
                            flash(f'Erro ao salvar arquivo {file.filename}: {str(e)}', 'warning')
                    elif file and file.filename and not allowed_file(file.filename):
                        flash(f'Tipo de arquivo não permitido: {file.filename}', 'warning')
            
            # Recalcula valor total considerando itens
            ordem.valor_total = ordem.valor_total_calculado_novo

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

            # Recalcula e atualiza valor total antes de confirmar transação
            ordem.valor_total = ordem.valor_total_calculado_novo
            print(f"🔍 DEBUG: Valor total calculado: R$ {ordem.valor_total}")

            try:
                print("🔍 DEBUG: Tentando fazer commit da ordem...")
                db.session.commit()
                print("✅ DEBUG: Commit realizado com sucesso!")
            except Exception as commit_error:
                print(f"❌ DEBUG: Erro no commit: {commit_error}")
                db.session.rollback()
                raise

            flash(f'✅ Ordem de Serviço {ordem.numero} criada com sucesso! Você pode visualizar, editar ou gerar o PDF.', 'success')
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

            if novo_status != ordem.status:
                if novo_status == 'em_andamento' and ordem.status == 'aberta':
                    ordem.data_inicio = datetime.now()
                elif novo_status == 'concluida' and ordem.status != 'concluida' and not ordem.data_conclusao:
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
            print(f"🔍 DEBUG: Removendo {len(ordem.servicos)} serviços antigos via loop delete")
            servicos_removidos = 0
            for item_existente in list(ordem.servicos):
                print(f"  🗑️ Removendo serviço: {item_existente.descricao}")
                db.session.delete(item_existente)
                servicos_removidos += 1
            print(f"✅ {servicos_removidos} serviços removidos")
            
            # Processa itens de serviço com nova estrutura de tipos
            print("🔍 DEBUG: Processando itens de serviço com nova estrutura de tipos (edição)")
            
            # Primeiro tenta coletar dados da estrutura de arrays simples (nova)
            servicos_desc_array = request.form.getlist('servico_descricao[]')
            servicos_tipo_array = request.form.getlist('servico_tipo[]')
            servicos_quantidade_array = request.form.getlist('servico_quantidade[]')
            servicos_valor_array = request.form.getlist('servico_valor[]')
            
            print(f"🔍 DEBUG: Arrays simples encontrados - desc: {len(servicos_desc_array)}, tipo: {len(servicos_tipo_array)}, qtd: {len(servicos_quantidade_array)}, valor: {len(servicos_valor_array)}")
            
            # Se encontrou arrays simples, usa essa estrutura
            servicos_data = []
            if servicos_desc_array:
                print("🔍 DEBUG: Usando estrutura de arrays simples para serviços")
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
                print("🔍 DEBUG: Usando estrutura indexada para serviços (fallback)")
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
            
            print(f"🔍 DEBUG: Coletados {len(servicos_data)} serviços para edição: {servicos_data}")

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
            print(f"✅ {servicos_adicionados} serviços adicionados")
            
            # Processa produtos utilizados - Remove antigos e adiciona novos
            print(f"🔍 DEBUG: Removendo {len(ordem.produtos_utilizados)} produtos antigos via loop delete")
            produtos_removidos = 0
            for produto_existente in list(ordem.produtos_utilizados):
                print(f"  🗑️ Removendo produto: {produto_existente.descricao}")
                db.session.delete(produto_existente)
                produtos_removidos += 1
            print(f"✅ {produtos_removidos} produtos removidos")
            
            produtos_desc = request.form.getlist('produto_descricao[]')
            produtos_qtd = request.form.getlist('produto_quantidade[]')
            produtos_valor = request.form.getlist('produto_valor[]')

            print(f"🔍 DEBUG: Processando {len(produtos_desc)} produtos do formulário")
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
            print(f"✅ {produtos_adicionados} produtos adicionados")
            
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
                            db.session.add(anexo)
                            
                        except Exception as e:
                            flash(f'Erro ao salvar arquivo {file.filename}: {str(e)}', 'warning')
                    elif file and file.filename and not allowed_file(file.filename):
                        flash(f'Tipo de arquivo não permitido: {file.filename}', 'warning')
            
            # Recalcula valor total novamente antes do commit final
            ordem.valor_total = ordem.valor_total_calculado

            # Commit final: salva novas linhas de serviços/produtos/parcelas/anexos
            try:
                db.session.commit()
                print(f"🏁 DEBUG: Ordem de Serviço salva com sucesso! Total final: R$ {ordem.valor_total}")
            except Exception as commit_err:
                try:
                    db.session.rollback()
                except Exception:
                    pass
                raise

            flash(f'✅ Ordem de Serviço {ordem.numero} atualizada com sucesso!', 'success')
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
            config=config,  # Adicionar configurações
            timedelta=timedelta  # Para cálculo de garantia
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