from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response, send_file
from aplicacao.extensoes import db
from .os_model import OrdemServico
from .simple_pdf_generator import SimplePDFGenerator
from datetime import datetime, time, date, timedelta
from sqlalchemy.orm import joinedload
from decimal import Decimal
import json
import os
import uuid
from werkzeug.utils import secure_filename

# Importar serviço financeiro para integração automática
try:
    from aplicacao.financeiro.lancamento_os_service import gerar_lancamentos_financeiro
    FINANCEIRO_DISPONIVEL = True
except ImportError:
    print("AVISO: Módulo financeiro não disponível. Integração desabilitada.")
    FINANCEIRO_DISPONIVEL = False

# Blueprint para Ordem de Serviço
bp = Blueprint('ordens', __name__, url_prefix='/ordens')

def integrar_financeiro_automatico(ordem, status_anterior=None):
    """
    Integração automática com módulo financeiro.
    
    Regras:
    - Quando status = 'Concluída' E status_pagamento = 'Pago' → Criar lançamentos pagos
    - Quando status = 'Concluída' E status_pagamento = 'Pendente' → Criar lançamentos pendentes
    """
    if not FINANCEIRO_DISPONIVEL:
        return
    
    try:
        # Verificar se deve gerar lançamentos
        deve_gerar = (
            ordem.status == 'Concluída' and 
            ordem.valor_total and 
            float(ordem.valor_total) > 0
        )
        
        if not deve_gerar:
            print(f"DEBUG FINANCEIRO: Não gerar para OS {ordem.codigo} - Status: {ordem.status}, Valor: {ordem.valor_total}")
            return
        
        print(f"DEBUG FINANCEIRO: Gerando lançamentos para OS {ordem.codigo}")
        print(f"  - Status: {ordem.status}")
        print(f"  - Status Pagamento: {ordem.status_pagamento}")
        print(f"  - Valor Total: R$ {ordem.valor_total}")
        print(f"  - Forma Pagamento: {ordem.forma_pagamento}")
        
        # Preparar dados para lançamento
        valor_total = Decimal(str(ordem.valor_total))
        forma_pagamento = ordem.forma_pagamento or 'dinheiro'
        qtd_parcelas = ordem.qtd_parcelas or 1
        valor_entrada = Decimal(str(ordem.valor_entrada or 0))
        
        # Criar cronograma personalizado se há parcelas JSON
        schedule_custom = None
        if ordem.parcelas_json:
            try:
                parcelas_data = json.loads(ordem.parcelas_json)
                if parcelas_data and len(parcelas_data) > 0:
                    schedule_custom = []
                    for parcela in parcelas_data:
                        valor = Decimal(str(parcela['valor']))
                        data_venc = datetime.strptime(parcela['data_vencimento'], '%Y-%m-%d').date()
                        schedule_custom.append((valor, data_venc))
                    print(f"  - Cronograma personalizado: {len(schedule_custom)} parcelas")
            except Exception as e:
                print(f"  - ERRO ao processar parcelas JSON: {e}")
        
        # Gerar lançamentos financeiros
        if schedule_custom:
            lancamentos = gerar_lancamentos_financeiro(
                ordem,
                forma_pagamento=forma_pagamento,
                valor_total=valor_total,
                schedule_custom=schedule_custom
            )
        else:
            lancamentos = gerar_lancamentos_financeiro(
                ordem,
                forma_pagamento=forma_pagamento,
                valor_total=valor_total,
                parcelas=qtd_parcelas,
                entrada=valor_entrada
            )
        
        # Se a OS está marcada como "Paga", marcar todos os lançamentos como pagos
        if ordem.status_pagamento == 'Pago':
            print(f"  - Marcando {len(lancamentos)} lançamentos como pagos")
            for lanc in lancamentos:
                lanc.status = 'Pago'
                lanc.data_pagamento = ordem.data_conclusao or date.today()
            db.session.commit()
            
        # TAMBÉM atualizar lançamentos existentes se mudou para "Pago"
        elif ordem.status_pagamento == 'Pago':
            # Buscar lançamentos existentes desta OS
            from aplicacao.financeiro.lancamento_os_model import LancamentoFinanceiroOS
            lancamentos_existentes = LancamentoFinanceiroOS.query.filter_by(os_id=ordem.id).all()
            if lancamentos_existentes:
                print(f"  - Atualizando {len(lancamentos_existentes)} lançamentos existentes para PAGO")
                for lanc in lancamentos_existentes:
                    lanc.status = 'Pago'
                    lanc.data_pagamento = ordem.data_conclusao or date.today()
                db.session.commit()
        
        print(f"✅ FINANCEIRO: {len(lancamentos)} lançamentos criados para OS {ordem.codigo}")
        
        # Adicionar mensagem de feedback para o usuário
        if ordem.status_pagamento == 'Pago':
            flash(f'💰 OS marcada como PAGA - {len(lancamentos)} lançamento(s) financeiro(s) criado(s) automaticamente!', 'info')
        else:
            flash(f'📋 OS concluída - {len(lancamentos)} lançamento(s) financeiro(s) pendente(s) criado(s)!', 'info')
        
    except Exception as e:
        print(f"❌ ERRO na integração financeira para OS {ordem.codigo}: {e}")
        # Não interromper o fluxo principal em caso de erro

# Configurações de upload
UPLOAD_FOLDER = 'uploads/ordem_servico'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt', 'zip', 'rar'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    """Verifica se a extensão do arquivo é permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def format_file_size(size_bytes):
    """Formatar tamanho do arquivo para exibição"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f}{size_names[i]}"

def salvar_arquivo(file, ordem_id):
    """Salva arquivo no diretório da ordem e retorna informações"""
    try:
        if not file or not file.filename:
            return None
            
        if not allowed_file(file.filename):
            print(f"Arquivo {file.filename} não permitido")
            return None
            
        # Verificar tamanho do arquivo
        file.seek(0, 2)  # Ir para o final do arquivo
        file_size = file.tell()
        file.seek(0)  # Voltar ao início
        
        if file_size > MAX_FILE_SIZE:
            print(f"Arquivo {file.filename} muito grande: {file_size} bytes")
            return None
        
        # Gerar nome seguro
        filename_seguro = secure_filename(file.filename)
        nome_unico = f"{uuid.uuid4()}_{filename_seguro}"
        
        # Criar diretório se não existir
        upload_dir = os.path.join(UPLOAD_FOLDER, str(ordem_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Salvar arquivo
        filepath = os.path.join(upload_dir, nome_unico)
        file.save(filepath)
        
        # Retornar informações do arquivo
        content_type = file.content_type or 'application/octet-stream'
        return {
            'nome_arquivo': nome_unico,
            'nome_original': file.filename,
            'tamanho': file_size,
            'tamanho_formatado': format_file_size(file_size),
            'tipo_arquivo': content_type,  # Campo novo
            'tipo': content_type,          # Campo antigo para compatibilidade
            'data_upload': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        print(f"Erro ao salvar arquivo: {e}")
        return None

def processar_dados_formulario(form_data, ordem=None):
    """Processa os dados do formulário e popula a ordem de serviço"""
    try:
        if ordem is None:
            ordem = OrdemServico()
            # GERAR CÓDIGO PARA NOVA OS
            ordem.codigo = ordem.gerar_codigo()
            print(f"DEBUG: Código gerado para nova OS: {ordem.codigo}")
        
        # BACKUP DOS ANEXOS ANTES DE QUALQUER PROCESSAMENTO
        backup_anexos = ordem.anexos_dados
        
        # 1. Cliente
        cliente_id = form_data.get('cliente_id')
        print(f"DEBUG: Dados do formulário recebidos: {dict(form_data)}")
        print(f"DEBUG: cliente_id recebido: '{cliente_id}'")
        
        if not cliente_id:
            raise ValueError('Cliente é obrigatório')
        ordem.cliente_id = int(cliente_id)
        
        # 2. Dados básicos da OS
        ordem.solicitante = form_data.get('solicitante', '').strip()
        ordem.contato = form_data.get('contato', '').strip()
        
        # 3. Datas
        if form_data.get('data_emissao'):
            ordem.data_emissao = datetime.strptime(form_data.get('data_emissao'), '%Y-%m-%d').date()
        else:
            ordem.data_emissao = datetime.now().date()
            
        if form_data.get('previsao_conclusao'):
            ordem.previsao_conclusao = datetime.strptime(form_data.get('previsao_conclusao'), '%Y-%m-%d').date()
        
        # 4. Status e prioridade
        ordem.status = form_data.get('status', 'Aberta')
        ordem.prioridade = form_data.get('prioridade', 'Media')
        
        # 5. Valores financeiros
        valor_total = form_data.get('valor_total', '0').replace(',', '.')
        ordem.valor_total = float(valor_total) if valor_total else 0.0
        
        valor_deslocamento = form_data.get('valor_deslocamento', '0').replace(',', '.')
        ordem.valor_deslocamento = float(valor_deslocamento) if valor_deslocamento else 0.0
        
        # 6. Forma de pagamento
        ordem.forma_pagamento = form_data.get('forma_pagamento', '').strip()
        
        # 7. Localização
        ordem.endereco = form_data.get('endereco', '').strip()
        ordem.bairro = form_data.get('bairro', '').strip()
        ordem.cidade = form_data.get('cidade', '').strip()
        ordem.uf = form_data.get('uf', '').strip()
        ordem.cep = form_data.get('cep', '').strip()
        
        # 8. Equipamento
        ordem.equipamento_nome = form_data.get('equipamento_nome', '').strip()
        ordem.equipamento_marca = form_data.get('equipamento_marca', '').strip()
        ordem.equipamento_modelo = form_data.get('equipamento_modelo', '').strip()
        ordem.equipamento_numero_serie = form_data.get('equipamento_numero_serie', '').strip()
        ordem.equipamento_acessorios = form_data.get('equipamento_acessorios', '').strip()
        ordem.equipamento_problema = form_data.get('equipamento_problema', '').strip()
        
        # 9. Execução do serviço
        ordem.tecnico_responsavel = form_data.get('tecnico_responsavel', '').strip()
        ordem.tipo_servico = form_data.get('tipo_servico', '').strip()
        
        # 9.2 HORÁRIOS - PROCESSAMENTO ADICIONADO
        if form_data.get('hora_inicio'):
            try:
                ordem.hora_inicio = datetime.strptime(form_data.get('hora_inicio'), '%H:%M').time()
            except ValueError:
                ordem.hora_inicio = None
        else:
            ordem.hora_inicio = None
            
        if form_data.get('hora_termino'):
            try:
                ordem.hora_termino = datetime.strptime(form_data.get('hora_termino'), '%H:%M').time()
            except ValueError:
                ordem.hora_termino = None
        else:
            ordem.hora_termino = None
        
        # Calcular total de horas automaticamente
        if ordem.hora_inicio and ordem.hora_termino:
            inicio = datetime.combine(datetime.today(), ordem.hora_inicio)
            termino = datetime.combine(datetime.today(), ordem.hora_termino)
            if termino < inicio:  # Passou da meia-noite
                termino += timedelta(days=1)
            diff = termino - inicio
            ordem.total_horas = diff.total_seconds() / 3600
        else:
            ordem.total_horas = 0.0
        
        print(f"DEBUG: Horários processados - Início: {ordem.hora_inicio}, Término: {ordem.hora_termino}, Total: {ordem.total_horas}h")
        
        # 9.1 Data de conclusão - permite salvamento independente do status
        status_atual = form_data.get('status', 'Aberta')
        data_conclusao_form = form_data.get('data_conclusao', '').strip()
        
        if data_conclusao_form:
            # Se foi informada uma data, usar ela (independente do status)
            try:
                ordem.data_conclusao = datetime.strptime(data_conclusao_form, '%Y-%m-%d').date()
                print(f"DEBUG: Data de conclusão definida pelo usuário: {ordem.data_conclusao}")
            except ValueError as e:
                print(f"DEBUG: Erro ao converter data de conclusão '{data_conclusao_form}': {e}")
                ordem.data_conclusao = None
        elif status_atual in ['Concluida', 'Concluída']:
            # Se status é "Concluída" mas não foi informada data, auto-preencher com hoje
            ordem.data_conclusao = datetime.now().date()
            print(f"DEBUG: Data de conclusão auto-preenchida (status concluída): {ordem.data_conclusao}")
        else:
            # Se não foi informada data e status não é concluída, manter valor atual ou None
            if not hasattr(ordem, 'data_conclusao') or ordem.data_conclusao is None:
                ordem.data_conclusao = None
            print(f"DEBUG: Data de conclusão mantida: {ordem.data_conclusao}")
        
        # 9.3. Descrições detalhadas - tratamento robusto para evitar None
        problema_descrito_raw = form_data.get('problema_descrito', '')
        if problema_descrito_raw and problema_descrito_raw.strip() and problema_descrito_raw.strip().lower() != 'none':
            ordem.problema_descrito = problema_descrito_raw.strip()
        else:
            ordem.problema_descrito = ''
            
        servico_realizado_raw = form_data.get('descricao_servico_realizado', '')
        if servico_realizado_raw and servico_realizado_raw.strip() and servico_realizado_raw.strip().lower() != 'none':
            ordem.descricao_servico_realizado = servico_realizado_raw.strip()
        else:
            ordem.descricao_servico_realizado = ''
            
        ordem.servico_realizado = form_data.get('servico_realizado', '').strip()
        
        print(f"DEBUG: Problema descrito FINAL: '{ordem.problema_descrito}'")
        print(f"DEBUG: Serviço realizado FINAL: '{ordem.descricao_servico_realizado}'")
        
        # 10. Observações
        ordem.observacoes = form_data.get('observacoes', '').strip()
        ordem.observacoes_tecnico = form_data.get('observacoes_tecnico', '').strip()
        ordem.observacoes_internas = form_data.get('observacoes_internas', '').strip()
        ordem.outras_informacoes = form_data.get('outras_informacoes', '').strip()
        
        # 11. Dados JSON (serviços, produtos, parcelas)
        servicos_raw = form_data.get('servicos_json', '[]')
        produtos_raw = form_data.get('produtos_json', '[]')
        parcelas_raw = form_data.get('parcelas_json', '[]')
        
        # DEBUG: Log detalhado dos dados JSON recebidos
        print(f"[DEBUG JSON] Servicos recebido (len={len(servicos_raw)}): {servicos_raw}")
        print(f"[DEBUG JSON] Produtos recebido (len={len(produtos_raw)}): {produtos_raw}")
        print(f"[DEBUG JSON] Parcelas recebido (len={len(parcelas_raw)}): {parcelas_raw}")
        
        # Validar JSONs antes de salvar
        try:
            if servicos_raw and servicos_raw != '[]':
                json.loads(servicos_raw)  # Teste de validade
        except json.JSONDecodeError as e:
            print(f"[ERRO JSON] Servicos JSON inválido: {e}")
            servicos_raw = '[]'
            
        try:
            if produtos_raw and produtos_raw != '[]':
                json.loads(produtos_raw)  # Teste de validade
        except json.JSONDecodeError as e:
            print(f"[ERRO JSON] Produtos JSON inválido: {e}")
            produtos_raw = '[]'
            
        try:
            if parcelas_raw and parcelas_raw != '[]':
                json.loads(parcelas_raw)  # Teste de validade
        except json.JSONDecodeError as e:
            print(f"[ERRO JSON] Parcelas JSON inválido: {e}")
            parcelas_raw = '[]'
        
        ordem.servicos_dados = servicos_raw
        ordem.produtos_dados = produtos_raw
        ordem.parcelas_json = parcelas_raw
        ordem.schedule_json = form_data.get('schedule_json', '')
        
        # 12. PRESERVAR ANEXOS - NUNCA sobrescrever aqui
        if backup_anexos is not None:
            ordem.anexos_dados = backup_anexos
        
        # 13. Processar novos anexos se houver
        anexos_info = []
        if hasattr(request, 'files') and 'arquivos_anexo' in request.files:
            files = request.files.getlist('arquivos_anexo')
            for file in files:
                if file and file.filename:
                    anexos_info.append(file)
        
        # Armazenar novos anexos temporariamente
        ordem._anexos_temp = anexos_info
        
        return ordem
        
    except ValueError as e:
        raise e
    except Exception as e:
        raise ValueError(f'Erro ao processar dados do formulário: {str(e)}')

@bp.route('/')
def listar_ordens():
    """Lista todas as ordens de serviço (READ)"""
    try:
        # Buscar ordens ativas ordenadas por data de emissão (mais recente primeiro)
        ordens = OrdemServico.query.options(
            joinedload(OrdemServico.cliente)
        ).filter_by(ativo=True).order_by(OrdemServico.data_emissao.desc()).all()
        
        return render_template('ordem_servico/lista.html', ordens=ordens)
        
    except Exception as e:
        print(f"DEBUG ERRO na listagem: {str(e)}")
        flash(f'Erro ao carregar lista de ordens: {str(e)}', 'error')
        return render_template('ordem_servico/lista.html', ordens=[])

@bp.route('/nova', methods=['GET', 'POST'])
def criar_ordem():
    """Criar nova ordem de serviço (CREATE)"""
    if request.method == 'POST':
        try:
            # Processar dados do formulário
            nova_ordem = processar_dados_formulario(request.form)
            
            # Salvar no banco de dados
            db.session.add(nova_ordem)
            db.session.commit()
            
            # Processar anexos após ter o ID da ordem
            if hasattr(nova_ordem, '_anexos_temp') and nova_ordem._anexos_temp:
                anexos_processados = []
                for file in nova_ordem._anexos_temp:
                    anexo_info = salvar_arquivo(file, nova_ordem.id)
                    if anexo_info:
                        anexos_processados.append(anexo_info)
                
                if anexos_processados:
                    nova_ordem.anexos_dados = json.dumps(anexos_processados)
                    db.session.commit()
            
            # Criar lançamento financeiro automático se necessário
            nova_ordem.criar_lancamento_financeiro()
            
            # INTEGRAÇÃO AUTOMÁTICA COM FINANCEIRO
            print(f"DEBUG: Verificando integração financeira para nova OS {nova_ordem.codigo}")
            integrar_financeiro_automatico(nova_ordem)
            
            flash(f'Ordem de Serviço {nova_ordem.codigo} criada com sucesso!', 'success')
            print(f"DEBUG: OS {nova_ordem.codigo} criada com ID {nova_ordem.id}")
            
            return redirect(url_for('ordens.visualizar_ordem', ordem_id=nova_ordem.id))
            
        except ValueError as e:
            db.session.rollback()
            print(f"ERRO de validação ao criar OS: {str(e)}")
            flash(f'Erro de validação: {str(e)}', 'error')
            
        except Exception as e:
            db.session.rollback()
            print(f"ERRO inesperado ao criar OS: {str(e)}")
            flash(f'Erro ao criar ordem de serviço: {str(e)}', 'error')
    
    # Gerar código para nova OS (apenas para GET)
    temp_ordem = OrdemServico()
    codigo_gerado = temp_ordem.gerar_codigo()
    
    # Buscar todos os clientes para o autocomplete
    from aplicacao.cliente.cliente_model import Cliente
    from aplicacao.servico.servico_model import Servico
    from aplicacao.produto.produto_model import Produto
    
    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
    servicos = Servico.query.filter_by(ativo=True).order_by(Servico.nome).all()
    produtos = Produto.query.filter_by(ativo=True).order_by(Produto.nome).all()
    
    return render_template('ordem_servico/cadastro_new.html', 
                         codigo_gerado=codigo_gerado, 
                         clientes=clientes,
                         servicos=servicos,
                         produtos=produtos,
                         anexos_salvos=[])

@bp.route('/<int:ordem_id>')
def visualizar_ordem(ordem_id):
    """Visualizar ordem de serviço específica (READ)"""
    try:
        ordem = OrdemServico.query.get_or_404(ordem_id)
        
        if not ordem.ativo:
            flash('Esta ordem de serviço foi removida.', 'warning')
            return redirect(url_for('ordens.listar_ordens'))
        
        return render_template('os_visualizar.html', ordem=ordem)
        
    except Exception as e:
        print(f"DEBUG ERRO na visualização: {str(e)}")
        flash(f'Erro ao carregar ordem de serviço: {str(e)}', 'error')
        return redirect(url_for('ordens.listar_ordens'))

@bp.route('/<int:ordem_id>/editar', methods=['GET', 'POST'])
def editar_ordem(ordem_id):
    """Editar ordem de serviço (UPDATE) - PRESERVAÇÃO GARANTIDA DE ANEXOS"""
    print(f"🔥 DEBUG: ACESSANDO ROTA DE EDIÇÃO - ID: {ordem_id}")
    print(f"🔥 DEBUG: Método da requisição: {request.method}")
    
    try:
        print(f"🔥 DEBUG: Buscando ordem no banco...")
        ordem = OrdemServico.query.get_or_404(ordem_id)
        print(f"🔥 DEBUG: Ordem encontrada: {ordem.codigo} - Ativo: {ordem.ativo}")
        
        # Verificar se a ordem está ativa (considerando NULL como ativo)
        if ordem.ativo is False:
            print(f"🔥 DEBUG: Ordem inativa - redirecionando")
            flash('Esta ordem de serviço foi removida e não pode ser editada.', 'warning')
            return redirect(url_for('ordens.listar_ordens'))
        
        if request.method == 'POST':
            try:
                print(f"DEBUG: INICIANDO EDIÇÃO DA ORDEM {ordem_id}")
                
                # STEP 1: BACKUP ABSOLUTO DOS ANEXOS
                anexos_backup = ordem.anexos_dados
                print(f"DEBUG: Backup de anexos criado. Dados brutos: {anexos_backup}")
                print(f"DEBUG: Backup de anexos criado: {len(json.loads(anexos_backup)) if anexos_backup else 0} anexos")
                
                # STEP 2: Processar dados do formulário (que já preserva anexos)
                ordem_atualizada = processar_dados_formulario(request.form, ordem)
                
                # STEP 3: FORÇA preservação dos anexos
                ordem.anexos_dados = anexos_backup
                print(f"DEBUG: Anexos forçadamente preservados. Valor atual: {ordem.anexos_dados}")
                
                # STEP 4: Salvar alterações no banco
                db.session.commit()
                print(f"DEBUG: Dados salvos no banco. Anexos após commit: {ordem.anexos_dados}")
                
                # STEP 5: Processar NOVOS anexos se houver
                if hasattr(ordem, '_anexos_temp') and ordem._anexos_temp:
                    print(f"DEBUG: Processando {len(ordem._anexos_temp)} novos anexos")
                    
                    # Carregar anexos existentes
                    anexos_existentes = []
                    if ordem.anexos_dados:
                        try:
                            anexos_existentes = json.loads(ordem.anexos_dados)
                        except Exception as e:
                            print(f"DEBUG: ERRO ao carregar anexos existentes: {e}")
                            anexos_existentes = []
                    
                    # Processar novos anexos
                    anexos_novos = []
                    for file in ordem._anexos_temp:
                        anexo_info = salvar_arquivo(file, ordem.id)
                        if anexo_info:
                            anexos_novos.append(anexo_info)
                    
                    # Combinar anexos existentes + novos
                    todos_anexos = anexos_existentes + anexos_novos
                    ordem.anexos_dados = json.dumps(todos_anexos)
                    db.session.commit()
                    print(f"DEBUG: Anexos finais salvos: {len(todos_anexos)} total")
                else:
                    print(f"DEBUG: Nenhum novo anexo para processar")
                
                # STEP 6: Criar lançamento financeiro se necessário
                ordem.criar_lancamento_financeiro()
                
                # STEP 7: INTEGRAÇÃO AUTOMÁTICA COM FINANCEIRO
                print(f"DEBUG: Verificando integração financeira para OS {ordem.codigo}")
                integrar_financeiro_automatico(ordem)
                
                flash(f'✅ Ordem de Serviço {ordem.codigo} foi atualizada com sucesso!', 'success')
                print(f"DEBUG: OS {ordem.codigo} atualizada com sucesso")
                
                # Permanecer na página de edição
                return redirect(url_for('ordens.editar_ordem', ordem_id=ordem.id))
                
            except ValueError as e:
                db.session.rollback()
                print(f"ERRO de validação ao atualizar OS: {str(e)}")
                flash(f'Erro de validação: {str(e)}', 'error')
                
            except Exception as e:
                db.session.rollback()
                print(f"ERRO inesperado ao atualizar OS: {str(e)}")
                flash(f'Erro ao atualizar ordem de serviço: {str(e)}', 'error')
        
        # Para GET: Preparar dados para edição
        print(f"🔥 DEBUG: Preparando dados para GET - carregando dados relacionados...")
        
        from aplicacao.cliente.cliente_model import Cliente
        from aplicacao.servico.servico_model import Servico
        from aplicacao.produto.produto_model import Produto
        
        print(f"🔥 DEBUG: Carregando clientes...")
        clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
        print(f"🔥 DEBUG: {len(clientes)} clientes carregados")
        
        print(f"🔥 DEBUG: Carregando serviços...")
        servicos = Servico.query.filter_by(ativo=True).order_by(Servico.nome).all()
        print(f"🔥 DEBUG: {len(servicos)} serviços carregados")
        
        print(f"🔥 DEBUG: Carregando produtos...")
        produtos = Produto.query.filter_by(ativo=True).order_by(Produto.nome).all()
        print(f"🔥 DEBUG: {len(produtos)} produtos carregados")
        
        # Processar anexos salvos para exibição
        anexos_salvos = []
        if ordem.anexos_dados:
            try:
                anexos_salvos = json.loads(ordem.anexos_dados)
                print(f"DEBUG: Carregando {len(anexos_salvos)} anexos para edição")
            except Exception as e:
                print(f"DEBUG: Erro ao carregar anexos para edição: {e}")
                anexos_salvos = []
        
        # Processar outros dados salvos
        servicos_salvos = []
        produtos_salvos = []
        parcelas_salvas = []
        
        if ordem.servicos_dados:
            try:
                servicos_salvos = json.loads(ordem.servicos_dados)
                # Validar e corrigir tipos de dados
                for servico in servicos_salvos:
                    if 'valor_hora' in servico:
                        servico['valor_hora'] = float(servico['valor_hora']) if servico['valor_hora'] else 0.0
                    if 'valor_total' in servico:
                        servico['valor_total'] = float(servico['valor_total']) if servico['valor_total'] else 0.0
                    if 'quantidade' in servico:
                        servico['quantidade'] = float(servico['quantidade']) if servico['quantidade'] else 0.0
                print(f"DEBUG EDIÇÃO: Carregados {len(servicos_salvos)} serviços: {servicos_salvos}")
            except Exception as e:
                print(f"DEBUG EDIÇÃO: Erro ao carregar serviços: {e}")
                print(f"DEBUG EDIÇÃO: Raw servicos_dados: {repr(ordem.servicos_dados)}")
                servicos_salvos = []
        
        if ordem.produtos_dados:
            try:
                produtos_salvos = json.loads(ordem.produtos_dados)
                # Validar e corrigir tipos de dados
                for produto in produtos_salvos:
                    if 'valor_unitario' in produto:
                        produto['valor_unitario'] = float(produto['valor_unitario']) if produto['valor_unitario'] else 0.0
                    if 'valor_total' in produto:
                        produto['valor_total'] = float(produto['valor_total']) if produto['valor_total'] else 0.0
                    if 'quantidade' in produto:
                        produto['quantidade'] = float(produto['quantidade']) if produto['quantidade'] else 0.0
                print(f"DEBUG EDIÇÃO: Carregados {len(produtos_salvos)} produtos: {produtos_salvos}")
            except Exception as e:
                print(f"DEBUG EDIÇÃO: Erro ao carregar produtos: {e}")
                print(f"DEBUG EDIÇÃO: Raw produtos_dados: {repr(ordem.produtos_dados)}")
                produtos_salvos = []
        
        if ordem.parcelas_json:
            try:
                parcelas_salvas = json.loads(ordem.parcelas_json)
                # Validar e corrigir tipos de dados
                for parcela in parcelas_salvas:
                    if 'valor' in parcela:
                        parcela['valor'] = float(parcela['valor']) if parcela['valor'] else 0.0
                print(f"DEBUG EDIÇÃO: Carregadas {len(parcelas_salvas)} parcelas: {parcelas_salvas}")
            except Exception as e:
                print(f"DEBUG EDIÇÃO: Erro ao carregar parcelas: {e}")
                print(f"DEBUG EDIÇÃO: Raw parcelas_json: {repr(ordem.parcelas_json)}")
                parcelas_salvas = []
        
        print(f"🔥 DEBUG: Preparando render_template...")
        print(f"🔥 DEBUG: ordem_servico.id = {ordem.id}")
        print(f"🔥 DEBUG: anexos_salvos = {len(anexos_salvos)} itens")
        print(f"🔥 DEBUG: servicos_salvos = {len(servicos_salvos)} itens")
        print(f"🔥 DEBUG: produtos_salvos = {len(produtos_salvos)} itens")
        print(f"🔥 DEBUG: parcelas_salvas = {len(parcelas_salvas)} itens")
        
        return render_template('ordem_servico/cadastro_new.html',
                             ordem_servico=ordem,
                             clientes=clientes,
                             servicos=servicos,
                             produtos=produtos,
                             anexos_salvos=anexos_salvos,
                             servicos_salvos=servicos_salvos,
                             produtos_salvos=produtos_salvos,
                             parcelas_salvas=parcelas_salvas)
        
    except Exception as e:
        import traceback
        print(f"🔥 DEBUG ERRO na edição: {str(e)}")
        print(f"🔥 DEBUG TRACEBACK:")
        print(traceback.format_exc())
        flash(f'Erro ao processar edição: {str(e)}', 'error')
        return redirect(url_for('ordens.listar_ordens'))

# Resto das funções...
@bp.route('/<int:os_id>/pdf')
def gerar_pdf(os_id):
    """Gera PDF da ordem de serviço"""
    try:
        os = OrdemServico.query.options(joinedload(OrdemServico.cliente)).get_or_404(os_id)
        
        pdf_generator = SimplePDFGenerator()
        pdf_bytes = pdf_generator.generate_pdf(os)
        
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="OS_{os.codigo}_JSP_ELETRICA.pdf"'
        
        return response
    
    except Exception as e:
        print(f"ERRO ao gerar PDF: {str(e)}")
        flash(f'Erro ao gerar PDF: {str(e)}', 'error')
        return redirect(url_for('ordens.listar_ordens'))

@bp.route('/anexo/<int:ordem_id>/<nome_arquivo>')
def download_anexo(ordem_id, nome_arquivo):
    """Download de anexo da ordem de serviço"""
    try:
        ordem = OrdemServico.query.get_or_404(ordem_id)
        file_path = os.path.join(UPLOAD_FOLDER, str(ordem_id), nome_arquivo)
        
        if not os.path.exists(file_path):
            flash('Arquivo não encontrado.', 'error')
            return redirect(url_for('ordens.visualizar_ordem', ordem_id=ordem_id))
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        print(f"ERRO ao fazer download do anexo: {str(e)}")
        flash('Erro ao fazer download do arquivo.', 'error')
        return redirect(url_for('ordens.visualizar_ordem', ordem_id=ordem_id))

@bp.route('/anexo/<int:ordem_id>/<nome_arquivo>/remover', methods=['POST'])
def remover_anexo(ordem_id, nome_arquivo):
    """Remove anexo específico da ordem de serviço"""
    try:
        ordem = OrdemServico.query.get_or_404(ordem_id)
        
        # Carregar anexos existentes
        anexos_existentes = []
        if ordem.anexos_dados:
            try:
                anexos_existentes = json.loads(ordem.anexos_dados)
            except:
                anexos_existentes = []
        
        # Filtrar anexo a ser removido
        anexos_filtrados = [a for a in anexos_existentes if a.get('nome_arquivo') != nome_arquivo]
        
        # Remover arquivo físico
        file_path = os.path.join(UPLOAD_FOLDER, str(ordem_id), nome_arquivo)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Atualizar dados no banco
        ordem.anexos_dados = json.dumps(anexos_filtrados)
        db.session.commit()
        
        flash('Anexo removido com sucesso!', 'success')
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"ERRO ao remover anexo: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/<int:ordem_id>/remover', methods=['POST'])
def remover_ordem(ordem_id):
    """Remover (desativar) uma ordem de serviço"""
    try:
        ordem = OrdemServico.query.get_or_404(ordem_id)
        
        # Marcar como inativa em vez de deletar
        ordem.ativo = False
        db.session.commit()
        
        # Se é requisição AJAX, retornar JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': f'Ordem {ordem.codigo} removida com sucesso!'
            })
        
        # Se não é AJAX, fazer redirect normal
        flash(f'Ordem {ordem.codigo} removida com sucesso!', 'success')
        return redirect(url_for('ordens.listar_ordens'))
        
    except Exception as e:
        print(f"ERRO ao remover ordem: {str(e)}")
        
        # Se é requisição AJAX, retornar JSON de erro
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': f'Erro ao remover ordem: {str(e)}'
            })
        
        # Se não é AJAX, fazer redirect com erro
        flash(f'Erro ao remover ordem: {str(e)}', 'error')
        return redirect(url_for('ordens.listar_ordens'))