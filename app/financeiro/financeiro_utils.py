from app.financeiro.financeiro_model import MovimentoFinanceiro
from sqlalchemy import func

def calcular_ponto_equilibrio(session):
    receitas = session.query(func.sum(MovimentoFinanceiro.valor)).filter_by(tipo='receita').scalar() or 0
    despesas = session.query(func.sum(MovimentoFinanceiro.valor)).filter_by(tipo='despesa').scalar() or 0
    return despesas  # ponto de equilíbrio = despesas totais

def calcular_lucro_liquido(session):
    receitas = session.query(func.sum(MovimentoFinanceiro.valor)).filter_by(tipo='receita').scalar() or 0
    despesas = session.query(func.sum(MovimentoFinanceiro.valor)).filter_by(tipo='despesa').scalar() or 0
    return receitas - despesas

