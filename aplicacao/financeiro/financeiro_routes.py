
from flask import render_template, request, redirect, url_for, flash
from datetime import datetime, date
from decimal import Decimal
from aplicacao.extensoes import db
try:
    from aplicacao.app import csrf
except ImportError:
    csrf = None
from aplicacao.financeiro.financeiro_model import LancamentoFinanceiro
from .lancamento_os_model import LancamentoFinanceiroOS
from .indicadores_service import (
    carregar_registros_financeiros,
    decimal_valor,
    normalizar_status,
    normalizar_tipo,
    periodo_mes_atual,
    resumir_registros_financeiros,
    resumir_financeiro_periodo,
)
from . import financeiro_bp

@financeiro_bp.app_template_filter('moeda')
def moeda_br(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"

@financeiro_bp.route('/dashboard')
def dashboard():
    inicio_mes, fim_mes = periodo_mes_atual()
    resumo = resumir_financeiro_periodo(inicio_mes, fim_mes)

    receitas = resumo.receitas_realizadas
    despesas = resumo.despesas_realizadas
    saldo = resumo.resultado_realizado
    rec_dre = resumo.receitas_realizadas
    des_dre = resumo.despesas_realizadas
    lucro = resumo.resultado_realizado
    pe_reais = resumo.saldo_projetado
    base_hora = Decimal('50.00')
    valor_hora = base_hora + (lucro / Decimal('160')) if lucro > 0 else base_hora
    
    return render_template('financeiro/dashboard.html',
                         periodo=[inicio_mes, fim_mes],
                         receitas=receitas,
                         despesas=despesas,
                         saldo=saldo,
                         pe_reais=pe_reais,
                         rec_dre=rec_dre,
                         des_dre=des_dre,
                         lucro=lucro,
                         valor_hora=valor_hora,
                         base_hora=base_hora,
                         contas_a_receber_pendentes=resumo.contas_a_receber_pendentes,
                         contas_a_pagar_pendentes=resumo.contas_a_pagar_pendentes,
                         saldo_projetado=resumo.saldo_projetado,
                         lancamentos_pagos_sem_data_qtd=resumo.lancamentos_pagos_sem_data_qtd,
                         lancamentos_pagos_sem_data_valor=resumo.lancamentos_pagos_sem_data_valor)

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
    tipo = request.args.get('tipo')
    status = request.args.get('status')
    de = request.args.get('de')
    ate = request.args.get('ate')

    inicio_filtro = datetime.strptime(de, '%Y-%m-%d').date() if de else None
    fim_filtro = datetime.strptime(ate, '%Y-%m-%d').date() if ate else None

    registros = carregar_registros_financeiros(
        inicio_filtro,
        fim_filtro,
        tipo=tipo,
        status=status,
    )
    resumo_lista = resumir_registros_financeiros(registros)

    return render_template('financeiro/lista_financeiro.html',
                           registros=registros,
                           total_receitas=resumo_lista['total_receitas'],
                           total_despesas=resumo_lista['total_despesas'],
                           saldo=resumo_lista['saldo'],
                           total_os=resumo_lista['total_os'],
                           valor_os=resumo_lista['valor_os'],
                           contas_a_receber_pendentes=resumo_lista['contas_a_receber_pendentes'],
                           contas_a_pagar_pendentes=resumo_lista['contas_a_pagar_pendentes'],
                           inconsistencias_qtd=resumo_lista['inconsistencias_qtd'],
                           inconsistencias_valor=resumo_lista['inconsistencias_valor'],
                           filtros={'tipo': tipo, 'status': status, 'de': de, 'ate': ate})


@financeiro_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    if request.method == 'POST':
        dados = request.form
        try:
            lanc = LancamentoFinanceiro(
                tipo=normalizar_tipo(dados.get('tipo')),
                categoria=dados.get('categoria'),
                descricao=dados.get('descricao'),
                valor=float(decimal_valor(dados.get('valor') or 0)),
                data=datetime.strptime(dados.get('data'), '%Y-%m-%d').date() if dados.get('data') else datetime.utcnow().date(),
                data_pagamento=datetime.strptime(dados.get('data_pagamento'), '%Y-%m-%d').date() if dados.get('data_pagamento') else None,
                forma_pagamento=dados.get('forma_pagamento'),
                status=normalizar_status(dados.get('status') or 'Pendente'),
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
            lanc.tipo = normalizar_tipo(dados.get('tipo'))
            lanc.categoria = dados.get('categoria')
            lanc.descricao = dados.get('descricao')
            lanc.valor = float(decimal_valor(dados.get('valor') or 0))
            lanc.data = datetime.strptime(dados.get('data'), '%Y-%m-%d').date() if dados.get('data') else datetime.utcnow().date()
            lanc.data_pagamento = datetime.strptime(dados.get('data_pagamento'), '%Y-%m-%d').date() if dados.get('data_pagamento') else None
            lanc.forma_pagamento = dados.get('forma_pagamento')
            lanc.status = normalizar_status(dados.get('status') or 'Pendente')
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
        ordens_pagas = OrdemServico.query.filter(
            OrdemServico.status == 'Concluída'
        ).all()
        
        total_atualizados = 0
        
        for ordem in ordens_pagas:
            # Buscar lançamentos pendentes desta OS
            lancamentos_pendentes = LancamentoFinanceiroOS.query.filter(
                LancamentoFinanceiroOS.os_id == ordem.id,
                LancamentoFinanceiroOS.status.ilike('pend%')
            ).all()
            
            if lancamentos_pendentes:
                for lanc in lancamentos_pendentes:
                    if not lanc.data_pagamento:
                        flash(f'⚠️ Lançamento da OS {ordem.codigo} está sem data de pagamento e não pode ser baixado automaticamente.', 'warning')
                        continue
                    lanc.status = 'Pago'
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
        
        status_normalizado = normalizar_status(novo_status)
        data_pagamento_form = request.form.get('data_pagamento')

        if status_normalizado == 'Pago':
            if not data_pagamento_form:
                flash('⚠️ Para marcar como pago é obrigatório informar a data de pagamento.', 'warning')
                return redirect(url_for('financeiro.listar'))
            lanc_os.status = 'Pago'
            lanc_os.data_pagamento = datetime.strptime(data_pagamento_form, '%Y-%m-%d').date()
        elif status_normalizado == 'Pendente':
            lanc_os.status = 'Pendente'
            lanc_os.data_pagamento = None
        else:
            flash('⚠️ Status inválido.', 'warning')
            return redirect(url_for('financeiro.listar'))

        db.session.commit()
        flash(f'✅ Status do lançamento atualizado para {status_normalizado}!', 'success')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar status: {str(e)}', 'danger')
    
    return redirect(url_for('financeiro.listar'))

