
from flask import render_template, request, redirect, url_for, flash
from datetime import datetime, date, timedelta
from aplicacao.extensoes import db
try:
    from aplicacao.app import csrf
except ImportError:
    csrf = None
from aplicacao.financeiro.financeiro_model import LancamentoFinanceiro
from .lancamento_os_model import LancamentoFinanceiroOS
from . import financeiro_bp

@financeiro_bp.app_template_filter('moeda')
def moeda_br(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"

@financeiro_bp.route('/dashboard')
def dashboard():
    # Período padrão: mês atual
    hoje = date.today()
    inicio_mes = hoje.replace(day=1)
    fim_mes = (inicio_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Buscar lançamentos do período - Modelo tradicional
    lancamentos = LancamentoFinanceiro.query.filter(
        LancamentoFinanceiro.data >= inicio_mes,
        LancamentoFinanceiro.data <= fim_mes
    ).all()
    
    # Buscar lançamentos de OS do período
    lancamentos_os = LancamentoFinanceiroOS.query.filter(
        LancamentoFinanceiroOS.data_vencimento >= inicio_mes,
        LancamentoFinanceiroOS.data_vencimento <= fim_mes
    ).all()
    
    # Calcular totais - Lançamentos tradicionais
    receitas = sum(x.valor for x in lancamentos if x.is_receita())
    despesas = sum(x.valor for x in lancamentos if x.is_despesa())
    
    # Calcular totais - Lançamentos de OS (sempre receitas)
    receitas_os = sum(float(x.valor) for x in lancamentos_os)
    
    # Total geral
    receitas_total = receitas + receitas_os
    saldo = receitas_total - despesas
    
    # Valores para DRE (simplificado)
    rec_dre = receitas_total
    des_dre = despesas
    lucro = rec_dre - des_dre
    
    # Valores fictícios para demonstração
    pe_reais = saldo * 0.1  # 10% do saldo como exemplo
    base_hora = 50.0  # valor base por hora
    valor_hora = base_hora + (lucro / 160) if lucro > 0 else base_hora  # 160h/mês
    
    return render_template('financeiro/dashboard.html',
                         periodo=[inicio_mes, fim_mes],
                         receitas=receitas_total,
                         despesas=despesas,
                         saldo=saldo,
                         pe_reais=pe_reais,
                         rec_dre=rec_dre,
                         des_dre=des_dre,
                         lucro=lucro,
                         valor_hora=valor_hora,
                         base_hora=base_hora)

class RegistroUnificado:
    """Classe para unificar lançamentos de diferentes modelos"""
    def __init__(self, dados):
        for key, value in dados.items():
            setattr(self, key, value)

def criar_registro_unificado(lancamento, tipo_origem='tradicional'):
    """Converte lançamentos de diferentes modelos para um formato unificado"""
    if tipo_origem == 'tradicional':
        dados = {
            'id': lancamento.id,
            'tipo': lancamento.tipo,
            'categoria': lancamento.categoria,
            'descricao': lancamento.descricao,
            'valor': float(lancamento.valor),
            'data': lancamento.data,
            'forma_pagamento': lancamento.forma_pagamento,
            'status': lancamento.status,
            'observacoes': getattr(lancamento, 'observacoes', ''),
            'origem': 'tradicional',
            'os_id': None,
            'parcela': None,
            'total_parcelas': None,
        }
        registro = RegistroUnificado(dados)
        registro.is_receita = lambda: lancamento.is_receita()
        registro.is_despesa = lambda: lancamento.is_despesa()
        return registro
    else:  # OS
        dados = {
            'id': lancamento.id,
            'tipo': 'Receita',  # OS sempre gera receitas
            'categoria': 'Serviços',
            'descricao': f"OS #{lancamento.os_id}: {lancamento.descricao}",
            'valor': float(lancamento.valor),
            'data': lancamento.data_vencimento,
            'forma_pagamento': lancamento.forma_pagamento,
            'status': lancamento.status,
            'observacoes': f"Parcela {lancamento.parcela}/{lancamento.total_parcelas}" if lancamento.parcela else "Entrada",
            'origem': 'OS',
            'os_id': lancamento.os_id,
            'parcela': lancamento.parcela,
            'total_parcelas': lancamento.total_parcelas,
        }
        registro = RegistroUnificado(dados)
        registro.is_receita = lambda: True
        registro.is_despesa = lambda: False
        return registro

@financeiro_bp.route('/')
def listar():
    tipo = request.args.get('tipo')      # Receita/Despesa/None
    status = request.args.get('status')  # Pago/Pendente/Atrasado/None
    de = request.args.get('de')          # YYYY-MM-DD
    ate = request.args.get('ate')        # YYYY-MM-DD

    # Query lançamentos tradicionais
    q = LancamentoFinanceiro.query
    if tipo: q = q.filter(LancamentoFinanceiro.tipo == tipo)
    if status: q = q.filter(LancamentoFinanceiro.status == status)
    if de: q = q.filter(LancamentoFinanceiro.data >= de)
    if ate: q = q.filter(LancamentoFinanceiro.data <= ate)
    lancamentos_tradicionais = q.all()

    # Para agora, vamos mostrar AMBOS: tradicionais + OS
    registros = list(lancamentos_tradicionais)
    
    # Buscar lançamentos de OS e adicionar à lista
    q_os = LancamentoFinanceiroOS.query
    if status: q_os = q_os.filter(LancamentoFinanceiroOS.status == status)
    if de: q_os = q_os.filter(LancamentoFinanceiroOS.data_vencimento >= de)
    if ate: q_os = q_os.filter(LancamentoFinanceiroOS.data_vencimento <= ate)
    
    lancamentos_os = q_os.all() if tipo != 'Despesa' else []
    
    # ADICIONAR lançamentos de OS à lista principal
    registros.extend(lancamentos_os)
    
    # Calcular totais incluindo OS
    total_receitas_trad = sum(float(x.valor) for x in lancamentos_tradicionais if x.is_receita())
    total_despesas_trad = sum(float(x.valor) for x in lancamentos_tradicionais if x.is_despesa())
    total_receitas_os = sum(float(x.valor) for x in lancamentos_os)
    
    total_receitas = total_receitas_trad + total_receitas_os
    total_despesas = total_despesas_trad
    saldo = total_receitas - total_despesas

    # Ordenar registros (tradicionais + OS) por data
    def get_sort_date(record):
        if hasattr(record, 'data_vencimento'):  # LancamentoFinanceiroOS
            return record.data_vencimento
        else:  # LancamentoFinanceiro tradicional
            return record.data
    
    registros.sort(key=get_sort_date, reverse=True)

    return render_template('financeiro/lista_financeiro.html',
                           registros=registros,
                           total_receitas=total_receitas,
                           total_despesas=total_despesas,
                           saldo=saldo,
                           total_os=len(lancamentos_os),
                           valor_os=total_receitas_os,
                           filtros={'tipo': tipo, 'status': status, 'de': de, 'ate': ate})


@financeiro_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    if request.method == 'POST':
        dados = request.form
        try:
            lanc = LancamentoFinanceiro(
                tipo=dados.get('tipo'),
                categoria=dados.get('categoria'),
                descricao=dados.get('descricao'),
                valor=float(dados.get('valor') or 0),
                data=datetime.strptime(dados.get('data'), '%Y-%m-%d').date() if dados.get('data') else datetime.utcnow().date(),
                forma_pagamento=dados.get('forma_pagamento'),
                status=dados.get('status') or 'Pendente',
                observacoes=dados.get('observacoes')
            )
            db.session.add(lanc)
            db.session.commit()
            flash('Lançamento salvo!', 'success')
            return redirect(url_for('financeiro.listar'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar: {e}', 'danger')
    return render_template('financeiro/cadastro_financeiro.html', lanc=None)


@financeiro_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    lanc = LancamentoFinanceiro.query.get_or_404(id)
    if request.method == 'POST':
        dados = request.form
        try:
            lanc.tipo = dados.get('tipo')
            lanc.categoria = dados.get('categoria')
            lanc.descricao = dados.get('descricao')
            lanc.valor = float(dados.get('valor') or 0)
            lanc.data = datetime.strptime(dados.get('data'), '%Y-%m-%d').date() if dados.get('data') else datetime.utcnow().date()
            lanc.forma_pagamento = dados.get('forma_pagamento')
            lanc.status = dados.get('status') or 'Pendente'
            lanc.observacoes = dados.get('observacoes')
            db.session.commit()
            flash('Lançamento atualizado!', 'success')
            return redirect(url_for('financeiro.listar'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar: {e}', 'danger')
    return render_template('financeiro/cadastro_financeiro.html', lanc=lanc)

@financeiro_bp.route('/excluir/<int:id>', methods=['POST'])
def excluir(id):
    lanc = LancamentoFinanceiro.query.get_or_404(id)
    db.session.delete(lanc)
    db.session.commit()
    flash('Lançamento excluído!', 'success')
    return redirect(url_for('financeiro.listar'))

@financeiro_bp.route('/excluir-os/<int:id>', methods=['POST'])
def excluir_os(id):
    """Excluir lançamento financeiro de Ordem de Serviço"""
    lanc_os = LancamentoFinanceiroOS.query.get_or_404(id)
    
    # Verificar se pode excluir (adicionar validações se necessário)
    os_numero = f"OS{lanc_os.os_id:04d}" if lanc_os.os_id else "N/A"
    
    try:
        db.session.delete(lanc_os)
        db.session.commit()
        flash(f'Lançamento da {os_numero} excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir lançamento: {str(e)}', 'danger')
    
    return redirect(url_for('financeiro.listar'))

@financeiro_bp.route('/atualizar-status-os', methods=['POST'])
def atualizar_status_os():
    """Atualizar status dos lançamentos de OS baseado no status da ordem"""
    try:
        from aplicacao.ordem_servico.os_model import OrdemServico
        
        # Buscar todas as OS pagas mas com lançamentos pendentes
        ordens_pagas = OrdemServico.query.filter_by(
            status='Concluída', 
            status_pagamento='Pago'
        ).all()
        
        total_atualizados = 0
        
        for ordem in ordens_pagas:
            # Buscar lançamentos pendentes desta OS
            lancamentos_pendentes = LancamentoFinanceiroOS.query.filter(
                LancamentoFinanceiroOS.os_id == ordem.id,
                LancamentoFinanceiroOS.status == 'Pendente'
            ).all()
            
            if lancamentos_pendentes:
                for lanc in lancamentos_pendentes:
                    lanc.status = 'Pago'
                    lanc.data_pagamento = ordem.data_conclusao or db.func.current_date()
                    total_atualizados += 1
        
        if total_atualizados > 0:
            db.session.commit()
            flash(f'✅ {total_atualizados} lançamento(s) atualizado(s) para PAGO!', 'success')
        else:
            flash('ℹ️ Todos os lançamentos já estão com status correto.', 'info')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar status: {str(e)}', 'danger')
    
    return redirect(url_for('financeiro.listar'))

@financeiro_bp.route('/editar-status-os/<int:id>', methods=['POST'])
def editar_status_os(id):
    """Editar status específico de um lançamento de OS"""
    try:
        lanc_os = LancamentoFinanceiroOS.query.get_or_404(id)
        novo_status = request.form.get('status')
        
        if novo_status in ['Pago', 'Pendente']:
            lanc_os.status = novo_status
            
            if novo_status == 'Pago':
                from datetime import date
                lanc_os.data_pagamento = date.today()
            else:
                lanc_os.data_pagamento = None
                
            db.session.commit()
            flash(f'✅ Status do lançamento atualizado para {novo_status}!', 'success')
        else:
            flash('⚠️ Status inválido.', 'warning')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar status: {str(e)}', 'danger')
    
    return redirect(url_for('financeiro.listar'))

