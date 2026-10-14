# -*- coding: utf-8 -*-
"""G5-F1: catálogo versionado de checklist para grupos geradores.

Módulo puro: não consulta SQLAlchemy, não acessa sessão Flask,
não gera PDFs, não cria OS, não movimenta estoque e não grava dados.

A execução digital e o PDF serão implementados em etapas posteriores,
a partir de uma cópia congelada da versão e das respostas validadas.
"""
from decimal import Decimal, InvalidOperation
from collections.abc import Mapping

VERSAO_CATALOGO = "G5-1.0"
TIPOS = ("BASICA", "INTERMEDIARIA", "AVANCADA")
STATUS_VALIDOS = (
    "CONFORME", "NAO_CONFORME", "NAO_APLICAVEL", "NAO_REALIZADO",
)
STATUS_ROTULOS = {
    "CONFORME": "Conforme",
    "NAO_CONFORME": "Não conforme",
    "NAO_APLICAVEL": "Não aplicável",
    "NAO_REALIZADO": "Não realizado",
}
_NIVEIS = {nome: posicao for posicao, nome in enumerate(TIPOS)}
MAX_OBSERVACAO = 1500
MAX_MEDICAO = 40


class ChecklistDominioError(ValueError):
    """Entrada inválida, sem efeitos colaterais."""


# (id, título, ((id, descrição, nível mínimo, unidade de medida), ...)).
# Uma unidade não impõe limite de aceitação: consultar manual do fabricante.
# Itens de teste funcional dependem de autorização e procedimento seguro.
_SECOES = (
    ("seguranca", "01. Segurança e condições iniciais", (
        ("SEG_EPI", "Conferir EPIs, condições de acesso e riscos da intervenção.", "BASICA", None),
        ("SEG_BLOQUEIO", "Conferir isolamento e bloqueio das fontes de energia quando aplicável.", "BASICA", None),
        ("SEG_VAZAMENTOS", "Inspecionar vazamentos, contenção e condições gerais da área.", "BASICA", None),
    )),
    ("motor", "02. Motor diesel e arrefecimento", (
        ("MOT_HORIMETRO", "Registrar horímetro apresentado pela controladora.", "BASICA", "h"),
        ("MOT_NIVEL_OLEO", "Verificar nível e condição visual do óleo lubrificante.", "BASICA", None),
        ("MOT_ARREFECIMENTO", "Verificar nível e condição do fluido de arrefecimento a frio.", "BASICA", None),
        ("MOT_CORREIAS", "Inspecionar correias, mangueiras, conexões e fixações.", "BASICA", None),
        ("MOT_PRESSAO_OLEO", "Medir pressão do óleo em operação, quando houver leitura segura.", "BASICA", "bar"),
        ("MOT_TEMPERATURA", "Registrar temperatura do motor em operação.", "BASICA", "°C"),
        ("MOT_TROCA_OLEO", "Executar troca de óleo conforme escopo e especificação do fabricante.", "INTERMEDIARIA", None),
        ("MOT_LIMPEZA", "Executar limpeza técnica de motor e compartimento, conforme escopo.", "INTERMEDIARIA", None),
    )),
    ("combustivel", "03. Alimentação de combustível e filtros", (
        ("COM_LINHAS", "Inspecionar tanque, linhas, conexões e indícios de vazamento.", "BASICA", None),
        ("COM_FILTROS", "Inspecionar condição e identificação dos filtros instalados.", "BASICA", None),
        ("COM_TROCA_FILTROS", "Substituir filtros especificados, registrando referências e quantidades.", "INTERMEDIARIA", None),
        ("COM_DRENO", "Inspecionar/drenar separador de água, quando equipado e autorizado.", "INTERMEDIARIA", None),
        ("COM_FILTRO_AR", "Verificar/substituir filtro de ar conforme especificação e necessidade.", "INTERMEDIARIA", None),
    )),
    ("eletrico", "04. Partida, alternador e medições", (
        ("ELE_BATERIA", "Medir tensão do banco de baterias em condição registrada.", "BASICA", "V"),
        ("ELE_PARTIDA", "Verificar partida, parada e alarmes sem forçar condição insegura.", "BASICA", None),
        ("ELE_TENSAO", "Registrar tensão de saída medida, informando o ponto de medição.", "BASICA", "V"),
        ("ELE_FREQUENCIA", "Registrar frequência de saída medida.", "BASICA", "Hz"),
        ("ELE_CONEXOES", "Inspecionar conexões e aterramento visualmente, com segurança.", "BASICA", None),
        ("ELE_CORRENTE", "Registrar corrente em regime definido, se o ensaio estiver contratado.", "AVANCADA", "A"),
        ("ELE_CARGA", "Realizar teste de carga somente com plano, autorização e condições seguras.", "AVANCADA", None),
        ("ELE_TERMOGRAFIA", "Executar termografia se prevista e tecnicamente viável.", "AVANCADA", None),
    )),
    ("controle", "05. Controladora, proteções e QTA/ATS", (
        ("CTL_ALARMES", "Inspecionar histórico de alarmes e indicadores da controladora.", "BASICA", None),
        ("QTA_INSPECAO", "Inspecionar visualmente QTA/ATS, intertravamentos e sinalizações.", "BASICA", None),
        ("CTL_BACKUP", "Efetuar backup de parâmetros da controladora, se suportado.", "INTERMEDIARIA", None),
        ("PROT_PRESSAO", "Testar trip de baixa pressão de óleo somente por procedimento controlado.", "INTERMEDIARIA", None),
        ("PROT_TEMPERATURA", "Testar trip de alta temperatura somente por procedimento controlado.", "INTERMEDIARIA", None),
        ("QTA_TRANSFERENCIA", "Testar transferência/retransferência com autorização operacional.", "AVANCADA", None),
        ("CTL_PROTECOES", "Revisar parametrizações e respostas das proteções previstas no escopo.", "AVANCADA", None),
    )),
    ("fechamento", "06. Fechamento e recomendações", (
        ("FIM_INSPECAO", "Conferir ausência de ferramentas, resíduos e intervenções pendentes.", "BASICA", None),
        ("FIM_RECOMENDACOES", "Registrar anomalias, restrições, ações e recomendações.", "BASICA", None),
        ("FIM_TESTE_FINAL", "Verificar retorno ao estado operacional acordado com o cliente.", "INTERMEDIARIA", None),
        ("FIM_REGISTRO", "Confirmar resultados e documentação do ensaio avançado.", "AVANCADA", None),
    )),
)


def obter_modelo(tipo):
    """Retorna cópia independente, na ordem estável de apresentação."""
    if not isinstance(tipo, str):
        raise ChecklistDominioError("Tipo de manutenção inválido.")
    tipo = tipo.strip().upper()
    if tipo not in _NIVEIS:
        raise ChecklistDominioError("Tipo de manutenção inválido.")
    secoes = []
    for codigo, titulo, itens in _SECOES:
        selecionados = [
            {
                "id": item_id,
                "descricao": descricao,
                "unidade": unidade,
                "status": None,
            }
            for item_id, descricao, nivel, unidade in itens
            if _NIVEIS[nivel] <= _NIVEIS[tipo]
        ]
        if selecionados:
            secoes.append({"id": codigo, "titulo": titulo, "itens": selecionados})
    return {"versao": VERSAO_CATALOGO, "tipo": tipo, "secoes": secoes}


def itens_do_modelo(tipo):
    """Mapeia IDs estáveis para definição, sem expor estado compartilhado."""
    modelo = obter_modelo(tipo)
    return {
        item["id"]: item
        for secao in modelo["secoes"] for item in secao["itens"]
    }


def validar_respostas(tipo, respostas, *, encerrar=False):
    """Valida respostas e devolve snapshot ordenado, sem modificar entradas.

    Rascunho aceita item ainda sem resposta. Conclusão exige que todos
    os itens sejam explicitamente classificados. Não executado, não
    aplicável e não conforme exigem justificativa para a conclusão.
    Valor de medição é obrigatório ao concluir um item mensurável
    classificado conforme/não conforme. Não calcula aprovação técnica.
    """
    itens = itens_do_modelo(tipo)
    if not isinstance(respostas, Mapping):
        raise ChecklistDominioError("Respostas devem formar um mapa de itens.")
    desconhecidos = set(respostas) - set(itens)
    if desconhecidos:
        raise ChecklistDominioError("Resposta para item não previsto no modelo.")

    normalizadas = []
    for item_id, definicao in itens.items():
        bruto = respostas.get(item_id) or {}
        if not isinstance(bruto, Mapping):
            raise ChecklistDominioError(f"{item_id}: resposta inválida.")
        if set(bruto) - {"status", "medicao", "observacao"}:
            raise ChecklistDominioError(f"{item_id}: campo não reconhecido.")

        status = bruto.get("status") or None
        if status is not None and status not in STATUS_VALIDOS:
            raise ChecklistDominioError(f"{item_id}: status inválido.")
        observacao = str(bruto.get("observacao") or "").strip()
        medicao = str(bruto.get("medicao") or "").strip()

        if len(observacao) > MAX_OBSERVACAO or len(medicao) > MAX_MEDICAO:
            raise ChecklistDominioError(f"{item_id}: tamanho de campo excedido.")
        if medicao and definicao["unidade"] is None:
            raise ChecklistDominioError(f"{item_id}: item não admite medição.")
        if medicao:
            try:
                numero = Decimal(medicao.replace(",", "."))
                if not numero.is_finite():
                    raise InvalidOperation
            except (InvalidOperation, ValueError):
                raise ChecklistDominioError(f"{item_id}: medição deve ser numérica.") from None
            medicao = format(numero, "f")

        if encerrar:
            if status is None:
                raise ChecklistDominioError(f"{item_id}: item não avaliado.")
            if status in {"NAO_CONFORME", "NAO_APLICAVEL", "NAO_REALIZADO"} and not observacao:
                raise ChecklistDominioError(f"{item_id}: justificativa obrigatória.")
            if status in {"CONFORME", "NAO_CONFORME"} and definicao["unidade"] and not medicao:
                raise ChecklistDominioError(f"{item_id}: medição obrigatória.")

        normalizadas.append({
            "item_id": item_id,
            "status": status,
            "medicao": medicao or None,
            "unidade": definicao["unidade"],
            "observacao": observacao,
        })
    return {
        "versao_modelo": VERSAO_CATALOGO,
        "tipo": obter_modelo(tipo)["tipo"],
        "respostas": normalizadas,
        "apto_para_encerramento": bool(encerrar),
    }
