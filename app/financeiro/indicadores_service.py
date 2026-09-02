# -*- coding: utf-8 -*-
"""
Serviço de Indicadores Financeiros
===================================

Centraliza cálculos e consolidação de indicadores financeiros.
Implementa as 12 regras de reconciliação funcional.

Regras implementadas:
1. Realizado calculado por data_pagamento
2. Vencimento como referência para pendências
3. Inconsistências quando pago sem data_pagamento
4. Cálculos monetários usando Decimal
5. Serviço central usado por dashboard e listagens
6. Preservação de lançamentos quitados
7. Idempotência em segunda baixa
8. Deduplicação por chave confiável
9-12. Integridade e independência de lançamentos
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
import re
from typing import Optional, List, Iterable

from app.financeiro.financeiro_model import LancamentoFinanceiro
from app.financeiro.financeiro_compat import (
    decimal_valor,
    normalizar_status,
    normalizar_texto,
    normalizar_tipo,
    status_eh_pago,
)


@dataclass
class RegistroFinanceiroView:
    """
    Visão unificada de um registro financeiro.

    Representa um lançamento financeiro processado e normalizado,
    independente da sua origem (manual, OS, custo fixo, etc.).
    """
    id: int
    tipo: str
    categoria: str
    descricao: str
    valor: Decimal
    status: str
    data: Optional[date]
    data_vencimento: Optional[date]
    data_pagamento: Optional[date]
    origem: str
    os_id: Optional[int]
    os_parcela_id: Optional[int]
    os_codigo: Optional[str]
    parcela: Optional[int]
    total_parcelas: Optional[int]
    chave_ocorrencia_confiavel: Optional[str] = None
    inconsistente_sem_data: bool = False

    @property
    def is_from_os(self) -> bool:
        """Verifica se o lançamento é originado de uma OS."""
        return self.os_id is not None

    @property
    def data_referencia(self) -> Optional[date]:
        """
        Retorna data de referência para ordenação e filtros.

        Regra 1 e 2: data_pagamento tem prioridade, depois vencimento.
        Regra 3: Inconsistências retornam None.
        """
        if self.inconsistente_sem_data:
            return None
        return self.data_pagamento or self.data_vencimento or self.data


@dataclass
class ResumoFinanceiro:
    """
    Resumo consolidado de período financeiro.

    Implementa Regra 1-5: Consolidação com Decimal, realizado por data_pagamento,
    pendente por vencimento, inconsistências identificadas.
    """
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
    inconsistencias: List[dict] = field(default_factory=list)
    # Contadores para compatibilidade com templates
    qtd_receitas: int = 0
    qtd_despesas: int = 0

    @property
    def receita_realizada(self) -> Decimal:
        """Alias para compatibilidade."""
        return self.receitas_realizadas

    @property
    def despesa_realizada(self) -> Decimal:
        """Alias para compatibilidade."""
        return self.despesas_realizadas

    @property
    def saldo_realizado(self) -> Decimal:
        """Alias para compatibilidade."""
        return self.resultado_realizado

    @property
    def a_receber_pendente(self) -> Decimal:
        """Alias para compatibilidade."""
        return self.contas_a_receber_pendentes

    @property
    def a_pagar_pendente(self) -> Decimal:
        """Alias para compatibilidade."""
        return self.contas_a_pagar_pendentes

    @property
    def total_inconsistencias(self) -> int:
        """Total de lançamentos com inconsistências."""
        return self.lancamentos_pagos_sem_data_qtd

    # Aliases para compatibilidade com templates legados
    @property
    def total_receitas(self) -> Decimal:
        """Alias para template: total_receitas → receitas_realizadas."""
        return self.receitas_realizadas

    @property
    def total_despesas(self) -> Decimal:
        """Alias para template: total_despesas → despesas_realizadas."""
        return self.despesas_realizadas

    @property
    def saldo(self) -> Decimal:
        """Alias para template: saldo → resultado_realizado."""
        return self.resultado_realizado

    def finalizar(self) -> 'ResumoFinanceiro':
        """
        Calcula totais derivados.

        Regra 4: Usa Decimal para todos os cálculos.
        """
        self.resultado_realizado = self.receitas_realizadas - self.despesas_realizadas
        self.saldo_projetado = (
            self.resultado_realizado
            + self.contas_a_receber_pendentes
            - self.contas_a_pagar_pendentes
        )
        return self


def periodo_mes_atual(referencia: Optional[date] = None) -> tuple[date, date]:
    """
    Retorna início e fim do mês atual ou da data de referência.

    Args:
        referencia: Data de referência (default: hoje)

    Returns:
        Tupla (inicio, fim) do mês
    """
    hoje = referencia or date.today()
    return periodo_mes_ano(hoje.month, hoje.year)


def periodo_mes_ano(mes: int, ano: int) -> tuple[date, date]:
    """
    Retorna início e fim exatos de um mês e ano específicos.

    Args:
        mes: Mês (1-12)
        ano: Ano (ex: 2026)

    Returns:
        Tupla (inicio, fim) do mês
    """
    from calendar import monthrange
    # Validação segura de limites
    try:
        mes = max(1, min(12, int(mes)))
        ano = int(ano)
    except (ValueError, TypeError):
        hoje = date.today()
        mes, ano = hoje.month, hoje.year

    inicio = date(ano, mes, 1)
    _, ultimo_dia = monthrange(ano, mes)
    fim = date(ano, mes, ultimo_dia)
    return inicio, fim


def calcular_ultimos_n_meses(ano_fim: int, mes_fim: int, quantidade: int = 6) -> list[tuple[int, int, date, date]]:
    """
    Calcula as N competências mensais terminando em (ano_fim, mes_fim).
    Trata corretamente viradas de ano (dezembro/janeiro) sem aproximação por timedelta(days=30).

    Returns:
        Lista de tuplas (ano, mes, data_inicio, data_fim) em ordem cronológica.
    """
    meses: list[tuple[int, int, date, date]] = []
    ano, mes = int(ano_fim), int(mes_fim)
    for _ in range(quantidade):
        inicio, fim = periodo_mes_ano(mes, ano)
        meses.append((ano, mes, inicio, fim))
        mes -= 1
        if mes == 0:
            mes = 12
            ano -= 1
    return list(reversed(meses))


def data_vencimento_ou_base(registro) -> Optional[date]:
    """Retorna data de vencimento ou data base do lançamento."""
    return getattr(registro, 'data_vencimento', None) or getattr(registro, 'data_lancamento', None)


def data_pagamento_efetivo(registro) -> Optional[date]:
    """
    Retorna data efetiva de pagamento.

    Regra 1: data_pagamento é a referência para realizado.
    """
    return getattr(registro, 'data_pagamento', None)


def lancamento_ativo(registro) -> bool:
    """
    Verifica se lançamento está ativo.

    Regra 6 e 8: Lançamentos de OS canceladas não devem aparecer.
    """
    # Verificar se lançamento está ativo
    if not getattr(registro, 'ativo', True):
        return False

    # Se vinculado a OS, verificar status da OS
    ordem_servico_id = getattr(registro, 'ordem_servico_id', None)
    if ordem_servico_id:
        ordem = getattr(registro, 'ordem_servico', None)
        if ordem:
            os_status = normalizar_status(getattr(ordem, 'status', ''))
            if os_status == 'Cancelada' or os_status == 'Cancelado':
                return False
            if not getattr(ordem, 'ativo', True):
                return False

    return True


def montar_registro_exibicao(registro: LancamentoFinanceiro) -> Optional[RegistroFinanceiroView]:
    """
    Converte lançamento em visão normalizada para exibição.

    Implementa Regras 1-3, 8, 11:
    - Status normalizado
    - Inconsistências detectadas (pago sem data_pagamento)
    - Chave confiável para deduplicação
    - OS canceladas excluídas

    Args:
        registro: Lançamento financeiro do banco

    Returns:
        RegistroFinanceiroView ou None se inativo/cancelado
    """
    if not lancamento_ativo(registro):
        return None

    tipo = normalizar_tipo(getattr(registro, 'tipo', ''))
    status_origem = normalizar_status(getattr(registro, 'status', 'Pendente'))
    data_base = data_vencimento_ou_base(registro)
    data_pgto = data_pagamento_efetivo(registro)
    valor = decimal_valor(getattr(registro, 'valor', 0))

    # Regra 3: Detectar inconsistências (pago sem data_pagamento)
    inconsistente_sem_data = status_eh_pago(status_origem) and data_pgto is None

    if inconsistente_sem_data:
        status_exibicao = 'Inconsistente'
        data_exibicao = None
    elif status_eh_pago(status_origem):
        # Regra 1: Status pago usa data_pagamento
        status_exibicao = 'Recebido' if tipo == 'Receita' else 'Pago'
        data_exibicao = data_pgto
    else:
        # Regra 2: Pendente usa data_vencimento
        status_exibicao = 'Pendente'
        data_exibicao = data_base

    categoria = getattr(registro, 'categoria', '')
    os_id = getattr(registro, 'ordem_servico_id', None)
    os_parcela_id = getattr(registro, 'ordem_servico_parcela_id', None)
    os_codigo = None
    chave_ocorrencia_confiavel = None

    ordem = getattr(registro, 'ordem_servico', None)
    if ordem:
        os_codigo = getattr(ordem, 'numero', None)

    # Identidade final da reconciliação (ordem de prioridade):
    # 1) parcela persistente
    # 2) OS comprovadamente sem parcelas
    # 3) fallback no próprio lançamento
    if os_parcela_id:
        chave_ocorrencia_confiavel = f'os_parcela:{os_parcela_id}'
        categoria = f'Ordem de Serviço (Parcela {os_parcela_id})'
    elif os_id and ordem is not None and len(getattr(ordem, 'parcelas', []) or []) == 0:
        chave_ocorrencia_confiavel = f'os:{os_id}:unica'
        categoria = f'Ordem de Serviço (OS {os_id})'
    else:
        chave_ocorrencia_confiavel = f'lancamento:{getattr(registro, "id", 0)}'

    # Extrair informações de parcela do numero_parcela
    parcela = None
    total_parcelas = None
    numero_parcela = getattr(registro, 'numero_parcela', None)
    if numero_parcela and '/' in numero_parcela:
        partes = numero_parcela.split('/')
        if len(partes) == 2:
            try:
                parcela = int(partes[0])
                total_parcelas = int(partes[1])
            except (ValueError, AttributeError):
                pass

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
        origem=getattr(registro, 'origem', 'MANUAL'),
        os_id=os_id,
        os_parcela_id=os_parcela_id,
        os_codigo=os_codigo,
        parcela=parcela,
        total_parcelas=total_parcelas,
        chave_ocorrencia_confiavel=chave_ocorrencia_confiavel,
        inconsistente_sem_data=inconsistente_sem_data,
    )


def _prioridade_fonte(registro: RegistroFinanceiroView) -> int:
    """
    Define prioridade da fonte para deduplicação.

    Regra 8: OS tem prioridade sobre lançamentos legados.
    """
    if registro.origem == 'ORDEM_SERVICO':
        return 2
    if registro.is_from_os:
        return 2
    return 1


def _deduplicar_ocorrencias_confiaveis(
    registros: List[RegistroFinanceiroView]
) -> List[RegistroFinanceiroView]:
    """
    Remove duplicatas usando chaves confiáveis.

    Implementa Regras 8-11:
    - Uma OS não aparece em múltiplas fontes (Regra 8)
    - Parcelas legítimas preservadas (Regra 10)
    - Deduplicação apenas por chave confiável (Regra 11)
    - OS diferentes com mesmo cliente/valor permanecem (Regra 9)

    Args:
        registros: Lista de registros a deduplic ar

    Returns:
        Lista deduplica sem repetições por chave confiável
    """
    escolhidos_sem_chave: List[RegistroFinanceiroView] = []
    escolhidos_por_chave: dict[str, RegistroFinanceiroView] = {}

    for registro in registros:
        chave = registro.chave_ocorrencia_confiavel
        if not chave:
            # Regra 9: Sem chave confiável, mantém todos (não deduplica)
            escolhidos_sem_chave.append(registro)
            continue

        atual = escolhidos_por_chave.get(chave)
        if atual is None or _prioridade_fonte(registro) > _prioridade_fonte(atual):
            # Regra 8: Prioriza fonte mais confiável
            escolhidos_por_chave[chave] = registro

    return escolhidos_sem_chave + list(escolhidos_por_chave.values())


def resumir_registros_financeiros(
    registros: List[RegistroFinanceiroView]
) -> dict[str, Decimal | int]:
    """
    Calcula resumo financeiro a partir de registros.

    Implementa Regras 1-5:
    - Realizado por data_pagamento (Regra 1)
    - Pendente por vencimento (Regra 2)
    - Inconsistências contabilizadas (Regra 3)
    - Decimal em todos os cálculos (Regra 4)
    - Serviço central único (Regra 5)

    Args:
        registros: Lista de registros financeiros

    Returns:
        Dicionário com totais e indicadores
    """
    registros_unicos = _deduplicar_ocorrencias_confiaveis(registros)

    total_receitas = Decimal('0')
    total_despesas = Decimal('0')
    contas_a_receber_pendentes = Decimal('0')
    contas_a_pagar_pendentes = Decimal('0')
    inconsistencias_qtd = 0
    inconsistencias_valor = Decimal('0')

    for reg in registros_unicos:
        # Regra 3: Inconsistências não integram realizado
        if reg.inconsistente_sem_data:
            inconsistencias_qtd += 1
            inconsistencias_valor += reg.valor
            continue

        # Regra 1: Realizado usa status Pago/Recebido (com data_pagamento válida)
        if reg.status in {'Recebido', 'Pago'}:
            if reg.tipo == 'Receita':
                total_receitas += reg.valor
            elif reg.tipo == 'Despesa':
                total_despesas += reg.valor
            continue

        # Regra 2: Pendente usa data_vencimento
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
    inicio: Optional[date] = None,
    fim: Optional[date] = None,
    *,
    tipo: Optional[str] = None,
    status: Optional[str] = None,
) -> List[RegistroFinanceiroView]:
    """
    Carrega e normaliza registros financeiros com filtros.

    Implementa Regra 5: Serviço central para dashboard e listagens.

    Args:
        inicio: Data inicial do período (opcional)
        fim: Data final do período (opcional)
        tipo: Filtro por tipo (Receita/Despesa)
        status: Filtro por status (Pago/Pendente)

    Returns:
        Lista de registros normalizados e filtrados
    """
    filtros_tipo = normalizar_tipo(tipo) if tipo else ''
    filtros_status = normalizar_status(status) if status else ''

    # Carregar todos os lançamentos ativos
    registros_brutos = list(LancamentoFinanceiro.query.filter_by(ativo=True).all())

    registros: List[RegistroFinanceiroView] = []
    for registro in registros_brutos:
        view = montar_registro_exibicao(registro)
        if view is None:
            continue

        # Aplicar filtros
        if filtros_tipo and view.tipo != filtros_tipo:
            continue
        if filtros_status and view.status != filtros_status:
            continue

        # Filtro de período
        if inicio and fim:
            data_referencia = view.data_referencia
            if data_referencia is None or data_referencia < inicio or data_referencia > fim:
                continue

        registros.append(view)

    # Ordenar por data de referência (mais recentes primeiro)
    registros.sort(key=lambda item: item.data_referencia or date.min, reverse=True)
    return registros


def resumir_financeiro_periodo(inicio: date, fim: date) -> ResumoFinanceiro:
    """
    Gera resumo financeiro completo de um período.

    Implementa todas as 12 regras de reconciliação.

    Args:
        inicio: Data inicial do período
        fim: Data final do período

    Returns:
        Resumo financeiro consolidado com indicadores e inconsistências
    """
    resumo = ResumoFinanceiro(inicio=inicio, fim=fim)

    # Carregar todos os lançamentos ativos
    registros = list(LancamentoFinanceiro.query.filter_by(ativo=True).all())

    views: List[RegistroFinanceiroView] = []
    for registro in registros:
        view = montar_registro_exibicao(registro)
        if view is None:
            continue
        views.append(view)

    # Regra 8-11: Deduplicar antes de processar
    views_unicas = _deduplicar_ocorrencias_confiaveis(views)

    # Regra 3: Coletar inconsistências
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

    # Processar registros únicos
    for view in views_unicas:
        if view.inconsistente_sem_data:
            continue

        # Regra 1: Realizado por data_pagamento dentro do período
        if view.status in {'Pago', 'Recebido'}:
            data_ref = view.data_pagamento
            if data_ref and inicio <= data_ref <= fim:
                if view.tipo == 'Receita':
                    resumo.receitas_realizadas += view.valor
                    resumo.qtd_receitas += 1
                elif view.tipo == 'Despesa':
                    resumo.despesas_realizadas += view.valor
                    resumo.qtd_despesas += 1
            continue

        # Regra 2: Pendente por data_vencimento dentro do período (fallback: data_lancamento)
        if view.status == 'Pendente':
            data_ref = view.data_vencimento or view.data
            if data_ref and inicio <= data_ref <= fim:
                if view.tipo == 'Receita':
                    resumo.contas_a_receber_pendentes += view.valor
                elif view.tipo == 'Despesa':
                    resumo.contas_a_pagar_pendentes += view.valor

    return resumo.finalizar()


def carregar_ultimos_lancamentos(limite: int = 10) -> list[LancamentoFinanceiro]:
    """
    Retorna os últimos lançamentos ativos cadastrados no sistema.
    Ordenados prioritariamente por data de criação / id decrescente,
    sem filtrar por mês específico.
    """
    return (
        LancamentoFinanceiro.query.filter_by(ativo=True)
        .order_by(
            LancamentoFinanceiro.criado_em.desc(),
            LancamentoFinanceiro.id.desc()
        )
        .limit(limite)
        .all()
    )


def obter_dados_dashboard_completos(mes: int, ano: int) -> dict:
    """
    Obtém todos os dados consolidados para o dashboard financeiro (HTML e API)
    utilizando rigorosamente as mesmas regras financeiras.

    Retorna:
        dict contendo:
        - resumo (ResumoFinanceiro)
        - evolucao_mensal (meses_labels, receitas, despesas)
        - resultado_acumulado (meses_labels, saldos)
        - top_categorias (categorias, valores, cores)
        - ultimos_lancamentos (list de LancamentoFinanceiro)
    """
    inicio_mes, fim_mes = periodo_mes_ano(mes, ano)
    resumo = resumir_financeiro_periodo(inicio_mes, fim_mes)

    # Carregar todos os lançamentos ativos e deduplicar pelas regras centrais
    registros = list(LancamentoFinanceiro.query.filter_by(ativo=True).all())
    views: list[RegistroFinanceiroView] = []
    for reg in registros:
        v = montar_registro_exibicao(reg)
        if v is not None:
            views.append(v)
    views_unicas = _deduplicar_ocorrencias_confiaveis(views)

    # 1. Evolução dos últimos 6 meses e Resultado Acumulado
    meses_6 = calcular_ultimos_n_meses(ano, mes, quantidade=6)
    meses_nomes = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                   'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

    meses_labels: list[str] = []
    receitas_mes: list[float] = []
    despesas_mes: list[float] = []
    saldos_acumulados: list[float] = []
    acumulado = Decimal('0')

    for a_comp, m_comp, dt_ini, dt_fim in meses_6:
        label = f"{meses_nomes[m_comp - 1]}/{str(a_comp)[2:]}" if len(set(a for a, _, _, _ in meses_6)) > 1 else meses_nomes[m_comp - 1]
        meses_labels.append(label)

        rec_comp = Decimal('0')
        desp_comp = Decimal('0')

        for v in views_unicas:
            if v.inconsistente_sem_data:
                continue
            if v.status in {'Pago', 'Recebido'}:
                data_ref = v.data_pagamento
                if data_ref and dt_ini <= data_ref <= dt_fim:
                    if v.tipo == 'Receita':
                        rec_comp += v.valor
                    elif v.tipo == 'Despesa':
                        desp_comp += v.valor

        rec_float = float(rec_comp)
        desp_float = float(desp_comp)
        receitas_mes.append(rec_float)
        despesas_mes.append(desp_float)

        # Resultado acumulado = resultado realizado acumulado dos 6 meses
        acumulado += (rec_comp - desp_comp)
        saldos_acumulados.append(float(acumulado))

    # 2. Top Categorias de Despesas do mês selecionado
    # Regra: Somente despesas ativas, status 'pago', cuja data_pagamento esteja dentro do período
    categorias_map: dict[str, Decimal] = {}
    for v in views_unicas:
        if v.inconsistente_sem_data:
            continue
        if v.tipo == 'Despesa' and v.status == 'Pago':
            data_ref = v.data_pagamento
            if data_ref and inicio_mes <= data_ref <= fim_mes:
                cat = v.categoria or 'Sem categoria'
                categorias_map[cat] = categorias_map.get(cat, Decimal('0')) + v.valor

    # Ordenar maiores despesas e pegar top 5
    categorias_ordenadas = sorted(categorias_map.items(), key=lambda x: x[1], reverse=True)[:5]
    categorias_nomes = [cat for cat, _ in categorias_ordenadas]
    categorias_valores = [float(val) for _, val in categorias_ordenadas]

    cores_padrao = [
        'rgba(220, 53, 69, 0.7)',
        'rgba(255, 193, 7, 0.7)',
        'rgba(23, 162, 184, 0.7)',
        'rgba(108, 117, 125, 0.7)',
        'rgba(0, 123, 255, 0.7)'
    ]

    ultimos_lancamentos = carregar_ultimos_lancamentos(limite=10)

    return {
        'resumo': resumo,
        'evolucao_mensal': {
            'meses': meses_labels,
            'receitas': receitas_mes,
            'despesas': despesas_mes
        },
        'fluxo_caixa': {  # chave mantida para compatibilidade com o front
            'meses': meses_labels,
            'saldos': saldos_acumulados
        },
        'top_categorias': {
            'categorias': categorias_nomes,
            'valores': categorias_valores,
            'cores': cores_padrao[:len(categorias_nomes)]
        },
        'ultimos_lancamentos': ultimos_lancamentos
    }
