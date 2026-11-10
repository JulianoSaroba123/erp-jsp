"""Saldo bancário por extrato importado ancorado em comprovante externo.

Nunca usar o saldo_atual legado como verdade para o dashboard.
A referência é documental; extratos posteriores são somados UMA vez, independentemente
de títulos financeiros e de seu status. Um extrato não conciliado já afeta o banco,
mas é destacado visualmente como pendência de conciliação.
"""
from datetime import date
from decimal import Decimal

from sqlalchemy import text


def _moeda(value):
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def obter_saldo_extrato(session, *, data_limite=None):
    """Retorna snapshot auditável da conta com checkpoint; None sem referência.

    Não consulta lançamentos financeiros para evitar dupla contagem e não
    modifica o banco. data_limite só permite reconstruir datas posteriores à
    referência. A data do saldo é a do último extrato, não o horário atual.
    """
    limite = data_limite or date(9999, 12, 31)
    linha = session.execute(text(
        "SELECT r.conta_bancaria_id,r.data_referencia,r.saldo_referencia,"
        "r.fonte,c.nome,c.saldo_atual FROM saldo_bancario_referencias r "
        "JOIN contas_bancarias c ON c.id=r.conta_bancaria_id "
        "WHERE c.ativo=true AND c.ativa=true "
         "AND r.data_referencia<=:limite "
        "ORDER BY r.data_referencia DESC,r.id DESC LIMIT 1"
    ), {"limite": limite}).mappings().first()
    if linha is None:
        return None

    resultado = session.execute(text(
        "SELECT count(*) AS qtd,"
        "count(*) FILTER (WHERE conciliado=false) AS pendentes,"
        "max(data_movimento) AS ultima_data,"
        "COALESCE(sum(valor) FILTER (WHERE tipo_movimento='credito'),0) AS entradas,"
        "COALESCE(sum(valor) FILTER (WHERE tipo_movimento='debito'),0) AS saidas,"
        "count(*) FILTER (WHERE tipo_movimento NOT IN ('credito','debito')) AS outros_tipos "
        "FROM extratos_bancarios WHERE ativo=true "
        "AND conta_bancaria_id=:conta_id "
        "AND data_movimento>:inicio "
        "AND (:limite IS NULL OR data_movimento<=:limite)"
    ), {"conta_id": linha["conta_bancaria_id"],
        "inicio": linha["data_referencia"], "limite": limite}).mappings().one()

    if resultado["outros_tipos"]:
        raise ValueError("Extrato possui tipo desconhecido: saldo não confiável.")

    saldo = (_moeda(linha["saldo_referencia"])
             + _moeda(resultado["entradas"]) - _moeda(resultado["saidas"]))
    saldo_erp = _moeda(linha["saldo_atual"])

    return {
        "conta_id": linha["conta_bancaria_id"],
        "conta_nome": linha["nome"],
        "referencia": linha["data_referencia"],
        "fonte": linha["fonte"],
        "data_ultimo_extrato": resultado["ultima_data"] or linha["data_referencia"],
        "qtd_extratos": int(resultado["qtd"] or 0),
        "pendentes": int(resultado["pendentes"] or 0),
        "entradas": _moeda(resultado["entradas"]),
        "saidas": _moeda(resultado["saidas"]),
        "saldo_extrato": saldo,
        "saldo_erp": saldo_erp,
        "diferenca_interna": (saldo_erp - saldo),
        "saldo_extrato_fmt": _formatar(saldo),
        "saldo_erp_fmt": _formatar(saldo_erp),
        "diferenca_fmt": _formatar(saldo_erp - saldo),
    }


def _formatar(value):
    return ("R$ " + f"{_moeda(value):,.2f}"
            .replace(",", "X").replace(".", ",").replace("X", "."))
