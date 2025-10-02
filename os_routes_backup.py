from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from aplicacao.extensoes import db
from .os_model import OrdemServico
from .os_calculos import CalculadoraOS
from aplicacao.produto.produto_model import Produto
from aplicacao.servico.servico_model import Servico
# from aplicacao.financeiro.financeiro_model import LancamentoFinanceiro  # Módulo financeiro não existe ainda
from datetime import datetime
from sqlalchemy.orm import joinedload
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, abort, make_response
from aplicacao.extensoes import db
from .os_model import OrdemServico
from .arquivo_model import OSArquivo
from .os_calculos import CalculadoraOS
from .upload_utils import UploadManager, allowed_file
from .simple_pdf_generator import SimplePDFGenerator
from aplicacao.cliente.cliente_model import Cliente
# from aplicacao.condicoes_pagamento.condicoes_pag_model import OSParcela  # Modelo não existe ainda
from datetime import datetime, date
import os
import tempfile


# Blueprint precisa ser definido após os imports

os_bp = Blueprint('os', __name__, url_prefix='/os', template_folder='templates')

# === LISTA ORDENS DE SERVIÇO (endpoint: os.listar) ===
@os_bp.route('/', methods=['GET'], endpoint='listar')
def listar_ordens():
    """Lista todas as ordens de serviço"""
    try:
        ordens = OrdemServico.query.order_by(OrdemServico.data_emissao.desc()).all()
        print(f"DEBUG: Carregando {len(ordens)} ordens")
        return render_template('ordem_servico/lista.html', ordens=ordens)
    except Exception as e:
        print(f"DEBUG ERRO na lista: {str(e)}")
        return f"Erro na listagem: {str(e)}", 500

# === NOVA ORDEM DE SERVIÇO (endpoint: os.nova_os) ===
@os_bp.route('/nova', methods=['GET', 'POST'], endpoint='nova_os')
@os_bp.route('/cadastrar', methods=['GET', 'POST'], endpoint='cadastrar_os')  # Alias para nova
def nova_os():
    """Exibe formulário e cria nova ordem de serviço (básico)"""
    if request.method == 'POST':
        try:
            dados_form = request.form.to_dict()
            # Validação mínima
            if not dados_form.get('cliente_id'):
                flash('Cliente é obrigatório', 'error')
                return redirect(url_for('os.nova_os'))
            if not dados_form.get('data_emissao'):
                flash('Data de emissão é obrigatória', 'error')
                return redirect(url_for('os.nova_os'))
            # Gerar código automático
            ultima_os = OrdemServico.query.order_by(OrdemServico.id.desc()).first()
            if ultima_os and ultima_os.codigo and ultima_os.codigo.startswith('OS'):
                try:
                    proximo_num = int(ultima_os.codigo[2:]) + 1
                    if proximo_num < 351:
                        proximo_num = 351
                    codigo = f'OS{proximo_num:05d}'
                except Exception:
                    codigo = 'OS00351'
            else:
                codigo = 'OS00351'

            ordem = OrdemServico(
                codigo=codigo,
                cliente_id=dados_form.get('cliente_id'),
                status=dados_form.get('status', 'Aberta'),
                prioridade=dados_form.get('prioridade', 'Normal'),
                tipo_servico=dados_form.get('tipo_servico', ''),
                solicitante=dados_form.get('solicitante'),
                contato=dados_form.get('contato'),
                data_emissao=datetime.strptime(dados_form.get('data_emissao'), '%Y-%m-%d').date() if dados_form.get('data_emissao') else None,
                previsao_conclusao=datetime.strptime(dados_form.get('previsao_conclusao'), '%Y-%m-%d').date() if dados_form.get('previsao_conclusao') else None,
                tecnico_responsavel=dados_form.get('tecnico_responsavel'),
                equipamento_nome=dados_form.get('equipamento_nome'),
                equipamento_marca=dados_form.get('equipamento_marca'),
                equipamento_modelo=dados_form.get('equipamento_modelo'),
                equipamento_numero_serie=dados_form.get('equipamento_numero_serie'),
                equipamento_acessorios=dados_form.get('equipamento_acessorios'),
                problema_descrito=dados_form.get('problema_descrito'),
                descricao_servico_realizado=dados_form.get('descricao_servico_realizado'),
                hora_inicio=datetime.strptime(dados_form.get('hora_inicio'), '%H:%M').time() if dados_form.get('hora_inicio') else None,
                hora_termino=datetime.strptime(dados_form.get('hora_termino'), '%H:%M').time() if dados_form.get('hora_termino') else None,
                km_inicial=float(dados_form.get('km_inicial')) if dados_form.get('km_inicial') else None,
                km_final=float(dados_form.get('km_final')) if dados_form.get('km_final') else None,
                valor_deslocamento=float(dados_form.get('valor_deslocamento')) if dados_form.get('valor_deslocamento') else 0.0,
                forma_pagamento=dados_form.get('forma_pagamento'),
                condicoes_pagamento=dados_form.get('condicoes_pagamento', 'À vista'),
                data_vencimento=datetime.strptime(dados_form.get('data_vencimento'), '%Y-%m-%d').date() if dados_form.get('data_vencimento') else None,
                outras_informacoes=dados_form.get('outras_informacoes'),
                # Campos JSON para dados dinâmicos
                servicos_dados=dados_form.get('servicos_json'),
                produtos_dados=dados_form.get('produtos_json'),
                parcelas_json=dados_form.get('parcelas_json'),
                # Valores financeiros (serão recalculados automaticamente)
                valor_servicos=float(dados_form.get('valor_servicos')) if dados_form.get('valor_servicos') else 0.0,
                valor_produtos=float(dados_form.get('valor_produtos')) if dados_form.get('valor_produtos') else 0.0,
                valor_total=float(dados_form.get('valor_total')) if dados_form.get('valor_total') else 0.0,
                ativo=True
            )
            db.session.add(ordem)
            db.session.commit()
            flash('Ordem de serviço criada com sucesso!', 'success')
            return redirect(url_for('os.listar_os'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar ordem de serviço: {str(e)}', 'error')
            import traceback
            print('ERRO AO CRIAR OS:', traceback.format_exc())
            return redirect(url_for('os.nova_os'))
    # GET: exibe o formulário (ajuste o template conforme seu projeto)
    # from aplicacao.cliente.cliente_model import Cliente  # Comentado por enquanto
    servicos = Servico.query.filter_by(ativo=True).all() if hasattr(Servico, 'ativo') else Servico.query.all()
    produtos = Produto.query.filter_by(ativo=True).all() if hasattr(Produto, 'ativo') else Produto.query.all()
    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
    # Gerar código automático (exemplo simples)
    ultima_os = OrdemServico.query.order_by(OrdemServico.id.desc()).first()
    if ultima_os and ultima_os.codigo and ultima_os.codigo.startswith('OS'):
        try:
            proximo_num = int(ultima_os.codigo[2:]) + 1
            codigo_gerado = f'OS{proximo_num:04d}'
        except Exception:
            codigo_gerado = 'OS0351'
    else:
        codigo_gerado = 'OS0351'
    print("DEBUG: Renderizando cadastro_new.html")
    print(f"DEBUG: Servicos={len(servicos)}, Produtos={len(produtos)}, Clientes={len(clientes)}")
    return render_template('ordem_servico/cadastro_new.html', servicos=servicos, produtos=produtos, clientes=clientes, codigo_gerado=codigo_gerado, ordem_servico=None, debug_timestamp="2025-09-26 09:05:45")

# === LISTAGEM DE ORDENS DE SERVIÇO (endpoint: os.listar_os) ===

@os_bp.route('/', endpoint='listar_os')
def listar_os():
    """Lista todas as ordens de serviço (página principal do módulo OS)"""
    try:
        # 1) Filtrar apenas ordens ativas
        ordens = OrdemServico.query.filter_by(ativo=True).order_by(OrdemServico.id.desc()).all()
        print("DEBUG /os -> total ordens ativas:", len(ordens))

        # 2) Contadores robustos
        total_os = len(ordens)
        norm = lambda s: (s or '').strip()
        os_abertas    = sum(1 for o in ordens if norm(o.status) == 'Aberta')
        os_andamento  = sum(1 for o in ordens if norm(o.status) == 'Em Andamento')
        os_concluidas = sum(1 for o in ordens if norm(o.status) == 'Concluída')

        valor_total = 0.0
        for o in ordens:
            try: valor_total += float(o.valor_total or 0)
            except: pass
        valor_medio = (valor_total / total_os) if total_os else 0.0

        return render_template(
            'lista_os.html',
            ordens=ordens,
            total_os=total_os,
            os_abertas=os_abertas,
            os_andamento=os_andamento,
            os_concluidas=os_concluidas,
            valor_total=valor_total,
            valor_medio=valor_medio
        )
    except Exception as e:
        from flask import flash
        import traceback
        print("ERRO listar_os:", e)
        print(traceback.format_exc())
        flash(f'Erro ao carregar lista de OS: {e}', 'error')
        return render_template('lista_os.html',
            ordens=[], total_os=0, os_abertas=0, os_andamento=0,
            os_concluidas=0, valor_total=0.0, valor_medio=0.0)

# === ROTA DE DEBUG RÁPIDO ===
@os_bp.route('/_debug')
def os_debug():
    try:
        rows = OrdemServico.query.order_by(OrdemServico.id.desc()).all()
        payload = []
        for o in rows:
            payload.append({
                "id": o.id,
                "codigo": getattr(o, "codigo", None),
                "status": getattr(o, "status", None),
                "ativo": getattr(o, "ativo", None),
                "cliente_id": getattr(o, "cliente_id", None),
                "valor_total": float(getattr(o, "valor_total", 0) or 0),
            })
        return {"count": len(payload), "items": payload}, 200
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "trace": traceback.format_exc()
        }, 500

# === DEBUG OS14 ===
@os_bp.route('/_debug/14')
def debug_os_14():
    try:
        os = OrdemServico.query.get(14)
        if not os:
            return {"error": "OS 14 não encontrada"}, 404
            
        debug_info = {
            "id": os.id,
            "codigo": os.codigo,
            "cliente": os.cliente.nome if os.cliente else None,
            "status": os.status,
            "valor_total": float(os.valor_total or 0),
            "valor_servicos": float(os.valor_servicos or 0),
            "valor_produtos": float(os.valor_produtos or 0),
            "total_horas": float(os.total_horas or 0),
            "hora_inicio": str(os.hora_inicio) if os.hora_inicio else None,
            "hora_termino": str(os.hora_termino) if os.hora_termino else None,
            "itens": [],
            "servicos": [],
            "produtos": []
        }
        
        # Calcular horas manualmente para debug
        if os.hora_inicio and os.hora_termino:
            inicio_str = os.hora_inicio.strftime('%H:%M')
            termino_str = os.hora_termino.strftime('%H:%M')
            inicio_parts = inicio_str.split(':')
            termino_parts = termino_str.split(':')
            inicio_minutos = (int(inicio_parts[0]) * 60) + int(inicio_parts[1])
            termino_minutos = (int(termino_parts[0]) * 60) + int(termino_parts[1])
            diff_minutos = termino_minutos - inicio_minutos
            horas_calculadas = diff_minutos / 60.0 if diff_minutos > 0 else 0
            debug_info["horas_calculadas"] = horas_calculadas
        
        # Verificar itens
        if hasattr(os, 'itens') and os.itens:
            for item in os.itens:
                debug_info["itens"].append({
                    "tipo": getattr(item, 'tipo_item', 'N/A'),
                    "descricao": getattr(item, 'descricao', 'N/A'),
                    "quantidade": float(getattr(item, 'quantidade', 0) or 0),
                    "valor_unitario": float(getattr(item, 'valor_unitario', 0) or 0),
                    "valor_total": float(getattr(item, 'valor_total', 0) or 0)
                })
        
        # Verificar serviços se existirem
        if hasattr(os, 'servicos'):
            for servico in os.servicos:
                debug_info["servicos"].append({
                    "nome": servico.nome,
                    "horas": float(servico.horas or 0),
                    "valor_por_hora": float(servico.valor_por_hora or 0),
                    "valor_total": float(servico.valor_total or 0)
                })
        
        # Verificar produtos se existirem
        if hasattr(os, 'produtos'):
            for produto in os.produtos:
                debug_info["produtos"].append({
                    "nome": produto.nome,
                    "quantidade": int(produto.quantidade or 0),
                    "valor_unitario": float(produto.valor_unitario or 0),
                    "valor_total": float(produto.valor_total or 0)
                })
                
        return debug_info, 200
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "trace": traceback.format_exc()
        }, 500


# ------- VISUALIZAR OS (GET) Mostra a OS formatada -------
@os_bp.route('/<int:id>/visualizar', methods=['GET'], endpoint='visualizar_os')
def visualizar_os(id):
    """Visualiza a ordem de serviço em formato de relatório"""
    try:
        # Buscar OS com relacionamentos
        ordem = OrdemServico.query.options(
            joinedload(OrdemServico.cliente),
            joinedload(OrdemServico.itens)
        ).get_or_404(id)
        
        # Preparar dados dos serviços
        servicos_dados = []
        if hasattr(ordem, 'itens') and ordem.itens:
            for item in ordem.itens:
                if hasattr(item, 'tipo_item') and item.tipo_item == 'servico':
                    servicos_dados.append({
                        'nome': item.descricao or '',
                        'quantidade': float(item.quantidade or 0),
                        'valor_unitario': float(item.valor_unitario or 0),
                        'valor_total': float(item.valor_total or 0)
                    })
        
        # Preparar dados dos produtos
        produtos_dados = []
        if hasattr(ordem, 'itens') and ordem.itens:
            for item in ordem.itens:
                if hasattr(item, 'tipo_item') and item.tipo_item == 'produto':
                    produtos_dados.append({
                        'nome': item.descricao or '',
                        'quantidade': int(item.quantidade or 0),
                        'valor_unitario': float(item.valor_unitario or 0),
                        'valor_total': float(item.valor_total or 0)
                    })
        
        # Se não há itens detalhados, usar dados JSON salvos
        if not servicos_dados and ordem.servicos_dados:
            try:
                servicos_dados = json.loads(ordem.servicos_dados)
                # Garantir que cada serviço tenha valor_unitario
                for s in servicos_dados:
                    if 'valor_unitario' not in s:
                        quantidade = float(s.get('quantidade', 1) or 1)
                        valor_total = float(s.get('valor_total', 0) or 0)
                        s['valor_unitario'] = valor_total / quantidade if quantidade > 0 else 0
            except:
                servicos_dados = []
                
        if not produtos_dados and ordem.produtos_dados:
            try:
                produtos_dados = json.loads(ordem.produtos_dados)
                # Garantir que cada produto tenha valor_unitario
                for p in produtos_dados:
                    if 'valor_unitario' not in p:
                        quantidade = float(p.get('quantidade', 1) or 1)
                        valor_total = float(p.get('valor_total', 0) or 0)
                        p['valor_unitario'] = valor_total / quantidade if quantidade > 0 else 0
            except:
                produtos_dados = []
        
        # Preparar dados das parcelas
        parcelas = []
        if hasattr(ordem, 'parcelas_json') and ordem.parcelas_json:
            try:
                parcelas = json.loads(ordem.parcelas_json)
            except:
                parcelas = []
        
        # Calcular totais
        total_servicos = float(ordem.valor_servicos or 0)
        total_produtos = float(ordem.valor_produtos or 0)
        valor_total = float(ordem.valor_total or 0)
        
        return render_template(
            'os_visualizar.html',
            os=ordem,
            servicos_dados=servicos_dados,
            produtos_dados=produtos_dados,
            parcelas=parcelas,
            total_servicos=total_servicos,
            total_produtos=total_produtos,
            valor_total=valor_total
        )
        
    except Exception as e:
        flash(f'Erro ao visualizar OS: {e}', 'error')
        return redirect(url_for('os.listar_os'))

# ------- EDITAR OS (GET) Mostra o formulário com os dados da OS -------
@os_bp.route('/<int:id>/editar', methods=['GET'], endpoint='editar_os')
def editar_os(id):
    # Limpar mensagens flash antigas
    from flask import session
    if '_flashes' in session:
        session.pop('_flashes', None)
    
    ordem = OrdemServico.query.get_or_404(id)
    servicos_salvos = json.loads(ordem.servicos_dados) if ordem.servicos_dados else []
    produtos_salvos = json.loads(ordem.produtos_dados) if ordem.produtos_dados else []
    parcelas_salvas = json.loads(ordem.parcelas_json) if getattr(ordem, 'parcelas_json', None) else []
    servicos = Servico.query.filter_by(ativo=True).all() if hasattr(Servico,'ativo') else Servico.query.all()
    produtos = Produto.query.filter_by(ativo=True).all() if hasattr(Produto,'ativo') else Produto.query.all()
    try:
        clientes = Cliente.query.filter_by(ativo=True).all()
    except:
        clientes = Cliente.query.all()
    return render_template(
        'ordem_servico/cadastro_new.html',
        ordem_servico=ordem,
        clientes=clientes,
        servicos=servicos,
        produtos=produtos,
        codigo_gerado=ordem.codigo,
        servicos_salvos=servicos_salvos,
        produtos_salvos=produtos_salvos,
        parcelas_salvas=parcelas_salvas
    )

# ------- EDITAR OS (POST) atualização dos dados da OS -------
@os_bp.route('/<int:id>/editar', methods=['POST'])
def atualizar_os(id):
    try:
        ordem = OrdemServico.query.get_or_404(id)
        dados = request.form.to_dict()
        
        # Para edição, se não vier cliente_id, manter o existente
        if not dados.get('cliente_id') and ordem.cliente_id:
            dados['cliente_id'] = str(ordem.cliente_id)
        
        # Validar
        is_valid, erros = CalculadoraOS.validar_dados_os(dados)
        if not is_valid:
            for erro in erros:
                flash(erro, 'error')
            return redirect(url_for('os.editar_os', id=id))

        # JSONs
        servicos_data = json.loads(dados.get('servicos_json','[]') or '[]')
        produtos_data = json.loads(dados.get('produtos_json','[]') or '[]')
        parcelas_data = json.loads(dados.get('parcelas_json','[]') or '[]')

        # DEBUG: Log dos valores antes e depois dos cálculos
        print(f"=== DEBUG EDIÇÃO OS {id} ===")
        print(f"Valores ANTES da atualização:")
        print(f"  valor_servicos: {ordem.valor_servicos}")
        print(f"  valor_produtos: {ordem.valor_produtos}")
        print(f"  valor_total: {ordem.valor_total}")
        print(f"Dados recebidos do form:")
        print(f"  servicos_data: {servicos_data}")
        print(f"  produtos_data: {produtos_data}")

        calculos = CalculadoraOS.calcular_todos_valores(dados, servicos_data, produtos_data)
        
        print(f"Valores CALCULADOS:")
        print(f"  valor_servicos: {calculos['valor_servicos']}")
        print(f"  valor_produtos: {calculos['valor_produtos']}")
        print(f"  valor_total: {calculos['valor_total']}")
        print(f"=== FIM DEBUG ===")

        # Campos básicos
        print(f"DEBUG - solicitante recebido: '{dados.get('solicitante')}'")
        print(f"DEBUG - contato recebido: '{dados.get('contato')}'")
        ordem.cliente_id = dados.get('cliente_id')
        ordem.status = dados.get('status','Aberta')
        ordem.prioridade = dados.get('prioridade', 'Normal')
        ordem.tipo_servico = dados.get('tipo_servico', '')
        ordem.solicitante = dados.get('solicitante')
        ordem.contato = dados.get('contato')
        print(f"DEBUG - após atribuição: solicitante={ordem.solicitante}, contato={ordem.contato}")
        if dados.get('data_emissao'):
            ordem.data_emissao = datetime.strptime(dados['data_emissao'],'%Y-%m-%d').date()
        ordem.previsao_conclusao = datetime.strptime(dados['previsao_conclusao'],'%Y-%m-%d').date() if dados.get('previsao_conclusao') else None
        ordem.tecnico_responsavel = dados.get('tecnico_responsavel')

        # Equipamento
        ordem.equipamento_nome = dados.get('equipamento_nome')
        ordem.equipamento_marca = dados.get('equipamento_marca')
        ordem.equipamento_modelo = dados.get('equipamento_modelo')
        ordem.equipamento_numero_serie = dados.get('equipamento_numero_serie')
        ordem.equipamento_acessorios = dados.get('equipamento_acessorios')

        # Descrição
        ordem.problema_descrito = dados.get('problema_descrito')
        ordem.descricao_servico_realizado = dados.get('descricao_servico_realizado')

        # Horários
        ordem.hora_inicio = datetime.strptime(dados['hora_inicio'],'%H:%M').time() if dados.get('hora_inicio') else None
        ordem.hora_termino = datetime.strptime(dados['hora_termino'],'%H:%M').time() if dados.get('hora_termino') else None
        ordem.total_horas = calculos['total_horas']

        # KM / valores
        ordem.km_inicial = float(dados.get('km_inicial')) if dados.get('km_inicial') else None
        ordem.km_final = float(dados.get('km_final')) if dados.get('km_final') else None
        ordem.km_total = calculos['km_total']
        ordem.valor_deslocamento = calculos['valor_deslocamento']
        
        # Valores calculados - SEMPRE RECALCULAR
        ordem.valor_servicos = calculos['valor_servicos']
        ordem.valor_produtos = calculos['valor_produtos']
        ordem.valor_total = calculos['valor_total']

        # Pagamento - ATUALIZAR AUTOMATICAMENTE
        ordem.forma_pagamento = dados.get('forma_pagamento', 'À Vista')
        ordem.condicoes_pagamento = dados.get('condicoes_pagamento','À vista')
        # Atualizar data_vencimento se fornecida
        if dados.get('data_vencimento'):
            ordem.data_vencimento = datetime.strptime(dados['data_vencimento'],'%Y-%m-%d').date()
        
        # Observações e outras informações
        ordem.outras_informacoes = dados.get('outras_informacoes')
        
        # JSONs de parcelas
        ordem.parcelas_json = json.dumps(parcelas_data) if parcelas_data else None

        # Salva JSONs
        ordem.servicos_dados = json.dumps(servicos_data) if servicos_data else None
        ordem.produtos_dados = json.dumps(produtos_data) if produtos_data else None

        # *** FORÇA RECÁLCULO AUTOMÁTICO SEMPRE ***
        print(f"[FORÇA RECÁLCULO] Executando recálculo automático para OS {ordem.codigo}")
        ordem.recalcular_valores()
        print(f"[APÓS RECÁLCULO] OS {ordem.codigo}: Serviços={ordem.valor_servicos}, Total={ordem.valor_total}")

        # --- Atualizar campos para integração com financeiro ---
        # Campos de pagamento (novos)
        ordem.condicao_pagamento = dados.get('condicao_pagamento', 'avista')
        ordem.qtd_parcelas = int(dados.get('qtd_parcelas', 1) or 1)
        ordem.valor_entrada = float(dados.get('valor_entrada', 0) or 0)
        ordem.status_pagamento = dados.get('status_pagamento', 'pendente')
        ordem.schedule_json = dados.get('schedule_json')

        # --- Criar lançamentos financeiros se status for Concluída ---
        status_atual = ordem.status
        status_pagamento = ordem.status_pagamento
        
        print(f"DEBUG - Status atual: {status_atual}, Status pagamento: {status_pagamento}")
        
        if status_atual == 'Concluída':
            print("DEBUG - OS marcada como Concluída, gerando lançamentos financeiros...")
            from app.financeiro.lancamento_os_service import gerar_lancamentos_financeiro, parse_schedule_custom
            from decimal import Decimal
            
            # Preparar dados para geração dos lançamentos
            forma_pagamento = dados.get('forma_pagamento', 'Dinheiro')
            valor_total = Decimal(str(ordem.valor_total))
            parcelas = ordem.qtd_parcelas
            entrada = Decimal(str(ordem.valor_entrada)) if ordem.valor_entrada else Decimal('0.00')
            
            # Parse cronograma personalizado se existir
            schedule_custom = parse_schedule_custom(ordem.schedule_json)
            
            # Gerar lançamentos (função idempotente)
            try:
                gerar_lancamentos_financeiro(
                    os=ordem,
                    forma_pagamento=forma_pagamento,
                    valor_total=valor_total,
                    parcelas=parcelas,
                    entrada=entrada,
                    schedule_custom=schedule_custom
                )
                flash('Lançamentos financeiros atualizados com sucesso!', 'success')
            except Exception as e:
                print(f"Erro ao gerar lançamentos financeiros: {str(e)}")
                flash(f'Erro ao gerar lançamentos financeiros: {str(e)}', 'error')

        db.session.commit()
        flash(f'Ordem de Serviço {ordem.codigo} atualizada com sucesso!', 'success')
        return redirect(url_for('os.listar_os'))  # Redireciona para a lista
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar ordem de serviço: {e}', 'error')
        return redirect(url_for('os.listar_os'))  # Redireciona para a lista mesmo em caso de erro



# === ROTAS DE DEBUG PARA BANCO DE DADOS ===
@os_bp.route('/debug/db')
def debug_db():
    """Testa conexão com o banco (SELECT 1)"""
    try:
        result = db.session.execute('SELECT 1').scalar()
        return {'success': True, 'result': result}, 200
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500

# === APIS PARA JS EM lista_os.html ===
@os_bp.route('/api/estatisticas')
def api_estatisticas():
    """API para estatísticas de OS (status, valores, etc)"""
    try:
        status = request.args.get('status')
        prioridade = request.args.get('prioridade')
        q = request.args.get('q')
        query = OrdemServico.query
        if status:
            query = query.filter(OrdemServico.status == status)
        if prioridade:
            query = query.filter(OrdemServico.prioridade == prioridade)
        if q:
            q_like = f"%{q}%"
            query = query.filter(
                (OrdemServico.codigo.ilike(q_like)) |
                (OrdemServico.status.ilike(q_like))
            )
        ordens = query.all()
        total_os = len(ordens)
        os_abertas = sum(1 for o in ordens if (o.status or '').strip() == 'Aberta')
        os_andamento = sum(1 for o in ordens if (o.status or '').strip() == 'Em Andamento')
        os_concluidas = sum(1 for o in ordens if (o.status or '').strip() == 'Concluída')
        valor_total = 0.0
        for o in ordens:
            try:
                valor_total += float(o.valor_total or 0)
            except Exception:
                pass
        valor_medio = (valor_total / total_os) if total_os else 0.0
        return jsonify({
            'success': True,
            'total_os': total_os,
            'os_abertas': os_abertas,
            'os_andamento': os_andamento,
            'os_concluidas': os_concluidas,
            'valor_total': valor_total,
            'valor_medio': valor_medio
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@os_bp.route('/api/lista')
def api_lista():
    """API para listar ordens de serviço (com filtros)"""
    try:
        status = request.args.get('status')
        prioridade = request.args.get('prioridade')
        q = request.args.get('q')
        query = OrdemServico.query
        if status:
            query = query.filter(OrdemServico.status == status)
        if prioridade:
            query = query.filter(OrdemServico.prioridade == prioridade)
        if q:
            q_like = f"%{q}%"
            query = query.filter(
                (OrdemServico.codigo.ilike(q_like)) |
                (OrdemServico.status.ilike(q_like))
            )
        ordens = query.order_by(OrdemServico.id.desc()).all()
        lista = []
        for o in ordens:
            lista.append({
                'id': o.id,
                'codigo': o.codigo,
                'status': o.status,
                'prioridade': getattr(o, 'prioridade', None),
                'valor_total': float(o.valor_total or 0),
                'cliente_id': o.cliente_id
            })
        return jsonify({'success': True, 'ordens': lista})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



@os_bp.route('/<int:id>/imprimir')
def imprimir_os(id):
    """Visualizar/Imprimir ordem de serviço"""
    try:
        ordem = OrdemServico.query.get_or_404(id)
        
        # Processar dados salvos para exibição
        servicos_salvos = []
        produtos_salvos = []
        parcelas_salvas = []
        
        try:
            if ordem.servicos_dados:
                servicos_salvos = json.loads(ordem.servicos_dados)
            if ordem.produtos_dados:
                produtos_salvos = json.loads(ordem.produtos_dados)
            if ordem.parcelas_json:
                parcelas_salvas = json.loads(ordem.parcelas_json)
        except (json.JSONDecodeError, TypeError):
            pass
        
        return render_template('imprimir_os.html',
                             ordem_servico=ordem,
                             servicos=servicos_salvos,
                             produtos=produtos_salvos,
                             parcelas=parcelas_salvas)
    
    except Exception as e:
        flash(f'Erro ao carregar ordem de serviço: {str(e)}', 'error')
        return redirect(url_for('.listar_os'))

@os_bp.route('/<int:id>/deletar', methods=['POST'], endpoint='deletar_os')
def deletar_os(id):
    """Deletar ordem de serviço (soft delete)"""
    try:
        print(f"DEBUG: Tentando excluir OS com ID: {id}")
        ordem = OrdemServico.query.get_or_404(id)
        print(f"DEBUG: OS encontrada: {ordem.codigo}")
        
        # Verificar se já está inativa
        if hasattr(ordem, 'ativo') and ordem.ativo == False:
            flash(f'Ordem de Serviço {ordem.codigo} já foi excluída!', 'warning')
            return redirect(url_for('os.listar_os'))
        
        # Cancelar lançamentos financeiros relacionados (quando o módulo existir)
        # TODO: Implementar cancelamento de lançamentos financeiros quando módulo estiver pronto
        try:
            # lancamentos = LancamentoFinanceiro.query.filter(
            #     LancamentoFinanceiro.descricao.like(f'%{ordem.codigo}%'),
            #     ~LancamentoFinanceiro.status.in_(['Cancelado', 'Excluído'])
            # ).all()
            # 
            # for lancamento in lancamentos:
            #     lancamento.status = 'Cancelado'
            #     lancamento.observacoes = (lancamento.observacoes or '') + f' [CANCELADO em {datetime.now().strftime("%d/%m/%Y %H:%M")} - OS excluída]'
            # 
            # print(f"DEBUG: {len(lancamentos)} lançamentos cancelados para OS {ordem.codigo}")
            print(f"DEBUG: Cancelamento de lançamentos financeiros será implementado no futuro")
            
        except Exception as e:
            print(f"DEBUG: Erro ao cancelar lançamentos: {e}")
        
        # Soft delete - marcar como inativo
        if hasattr(ordem, 'ativo'):
            ordem.ativo = False
        else:
            # Se não tem campo ativo, fazer delete real
            db.session.delete(ordem)
        
        db.session.commit()
        print(f"DEBUG: OS {ordem.codigo} excluída com sucesso")
        
        flash(f'Ordem de Serviço {ordem.codigo} excluída com sucesso!', 'success')
        return redirect(url_for('os.listar_os'))
    
    except Exception as e:
        print(f"DEBUG: Erro ao excluir OS: {str(e)}")
        db.session.rollback()
        flash(f'Erro ao excluir ordem de serviço: {str(e)}', 'error')
        return redirect(url_for('os.listar_os'))

@os_bp.route('/<int:id>/alterar-status', methods=['POST'], endpoint='alterar_status')
def alterar_status(id):
    """Alterar status da ordem de serviço e gerar lançamentos financeiros se concluída"""
    try:
        novo_status = request.form.get('status')
        ordem = OrdemServico.query.get_or_404(id)
        status_anterior = ordem.status
        
        print(f"DEBUG: Alterando status da OS {ordem.codigo} de '{status_anterior}' para '{novo_status}'")
        
        ordem.status = novo_status
        
        # Se marcou como concluída, verificar se pode criar lançamentos financeiros
        if novo_status == 'Concluída' and status_anterior != 'Concluída':
            print(f"DEBUG: OS {ordem.codigo} marcada como concluída")
            
            # Verificar se a forma de pagamento permite lançamento financeiro
            forma_pag = (ordem.forma_pagamento or '').lower()
            pode_lancar = forma_pag in ['pago', 'à vista', 'a vista', 'dinheiro', 'pix', 'cartão', 'cartao']
            
            print(f"DEBUG: Forma de pagamento: '{ordem.forma_pagamento}' - Pode lançar: {pode_lancar}")
            
            if pode_lancar:
                print(f"DEBUG: Criando lançamentos financeiros para OS {ordem.codigo}")
                try:
                    # Primeiro, verificar se existem lançamentos cancelados para reativar
                    # lancamentos_cancelados = LancamentoFinanceiro.query.filter(
                    #     LancamentoFinanceiro.descricao.like(f'%{ordem.codigo}%'),
                    #     LancamentoFinanceiro.status.in_(['Cancelado', 'Excluído'])
                    # ).all()
                    lancamentos_cancelados = []  # Temporariamente desabilitado
                    
                    if lancamentos_cancelados:
                        print(f"DEBUG: Reativando {len(lancamentos_cancelados)} lançamentos cancelados")
                        # for lancamento in lancamentos_cancelados:
                        #     lancamento.status = 'Pago'  # Marca como pago pois forma_pagamento indica pagamento
                        #     lancamento.observacoes = (lancamento.observacoes or '') + f' [REATIVADO e PAGO em {datetime.now().strftime("%d/%m/%Y %H:%M")} - OS concluída e paga]'
                        print(f"DEBUG: Lançamentos reativados e marcados como pagos!")
                    else:
                        # Se não há lançamentos cancelados, criar novos
                        # criar_lancamentos_financeiros(ordem)
                        # Marcar novos lançamentos como pagos
                        # novos_lancamentos = LancamentoFinanceiro.query.filter(
                        #     LancamentoFinanceiro.descricao.like(f'%{ordem.codigo}%'),
                        #     LancamentoFinanceiro.status == 'Pendente'
                        # ).all()
                        # for lancamento in novos_lancamentos:
                        #     lancamento.status = 'Pago'
                        print(f"DEBUG: Novos lançamentos criados e marcados como pagos! (Módulo financeiro desabilitado)")
                        
                except Exception as e:
                    print(f"DEBUG: Erro ao criar/reativar lançamentos: {str(e)}")
                    raise e
            else:
                print(f"DEBUG: Não criando lançamentos. Forma de pagamento '{ordem.forma_pagamento}' não indica pagamento efetivado.")
                flash(f'OS {ordem.codigo} concluída. Para registrar no financeiro, defina a forma de pagamento como "Pago".', 'info')
        else:
            print(f"DEBUG: Não criando lançamentos. Status: {novo_status}, Anterior: {status_anterior}")
        
        db.session.commit()
        flash(f'Status da OS {ordem.codigo} alterado para {novo_status}!', 'success')
        
    except Exception as e:
        print(f"DEBUG: Erro ao alterar status: {str(e)}")
        db.session.rollback()
        flash(f'Erro ao alterar status: {str(e)}', 'error')
    
    return redirect(url_for('os.listar_os'))

def criar_lancamentos_financeiros(ordem):
    """Criar lançamentos financeiros baseados nas parcelas da OS"""
    # TEMPORARIAMENTE DESABILITADO - Módulo financeiro não existe ainda
    print(f"DEBUG: Função financeira desabilitada para OS {ordem.codigo}")
    return
    
    # try:
    #     print(f"DEBUG: Iniciando criação de lançamentos financeiros para OS {ordem.codigo}")
    #     
    #     # Verificar se já existem lançamentos ATIVOS para esta OS
    #     # Exclui lançamentos com status 'Cancelado' ou 'Excluído'
    #     lancamentos_existentes = LancamentoFinanceiro.query.filter(
    #         LancamentoFinanceiro.descricao.like(f'%{ordem.codigo}%'),
    #         ~LancamentoFinanceiro.status.in_(['Cancelado', 'Excluído'])
    #     ).count()
    #     
    #     print(f"DEBUG: Lançamentos ativos encontrados: {lancamentos_existentes}")
    #     
    #     if lancamentos_existentes > 0:
    #         print(f"DEBUG: Já existem {lancamentos_existentes} lançamentos ativos para esta OS, pulando criação")
    # TEMPORARIAMENTE DESABILITADO - Módulo financeiro não existe ainda
    print(f"DEBUG: Função financeira desabilitada para OS {ordem.codigo}")
    return
    
    # Código da função comentado até o módulo financeiro estar disponível
    # ... resto da função comentado ...

# APIs para AJAX
@os_bp.route('/api/calcular', methods=['POST'])
def api_calcular():
    """API para calcular valores em tempo real"""
    try:
        dados = request.get_json()
        
        # Extrair dados dos arrays
        servicos_data = dados.get('servicos', [])
        produtos_data = dados.get('produtos', [])
        dados_form = dados.get('form_data', {})
        
        # Calcular valores
        calculos = CalculadoraOS.calcular_todos_valores(
            dados_form, 
            servicos_data, 
            produtos_data
        )
        
        return jsonify({
            'success': True,
            'calculos': calculos
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@os_bp.route('/teste-financeiro-os14')
def teste_financeiro_os14():
    """TEMPORARIAMENTE DESABILITADO - Módulo financeiro não existe"""
    return "Função financeira desabilitada temporariamente - módulo não existe"
    """Rota de teste para verificar integração financeira da OS0014"""
    try:
        # Buscar OS0014
        os = OrdemServico.query.filter_by(codigo='OS0014').first()
        if not os:
            return f"❌ OS0014 não encontrada!"
        
        resultado = []
        resultado.append(f"✅ OS encontrada: {os.codigo}")
        resultado.append(f"Status: {os.status}")
        resultado.append(f"Valor: R$ {os.valor_total}")
        resultado.append(f"Cliente: {os.cliente.nome if os.cliente else 'N/A'}")
        
        # Verificar lançamentos existentes
        # lancamentos = LancamentoFinanceiro.query.filter(
        #     LancamentoFinanceiro.descricao.like(f'%{os.codigo}%')
        # ).all()
        lancamentos = []  # Temporariamente desabilitado
        
        resultado.append(f"\n📊 Lançamentos existentes: {len(lancamentos)} (Módulo financeiro desabilitado)")
        # for lanc in lancamentos:
        #     resultado.append(f"- {lanc.descricao}: R$ {lanc.valor:.2f}")
        
        # Se não tem lançamentos, criar agora
        if len(lancamentos) == 0:
            resultado.append(f"\n🔧 Criando lançamentos... (Módulo financeiro desabilitado)")
            
            # Criar lançamento à vista
            # valor_total = float(os.valor_total or 0)
            # lancamento = LancamentoFinanceiro(
            #     tipo='Receita',
            #     categoria='Serviços',
            #     descricao=f'{os.codigo} - À Vista - {os.cliente.nome if os.cliente else "Cliente"}',
            #     valor=valor_total,
            #     data=datetime.today().date(),
            #     status='Pendente',
            #     observacoes=f'Gerado automaticamente da {os.codigo}'
            # )
            # db.session.add(lancamento)
            # db.session.commit()
            
            # resultado.append(f"✅ Lançamento criado: R$ {valor_total:.2f}")
            resultado.append(f"✅ Lançamentos financeiros desabilitados temporariamente")
        
        return "<br>".join(resultado)
        
    except Exception as e:
        import traceback
        return f"❌ Erro: {str(e)}<br><pre>{traceback.format_exc()}</pre>"

@os_bp.route('/teste-valores-servicos-os14')
def teste_valores_servicos_os14():
    """Rota de teste para verificar valores dos serviços da OS0014"""
    try:
        # Buscar OS0014
        os = OrdemServico.query.filter_by(codigo='OS0014').first()
        if not os:
            return f"❌ OS0014 não encontrada!"
        
        resultado = []
        resultado.append(f"=== VALORES DA OS {os.codigo} ===")
        resultado.append(f"Valor Total: R$ {os.valor_total or 0}")
        resultado.append(f"Valor Serviços: R$ {os.valor_servicos or 0}")
        resultado.append(f"Total Horas: {os.total_horas or 0}h")
        
        # Calcular valor por hora
        if os.total_horas and os.total_horas > 0:
            valor_por_hora = (os.valor_servicos or 0) / os.total_horas
            resultado.append(f"Valor por Hora: R$ {valor_por_hora:.2f}")
        else:
            resultado.append(f"Valor por Hora: Não calculável (sem horas)")
        
        # Verificar relacionamento com serviço
        if os.servico:
            resultado.append(f"\nServiço Relacionado: {os.servico.nome}")
            resultado.append(f"Valor do Serviço no Cadastro: R$ {os.servico.valor}")
        else:
            resultado.append(f"\nNenhum serviço relacionado")
        
        # Verificar dados JSON
        if os.servicos_dados:
            resultado.append(f"\nDados JSON dos Serviços:")
            try:
                import json
                servicos = json.loads(os.servicos_dados)
                for i, s in enumerate(servicos):
                    resultado.append(f"  Serviço {i+1}: {s}")
            except Exception as e:
                resultado.append(f"  Erro ao parsear JSON: {e}")
        else:
            resultado.append(f"\nSem dados JSON de serviços")
        
        resultado.append(f"\n=== SIMULAÇÃO TEMPLATE ===")
        
        # Simular cálculo do template
        horas = os.total_horas or 0
        valor_servicos = os.valor_servicos or 0
        
        if horas > 0:
            valor_unitario = valor_servicos / horas
            resultado.append(f"Template mostrará: R$ {valor_unitario:.2f} por hora")
        elif os.servico:
            resultado.append(f"Template mostrará: R$ {os.servico.valor:.2f} (valor do cadastro)")
        else:
            resultado.append(f"Template mostrará: R$ 0.00")
        
        return "<br>".join(resultado)
        
    except Exception as e:
        import traceback
        return f"❌ Erro: {str(e)}<br><pre>{traceback.format_exc()}</pre>"
    """Rota de teste para simular mudança de status da OS0014"""
    try:
        # Buscar OS0014
        os = OrdemServico.query.filter_by(codigo='OS0014').first()
        if not os:
            return f"❌ OS0014 não encontrada!"
        
        resultado = []
        resultado.append(f"✅ OS encontrada: {os.codigo}")
        resultado.append(f"Status atual: {os.status}")
        
        # Primeiro mudar para Em Andamento
        if os.status == 'Concluída':
            os.status = 'Em Andamento'
            db.session.commit()
            resultado.append(f"⚠️ Status alterado para: {os.status}")
        
        # Agora simular mudança para Concluída
        status_anterior = os.status
        os.status = 'Concluída'
        
        resultado.append(f"\n🔄 Simulando mudança de '{status_anterior}' para 'Concluída'")
        
        # Chamar função criar_lancamentos_financeiros
        try:
            criar_lancamentos_financeiros(os)
            resultado.append(f"✅ Função criar_lancamentos_financeiros executada")
        except Exception as e:
            resultado.append(f"❌ Erro na função: {str(e)}")
            import traceback
            resultado.append(f"<pre>{traceback.format_exc()}</pre>")
        
        db.session.commit()
        resultado.append(f"💾 Status salvo: {os.status}")
        
        # Verificar lançamentos após
        lancamentos = LancamentoFinanceiro.query.filter(
            LancamentoFinanceiro.descricao.like(f'%{os.codigo}%')
        ).all()
        
        resultado.append(f"\n📊 Lançamentos após teste: {len(lancamentos)}")
        for lanc in lancamentos:
            resultado.append(f"- {lanc.descricao}: R$ {lanc.valor:.2f}")
        
        return "<br>".join(resultado)
        
    except Exception as e:
        import traceback
        return f"❌ Erro: {str(e)}<br><pre>{traceback.format_exc()}</pre>"






# === RELATÓRIO HTML JSP ===
@os_bp.route('/<int:os_id>/relatorio')
def relatorio_os(os_id):
    """Visualiza o relatório da OS em HTML (padrão JSP)"""
    try:
        ordem = OrdemServico.query.options(
            joinedload(OrdemServico.cliente),
            joinedload(OrdemServico.itens)
        ).get_or_404(os_id)

        servicos_dados = []
        produtos_dados = []
        parcelas = []
        
        try:
            if ordem.servicos_dados:
                servicos_dados = json.loads(ordem.servicos_dados)
            if ordem.produtos_dados:
                produtos_dados = json.loads(ordem.produtos_dados)
            if ordem.parcelas_json:
                parcelas = json.loads(ordem.parcelas_json)
        except Exception:
            pass

        # Calcular totais
        total_servicos = float(ordem.valor_servicos or 0)
        total_produtos = float(ordem.valor_produtos or 0)
        valor_total = float(ordem.valor_total or 0)

        return render_template(
            'relatorio_os.html',
            os=ordem,
            servicos_dados=servicos_dados,
            produtos_dados=produtos_dados,
            parcelas=parcelas,
            total_servicos=total_servicos,
            total_produtos=total_produtos,
            valor_total=valor_total
        )
        
    except Exception as e:
        flash(f'Erro ao visualizar relatório: {e}', 'error')
        return redirect(url_for('os.listar_os'))




# ===== ROTAS PARA GERENCIAMENTO DE ARQUIVOS =====


@os_bp.route('/<int:os_id>/upload', methods=['POST'])
def upload_arquivo(os_id):
    """Upload de arquivo para uma OS"""
    try:
        # Verificar se a OS existe
        os = OrdemServico.query.get_or_404(os_id)
        
        # Verificar se há arquivo no request
        if 'arquivo' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Nenhum arquivo foi enviado'
            }), 400
        
        file = request.files['arquivo']
        categoria = request.form.get('categoria', 'documento')
        descricao = request.form.get('descricao', '')
        
        # Validar arquivo
        upload_manager = UploadManager()
        errors = upload_manager.validate_file(file)
        
        if errors:
            return jsonify({
                'success': False,
                'error': '; '.join(errors)
            }, 400)
        
        # Salvar arquivo localmente
        resultado = upload_manager.save_file_local(file, os_id, categoria)
        
        if not resultado['success']:
            return jsonify({
                'success': False,
                'error': resultado['error']
            }, 500)
        
        # Criar registro no banco
        arquivo = OSArquivo(
            ordem_servico_id=os_id,
            nome_original=file.filename,
            nome_arquivo=resultado['nome_arquivo'],
            tipo_arquivo=resultado['tipo_arquivo'],
            tamanho=resultado['tamanho'],
            categoria=categoria,
            descricao=descricao,
            caminho_local=resultado['caminho_local'],
            url_publica=resultado['url_relativa'],
            usuario_upload='Sistema'  # TODO: Implementar autenticação
        )
        
        db.session.add(arquivo)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Arquivo enviado com sucesso',
            'arquivo': arquivo.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

@os_bp.route('/arquivo/<int:arquivo_id>')
def visualizar_arquivo(arquivo_id):
    """Visualizar arquivo"""
    try:
        arquivo = OSArquivo.query.get_or_404(arquivo_id)
        
        # Verificar se arquivo existe fisicamente
        if arquivo.caminho_local and os.path.exists(arquivo.caminho_local):
            return send_file(
                arquivo.caminho_local,
                as_attachment=False,
                download_name=arquivo.nome_original
            )
        elif arquivo.url_s3:
            # Redirecionar para URL do S3
            return redirect(arquivo.url_s3)
        else:
            abort(404, "Arquivo não encontrado")
    
    except Exception as e:
        abort(500, f"Erro ao acessar arquivo: {str(e)}")

@os_bp.route('/arquivo/<int:arquivo_id>/download')
def download_arquivo(arquivo_id):
    """Download de arquivo"""
    try:
        arquivo = OSArquivo.query.get_or_404(arquivo_id)
        
        # Verificar se arquivo existe fisicamente
        if arquivo.caminho_local and os.path.exists(arquivo.caminho_local):
            return send_file(
                arquivo.caminho_local,
                as_attachment=True,
                download_name=arquivo.nome_original
            )
        elif arquivo.url_s3:
            # Redirecionar para URL do S3
            return redirect(arquivo.url_s3)
        else:
            abort(404, "Arquivo não encontrado")
    
    except Exception as e:
        abort(500, f"Erro ao baixar arquivo: {str(e)}")

@os_bp.route('/arquivo/<int:arquivo_id>/excluir', methods=['POST'])
def excluir_arquivo(arquivo_id):
    """Excluir arquivo"""
    try:
        arquivo = OSArquivo.query.get_or_404(arquivo_id)
        os_id = arquivo.ordem_servico_id
        
        # Remover arquivo físico
        upload_manager = UploadManager()
        if arquivo.caminho_local:
            upload_manager.delete_file_local(arquivo.caminho_local)
        
        # Marcar como inativo no banco (soft delete)
        arquivo.ativo = False
        db.session.commit()
        
        flash('Arquivo excluído com sucesso', 'success')
        
        # Se for requisição AJAX
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Arquivo excluído com sucesso'
            })
        
        return redirect(url_for('os.gerenciar_arquivos', os_id=os_id))
    
    except Exception as e:
        db.session.rollback()
        
        if request.is_json:
            return jsonify({
                'success': False,
                'error': str(e)
            }, 500)
        
        flash(f'Erro ao excluir arquivo: {str(e)}', 'error')
        return redirect(url_for('os.gerenciar_arquivos', os_id=arquivo.ordem_servico_id))

@os_bp.route('/<int:os_id>/arquivos/api')
def api_arquivos(os_id):
    """API para listar arquivos de uma OS (para AJAX)"""
    try:
        arquivos = OSArquivo.query.filter_by(
            ordem_servico_id=os_id,
            ativo=True
        ).order_by(OSArquivo.data_upload.desc()).all()
        
        return jsonify({
            'success': True,
            'arquivos': [arquivo.to_dict() for arquivo in arquivos]
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ===== ROTAS PARA GERAÇÃO DE PDF =====

@os_bp.route('/<int:os_id>/pdf')
def gerar_pdf(os_id):
    """Gera PDF da ordem de serviço com template JSP ELÉTRICA"""
    print(f"=== GERANDO PDF PARA OS ID: {os_id} ===")
    
    # Buscar OS com relacionamentos ANTES do try
    os = OrdemServico.query.options(
        joinedload(OrdemServico.cliente)
    ).get_or_404(os_id)
    
    print(f"OS encontrada: {os.codigo}")
    print(f"Cliente: {os.cliente.nome if os.cliente else 'Sem cliente'}")
    print(f"Status: {os.status}")
    
    try:
        # Gerar PDF com template JSP completo
        print("Importando SimplePDFGenerator...")
        
        print("Criando instância do gerador...")
        pdf_generator = SimplePDFGenerator()
        
        print("Gerando PDF com template JSP...")
        pdf_bytes = pdf_generator.generate_pdf(os)
        
        print(f"PDF gerado com sucesso! Tamanho: {len(pdf_bytes)} bytes")
        
        # Criar resposta com PDF
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="OS_{os.codigo}_JSP_ELETRICA.pdf"'
        
        print("Retornando PDF...")
        return response
    
    except Exception as e:
        print(f"ERRO ao gerar PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Em caso de erro, tentar PDF simples como fallback
        try:
            print("Tentando PDF simples como fallback...")
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from io import BytesIO
            
            buffer = BytesIO()
            p = canvas.Canvas(buffer, pagesize=A4)
            
            # Cabeçalho de erro
            p.drawString(100, 750, f"JSP ELÉTRICA - Ordem de Serviço {os.codigo}")
            p.drawString(100, 720, f"ERRO: Não foi possível gerar o template completo")
            p.drawString(100, 690, f"Cliente: {os.cliente.nome if os.cliente else 'N/A'}")
            p.drawString(100, 660, f"Data: {os.data_emissao.strftime('%d/%m/%Y') if os.data_emissao else 'N/A'}")
            p.drawString(100, 630, f"Erro: {str(e)}")
            
            p.save()
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            response = make_response(pdf_bytes)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'inline; filename="OS_{os.codigo}_ERROR.pdf"'
            
            return response
            
        except Exception as fallback_error:
            print(f"ERRO no fallback: {str(fallback_error)}")
            flash(f'Erro ao gerar PDF: {str(e)}', 'error')
            return redirect(url_for('os.listar_os'))

@os_bp.route('/<int:os_id>/pdf/download')
def download_pdf(os_id):
    """Download do PDF da ordem de serviço"""
    try:
        # Buscar OS com relacionamentos
        os = OrdemServico.query.options(
            joinedload(OrdemServico.cliente),
            joinedload(OrdemServico.itens),
            joinedload(OrdemServico.arquivos)
        ).get_or_404(os_id)
        
        # Gerar PDF
        pdf_generator = SimplePDFGenerator()
        pdf_bytes = pdf_generator.generate_pdf(os)
        
        # Criar resposta para download
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="Ordem_de_servico_{os.codigo}_{os.cliente.nome if os.cliente else "sem_cliente"}.pdf"'
        
        return response
    
    except Exception as e:
        flash(f'Erro ao baixar PDF: {str(e)}', 'error')
        return redirect(url_for('os.listar_os'))




@os_bp.route('/teste-reativacao-lancamentos')
def teste_reativacao_lancamentos():
    """TEMPORARIAMENTE DESABILITADO - Módulo financeiro não existe"""
    return "Função financeira desabilitada temporariamente - módulo não existe"
    """Rota de teste para verificar reativação de lançamentos financeiros"""
    try:
        resultado = []
        resultado.append("=== TESTE DE REATIVAÇÃO DE LANÇAMENTOS ===")
        
        # Verificar todas as OS
        ordens = OrdemServico.query.all()
        resultado.append(f"Total de ordens no sistema: {len(ordens)}")
        
        for os in ordens:
            if hasattr(os, 'ativo') and not os.ativo:
                continue  # Pular OS inativas
                
            # Verificar lançamentos da OS
            lancamentos_ativos = LancamentoFinanceiro.query.filter(
                LancamentoFinanceiro.descricao.like(f'%{os.codigo}%'),
                ~LancamentoFinanceiro.status.in_(['Cancelado', 'Excluído'])
            ).count()
            
            lancamentos_cancelados = LancamentoFinanceiro.query.filter(
                LancamentoFinanceiro.descricao.like(f'%{os.codigo}%'),
                LancamentoFinanceiro.status.in_(['Cancelado', 'Excluído'])
            ).count()
            
            if lancamentos_ativos > 0 or lancamentos_cancelados > 0:
                resultado.append(f"")
                resultado.append(f"OS {os.codigo} (Status: {os.status}):")
                resultado.append(f"  - Lançamentos ativos: {lancamentos_ativos}")
                resultado.append(f"  - Lançamentos cancelados: {lancamentos_cancelados}")
        
        resultado.append(f"")
        resultado.append("=== COMO TESTAR ===")
        resultado.append("1. Marque uma OS como 'Concluída' (cria lançamentos)")
        resultado.append("2. Exclua a OS (cancela lançamentos)")
        resultado.append("3. Marque a OS como 'Concluída' novamente (reativa lançamentos)")
        
        return "<br>".join(resultado)
        
    except Exception as e:
        import traceback
        return f"❌ Erro: {str(e)}<br><pre>{traceback.format_exc()}</pre>"

@os_bp.route('/teste-forma-pagamento')
def teste_forma_pagamento():
    """TEMPORARIAMENTE DESABILITADO - Módulo financeiro não existe"""
    return "Função financeira desabilitada temporariamente - módulo não existe"
    """Rota de teste para verificar lógica de forma de pagamento"""
    try:
        resultado = []
        resultado.append("=== TESTE FORMA DE PAGAMENTO ===")
        resultado.append("")
        
        # Testar diferentes formas de pagamento
        formas_teste = [
            'Pago', 'pago', 'PAGO',
            'À vista', 'A vista', 'a vista',
            'Dinheiro', 'PIX', 'Cartão',
            'Parcelado', 'Pendente', 'A prazo',
            '', None
        ]
        
        resultado.append("Formas de pagamento que GERAM lançamentos:")
        for forma in formas_teste:
            forma_lower = (forma or '').lower()
            pode_lancar = forma_lower in ['pago', 'à vista', 'a vista', 'dinheiro', 'pix', 'cartão', 'cartao']
            if pode_lancar:
                resultado.append(f"  ✅ '{forma}' → Gera lançamento")
        
        resultado.append("")
        resultado.append("Formas de pagamento que NÃO geram lançamentos:")
        for forma in formas_teste:
            forma_lower = (forma or '').lower()
            pode_lancar = forma_lower in ['pago', 'à vista', 'a vista', 'dinheiro', 'pix', 'cartão', 'cartao']
            if not pode_lancar:
                resultado.append(f"  ❌ '{forma}' → Não gera lançamento")
        
        resultado.append("")
        resultado.append("=== ORDENS DE SERVIÇO NO SISTEMA ===")
        
        # Verificar OS existentes
        ordens = OrdemServico.query.filter(
            OrdemServico.ativo == True if hasattr(OrdemServico, 'ativo') else True
        ).all()
        
        for os in ordens:
            forma_pag = (os.forma_pagamento or '').lower()
            pode_lancar = forma_pag in ['pago', 'à vista', 'a vista', 'dinheiro', 'pix', 'cartão', 'cartao']
            
            lancamentos_ativos = LancamentoFinanceiro.query.filter(
                LancamentoFinanceiro.descricao.like(f'%{os.codigo}%'),
                ~LancamentoFinanceiro.status.in_(['Cancelado', 'Excluído'])
            ).count()
            
            resultado.append(f"")
            resultado.append(f"OS {os.codigo}:")
            resultado.append(f"  Status: {os.status}")
            resultado.append(f"  Forma Pagamento: '{os.forma_pagamento}'")
            resultado.append(f"  Pode gerar lançamento: {'✅ Sim' if pode_lancar else '❌ Não'}")
            resultado.append(f"  Lançamentos ativos: {lancamentos_ativos}")
        
        resultado.append("")
        resultado.append("=== REGRA DE NEGÓCIO ===")
        resultado.append("Para gerar lançamentos financeiros:")
        resultado.append("1. ✅ Status = 'Concluída' (serviço executado)")
        resultado.append("2. ✅ Forma pagamento indica pagamento efetivado")
        resultado.append("   - Aceitos: 'pago', 'à vista', 'dinheiro', 'pix', 'cartão'")
        resultado.append("   - Rejeitados: 'parcelado', 'pendente', 'a prazo', etc.")
        
        return "<br>".join(resultado)
        
    except Exception as e:
        import traceback
        return f"❌ Erro: {str(e)}<br><pre>{traceback.format_exc()}</pre>"

# ========== APIS DE CÁLCULO PARA JAVASCRIPT ==========

@os_bp.route('/api/calcular-horas', methods=['POST'])
def calcular_horas_api():
    """API para calcular horas trabalhadas"""
    try:
        data = request.get_json()
        hora_inicio = data.get('hora_inicio')
        hora_termino = data.get('hora_termino')
        
        horas = CalculadoraOS.calcular_horas_trabalhadas(hora_inicio, hora_termino)
        
        return jsonify({
            'sucesso': True,
            'total_horas': horas,  # Mudança aqui!
            'horas_trabalhadas': horas,  # Mantém compatibilidade
            'horas_formatadas': f"{horas:.2f}h"
        })
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        }), 400

@os_bp.route('/api/calcular-deslocamento', methods=['POST'])
def calcular_deslocamento_api():
    """API para calcular deslocamento"""
    try:
        data = request.get_json()
        km_inicial = data.get('km_inicial')
        km_final = data.get('km_final')
        
        km_total = CalculadoraOS.calcular_km_total(km_inicial, km_final)
        valor_deslocamento = CalculadoraOS.calcular_valor_deslocamento(km_total)
        
        return jsonify({
            'sucesso': True,
            'km_total': km_total,
            'km_total_formatado': f"{km_total:.1f} km",
            'valor_deslocamento': valor_deslocamento,
            'valor_formatado': f"R$ {valor_deslocamento:.2f}",
            'observacao': "R$ 0,00 (≤50km)" if km_total <= 50 else f"R$ 1,50/km se > 50km"
        })
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        }), 400

@os_bp.route('/api/calcular-totais', methods=['POST'])
def calcular_totais_api():
    """API para calcular todos os totais"""
    try:
        data = request.get_json()
        
        # Extrair dados do formulário
        dados_form = {
            'hora_inicio': data.get('hora_inicio'),
            'hora_termino': data.get('hora_termino'),
            'km_inicial': data.get('km_inicial'),
            'km_final': data.get('km_final')
        }
        
        servicos_data = data.get('servicos', [])
        produtos_data = data.get('produtos', [])
        
        # Calcular todos os valores usando a classe CalculadoraOS
        calculos = CalculadoraOS.calcular_todos_valores(dados_form, servicos_data, produtos_data)
        
        return jsonify({
            'sucesso': True,
            'calculos': calculos
        })
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'erro': str(e)
        }), 400

# === NOVA ROTA PARA FINALIZAR ORDEM DE SERVIÇO E LANÇAR NO FINANCEIRO ===
@os_bp.route('/<int:id>/finalizar', methods=['POST'], endpoint='finalizar_os')
def finalizar_os(id):
    """Finaliza uma ordem de serviço e lança no financeiro"""
    try:
        ordem = OrdemServico.query.get_or_404(id)

        # Verificar se a OS já está finalizada
        if ordem.status == 'Finalizada':
            flash('Ordem de serviço já está finalizada.', 'info')
            return redirect(url_for('os.visualizar_os', id=id))

        # Atualizar status da OS
        ordem.status = 'Finalizada'
        
        # Verificar se deve lançar no financeiro (se status_pagamento for 'pago')
        if ordem.status_pagamento == 'pago':
            # Importar serviço de lançamentos
            from app.financeiro.lancamento_os_service import gerar_lancamentos_financeiro, parse_schedule_custom
            from decimal import Decimal
            
            # Preparar dados para geração dos lançamentos
            forma_pagamento = ordem.forma_pagamento or 'Dinheiro'
            valor_total = Decimal(str(ordem.valor_total))
            parcelas = ordem.qtd_parcelas or 1
            entrada = Decimal(str(ordem.valor_entrada)) if ordem.valor_entrada else Decimal('0.00')
            
            # Parse cronograma personalizado se existir
            schedule_custom = parse_schedule_custom(ordem.schedule_json)
            
            # Gerar lançamentos (função idempotente)
            gerar_lancamentos_financeiro(
                os=ordem,
                forma_pagamento=forma_pagamento,
                valor_total=valor_total,
                parcelas=parcelas,
                entrada=entrada,
                schedule_custom=schedule_custom
            )
            
            # Também criar um lançamento no módulo financeiro geral
            from app.financeiro.financeiro_model import LancamentoFinanceiro
            lancamento = LancamentoFinanceiro(
                descricao=f'Ordem de Serviço {ordem.codigo}',
                valor=ordem.valor_total,
                data=datetime.now(),
                tipo='Receita',
                categoria='Serviços',
                origem='Ordem de Serviço',
                referencia=ordem.codigo
            )
            db.session.add(lancamento)
            
        # Salvar todas as alterações
        db.session.commit()

        flash('Ordem de serviço finalizada e lançada no financeiro com sucesso!', 'success')
        return redirect(url_for('os.visualizar_os', id=id))

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao finalizar OS: {e}', 'error')
        return redirect(url_for('os.visualizar_os', id=id))


# === ROTA TEMPORÁRIA PARA RECALCULAR TODAS AS OS ===
@os_bp.route('/recalcular_todas', methods=['GET'])
def recalcular_todas_os():
    """Rota temporária para recalcular todas as ordens de serviço"""
    try:
        # Buscar todas as ordens de serviço
        ordens = OrdemServico.query.order_by(OrdemServico.id).all()
        total_ordens = len(ordens)
        ordens_atualizadas = 0
        
        # Renumerar ordens de serviço a partir de OS0350
        novo_numero = 350
        
        for ordem in ordens:
            valor_antes = ordem.valor_total
            codigo_antes = ordem.codigo
            
            # Atualizar código
            novo_codigo = f"OS{novo_numero:04d}"
            ordem.codigo = novo_codigo
            
            # Recalcular valores
            ordem.recalcular_valores()
            
            if valor_antes != ordem.valor_total or codigo_antes != novo_codigo:
                ordens_atualizadas += 1
            
            print(f"OS {codigo_antes} → {novo_codigo} | Valor: R$ {valor_antes:.2f} → R$ {ordem.valor_total:.2f}")
            novo_numero += 1
        
        # Salvar todas as alterações
        db.session.commit()
        
        flash(f'Recálculo e renumeração concluídos! {ordens_atualizadas} de {total_ordens} ordens atualizadas.', 'success')
        return redirect(url_for('os.listar_os'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro durante o recálculo: {e}', 'error')
        return redirect(url_for('os.listar_os'))

# === ROTA DE TESTE AUTOCOMPLETE ===
@os_bp.route('/test-autocomplete')
def test_autocomplete():
    from flask import render_template_string
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Teste Autocomplete</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background: #f8f9fa; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .input-group { position: relative; width: 100%; margin: 20px 0; }
        .form-control { 
            width: 100%; 
            padding: 12px; 
            font-size: 16px; 
            border: 2px solid #ddd; 
            border-radius: 6px; 
            box-sizing: border-box;
        }
        .form-control:focus { border-color: #007bff; outline: none; }
        .dropdown-menu {
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            border: 2px solid #ddd;
            background: white;
            z-index: 1000;
            border-radius: 0 0 6px 6px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            max-height: 300px;
            overflow-y: auto;
        }
        .dropdown-item {
            display: block;
            padding: 12px 16px;
            text-decoration: none;
            color: #333;
            cursor: pointer;
            border-bottom: 1px solid #eee;
        }
        .dropdown-item:hover {
            background: #f8f9fa;
        }
        .dropdown-item:last-child {
            border-bottom: none;
        }
        .status {
            margin: 15px 0;
            padding: 12px;
            border-radius: 6px;
            font-weight: 500;
        }
        .status.info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        .status.success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .status.error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .status.warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 Teste de Autocomplete de Clientes</h1>
        <p><strong>Instruções:</strong> Digite 2 ou mais letras para buscar clientes. Exemplo: "SA" para encontrar "SAROBA"</p>
        
        <div class="input-group">
            <input id="cliente_input" class="form-control" placeholder="Digite para buscar clientes..." autocomplete="off">
            <div id="cliente_dropdown" class="dropdown-menu" style="display: none;"></div>
        </div>
        
        <div id="status" class="status info">
            ✅ Página carregada. Digite para testar o autocomplete...
        </div>
        
        <div id="resultado" style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 6px; border-left: 4px solid #007bff;">
            <strong>Resultado:</strong> Nenhum cliente selecionado ainda.
        </div>
        
        <div style="margin-top: 30px; padding: 15px; background: #e9ecef; border-radius: 6px; font-size: 14px;">
            <strong>Debug Info:</strong>
            <div id="debug">Aguardando ações...</div>
        </div>
    </div>
    
    <script>
        console.log('🚀 Página de teste carregada');
        
        const input = document.getElementById('cliente_input');
        const dropdown = document.getElementById('cliente_dropdown');
        const status = document.getElementById('status');
        const resultado = document.getElementById('resultado');
        const debug = document.getElementById('debug');
        
        function updateStatus(message, type = 'info') {
            status.className = 'status ' + type;
            status.innerHTML = message;
            debug.innerHTML += '<br>' + new Date().toLocaleTimeString() + ': ' + message.replace(/[🔍📝📡👥✅❌⌨️🎯]/g, '');
        }
        
        console.log('Elementos encontrados:', {input, dropdown, status, resultado});
        
        if (!input || !dropdown) {
            updateStatus('❌ Elementos não encontrados!', 'error');
        } else {
            updateStatus('✅ Elementos DOM encontrados. Digite para testar...', 'success');
        }
        
        let timeout = null;
        let requestCount = 0;
        
        input.addEventListener('input', function() {
            const query = this.value.trim();
            console.log('📝 Input event. Valor:', query);
            
            updateStatus('⌨️ Digitando: "' + query + '"', 'info');
            
            if (timeout) {
                clearTimeout(timeout);
            }
            
            if (query.length < 2) {
                dropdown.style.display = 'none';
                updateStatus('Digite pelo menos 2 caracteres...', 'warning');
                return;
            }
            
            updateStatus('🔍 Preparando busca para: "' + query + '"', 'warning');
            
            timeout = setTimeout(function() {
                requestCount++;
                const url = '/clientes/api/busca?q=' + encodeURIComponent(query);
                console.log('🌐 Fazendo requisição #' + requestCount + ' para:', url);
                
                updateStatus('📡 Fazendo requisição #' + requestCount + ' para API...', 'warning');
                
                fetch(url)
                    .then(response => {
                        console.log('📡 Resposta recebida. Status:', response.status);
                        updateStatus('📡 Resposta recebida (status: ' + response.status + ')', 'info');
                        
                        if (!response.ok) {
                            throw new Error('HTTP ' + response.status);
                        }
                        
                        return response.json();
                    })
                    .then(clientes => {
                        console.log('👥 Dados recebidos:', clientes);
                        
                        if (!Array.isArray(clientes)) {
                            console.error('Resposta não é um array:', clientes);
                            updateStatus('❌ Resposta inválida da API', 'error');
                            return;
                        }
                        
                        updateStatus('👥 Encontrados: ' + clientes.length + ' clientes', 'success');
                        
                        dropdown.innerHTML = '';
                        
                        if (clientes.length === 0) {
                            dropdown.innerHTML = '<div class="dropdown-item" style="color: #666;">Nenhum cliente encontrado</div>';
                            dropdown.style.display = 'block';
                            return;
                        }
                        
                        clientes.forEach((cliente, index) => {
                            console.log('Cliente #' + (index + 1) + ':', cliente);
                            
                            const item = document.createElement('a');
                            item.className = 'dropdown-item';
                            item.textContent = cliente.nome + ' (' + (cliente.cpf_cnpj || 'Sem CPF/CNPJ') + ')';
                            
                            item.addEventListener('click', function(e) {
                                e.preventDefault();
                                console.log('✅ Cliente selecionado:', cliente);
                                
                                input.value = item.textContent;
                                dropdown.style.display = 'none';
                                
                                updateStatus('🎯 Cliente selecionado!', 'success');
                                resultado.innerHTML = '<strong>Cliente Selecionado:</strong><br>' +
                                    'Nome: ' + cliente.nome + '<br>' +
                                    'CPF/CNPJ: ' + (cliente.cpf_cnpj || 'Não informado') + '<br>' +
                                    'Telefone: ' + (cliente.telefone || 'Não informado') + '<br>' +
                                    'Email: ' + (cliente.email || 'Não informado');
                            });
                            
                            dropdown.appendChild(item);
                        });
                        
                        dropdown.style.display = 'block';
                        updateStatus('📋 Lista de ' + clientes.length + ' clientes exibida', 'success');
                    })
                    .catch(error => {
                        console.error('❌ Erro na requisição:', error);
                        updateStatus('❌ Erro: ' + error.message, 'error');
                        dropdown.style.display = 'none';
                    });
            }, 300);
        });
        
        // Fechar dropdown ao clicar fora
        document.addEventListener('click', function(e) {
            if (!input.contains(e.target) && !dropdown.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });
        
        updateStatus('✅ Event listeners configurados. Pronto para uso!', 'success');
        console.log('✅ Script totalmente configurado');
    </script>
</body>
</html>
    ''')
