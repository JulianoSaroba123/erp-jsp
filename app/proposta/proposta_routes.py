from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response
from sqlalchemy import text, or_
from sqlalchemy.orm import joinedload
from decimal import Decimal
from datetime import datetime, date
import logging

# Importar modelos
from app.cliente.cliente_model import Cliente
from app.proposta.proposta_model import Proposta, PropostaProduto, PropostaServico
from app.extensoes import db

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Função auxiliar para converter valores monetários
def converter_valor_monetario(valor_str):
    """Converte string monetária brasileira para float."""
    if not valor_str:
        return 0.0
    
    # Tratar diferentes formatos
    valor_str = str(valor_str).strip()
    
    # Remover símbolos de moeda se existirem
    valor_str = valor_str.replace('R$', '').replace('r$', '').strip()
    
    # Se contém vírgula e ponto, assume formato brasileiro (1.234,56)
    if ',' in valor_str and '.' in valor_str:
        # Remove pontos (separadores de milhares) e troca vírgula por ponto
        valor_str = valor_str.replace('.', '').replace(',', '.')
    elif ',' in valor_str:
        # Só vírgula, troca por ponto
        valor_str = valor_str.replace(',', '.')
    
    try:
        return float(valor_str)
    except (ValueError, TypeError):
        logger.warning(f"Erro ao converter valor monetário: {valor_str}")
        return 0.0

proposta_bp = Blueprint('proposta', __name__, template_folder='templates')

@proposta_bp.route('/')
def listar_propostas():
    """Listar propostas com filtros funcionais."""
    try:
        logger.debug("Iniciando listagem de propostas...")
        
        # Pegar parâmetros de filtro
        status_filtro = request.args.get('status', '')
        cliente_filtro = request.args.get('cliente', '')
        codigo_filtro = request.args.get('codigo', '')
        
        logger.debug(f"Filtros: status={status_filtro}, cliente={cliente_filtro}, codigo={codigo_filtro}")
        
        # Construir query base - apenas propostas ativas
        query = db.session.query(Proposta).join(Cliente, Proposta.cliente_id == Cliente.id, isouter=True).filter(Proposta.ativo == True)
        
        # Aplicar filtros
        if status_filtro:
            query = query.filter(Proposta.status == status_filtro)
        
        if cliente_filtro:
            query = query.filter(Cliente.nome.ilike(f'%{cliente_filtro}%'))
        
        if codigo_filtro:
            query = query.filter(Proposta.codigo.ilike(f'%{codigo_filtro}%'))
        
        # Executar query
        propostas = query.order_by(Proposta.data_emissao.desc()).all()
        
        logger.debug(f"Encontradas {len(propostas)} propostas")
        
        # Calcular estatísticas
        total_propostas = len(propostas)
        propostas_pendentes = len([p for p in propostas if p.status in ['Pendente', 'Enviada']])
        propostas_aprovadas = len([p for p in propostas if p.status == 'Aprovada'])
        valor_total = sum([p.valor_total or 0 for p in propostas])
        
        logger.debug(f"Estatísticas: total={total_propostas}, pendentes={propostas_pendentes}, aprovadas={propostas_aprovadas}, valor={valor_total}")
        
        # Render template
        logger.debug("Renderizando template proposta/listar.html")
        return render_template('proposta/listar.html',
                             propostas=propostas,
                             total_propostas=total_propostas,
                             propostas_pendentes=propostas_pendentes,
                             propostas_aprovadas=propostas_aprovadas,
                             valor_total=valor_total)
        
    except Exception as e:
        logger.error(f"Erro ao listar propostas: {str(e)}")
        flash(f'Erro ao carregar propostas: {str(e)}', 'error')
        return render_template('proposta/listar.html', propostas=[])

@proposta_bp.route('/teste-simples')
def teste_simples():
    """Teste com formulário simples."""
    return render_template('proposta/form_simples.html')

@proposta_bp.route('/nova', methods=['GET', 'POST'])
def nova_proposta():
    """Criar nova proposta."""
    try:
        logger.debug("Acessando rota nova proposta...")
        
        if request.method == 'POST':
            logger.debug("Processando POST para nova proposta...")
            
            # Validar dados obrigatórios
            titulo = request.form.get('titulo')
            cliente_id = request.form.get('cliente_id')
            
            if not titulo or not cliente_id:
                flash('Título e cliente são obrigatórios', 'error')
                clientes = Cliente.query.order_by(Cliente.nome).all()
                return render_template('proposta/form.html', 
                                     proposta=None, 
                                     clientes=clientes)
            
            # Criar nova proposta
            nova_prop = Proposta(
                cliente_id=int(cliente_id),
                titulo=titulo,
                descricao=request.form.get('descricao', ''),
                status='Pendente',
                vendedor=request.form.get('vendedor', ''),
                prioridade=request.form.get('prioridade', 'normal'),
                tempo_estimado=request.form.get('tempo_estimado', ''),
                forma_pagamento=request.form.get('forma_pagamento', ''),
                prazo_execucao=request.form.get('prazo_execucao', ''),
                garantia=request.form.get('garantia', ''),
                validade=int(request.form.get('validade', 30) or 30),
                observacoes=request.form.get('observacoes', ''),
                condicoes_pagamento=request.form.get('condicoes_pagamento', ''),
                desconto=converter_valor_monetario(request.form.get('desconto', 0)),
                valor_total=0  # Será calculado depois
            )
            
            # Processar KM estimado
            km_estimado_str = request.form.get('km_estimado', '').strip()
            if km_estimado_str:
                try:
                    km_estimado_str = km_estimado_str.replace(',', '.')
                    nova_prop.km_estimado = Decimal(km_estimado_str)
                except (ValueError, TypeError, Exception):
                    nova_prop.km_estimado = None
            
            # Processar data de emissão
            data_emissao = request.form.get('data_emissao')
            if data_emissao:
                nova_prop.data_emissao = datetime.strptime(data_emissao, '%Y-%m-%d').date()
            else:
                nova_prop.data_emissao = date.today()
            
            db.session.add(nova_prop)
            db.session.commit()
            
            logger.debug(f"Nova proposta criada com ID: {nova_prop.id}")
            flash('Proposta criada com sucesso!', 'success')
            return redirect(url_for('proposta.editar_proposta', id=nova_prop.id))
        
        # GET - Mostrar formulário
        clientes = Cliente.query.order_by(Cliente.nome).all()
        logger.debug(f"Encontrados {len(clientes)} clientes")
        
        return render_template('proposta/form.html', 
                             proposta=None, 
                             clientes=clientes)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro na rota nova proposta: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Erro ao processar proposta: {str(e)}', 'error')
        
        # Retornar formulário com erro
        clientes = Cliente.query.order_by(Cliente.nome).all()
        return render_template('proposta/form.html', 
                             proposta=None, 
                             clientes=clientes)

@proposta_bp.route('/<int:id>')
def visualizar_proposta(id):
    """Visualizar detalhes de uma proposta."""
    try:
        proposta = Proposta.query.filter_by(id=id, ativo=True).first_or_404()
        return render_template('proposta/visualizar.html', proposta=proposta)
    except Exception as e:
        logger.error(f"Erro ao visualizar proposta {id}: {str(e)}")
        flash(f'Erro ao carregar proposta: {str(e)}', 'error')
        return redirect(url_for('proposta.listar_propostas'))

@proposta_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar_proposta(id):
    """Editar uma proposta existente."""
    # Carregar proposta com todos os relacionamentos - apenas se ativa
    proposta = Proposta.query.options(
        joinedload(Proposta.itens_produto),
        joinedload(Proposta.itens_servico),
        joinedload(Proposta.cliente)
    ).filter_by(id=id, ativo=True).first_or_404()
    
    if request.method == 'POST':
        try:
            # Debug: Log dos dados recebidos
            logger.debug(f"💾 Salvando proposta {id}")
            logger.debug(f"📝 Form data recebido: {dict(request.form)}")
            
            # Validar dados obrigatórios
            titulo = request.form.get('titulo')
            cliente_id = request.form.get('cliente_id')
            
            if not titulo or not cliente_id:
                flash('Título e cliente são obrigatórios', 'error')
                return redirect(url_for('proposta.editar_proposta', id=id))
            
            # Atualizar proposta
            proposta.titulo = titulo
            proposta.cliente_id = int(cliente_id)
            proposta.descricao = request.form.get('descricao', '')
            proposta.status = request.form.get('status', 'pendente')
            proposta.vendedor = request.form.get('vendedor', '')
            proposta.prioridade = request.form.get('prioridade', 'normal')
            proposta.tempo_estimado = request.form.get('tempo_estimado', '')
            
            # Processar KM estimado
            km_estimado_str = request.form.get('km_estimado', '').strip()
            if km_estimado_str:
                try:
                    # Converter vírgula para ponto se necessário
                    km_estimado_str = km_estimado_str.replace(',', '.')
                    proposta.km_estimado = Decimal(km_estimado_str)
                except (ValueError, TypeError, Exception):
                    proposta.km_estimado = None
            else:
                proposta.km_estimado = None
                
            proposta.forma_pagamento = request.form.get('forma_pagamento', '')
            proposta.prazo_execucao = request.form.get('prazo_execucao', '')
            proposta.garantia = request.form.get('garantia', '')
            proposta.validade = int(request.form.get('validade', 30) or 30)
            proposta.observacoes = request.form.get('observacoes', '')
            proposta.condicoes_pagamento = request.form.get('condicoes_pagamento', '')
            proposta.desconto = converter_valor_monetario(request.form.get('desconto', 0))
            
            # Processar data de emissão
            data_emissao = request.form.get('data_emissao')
            if data_emissao:
                proposta.data_emissao = datetime.strptime(data_emissao, '%Y-%m-%d').date()
            
            # Processar produtos
            produtos_descricoes = request.form.getlist('produto_descricao[]')
            produtos_qtds = request.form.getlist('produto_quantidade[]')
            produtos_valores = request.form.getlist('produto_valor[]')
            
            logger.debug(f"📦 Produtos recebidos: desc={produtos_descricoes}, qtd={produtos_qtds}, valor={produtos_valores}")
            
            valor_total_produtos = 0
            produtos_validos = []
            
            # Validar e preparar produtos
            for i in range(len(produtos_descricoes)):
                descricao = produtos_descricoes[i].strip()
                if descricao:  # Só processa se tiver descrição
                    qtd_str = produtos_qtds[i] if i < len(produtos_qtds) else '1'
                    valor_str = produtos_valores[i] if i < len(produtos_valores) else '0'
                    
                    qtd = converter_valor_monetario(qtd_str) or 1.0
                    valor = converter_valor_monetario(valor_str) or 0.0
                    valor_item = qtd * valor
                    
                    produtos_validos.append({
                        'descricao': descricao,
                        'quantidade': qtd,
                        'valor_unitario': valor,
                        'valor_total': valor_item
                    })
                    valor_total_produtos += valor_item
            
            # Processar serviços
            servicos_descricoes = request.form.getlist('servico_descricao[]')
            servicos_qtds = request.form.getlist('servico_horas[]')  # Corrigido: usar servico_horas[]
            servicos_valores = request.form.getlist('servico_valor[]')
            
            logger.debug(f"🔧 Serviços recebidos: desc={servicos_descricoes}, horas={servicos_qtds}, valor={servicos_valores}")
            
            valor_total_servicos = 0
            servicos_validos = []
            
            # Validar e preparar serviços
            for i in range(len(servicos_descricoes)):
                descricao = servicos_descricoes[i].strip()
                if descricao:  # Só processa se tiver descrição
                    qtd_str = servicos_qtds[i] if i < len(servicos_qtds) else '1'
                    valor_str = servicos_valores[i] if i < len(servicos_valores) else '0'
                    
                    qtd = converter_valor_monetario(qtd_str) or 1.0
                    valor = converter_valor_monetario(valor_str) or 0.0
                    valor_item = qtd * valor
                    
                    servicos_validos.append({
                        'descricao': descricao,
                        'quantidade': qtd,
                        'valor_unitario': valor,
                        'valor_total': valor_item
                    })
                    valor_total_servicos += valor_item
            
            # Desativar produtos e serviços existentes
            db.session.execute(
                text("UPDATE proposta_produto SET ativo = 0 WHERE proposta_id = :id"),
                {"id": id}
            )
            db.session.execute(
                text("UPDATE proposta_servico SET ativo = 0 WHERE proposta_id = :id"),
                {"id": id}
            )
            
            # Inserir produtos válidos usando ORM
            from app.proposta.proposta_model import PropostaProduto, PropostaServico
            
            for produto in produtos_validos:
                novo_produto = PropostaProduto(
                    proposta_id=id,
                    descricao=produto['descricao'],
                    quantidade=produto['quantidade'],
                    valor_unitario=produto['valor_unitario'],
                    valor_total=produto['valor_total'],
                    ativo=True
                )
                db.session.add(novo_produto)
            
            # Inserir serviços válidos usando ORM
            for servico in servicos_validos:
                novo_servico = PropostaServico(
                    proposta_id=id,
                    descricao=servico['descricao'],
                    quantidade=servico['quantidade'],
                    valor_unitario=servico['valor_unitario'],
                    valor_total=servico['valor_total'],
                    ativo=True
                )
                db.session.add(novo_servico)
            
            # Calcular valores finais
            subtotal = valor_total_produtos + valor_total_servicos
            desconto_valor = subtotal * (proposta.desconto / 100)
            valor_final = subtotal - desconto_valor
            
            # Atualizar valores na proposta
            proposta.valor_produtos = valor_total_produtos
            proposta.valor_servicos = valor_total_servicos
            proposta.valor_total = valor_final
            
            logger.debug(f"💰 Valores calculados: produtos={valor_total_produtos}, servicos={valor_total_servicos}, total={valor_final}")
            logger.debug(f"📊 Produtos válidos: {len(produtos_validos)}, Serviços válidos: {len(servicos_validos)}")
            
            db.session.commit()
            
            logger.debug(f"✅ Proposta {id} atualizada com sucesso!")
            flash('Proposta atualizada com sucesso!', 'success')
            return redirect(url_for('proposta.visualizar_proposta', id=id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao editar proposta {id}: {str(e)}")
            flash(f'Erro ao atualizar proposta: {str(e)}', 'error')
    
    # GET - mostrar formulário
    clientes = Cliente.query.order_by(Cliente.nome).all()
    return render_template('proposta/form.html', proposta=proposta, clientes=clientes)

@proposta_bp.route('/<int:id>/excluir', methods=['GET', 'POST'])
def excluir_proposta(id):
    """Excluir uma proposta (soft delete)."""
    try:
        proposta = Proposta.query.get_or_404(id)
        
        # Se for GET, mostrar página de confirmação
        if request.method == 'GET':
            return render_template('proposta/confirmar_exclusao.html', proposta=proposta)
        
        # Se for POST, executar exclusão (soft delete)
        if request.method == 'POST':
            codigo = proposta.codigo
            
            # Soft delete - marcar como inativo
            proposta.ativo = False
            
            # Marcar parcelas como inativas também
            from app.proposta.proposta_model import PropostaParcela, PropostaAnexo
            
            parcelas = PropostaParcela.query.filter_by(proposta_id=proposta.id).all()
            for parcela in parcelas:
                parcela.ativo = False
            
            # Marcar anexos como inativos também
            anexos = PropostaAnexo.query.filter_by(proposta_id=proposta.id).all()
            for anexo in anexos:
                anexo.ativo = False
            
            db.session.commit()
            
            flash(f'Proposta {codigo} excluída com sucesso!', 'success')
            return redirect(url_for('proposta.listar_propostas'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao excluir proposta {id}: {str(e)}")
        flash(f'Erro ao excluir proposta: {str(e)}', 'error')
        return redirect(url_for('proposta.listar_propostas'))

@proposta_bp.route('/<int:id>/pdf')
def gerar_pdf(id):
    """Gerar PDF de uma proposta."""
    try:
        # Importar db no início
        from app.extensoes import db
        
        # Carregar proposta com relacionamentos
        proposta = Proposta.query.options(
            db.joinedload(Proposta.cliente)
        ).get_or_404(id)
        
        # Carregar produtos e serviços via SQL direto
        produtos_result = db.session.execute(
            text("SELECT descricao, quantidade, valor_unitario, valor_total FROM proposta_produto WHERE proposta_id = :id AND ativo = 1"), 
            {"id": id}
        ).fetchall()
        
        servicos_result = db.session.execute(
            text("SELECT descricao, quantidade, valor_unitario, valor_total FROM proposta_servico WHERE proposta_id = :id AND ativo = 1"), 
            {"id": id}
        ).fetchall()
        
        # Converter para objetos simples
        class ItemProposta:
            def __init__(self, descricao, quantidade, valor_unitario, valor_total):
                self.descricao = descricao
                self.quantidade = quantidade
                self.valor_unitario = valor_unitario
                self.valor_total = valor_total
        
        proposta.produtos = [ItemProposta(p[0], p[1], p[2], p[3]) for p in produtos_result]
        proposta.servicos = [ItemProposta(s[0], s[1], s[2], s[3]) for s in servicos_result]
        
        # Tentar importar WeasyPrint
        try:
            import weasyprint
            from flask import current_app
            import os
            
            # Importar configurações da empresa
            from app.configuracao.configuracao_utils import get_config
            config = get_config()
            
            # Caminho absoluto para a logo
            project_root = os.path.dirname(current_app.root_path)
            logo_path = os.path.join(project_root, "static", "img", "JSP.jpg")
            logo_url = f"file:///{logo_path.replace(os.sep, '/')}"
            
            # Renderizar template HTML com o caminho da logo e configurações
            html_content = render_template('proposta/pdf_proposta.html', 
                                         proposta=proposta, 
                                         logo_url=logo_url,
                                         config=config)
            
            # Base URL para resolver outros caminhos relativos
            base_url = f"file:///{project_root.replace(os.sep, '/')}/"
            
            # Gerar PDF com base_url para resolver imagens
            pdf = weasyprint.HTML(string=html_content, base_url=base_url).write_pdf()
            
            # Criar resposta com headers para evitar cache
            response = make_response(pdf)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'inline; filename=proposta_{proposta.codigo}.pdf'
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            
            return response
            
        except ImportError:
            # WeasyPrint não disponível - retornar HTML
            logger.warning("WeasyPrint não encontrado - retornando HTML")
            flash('Biblioteca PDF não disponível - exibindo versão HTML', 'warning')
            
            # Importar configurações da empresa para HTML também
            from app.configuracao.configuracao_utils import get_config
            config = get_config()
            
            # Criar resposta HTML com headers de não-cache
            html_response = make_response(render_template('proposta/pdf_proposta.html', 
                                                        proposta=proposta,
                                                        config=config))
            html_response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            html_response.headers['Pragma'] = 'no-cache'
            html_response.headers['Expires'] = '0'
            
            return html_response
            
    except Exception as e:
        logger.error(f"Erro ao gerar PDF da proposta {id}: {str(e)}")
        flash(f'Erro ao gerar PDF: {str(e)}', 'error')
        return redirect(url_for('proposta.visualizar_proposta', id=id))

@proposta_bp.route('/<int:id>/duplicar', methods=['POST'])
def duplicar_proposta(id):
    """Duplicar uma proposta existente."""
    try:
        proposta_original = Proposta.query.get_or_404(id)
        
        # Criar nova proposta (código será gerado automaticamente)
        nova_proposta = Proposta(
            cliente_id=proposta_original.cliente_id,
            titulo=f"CÓPIA - {proposta_original.titulo}",
            descricao=proposta_original.descricao,
            valor_total=proposta_original.valor_total,
            status='Pendente',
            vendedor=proposta_original.vendedor,
            forma_pagamento=proposta_original.forma_pagamento,
            prazo_execucao=proposta_original.prazo_execucao,
            garantia=proposta_original.garantia,
            validade=proposta_original.validade,
            observacoes=f"Duplicada de: {proposta_original.codigo}",
            itens_json=proposta_original.itens_json
        )
        
        db.session.add(nova_proposta)
        db.session.commit()
        
        flash(f'Proposta duplicada com sucesso! Novo código: {nova_proposta.codigo}', 'success')
        return redirect(url_for('proposta.editar_proposta', id=nova_proposta.id))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao duplicar proposta {id}: {str(e)}")
        flash(f'Erro ao duplicar proposta: {str(e)}', 'error')
        return redirect(url_for('proposta.visualizar_proposta', id=id))

# API Endpoints

@proposta_bp.route('/api/clientes')
def api_clientes():
    """API para buscar clientes (autocomplete)."""
    try:
        termo = request.args.get('q', '')
        clientes = Cliente.query.filter(
            Cliente.nome.ilike(f'%{termo}%')
        ).limit(10).all()
        
        return jsonify([{
            'id': c.id,
            'nome': c.nome,
            'email': c.email or ''
        } for c in clientes])
        
    except Exception as e:
        logger.error(f"Erro na API de clientes: {str(e)}")
        return jsonify([]), 500

@proposta_bp.route('/api/<int:id>/status', methods=['PUT'])
def atualizar_status(id):
    """API para atualizar status de proposta via AJAX."""
    try:
        proposta = Proposta.query.get_or_404(id)
        novo_status = request.json.get('status')
        
        if novo_status not in ['Pendente', 'Enviada', 'Aprovada', 'Rejeitada']:
            return jsonify({'error': 'Status inválido'}), 400
        
        proposta.status = novo_status
        
        # Se aprovada, definir data de aprovação
        if novo_status == 'Aprovada':
            proposta.data_aprovacao = date.today()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'status': novo_status,
            'message': f'Status atualizado para: {novo_status}'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar status da proposta {id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@proposta_bp.route('/<int:id>/relatorio-proposta')
def relatorio_proposta(id):
    """Gera relatório detalhado da proposta."""
    try:
        proposta = Proposta.query.options(
            db.joinedload(Proposta.cliente)
        ).get_or_404(id)
        
        # Preparar dados para o template
        dados_proposta = {
            'numero': proposta.codigo or f"PROP-{proposta.id:04d}",
            'data': proposta.data_emissao.strftime('%d/%m/%Y') if proposta.data_emissao else datetime.now().strftime('%d/%m/%Y'),
            'vendedor': 'JSP Automação',
            'validade': '30',
            'previsao_entrega': '15 dias úteis',
            'cliente': {
                'razao_social': proposta.cliente.nome if proposta.cliente else 'N/A',
                'nome_fantasia': proposta.cliente.nome if proposta.cliente else 'N/A',
                'cnpj': proposta.cliente.cpf_cnpj if proposta.cliente and proposta.cliente.tipo == 'PJ' else '-',
                'cpf': proposta.cliente.cpf_cnpj if proposta.cliente and proposta.cliente.tipo == 'PF' else '-',
                'endereco': f"{proposta.cliente.endereco or ''} - {proposta.cliente.cidade or ''}" if proposta.cliente else 'N/A',
                'cep': proposta.cliente.cep if proposta.cliente else 'N/A',
                'cidade_uf': f"{proposta.cliente.cidade or ''}/{proposta.cliente.estado or ''}" if proposta.cliente else 'N/A',
                'telefones': proposta.cliente.telefone if proposta.cliente else 'N/A',
                'email': proposta.cliente.email if proposta.cliente else 'N/A'
            },
            'itens': [],
            'pagamentos': [
                {
                    'vencimento': '30 dias',
                    'valor': f"R$ {proposta.valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if proposta.valor_total else 'R$ 0,00',
                    'forma': 'PIX/Transferência',
                    'observacao': 'Pagamento à vista'
                }
            ],
            'observacoes': [
                'Proposta válida por 30 dias',
                'Preço sujeito a alteração sem aviso prévio',
                'Produto sujeito a disponibilidade de estoque',
                'Garantia conforme fabricante'
            ],
            'dados_bancarios': {
                'instituicao': 'Banco do Brasil',
                'agencia': '1234-5',
                'conta': '12345-6',
                'titular': 'JSP Automação Industrial & Solar',
                'cnpj': '41.280.764/0001-65',
                'pix': 'atendimento@eletricasaroba.com'
            }
        }
        
        # Processar itens da proposta se existirem
        if proposta.itens_json:
            import json
            try:
                itens = json.loads(proposta.itens_json)
                for item in itens:
                    dados_proposta['itens'].append({
                        'descricao': item.get('descricao', ''),
                        'quantidade': item.get('quantidade', 1),
                        'valor_unitario': f"R$ {float(item.get('valor_unitario', 0)):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                        'subtotal': f"R$ {float(item.get('subtotal', 0)):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    })
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        
        return render_template('proposta/relatorios/relatorio_proposta.html', proposta=proposta, dados=dados_proposta)
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório da proposta {id}: {str(e)}")
        flash(f'Erro ao gerar relatório: {str(e)}', 'error')
        return redirect(url_for('proposta.listar_propostas'))

@proposta_bp.route('/<int:id>/relatorio-os')
def relatorio_os(id):
    """Gera relatório de Ordem de Serviço baseado na proposta."""
    try:
        proposta = Proposta.query.options(
            db.joinedload(Proposta.cliente)
        ).get_or_404(id)
        
        # Preparar dados para o template de OS
        dados_os = {
            'numero': f"OS-{proposta.codigo or proposta.id:04d}",
            'data': proposta.data_criacao.strftime('%d/%m/%Y') if proposta.data_criacao else datetime.now().strftime('%d/%m/%Y'),
            'tecnico': 'JSP Automação',
            'prioridade': 'Normal',
            'prazo': '15 dias úteis',
            'cliente': {
                'razao_social': proposta.cliente.nome if proposta.cliente else 'N/A',
                'nome_fantasia': proposta.cliente.nome if proposta.cliente else 'N/A',
                'cnpj': proposta.cliente.cpf_cnpj if proposta.cliente and proposta.cliente.tipo == 'PJ' else '-',
                'cpf': proposta.cliente.cpf_cnpj if proposta.cliente and proposta.cliente.tipo == 'PF' else '-',
                'endereco': f"{proposta.cliente.endereco or ''} - {proposta.cliente.cidade or ''}" if proposta.cliente else 'N/A',
                'cep': proposta.cliente.cep if proposta.cliente else 'N/A',
                'cidade_uf': f"{proposta.cliente.cidade or ''}/{proposta.cliente.estado or ''}" if proposta.cliente else 'N/A',
                'telefones': proposta.cliente.telefone if proposta.cliente else 'N/A',
                'email': proposta.cliente.email if proposta.cliente else 'N/A'
            },
            'servicos': [],
            'materiais': [],
            'observacoes': [
                'Serviço será executado conforme normas técnicas',
                'Garantia de 12 meses para serviços executados',
                'Cliente deve fornecer acesso ao local',
                'Horário de execução: 8h às 17h'
            ],
            'valor_total': f"R$ {proposta.valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if proposta.valor_total else 'R$ 0,00'
        }
        
        # Processar itens da proposta como serviços/materiais
        if proposta.itens_json:
            import json
            try:
                itens = json.loads(proposta.itens_json)
                for item in itens:
                    # Adicionar como serviço
                    dados_os['servicos'].append({
                        'descricao': item.get('descricao', ''),
                        'quantidade': item.get('quantidade', 1),
                        'valor_unitario': f"R$ {float(item.get('valor_unitario', 0)):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                        'subtotal': f"R$ {float(item.get('subtotal', 0)):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    })
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        
        return render_template('os/relatorios/relatorio_os.html', os=dados_os)
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório de OS da proposta {id}: {str(e)}")
        flash(f'Erro ao gerar relatório de OS: {str(e)}', 'error')
        return redirect(url_for('proposta.listar_propostas'))