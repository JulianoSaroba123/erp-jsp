# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Routes de Colaborador
=====================================

Rotas para gerenciamento de colaboradores/técnicos.
CRUD completo com controle de horas trabalhadas.

Autor: JSP Soluções
Data: 2025
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from datetime import datetime, date
from app.extensoes import db
from app.colaborador.colaborador_model import Colaborador, OrdemServicoColaborador

# Cria o blueprint
colaborador_bp = Blueprint('colaborador', __name__, template_folder='templates')

# Handler de erros
@colaborador_bp.errorhandler(404)
def colaborador_nao_encontrado(e):
    """Handler para erro 404 no módulo de colaboradores."""
    flash('Colaborador não encontrado.', 'error')
    return redirect(url_for('colaborador.listar'))

@colaborador_bp.errorhandler(500)
def erro_interno_colaborador(e):
    """Handler para erro 500 no módulo de colaboradores."""
    import traceback
    print(f"❌ Erro 500 no módulo colaborador:")
    print(traceback.format_exc())
    flash(f'Erro interno ao processar colaborador: {str(e)}', 'error')
    return redirect(url_for('colaborador.listar'))

@colaborador_bp.route('/')
@colaborador_bp.route('/listar')
def listar():
    """Lista todos os colaboradores ativos."""
    busca = request.args.get('busca', '').strip()
    
    if busca:
        colaboradores = Colaborador.query.filter(
            db.or_(
                Colaborador.nome.ilike(f'%{busca}%'),
                Colaborador.cpf.ilike(f'%{busca}%'),
                Colaborador.cargo.ilike(f'%{busca}%')
            ),
            Colaborador.ativo == True,
            db.or_(
                Colaborador.data_demissao.is_(None),
                Colaborador.data_demissao > date.today()
            )
        ).order_by(Colaborador.nome).all()
    else:
        colaboradores = Colaborador.query.filter(
            Colaborador.ativo == True,
            db.or_(
                Colaborador.data_demissao.is_(None),
                Colaborador.data_demissao > date.today()
            )
        ).order_by(Colaborador.nome).all()
    
    return render_template('colaborador/listar.html', colaboradores=colaboradores, busca=busca)

@colaborador_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    """Cria um novo colaborador."""
    if request.method == 'POST':
        try:
            # Validar se CPF já existe (se fornecido)
            cpf = request.form.get('cpf', '').strip()
            if cpf:
                colaborador_existente = Colaborador.query.filter(
                    Colaborador.cpf == cpf
                ).first()
                
                if colaborador_existente:
                    if not colaborador_existente.ativo or (
                        colaborador_existente.data_demissao and 
                        colaborador_existente.data_demissao <= date.today()
                    ):
                        # Colaborador inativo - reativar
                        flash(f'Colaborador {colaborador_existente.nome} com CPF {cpf} existe mas está inativo. Reativando...', 'info')
                        
                        colaborador_existente.ativo = True
                        colaborador_existente.data_demissao = None
                        colaborador_existente.nome = request.form.get('nome') or colaborador_existente.nome
                        colaborador_existente.cargo = request.form.get('cargo') or colaborador_existente.cargo
                        colaborador_existente.telefone = request.form.get('telefone') or colaborador_existente.telefone
                        colaborador_existente.celular = request.form.get('celular') or colaborador_existente.celular
                        colaborador_existente.email = request.form.get('email') or colaborador_existente.email
                        
                        db.session.commit()
                        flash(f'Colaborador {colaborador_existente.nome} reativado com sucesso!', 'success')
                        return redirect(url_for('colaborador.listar'))
                    else:
                        # Colaborador ativo - erro
                        flash(f'CPF {cpf} já está cadastrado no colaborador: {colaborador_existente.nome}', 'error')
                        return render_template('colaborador/form.html', colaborador=Colaborador())
            
            # Validar nome obrigatório
            nome = request.form.get('nome', '').strip()
            if not nome:
                flash('Nome é obrigatório!', 'error')
                return render_template('colaborador/form.html', colaborador=Colaborador())
            
            # Criar novo colaborador
            colaborador = Colaborador(
                nome=nome,
                cpf=cpf if cpf else None,
                telefone=request.form.get('telefone'),
                celular=request.form.get('celular'),
                email=request.form.get('email'),
                cargo=request.form.get('cargo', 'tecnico'),
                especialidade=request.form.get('especialidade'),
                data_admissao=datetime.strptime(request.form.get('data_admissao'), '%Y-%m-%d').date() 
                    if request.form.get('data_admissao') else None,
                valor_hora=float(request.form.get('valor_hora', 0) or 0),
                salario_mensal=float(request.form.get('salario_mensal', 0) or 0),
                observacoes=request.form.get('observacoes'),
                ativo=True
            )
            
            db.session.add(colaborador)
            db.session.commit()
            
            flash(f'Colaborador {colaborador.nome} cadastrado com sucesso!', 'success')
            return redirect(url_for('colaborador.listar'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar colaborador: {str(e)}', 'error')
            import traceback
            print(traceback.format_exc())
            return render_template('colaborador/form.html', colaborador=Colaborador())
    
    # GET - mostrar formulário vazio
    return render_template('colaborador/form.html', colaborador=None)

@colaborador_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    """Edita um colaborador existente."""
    colaborador = Colaborador.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Validar CPF duplicado (exceto o próprio colaborador)
            cpf = request.form.get('cpf', '').strip()
            if cpf and cpf != colaborador.cpf:
                cpf_duplicado = Colaborador.query.filter(
                    Colaborador.cpf == cpf,
                    Colaborador.id != id,
                    Colaborador.ativo == True
                ).first()
                
                if cpf_duplicado:
                    flash(f'CPF {cpf} já está cadastrado no colaborador: {cpf_duplicado.nome}', 'error')
                    return render_template('colaborador/form.html', colaborador=colaborador)
            
            # Validar nome
            nome = request.form.get('nome', '').strip()
            if not nome:
                flash('Nome é obrigatório!', 'error')
                return render_template('colaborador/form.html', colaborador=colaborador)
            
            # Atualizar dados
            colaborador.nome = nome
            colaborador.cpf = cpf if cpf else None
            colaborador.telefone = request.form.get('telefone')
            colaborador.celular = request.form.get('celular')
            colaborador.email = request.form.get('email')
            colaborador.cargo = request.form.get('cargo', 'tecnico')
            colaborador.especialidade = request.form.get('especialidade')
            colaborador.valor_hora = float(request.form.get('valor_hora', 0) or 0)
            colaborador.salario_mensal = float(request.form.get('salario_mensal', 0) or 0)
            colaborador.observacoes = request.form.get('observacoes')
            
            # Datas
            if request.form.get('data_admissao'):
                colaborador.data_admissao = datetime.strptime(request.form.get('data_admissao'), '%Y-%m-%d').date()
            
            if request.form.get('data_demissao'):
                colaborador.data_demissao = datetime.strptime(request.form.get('data_demissao'), '%Y-%m-%d').date()
            
            db.session.commit()
            
            flash(f'Colaborador {colaborador.nome} atualizado com sucesso!', 'success')
            return redirect(url_for('colaborador.listar'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar colaborador: {str(e)}', 'error')
            import traceback
            print(traceback.format_exc())
    
    # GET - mostrar formulário preenchido
    return render_template('colaborador/form.html', colaborador=colaborador)

@colaborador_bp.route('/excluir/<int:id>', methods=['POST'])
def excluir(id):
    """Exclui (desativa) um colaborador."""
    try:
        colaborador = Colaborador.query.get_or_404(id)
        
        # Soft delete - apenas desativa
        colaborador.ativo = False
        colaborador.data_demissao = date.today()
        
        db.session.commit()
        
        flash(f'Colaborador {colaborador.nome} removido com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao remover colaborador: {str(e)}', 'error')
        import traceback
        print(traceback.format_exc())
    
    return redirect(url_for('colaborador.listar'))

@colaborador_bp.route('/visualizar/<int:id>')
def visualizar(id):
    """Visualiza detalhes de um colaborador."""
    colaborador = Colaborador.query.get_or_404(id)
    
    # Buscar histórico de trabalhos (OSs)
    trabalhos = OrdemServicoColaborador.query.filter_by(
        colaborador_id=id,
        ativo=True
    ).order_by(OrdemServicoColaborador.data_trabalho.desc()).all()
    
    return render_template('colaborador/visualizar.html', 
                         colaborador=colaborador, 
                         trabalhos=trabalhos)

# === APIs JSON ===

@colaborador_bp.route('/api/buscar_ativos')
def api_buscar_ativos():
    """API: Retorna lista de colaboradores ativos para autocomplete."""
    try:
        colaboradores = Colaborador.buscar_ativos()
        
        resultado = [{
            'id': c.id,
            'nome': c.nome,
            'cargo': c.cargo_formatado,
            'valor_hora': float(c.valor_hora or 0)
        } for c in colaboradores]
        
        return jsonify({'sucesso': True, 'colaboradores': resultado})
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 500

@colaborador_bp.route('/api/dados/<int:id>')
def api_dados(id):
    """API: Retorna dados de um colaborador específico."""
    try:
        colaborador = Colaborador.query.get_or_404(id)
        
        dados = {
            'id': colaborador.id,
            'nome': colaborador.nome,
            'cpf': colaborador.cpf,
            'cargo': colaborador.cargo_formatado,
            'telefone': colaborador.celular or colaborador.telefone,
            'email': colaborador.email,
            'valor_hora': float(colaborador.valor_hora or 0),
            'total_horas': colaborador.total_horas_trabalhadas,
            'total_os': colaborador.total_os_trabalhadas
        }
        
        return jsonify({'sucesso': True, 'colaborador': dados})
    except Exception as e:
        return jsonify({'sucesso': False, 'erro': str(e)}), 404


@colaborador_bp.route('/relatorio-pagamento/<int:id>')
def relatorio_pagamento(id):
    """
    Gera relatório de pagamento individual do colaborador (PDF/impressão).
    Mostra todas as OSs trabalhadas, horas por dia e valor a receber.
    Aceita parâmetros: ?mes=MM&ano=AAAA para filtrar por período.
    Admin only.
    """
    from flask_login import current_user
    from flask import make_response
    from datetime import datetime as dt
    from app.configuracao.configuracao_utils import get_config

    if current_user.tipo_usuario != 'admin':
        flash('Acesso restrito ao administrador.', 'error')
        return redirect(url_for('colaborador.listar'))

    colaborador = Colaborador.query.get_or_404(id)

    # Filtro de período (padrão: mês atual)
    hoje = dt.today()
    try:
        mes = int(request.args.get('mes', hoje.month))
        ano = int(request.args.get('ano', hoje.year))
    except (ValueError, TypeError):
        mes, ano = hoje.month, hoje.year

    # Busca todos os registros de trabalho do colaborador no período
    from app.colaborador.colaborador_model import OrdemServicoColaborador
    trabalhos = (
        OrdemServicoColaborador.query
        .filter_by(colaborador_id=colaborador.id, ativo=True)
        .join(OrdemServicoColaborador.ordem_servico)
        .filter(
            db.extract('month', OrdemServicoColaborador.data_trabalho) == mes,
            db.extract('year', OrdemServicoColaborador.data_trabalho) == ano
        )
        .order_by(OrdemServicoColaborador.data_trabalho.asc())
        .all()
    )

    # Totais
    total_horas = sum(float(t.total_horas or 0) for t in trabalhos)
    salario = float(colaborador.salario_mensal or 0)
    custo_hora = salario / 220.0 if salario > 0 else 0.0
    valor_a_receber = total_horas * custo_hora

    config = get_config()

    # Meses em português
    MESES = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
             'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

    html_content = render_template(
        'colaborador/pdf_pagamento.html',
        colaborador=colaborador,
        trabalhos=trabalhos,
        total_horas=total_horas,
        salario=salario,
        custo_hora=custo_hora,
        valor_a_receber=valor_a_receber,
        mes=mes,
        ano=ano,
        mes_nome=MESES[mes],
        config=config,
        now=dt,
    )

    # Auto-print
    script = '<script>window.onload = function(){ window.print(); };</script>'
    if '</body>' in html_content:
        html_content = html_content.replace('</body>', f'{script}</body>')
    else:
        html_content += script

    response = make_response(html_content)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Content-Disposition'] = (
        f'inline; filename="Pagamento_{colaborador.nome.replace(" ", "_")}_{MESES[mes]}_{ano}.pdf"'
    )
    return response


# === ROTA DE SEGURANÇA: captura qualquer URL inválida no blueprint ===
@colaborador_bp.route('/<path:qualquer_coisa>')
def rota_invalida(qualquer_coisa):
    """Redireciona qualquer URL não reconhecida para a lista de colaboradores."""
    flash('Página de colaborador não encontrada. Redirecionado para a lista.', 'warning')
    return redirect(url_for('colaborador.listar'))
