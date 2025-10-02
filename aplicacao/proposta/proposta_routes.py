from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, date, timedelta
from aplicacao.extensoes import db
from aplicacao.proposta.proposta_model import Proposta, PropostaItem
from aplicacao.cliente.cliente_model import Cliente

proposta_bp = Blueprint('proposta', __name__, url_prefix='/propostas', 
                       template_folder='templates')

@proposta_bp.route('/')
def listar_propostas():
    """Lista todas as propostas"""
    print("DEBUG LISTAR: Iniciando listagem de propostas...")
    try:
        # Buscar propostas não excluídas
        propostas = Proposta.query.filter(Proposta.data_exclusao.is_(None)).order_by(Proposta.data_criacao.desc()).all()
        print(f"DEBUG LISTAR: {len(propostas)} propostas encontradas")
        
        for proposta in propostas:
            print(f"DEBUG: ID: {proposta.id}, Número: {proposta.numero}, Título: {proposta.titulo}")
        
        return render_template('proposta/lista.html', propostas=propostas)
    except Exception as e:
        print(f"DEBUG LISTAR: Erro - {str(e)}")
        flash(f'Erro ao listar propostas: {str(e)}', 'danger')
        return render_template('proposta/lista.html', propostas=[])

@proposta_bp.route('/nova', methods=['GET', 'POST'])
def nova_proposta():
    """Criar nova proposta"""
    if request.method == 'GET':
        try:
            clientes = Cliente.query.filter(Cliente.ativo == True).order_by(Cliente.nome).all()
            return render_template('proposta/cadastro.html', clientes=clientes, proposta=None)
        except Exception as e:
            flash(f'Erro ao carregar formulário: {str(e)}', 'danger')
            return redirect(url_for('proposta.listar_propostas'))
    
    # DEBUG: Log do POST
    print(f"DEBUG PROPOSTA POST: Dados recebidos: {dict(request.form)}")
    
    try:
        # Criar nova proposta
        proposta = Proposta()
        
        # Dados básicos
        proposta.cliente_id = request.form.get('cliente_id')
        proposta.titulo = request.form.get('titulo', '').strip()
        proposta.descricao = request.form.get('descricao', '').strip()
        proposta.status = request.form.get('status', 'Pendente')
        
        print(f"DEBUG: Cliente ID: {proposta.cliente_id}, Título: {proposta.titulo}")
        
        # Valores
        proposta.valor_total = float(request.form.get('valor_total', 0) or 0)
        proposta.desconto = float(request.form.get('desconto', 0) or 0)
        proposta.calcular_valor_final()
        
        print(f"DEBUG: Valor Total: {proposta.valor_total}, Valor Final: {proposta.valor_final}")
        
        # Condições comerciais
        proposta.forma_pagamento = request.form.get('forma_pagamento', '').strip()
        proposta.prazo_entrega = request.form.get('prazo_entrega', '').strip()
        proposta.condicoes_gerais = request.form.get('condicoes_gerais', '').strip()
        
        # Data de validade
        data_validade_str = request.form.get('data_validade')
        if data_validade_str:
            proposta.data_validade = datetime.strptime(data_validade_str, '%Y-%m-%d').date()
        else:
            # Default: 7 dias de validade
            proposta.data_validade = date.today() + timedelta(days=7)
        
        # Observações
        proposta.observacoes_internas = request.form.get('observacoes_internas', '').strip()
        
        # Validações
        if not proposta.cliente_id:
            print("DEBUG: Erro - Cliente não selecionado")
            raise ValueError("Cliente é obrigatório")
        if not proposta.titulo:
            print("DEBUG: Erro - Título vazio")
            raise ValueError("Título é obrigatório")
        if proposta.valor_total < 0:
            print("DEBUG: Erro - Valor negativo")
            raise ValueError("Valor total não pode ser negativo")
        
        # Gerar número da proposta
        print("DEBUG: Gerando número...")
        proposta.gerar_numero()
        print(f"DEBUG: Número gerado: {proposta.numero}")
        
        # Salvar
        print("DEBUG: Salvando no banco...")
        db.session.add(proposta)
        db.session.commit()
        print(f"DEBUG: Proposta salva com ID: {proposta.id}")
        
        flash(f'Proposta {proposta.numero} criada com sucesso!', 'success')
        return redirect(url_for('proposta.listar_propostas'))
        
    except ValueError as e:
        flash(str(e), 'warning')
        clientes = Cliente.query.filter(Cliente.ativo == True).order_by(Cliente.nome).all()
        return render_template('proposta/cadastro.html', clientes=clientes, proposta=None)
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao criar proposta: {str(e)}', 'danger')
        clientes = Cliente.query.filter(Cliente.ativo == True).order_by(Cliente.nome).all()
        return render_template('proposta/cadastro.html', clientes=clientes, proposta=None)

@proposta_bp.route('/<int:proposta_id>')
def visualizar_proposta(proposta_id):
    """Visualizar detalhes da proposta"""
    try:
        proposta = Proposta.query.get_or_404(proposta_id)
        if proposta.data_exclusao:
            flash('Proposta não encontrada.', 'warning')
            return redirect(url_for('proposta.listar_propostas'))
        
        return render_template('proposta/visualizar.html', proposta=proposta)
    except Exception as e:
        flash(f'Erro ao visualizar proposta: {str(e)}', 'danger')
        return redirect(url_for('proposta.listar_propostas'))

@proposta_bp.route('/editar/<int:proposta_id>', methods=['GET', 'POST'])
def editar_proposta(proposta_id):
    """Editar proposta existente"""
    try:
        proposta = Proposta.query.get_or_404(proposta_id)
        if proposta.data_exclusao:
            flash('Proposta não encontrada.', 'warning')
            return redirect(url_for('proposta.listar_propostas'))
        
        if request.method == 'GET':
            clientes = Cliente.query.filter(Cliente.ativo == True).order_by(Cliente.nome).all()
            return render_template('proposta/cadastro.html', clientes=clientes, proposta=proposta)
        
        # Atualizar dados
        proposta.cliente_id = request.form.get('cliente_id')
        proposta.titulo = request.form.get('titulo', '').strip()
        proposta.descricao = request.form.get('descricao', '').strip()
        proposta.status = request.form.get('status', 'Pendente')
        
        # Valores
        proposta.valor_total = float(request.form.get('valor_total', 0) or 0)
        proposta.desconto = float(request.form.get('desconto', 0) or 0)
        proposta.calcular_valor_final()
        
        # Condições comerciais
        proposta.forma_pagamento = request.form.get('forma_pagamento', '').strip()
        proposta.prazo_entrega = request.form.get('prazo_entrega', '').strip()
        proposta.condicoes_gerais = request.form.get('condicoes_gerais', '').strip()
        
        # Data de validade
        data_validade_str = request.form.get('data_validade')
        if data_validade_str:
            proposta.data_validade = datetime.strptime(data_validade_str, '%Y-%m-%d').date()
        
        # Observações
        proposta.observacoes_internas = request.form.get('observacoes_internas', '').strip()
        
        # Validações
        if not proposta.cliente_id:
            raise ValueError("Cliente é obrigatório")
        if not proposta.titulo:
            raise ValueError("Título é obrigatório")
        if proposta.valor_total < 0:
            raise ValueError("Valor total não pode ser negativo")
        
        # Salvar
        db.session.commit()
        
        flash(f'Proposta {proposta.numero} atualizada com sucesso!', 'success')
        return redirect(url_for('proposta.listar_propostas'))
        
    except ValueError as e:
        flash(str(e), 'warning')
        clientes = Cliente.query.filter(Cliente.ativo == True).order_by(Cliente.nome).all()
        return render_template('proposta/cadastro.html', clientes=clientes, proposta=proposta)
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar proposta: {str(e)}', 'danger')
        return redirect(url_for('proposta.listar_propostas'))

@proposta_bp.route('/excluir/<int:proposta_id>', methods=['POST'])
def excluir_proposta(proposta_id):
    """Excluir proposta (soft delete)"""
    try:
        proposta = Proposta.query.get_or_404(proposta_id)
        proposta.soft_delete()
        db.session.commit()
        
        flash(f'Proposta {proposta.numero} excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir proposta: {str(e)}', 'danger')
    
    return redirect(url_for('proposta.listar_propostas'))

@proposta_bp.route('/api/buscar')
def api_buscar_propostas():
    """API para buscar propostas (autocomplete)"""
    try:
        termo = request.args.get('termo', '').strip()
        if len(termo) < 2:
            return jsonify([])
        
        # Buscar por número ou título
        propostas = Proposta.query.filter(
            Proposta.data_exclusao.is_(None),
            db.or_(
                Proposta.numero.ilike(f'%{termo}%'),
                Proposta.titulo.ilike(f'%{termo}%')
            )
        ).limit(10).all()
        
        resultados = []
        for proposta in propostas:
            resultados.append({
                'id': proposta.id,
                'numero': proposta.numero,
                'titulo': proposta.titulo,
                'cliente': proposta.cliente.nome if proposta.cliente else '',
                'valor_final': float(proposta.valor_final),
                'status': proposta.status
            })
        
        return jsonify(resultados)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500