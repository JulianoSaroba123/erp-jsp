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
from app.extensoes import db
from app.financeiro.financeiro_model import LancamentoFinanceiro
from sqlalchemy import func


def gerar_lancamento_ordem_servico(ordem_servico):
    """
    Gera lançamento financeiro automático para ordem de serviço.
    
    Args:
        ordem_servico: Instância da OrdemServico
        
    Returns:
        LancamentoFinanceiro: Lançamento criado ou None se já existe
    """
    try:
        # Verificar se já existe lançamento para esta OS
        lancamento_existente = LancamentoFinanceiro.query.filter_by(
            ordem_servico_id=ordem_servico.id,
            ativo=True
        ).first()
        
        if lancamento_existente:
            # Atualizar valor se mudou
            if float(lancamento_existente.valor) != float(ordem_servico.valor_total):
                lancamento_existente.valor = ordem_servico.valor_total
                lancamento_existente.descricao = f"OS {ordem_servico.numero} - {ordem_servico.titulo}"
                db.session.commit()
                print(f" Lançamento atualizado para OS {ordem_servico.numero}")
            return lancamento_existente
        
        # Criar novo lançamento apenas se valor > 0
        if ordem_servico.valor_total and float(ordem_servico.valor_total) > 0:
            lancamento = LancamentoFinanceiro(
                descricao=f"OS {ordem_servico.numero} - {ordem_servico.titulo}",
                valor=ordem_servico.valor_total,
                tipo='conta_receber',  # Ordem de serviço é receita a receber
                status='pendente' if ordem_servico.status != 'concluida' else 'recebido',
                categoria='Serviços',
                subcategoria='Ordem de Serviço',
                data_lancamento=ordem_servico.data_abertura,
                data_vencimento=ordem_servico.data_prevista,
                cliente_id=ordem_servico.cliente_id,
                ordem_servico_id=ordem_servico.id,
                observacoes=f"Lançamento automático da {ordem_servico.numero}"
            )
            
            db.session.add(lancamento)
            db.session.commit()
            
            print(f" Lançamento criado para OS {ordem_servico.numero}: R$ {ordem_servico.valor_total}")
            return lancamento
            
    except Exception as e:
        print(f" Erro ao gerar lançamento para OS {ordem_servico.numero}: {e}")
        db.session.rollback()
        
    return None


def atualizar_status_financeiro_ordem(ordem_servico):
    """
    Atualiza status financeiro quando ordem de serviço muda status.
    
    Args:
        ordem_servico: Instância da OrdemServico
    """
    try:
        lancamento = LancamentoFinanceiro.query.filter_by(
            ordem_servico_id=ordem_servico.id,
            ativo=True
        ).first()
        
        if lancamento:
            # Mapear status da OS para status financeiro
            status_map = {
                'concluida': 'recebido',
                'cancelada': 'cancelado',
                'pendente': 'pendente',
                'em_execucao': 'pendente',
                'em_andamento': 'pendente'
            }
            
            novo_status = status_map.get(ordem_servico.status, 'pendente')
            
            if lancamento.status != novo_status:
                lancamento.status = novo_status
                if novo_status == 'recebido':
                    lancamento.data_pagamento = ordem_servico.data_conclusao or date.today()
                
                db.session.commit()
                print(f" Status financeiro atualizado para OS {ordem_servico.numero}: {novo_status}")
                
    except Exception as e:
        print(f" Erro ao atualizar status financeiro da OS {ordem_servico.numero}: {e}")
        db.session.rollback()


def calcular_metricas_dashboard():
    """
    Calcula métricas financeiras para o dashboard.
    
    Returns:
        dict: Dicionário com métricas financeiras
    """
    try:
        from app.ordem_servico.ordem_servico_model import OrdemServico
        
        # Data atual para filtros
        hoje = date.today()
        mes_atual = hoje.month
        ano_atual = hoje.year
        
        # === ORDENS DE SERVIÇO ===
        # Total de ordens de serviço
        total_ordens = OrdemServico.query.filter_by(ativo=True).count()
        
        # Ordens por status
        ordens_abertas = OrdemServico.query.filter(
            OrdemServico.ativo == True,
            OrdemServico.status.in_(['aberta', 'pendente', 'iniciada', 'em_andamento'])
        ).count()
        
        ordens_concluidas = OrdemServico.query.filter_by(
            ativo=True, 
            status='concluida'
        ).count()
        
        # Valor total das ordens de serviço (todas as ativas)
        valor_total_ordens = db.session.query(
            db.func.sum(OrdemServico.valor_total)
        ).filter(
            OrdemServico.ativo == True,
            OrdemServico.valor_total.isnot(None)
        ).scalar() or 0
        
        # Valor das ordens concluídas (receita realizada)
        valor_ordens_concluidas = db.session.query(
            db.func.sum(OrdemServico.valor_total)
        ).filter(
            OrdemServico.ativo == True,
            OrdemServico.status == 'concluida',
            OrdemServico.valor_total.isnot(None)
        ).scalar() or 0
        
        # Valor das ordens em aberto (receita a receber)
        valor_ordens_abertas = db.session.query(
            db.func.sum(OrdemServico.valor_total)
        ).filter(
            OrdemServico.ativo == True,
            OrdemServico.status.in_(['aberta', 'pendente', 'iniciada', 'em_andamento']),
            OrdemServico.valor_total.isnot(None)
        ).scalar() or 0
        
        # === RECEITA DO MÊS ATUAL ===
        # Ordens concluídas neste mês
        ordens_mes = OrdemServico.query.filter(
            OrdemServico.ativo == True,
            OrdemServico.status == 'concluida',
            db.extract('month', OrdemServico.data_conclusao) == mes_atual,
            db.extract('year', OrdemServico.data_conclusao) == ano_atual
        ).all()
        
        receita_mes = sum(float(ordem.valor_total or 0) for ordem in ordens_mes)
        qtd_ordens_mes = len(ordens_mes)
        
        # === LANÇAMENTOS FINANCEIROS ===
        receitas_mes = LancamentoFinanceiro.query.filter(
            LancamentoFinanceiro.ativo == True,
            LancamentoFinanceiro.tipo.in_(['receita', 'conta_receber']),
            LancamentoFinanceiro.status == 'recebido',
            db.extract('month', LancamentoFinanceiro.data_pagamento) == mes_atual,
            db.extract('year', LancamentoFinanceiro.data_pagamento) == ano_atual
        ).all()
        
        despesas_mes = LancamentoFinanceiro.query.filter(
            LancamentoFinanceiro.ativo == True,
            LancamentoFinanceiro.tipo.in_(['despesa', 'conta_pagar']),
            LancamentoFinanceiro.status == 'pago',
            db.extract('month', LancamentoFinanceiro.data_pagamento) == mes_atual,
            db.extract('year', LancamentoFinanceiro.data_pagamento) == ano_atual
        ).all()
        
        total_receitas_mes = sum(float(r.valor) for r in receitas_mes)
        total_despesas_mes = sum(float(d.valor) for d in despesas_mes)
        saldo_mes = total_receitas_mes - total_despesas_mes
        
        # Contas a receber (pendentes)
        contas_receber = LancamentoFinanceiro.query.filter(
            LancamentoFinanceiro.ativo == True,
            LancamentoFinanceiro.tipo == 'conta_receber',
            LancamentoFinanceiro.status == 'pendente'
        ).all()
        
        total_contas_receber = sum(float(c.valor) for c in contas_receber)
        
        # Contas a pagar (pendentes)
        contas_pagar = LancamentoFinanceiro.query.filter(
            LancamentoFinanceiro.ativo == True,
            LancamentoFinanceiro.tipo == 'conta_pagar',
            LancamentoFinanceiro.status == 'pendente'
        ).all()
        
        total_contas_pagar = sum(float(c.valor) for c in contas_pagar)
        
        # === RETORNO ===
        return {
            # Ordens de Serviço
            'total_ordens': total_ordens,
            'ordens_abertas': ordens_abertas,
            'ordens_concluidas': ordens_concluidas,
            'valor_total_ordens': float(valor_total_ordens),
            'valor_ordens_concluidas': float(valor_ordens_concluidas),
            'valor_ordens_abertas': float(valor_ordens_abertas),
            
            # Receita do Mês
            'receita_mes': receita_mes,
            'qtd_ordens_mes': qtd_ordens_mes,
            
            # Financeiro
            'total_receitas_mes': total_receitas_mes,
            'total_despesas_mes': total_despesas_mes,
            'saldo_mes': saldo_mes,
            'total_contas_receber': total_contas_receber,
            'total_contas_pagar': total_contas_pagar,
            'qtd_contas_receber': len(contas_receber),
            'qtd_contas_pagar': len(contas_pagar),
            
            # Resumo
            'fluxo_caixa': float(valor_ordens_concluidas) + total_contas_receber - total_contas_pagar
        }
        
    except Exception as e:
        print(f" Erro ao calcular métricas do dashboard: {e}")
        # Retornar valores zerados em caso de erro
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
        # Busca lançamento existente
        lancamento_existente = LancamentoFinanceiro.query.filter_by(
            ordem_servico_id=ordem_servico.id
        ).first()
        
        if lancamento_existente:
            # Remove o lançamento
            db.session.delete(lancamento_existente)
            db.session.commit()
            print(f"💰 Lançamento financeiro removido para OS {ordem_servico.numero}")
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
                    # Verificar se foi criado ou atualizado
                    if resultado.criado_em.date() == date.today():
                        criados += 1
                    else:
                        atualizados += 1
                        
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

