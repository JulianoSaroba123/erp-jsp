# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Utilitários Financeiros
======================================

Funções auxiliares para integração financeira com ordens de serviço.
Inclui geração automática de lançamentos e cálculos de dashboard.

Autor: JSP Soluções
Data: 2025
"""

from datetime import datetime, date
from decimal import Decimal
import logging
from app.extensoes import db
from app.financeiro.financeiro_model import LancamentoFinanceiro
from sqlalchemy import func


logger = logging.getLogger(__name__)


def _status_financeiro_por_os(ordem_servico):
    """Mapeia status da OS para status financeiro."""
    return 'pendente' if ordem_servico.status != 'concluida' else 'recebido'


def _numero_parcela_exibicao(parcela, total_parcelas):
    """Monta string de exibição da parcela (não usada como identidade)."""
    if not parcela:
        return None
    total = total_parcelas if total_parcelas > 0 else 1
    return f'{parcela.numero_parcela}/{total}'


def _atualizar_lancamento_os(lancamento, ordem_servico, forma_pagamento=None, parcela=None, total_parcelas=0):
    """Aplica atualização segura em lançamento de OS preservando quitados."""
    if forma_pagamento is not None:
        lancamento.forma_pagamento = forma_pagamento

    if lancamento.status in {'pago', 'recebido'}:
        # Preserva lançamentos quitados mesmo com edição de OS.
        return

    status_financeiro = _status_financeiro_por_os(ordem_servico)
    numero_parcela = _numero_parcela_exibicao(parcela, total_parcelas)

    if parcela is not None:
        descricao = f"OS {ordem_servico.numero} - {ordem_servico.titulo} - Parcela {parcela.numero_parcela}"
        valor = Decimal(str(parcela.valor or 0)).quantize(Decimal('0.01'))
        data_vencimento = parcela.data_vencimento
        ordem_servico_parcela_id = parcela.id
    else:
        descricao = f"OS {ordem_servico.numero} - {ordem_servico.titulo}"
        valor = Decimal(str(ordem_servico.valor_total or 0)).quantize(Decimal('0.01'))
        data_vencimento = ordem_servico.data_prevista
        ordem_servico_parcela_id = None

    lancamento.descricao = descricao
    lancamento.valor = valor
    lancamento.tipo = 'conta_receber'
    if lancamento.status not in {'pago', 'recebido'}:
        lancamento.status = status_financeiro
    lancamento.categoria = 'Serviços'
    lancamento.subcategoria = 'Ordem de Serviço'
    lancamento.data_lancamento = ordem_servico.data_abertura
    lancamento.data_vencimento = data_vencimento
    lancamento.cliente_id = ordem_servico.cliente_id
    lancamento.ordem_servico_id = ordem_servico.id
    lancamento.ordem_servico_parcela_id = ordem_servico_parcela_id
    lancamento.numero_parcela = numero_parcela
    lancamento.observacoes = f"Lançamento automático da {ordem_servico.numero}"
    lancamento.origem = 'ORDEM_SERVICO'

    if status_financeiro == 'recebido' and lancamento.data_pagamento is None:
        lancamento.data_pagamento = ordem_servico.data_conclusao or date.today()


def gerar_lancamento_ordem_servico(ordem_servico, forma_pagamento=None):
    """
    Gera lançamento financeiro automático para ordem de serviço.
    
    Args:
        ordem_servico: Instância da OrdemServico
        
    Returns:
        list[LancamentoFinanceiro]: Lançamentos criados/atualizados
    """
    try:
        total_os = Decimal(str(ordem_servico.valor_total or 0))
        if total_os <= 0:
            return []

        parcelas = sorted(list(getattr(ordem_servico, 'parcelas', []) or []), key=lambda p: p.numero_parcela)
        lancamentos_processados = []

        if parcelas:
            total_parcelas = len(parcelas)
            parcela_ids = [parcela.id for parcela in parcelas]
            existentes = LancamentoFinanceiro.query.filter(
                LancamentoFinanceiro.ordem_servico_parcela_id.in_(parcela_ids)
            ).all()
            existentes_por_parcela = {
                lancamento.ordem_servico_parcela_id: lancamento
                for lancamento in existentes
            }
            for parcela in parcelas:
                lancamento = existentes_por_parcela.get(parcela.id)

                if not lancamento:
                    lancamento = LancamentoFinanceiro(
                        origem='ORDEM_SERVICO',
                        ordem_servico_id=ordem_servico.id,
                        ordem_servico_parcela_id=parcela.id,
                    )
                    db.session.add(lancamento)

                _atualizar_lancamento_os(lancamento, ordem_servico, forma_pagamento=forma_pagamento, parcela=parcela, total_parcelas=total_parcelas)
                lancamentos_processados.append(lancamento)
        else:
            # OS sem parcelas: mantém comportamento de lançamento único por OS.
            lancamento = LancamentoFinanceiro.query.filter_by(
                ordem_servico_id=ordem_servico.id,
                ordem_servico_parcela_id=None,
            ).first()

            if not lancamento:
                lancamento = LancamentoFinanceiro(
                    origem='ORDEM_SERVICO',
                    ordem_servico_id=ordem_servico.id,
                )
                db.session.add(lancamento)

            _atualizar_lancamento_os(lancamento, ordem_servico, forma_pagamento=forma_pagamento)
            lancamentos_processados.append(lancamento)

        db.session.commit()

        print(f" Lançamentos processados para OS {ordem_servico.numero}: {len(lancamentos_processados)}")
        return lancamentos_processados
            
    except Exception as e:
        db.session.rollback()
        logger.exception("Erro ao gerar lancamento para OS %s", ordem_servico.numero)
        
    return []


def atualizar_status_financeiro_ordem(ordem_servico):
    """
    Atualiza status financeiro quando ordem de serviço muda status.
    
    Args:
        ordem_servico: Instância da OrdemServico
    """
    try:
        lancamentos = LancamentoFinanceiro.query.filter_by(
            ordem_servico_id=ordem_servico.id,
            ativo=True
        ).all()

        if lancamentos:
            status_map = {
                'concluida': 'recebido',
                'cancelada': 'cancelado',
                'pendente': 'pendente',
                'em_execucao': 'pendente',
                'em_andamento': 'pendente'
            }
            novo_status = status_map.get(ordem_servico.status, 'pendente')

            alterou = False
            for lancamento in lancamentos:
                if lancamento.status in {'pago', 'recebido'} and lancamento.data_pagamento is not None:
                    continue

                if lancamento.status != novo_status:
                    lancamento.status = novo_status
                    if novo_status == 'recebido' and lancamento.data_pagamento is None:
                        lancamento.data_pagamento = ordem_servico.data_conclusao or date.today()
                    alterou = True

            if alterou:
                db.session.commit()
                print(f" Status financeiro atualizado para OS {ordem_servico.numero}: {novo_status}")
                
    except Exception as e:
        print(f" Erro ao atualizar status financeiro da OS {ordem_servico.numero}: {e}")
        db.session.rollback()


def calcular_metricas_dashboard():
    """
    Calcula métricas financeiras para o dashboard.
    USA SQL PURO para evitar incompatibilidade psycopg3 + SQLAlchemy com VARCHAR.
    """
    try:
        from sqlalchemy import text

        hoje = date.today()
        primeiro_dia_mes = date(hoje.year, hoje.month, 1)
        if hoje.month == 12:
            ultimo_dia_mes = date(hoje.year + 1, 1, 1)
        else:
            ultimo_dia_mes = date(hoje.year, hoje.month + 1, 1)

        # === ORDENS DE SERVIÇO (SQL puro) ===
        r = db.session.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE ativo = true) AS total_ordens,
                COUNT(*) FILTER (WHERE ativo = true AND status IN ('aberta','pendente','iniciada','em_andamento')) AS ordens_abertas,
                COUNT(*) FILTER (WHERE ativo = true AND status = 'concluida') AS ordens_concluidas,
                COALESCE(SUM(valor_total) FILTER (WHERE ativo = true), 0) AS valor_total_ordens,
                COALESCE(SUM(valor_total) FILTER (WHERE ativo = true AND status = 'concluida'), 0) AS valor_ordens_concluidas,
                COALESCE(SUM(valor_total) FILTER (WHERE ativo = true AND status IN ('aberta','pendente','iniciada','em_andamento')), 0) AS valor_ordens_abertas,
                COALESCE(SUM(valor_total) FILTER (WHERE ativo = true AND status = 'concluida' AND data_conclusao >= :p1 AND data_conclusao < :p2), 0) AS receita_mes,
                COUNT(*) FILTER (WHERE ativo = true AND status = 'concluida' AND data_conclusao >= :p1 AND data_conclusao < :p2) AS qtd_ordens_mes
            FROM ordem_servico
        """), {"p1": primeiro_dia_mes, "p2": ultimo_dia_mes}).first()

        total_ordens = int(r[0] or 0)
        ordens_abertas = int(r[1] or 0)
        valor_ordens_concluidas = float(r[4] or 0)
        valor_ordens_abertas = float(r[5] or 0)
        receita_mes = float(r[6] or 0)
        qtd_ordens_mes = int(r[7] or 0)

        # === LANÇAMENTOS FINANCEIROS (SQL puro) ===
        rf = db.session.execute(text("""
            SELECT
                COALESCE(SUM(valor) FILTER (WHERE ativo = true AND tipo IN ('receita','conta_receber') AND status = 'recebido' AND data_pagamento >= :p1 AND data_pagamento < :p2), 0) AS receitas_mes,
                COALESCE(SUM(valor) FILTER (WHERE ativo = true AND tipo IN ('despesa','conta_pagar') AND status = 'pago' AND data_pagamento >= :p1 AND data_pagamento < :p2), 0) AS despesas_mes,
                COALESCE(SUM(valor) FILTER (WHERE ativo = true AND tipo = 'conta_receber' AND status = 'pendente'), 0) AS contas_receber,
                COUNT(*) FILTER (WHERE ativo = true AND tipo = 'conta_receber' AND status = 'pendente') AS qtd_receber,
                COALESCE(SUM(valor) FILTER (WHERE ativo = true AND tipo = 'conta_pagar' AND status = 'pendente'), 0) AS contas_pagar,
                COUNT(*) FILTER (WHERE ativo = true AND tipo = 'conta_pagar' AND status = 'pendente') AS qtd_pagar
            FROM lancamentos_financeiros
        """), {"p1": primeiro_dia_mes, "p2": ultimo_dia_mes}).first()

        total_receitas_mes = float(rf[0] or 0)
        total_despesas_mes = float(rf[1] or 0)
        total_contas_receber = float(rf[2] or 0)
        qtd_contas_receber = int(rf[3] or 0)
        total_contas_pagar = float(rf[4] or 0)
        qtd_contas_pagar = int(rf[5] or 0)
        saldo_mes = total_receitas_mes - total_despesas_mes

        return {
            'total_ordens': total_ordens,
            'ordens_abertas': ordens_abertas,
            'ordens_concluidas': ordens_concluidas,
            'valor_total_ordens': valor_total_ordens,
            'valor_ordens_concluidas': valor_ordens_concluidas,
            'valor_ordens_abertas': valor_ordens_abertas,
            'receita_mes': receita_mes,
            'qtd_ordens_mes': qtd_ordens_mes,
            'total_receitas_mes': total_receitas_mes,
            'total_despesas_mes': total_despesas_mes,
            'saldo_mes': saldo_mes,
            'total_contas_receber': total_contas_receber,
            'total_contas_pagar': total_contas_pagar,
            'qtd_contas_receber': qtd_contas_receber,
            'qtd_contas_pagar': qtd_contas_pagar,
            'fluxo_caixa': valor_ordens_concluidas + total_contas_receber - total_contas_pagar
        }

    except Exception as e:
        print(f" Erro ao calcular métricas do dashboard: {e}")
        return {
            'total_ordens': 0, 'ordens_abertas': 0, 'ordens_concluidas': 0,
            'valor_total_ordens': 0, 'valor_ordens_concluidas': 0, 'valor_ordens_abertas': 0,
            'receita_mes': 0, 'qtd_ordens_mes': 0,
            'total_receitas_mes': 0, 'total_despesas_mes': 0, 'saldo_mes': 0,
            'total_contas_receber': 0, 'total_contas_pagar': 0,
            'qtd_contas_receber': 0, 'qtd_contas_pagar': 0,
            'fluxo_caixa': 0
        }


def formatar_valor_real(valor):
    """
    Formata valor numérico para moeda brasileira.
    
    Args:
        valor: Valor numérico
        
    Returns:
        str: Valor formatado (ex: "R$ 1.234,56")
    """
    if valor is None or valor == 0:
        return "R$ 0,00"
    
    try:
        valor_float = float(valor)
        return f"R$ {valor_float:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return "R$ 0,00"


def cancelar_lancamento_ordem_servico(ordem_servico):
    """
    Remove ou cancela lançamento financeiro de uma ordem de serviço excluída.
    
    Args:
        ordem_servico: Instância da OrdemServico
    """
    try:
        lancamentos = LancamentoFinanceiro.query.filter_by(
            ordem_servico_id=ordem_servico.id
        ).all()

        if lancamentos:
            for lancamento in lancamentos:
                db.session.delete(lancamento)
            db.session.commit()
            print(f"💰 Lançamentos financeiros removidos para OS {ordem_servico.numero}: {len(lancamentos)}")
        else:
            print(f"💰 Nenhum lançamento financeiro encontrado para OS {ordem_servico.numero}")
            
    except Exception as e:
        print(f" Erro ao cancelar lançamento financeiro: {e}")
        db.session.rollback()
        raise


def sincronizar_ordens_financeiro():
    """
    Sincroniza todas as ordens de serviço com lançamentos financeiros.
    Útil para primeira execução ou correções.
    
    Returns:
        dict: Resumo da sincronização
    """
    try:
        from app.ordem_servico.ordem_servico_model import OrdemServico
        
        ordens = OrdemServico.query.filter_by(ativo=True).all()
        criados = 0
        atualizados = 0
        erros = 0
        
        print(f" Sincronizando {len(ordens)} ordens de serviço com financeiro...")
        
        for ordem in ordens:
            try:
                resultado = gerar_lancamento_ordem_servico(ordem)
                if resultado:
                    if isinstance(resultado, list):
                        criados += len(resultado)
                    else:
                        criados += 1
                        
                # Atualizar status
                atualizar_status_financeiro_ordem(ordem)
                
            except Exception as e:
                print(f" Erro na OS {ordem.numero}: {e}")
                erros += 1
                continue
        
        resumo = {
            'total_processadas': len(ordens),
            'criados': criados,
            'atualizados': atualizados,
            'erros': erros
        }
        
        print(f" Sincronização concluída: {criados} criados, {atualizados} atualizados, {erros} erros")
        return resumo
        
    except Exception as e:
        print(f" Erro na sincronização: {e}")
        return {'total_processadas': 0, 'criados': 0, 'atualizados': 0, 'erros': 1}


# Funções legadas mantidas para compatibilidade
def calcular_ponto_equilibrio(session):
    """Função legada mantida para compatibilidade."""
    from app.financeiro.financeiro_model import MovimentoFinanceiro
    try:
        receitas = session.query(func.sum(MovimentoFinanceiro.valor)).filter_by(tipo='receita').scalar() or 0
        despesas = session.query(func.sum(MovimentoFinanceiro.valor)).filter_by(tipo='despesa').scalar() or 0
        return despesas  # ponto de equilíbrio = despesas totais
    except:
        return 0


def calcular_lucro_liquido(session):
    """Função legada mantida para compatibilidade."""
    from app.financeiro.financeiro_model import MovimentoFinanceiro
    try:
        receitas = session.query(func.sum(MovimentoFinanceiro.valor)).filter_by(tipo='receita').scalar() or 0
        despesas = session.query(func.sum(MovimentoFinanceiro.valor)).filter_by(tipo='despesa').scalar() or 0
        return receitas - despesas
    except:
        return 0

