from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
import re

from sqlalchemy.orm import joinedload

from aplicacao.financeiro.financeiro_model import LancamentoFinanceiro
from aplicacao.financeiro.lancamento_os_model import LancamentoFinanceiroOS
from .financeiro_compat import (
    decimal_valor,
    normalizar_status,
    normalizar_texto,
    normalizar_tipo,
    status_eh_pago,
)


@dataclass
class RegistroFinanceiroView:
    id: int
    tipo: str
    categoria: str
    descricao: str
    valor: Decimal
    status: str
    data: date | None
    data_vencimento: date | None
    data_pagamento: date | None
    origem: str
    os_id: int | None
    os_codigo: str | None
    parcela: int | None
    total_parcelas: int | None
    chave_ocorrencia_confiavel: str | None = None
    inconsistente_sem_data: bool = False

    @property
    def is_from_os(self) -> bool:
        return self.origem == 'OS'

    @property
    def data_referencia(self) -> date | None:
        if self.inconsistente_sem_data:
            return None
        return self.data_pagamento or self.data_vencimento or self.data


@dataclass
class ResumoFinanceiro:
    inicio: date
    fim: date
    receitas_realizadas: Decimal = Decimal('0')
    despesas_realizadas: Decimal = Decimal('0')
    resultado_realizado: Decimal = Decimal('0')
    contas_a_receber_pendentes: Decimal = Decimal('0')
    contas_a_pagar_pendentes: Decimal = Decimal('0')
    saldo_projetado: Decimal = Decimal('0')
    lancamentos_pagos_sem_data_qtd: int = 0
    lancamentos_pagos_sem_data_valor: Decimal = Decimal('0')
    inconsistencias: list[dict] = field(default_factory=list)

    @property
    def receita_realizada(self) -> Decimal:
        return self.receitas_realizadas

    @property
    def despesa_realizada(self) -> Decimal:
        return self.despesas_realizadas

    @property
    def saldo_realizado(self) -> Decimal:
        return self.resultado_realizado

    @property
    def a_receber_pendente(self) -> Decimal:
        return self.contas_a_receber_pendentes

    @property
    def a_pagar_pendente(self) -> Decimal:
        return self.contas_a_pagar_pendentes

    @property
    def total_inconsistencias(self) -> int:
        return self.lancamentos_pagos_sem_data_qtd

    def finalizar(self) -> 'ResumoFinanceiro':
        self.resultado_realizado = self.receitas_realizadas - self.despesas_realizadas
        self.saldo_projetado = (
            self.resultado_realizado
            + self.contas_a_receber_pendentes
            - self.contas_a_pagar_pendentes
        )
        return self


def periodo_mes_atual(referencia: date | None = None) -> tuple[date, date]:
    hoje = referencia or date.today()
    inicio = hoje.replace(day=1)
    fim = (inicio + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    return inicio, fim


def data_vencimento_ou_base(registro) -> date | None:
    return getattr(registro, 'data_vencimento', None) or getattr(registro, 'data', None)


def data_pagamento(registro) -> date | None:
    return getattr(registro, 'data_pagamento', None)


def lancamento_os_ativo(registro) -> bool:
    os_status = normalizar_status(getattr(registro, 'os_status', ''))
    if os_status == 'Cancelada':
        return False

    ordem = getattr(registro, 'os', None)
    if ordem is None:
        return True
    if normalizar_status(getattr(ordem, 'status', '')) == 'Cancelada':
        return False
    return getattr(ordem, 'ativo', True) is not False


def montar_registro_exibicao(registro) -> RegistroFinanceiroView | None:
    if isinstance(registro, LancamentoFinanceiroOS) and not lancamento_os_ativo(registro):
        return None

    tipo = normalizar_tipo(getattr(registro, 'tipo', ''))
    status_origem = normalizar_status(getattr(registro, 'status', 'Pendente'))
    data_base = data_vencimento_ou_base(registro)
    data_pgto = data_pagamento(registro)
    valor = decimal_valor(getattr(registro, 'valor', 0))

    inconsistente_sem_data = status_eh_pago(status_origem) and data_pgto is None

    if inconsistente_sem_data:
        status_exibicao = 'Inconsistente'
        data_exibicao = None
    elif status_eh_pago(status_origem):
        status_exibicao = 'Recebido' if tipo == 'Receita' else 'Pago'
        data_exibicao = data_pgto
    else:
        status_exibicao = 'Pendente'
        data_exibicao = data_base

    categoria = getattr(registro, 'categoria', '')
    os_codigo = None
    chave_ocorrencia_confiavel = None

    if isinstance(registro, LancamentoFinanceiroOS):
        ordem = getattr(registro, 'os', None)
        os_codigo = getattr(ordem, 'codigo', None)
        categoria = f'Ordem de Serviço (OS {registro.os_id})'

        parcela_val = getattr(registro, 'parcela', None)
        total_parcelas_val = getattr(registro, 'total_parcelas', None)
        parcela_canonica = parcela_val if parcela_val not in (None, 0) else 1
        total_canonico = total_parcelas_val if total_parcelas_val not in (None, 0) else 1
        if os_codigo:
            chave_ocorrencia_confiavel = f'os:{os_codigo}:parcela:{parcela_canonica}:{total_canonico}'
    else:
        categoria_texto = normalizar_texto(categoria)
        observacoes_texto = normalizar_texto(getattr(registro, 'observacoes', ''))
        match = re.match(r'^Ordem de Serviço\s+(OS\d+)$', categoria_texto)
        if match and observacoes_texto.startswith('Lançamento automático'):
            os_codigo = match.group(1)
            # No fluxo legado, o registro representa ocorrência única (não parcelada).
            chave_ocorrencia_confiavel = f'os:{os_codigo}:parcela:1:1'

    return RegistroFinanceiroView(
        id=getattr(registro, 'id', 0),
        tipo=tipo or 'Indefinido',
        categoria=categoria or '-',
        descricao=normalizar_texto(getattr(registro, 'descricao', '')) or '-',
        valor=valor,
        status=status_exibicao,
        data=data_exibicao,
        data_vencimento=data_base,
        data_pagamento=data_pgto,
        origem='OS' if isinstance(registro, LancamentoFinanceiroOS) else 'tradicional',
        os_id=getattr(registro, 'os_id', None),
        os_codigo=os_codigo,
        parcela=getattr(registro, 'parcela', None),
        total_parcelas=getattr(registro, 'total_parcelas', None),
        chave_ocorrencia_confiavel=chave_ocorrencia_confiavel,
        inconsistente_sem_data=inconsistente_sem_data,
    )


def _prioridade_fonte(registro: RegistroFinanceiroView) -> int:
    if registro.origem == 'OS':
        return 2
    return 1


def _deduplicar_ocorrencias_confiaveis(registros: list[RegistroFinanceiroView]) -> list[RegistroFinanceiroView]:
    escolhidos_sem_chave: list[RegistroFinanceiroView] = []
    escolhidos_por_chave: dict[str, RegistroFinanceiroView] = {}

    for registro in registros:
        chave = registro.chave_ocorrencia_confiavel
        if not chave:
            escolhidos_sem_chave.append(registro)
            continue

        atual = escolhidos_por_chave.get(chave)
        if atual is None or _prioridade_fonte(registro) > _prioridade_fonte(atual):
            escolhidos_por_chave[chave] = registro

    return escolhidos_sem_chave + list(escolhidos_por_chave.values())


def resumir_registros_financeiros(registros: list[RegistroFinanceiroView]) -> dict[str, Decimal | int]:
    registros_unicos = _deduplicar_ocorrencias_confiaveis(registros)

    total_receitas = Decimal('0')
    total_despesas = Decimal('0')
    contas_a_receber_pendentes = Decimal('0')
    contas_a_pagar_pendentes = Decimal('0')
    inconsistencias_qtd = 0
    inconsistencias_valor = Decimal('0')

    for reg in registros_unicos:
        if reg.inconsistente_sem_data:
            inconsistencias_qtd += 1
            inconsistencias_valor += reg.valor
            continue

        if reg.status in {'Recebido', 'Pago'}:
            if reg.tipo == 'Receita':
                total_receitas += reg.valor
            elif reg.tipo == 'Despesa':
                total_despesas += reg.valor
            continue

        if reg.status == 'Pendente':
            if reg.tipo == 'Receita':
                contas_a_receber_pendentes += reg.valor
            elif reg.tipo == 'Despesa':
                contas_a_pagar_pendentes += reg.valor

    saldo = total_receitas - total_despesas
    saldo_projetado = saldo + contas_a_receber_pendentes - contas_a_pagar_pendentes

    return {
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'saldo': saldo,
        'contas_a_receber_pendentes': contas_a_receber_pendentes,
        'contas_a_pagar_pendentes': contas_a_pagar_pendentes,
        'saldo_projetado': saldo_projetado,
        'inconsistencias_qtd': inconsistencias_qtd,
        'inconsistencias_valor': inconsistencias_valor,
        'total_os': sum(1 for reg in registros_unicos if reg.is_from_os),
        'valor_os': sum(
            reg.valor for reg in registros_unicos
            if reg.is_from_os and reg.status in {'Recebido', 'Pago'} and not reg.inconsistente_sem_data
        ),
    }


def carregar_registros_financeiros(
    inicio: date | None = None,
    fim: date | None = None,
    *,
    tipo: str | None = None,
    status: str | None = None,
) -> list[RegistroFinanceiroView]:
    filtros_tipo = normalizar_tipo(tipo) if tipo else ''
    filtros_status = normalizar_status(status) if status else ''

    registros_brutos = list(LancamentoFinanceiro.query.all())
    registros_brutos.extend(
        LancamentoFinanceiroOS.query.options(joinedload(LancamentoFinanceiroOS.os)).all()
    )

    registros: list[RegistroFinanceiroView] = []
    for registro in registros_brutos:
        view = montar_registro_exibicao(registro)
        if view is None:
            continue

        if filtros_tipo and view.tipo != filtros_tipo:
            continue
        if filtros_status and view.status != filtros_status:
            continue

        if inicio and fim:
            data_referencia = view.data_referencia
            if data_referencia is None or data_referencia < inicio or data_referencia > fim:
                continue

        registros.append(view)

    registros.sort(key=lambda item: item.data_referencia or date.min, reverse=True)
    return registros


def resumir_financeiro_periodo(inicio: date, fim: date) -> ResumoFinanceiro:
    resumo = ResumoFinanceiro(inicio=inicio, fim=fim)

    registros = list(LancamentoFinanceiro.query.all())
    registros.extend(
        LancamentoFinanceiroOS.query.options(joinedload(LancamentoFinanceiroOS.os)).all()
    )

    views: list[RegistroFinanceiroView] = []
    for registro in registros:
        view = montar_registro_exibicao(registro)
        if view is None:
            continue
        views.append(view)

    views_unicas = _deduplicar_ocorrencias_confiaveis(views)

    for view in views:
        if view.inconsistente_sem_data:
            resumo.lancamentos_pagos_sem_data_qtd += 1
            resumo.lancamentos_pagos_sem_data_valor += view.valor
            resumo.inconsistencias.append(
                {
                    'id': view.id,
                    'tipo': view.tipo,
                    'descricao': view.descricao,
                    'valor': view.valor,
                    'origem': view.origem,
                    'os_id': view.os_id,
                }
            )

    for view in views_unicas:
        if view.inconsistente_sem_data:
            continue

        if view.status in {'Pago', 'Recebido'}:
            data_ref = view.data_pagamento
            if data_ref and inicio <= data_ref <= fim:
                if view.tipo == 'Receita':
                    resumo.receitas_realizadas += view.valor
                elif view.tipo == 'Despesa':
                    resumo.despesas_realizadas += view.valor
            continue

        if view.status == 'Pendente':
            data_ref = view.data_vencimento or view.data
            if data_ref and inicio <= data_ref <= fim:
                if view.tipo == 'Receita':
                    resumo.contas_a_receber_pendentes += view.valor
                elif view.tipo == 'Despesa':
                    resumo.contas_a_pagar_pendentes += view.valor

    return resumo.finalizar()
