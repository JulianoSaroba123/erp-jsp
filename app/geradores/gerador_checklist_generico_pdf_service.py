# -*- coding: utf-8 -*-
"""G5: ficha genérica de preparação e checklist para impressão A4.

Não exige OS, gerador cadastrado nem vínculo. Utiliza o catálogo versionado
G5 e o cabeçalho institucional já homologado. Sem leitura/escrita no banco.
Documento em branco: não constitui evidência de execução.
"""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether, LongTable, Paragraph, SimpleDocTemplate, Spacer,
    TableStyle,
)

from app.geradores.gerador_checklist_catalogo import (
    ChecklistDominioError, obter_modelo,
)
from app.geradores.gerador_checklist_pdf_service import (
    AZUL, BORDA, FUNDO, LARGURA_UTIL, MARGEM,
    PDFChecklistError, _cabecalho, _estilos, _item_documento, _tabela_dados,
)

# Lista referencial, a conferir conforme modelo, escopo e manual do fabricante.
_FERRAMENTAS = (
    "Multímetro apropriado à categoria de medição",
    "Alicate amperímetro e pontas de prova íntegras",
    "Detector de tensão adequado / kit de bloqueio",
    "Ferramentas isoladas e jogo de chaves",
    "Torquímetro e soquetes, se aplicável",
    "Lanterna, espelho de inspeção e bandeja de peças",
    "Ferramentas para filtros e drenagem/abastecimento",
    "Bomba/coletor de óleo e recipientes de contenção",
    "Equipamentos de limpeza e panos apropriados",
    "Termômetro / instrumento de medição previsto",
    "Notebook e interface de controladora, se autorizados",
    "Megômetro / termovisor, somente se previstos",
    "Extensão, iluminação portátil e sinalização",
    "Ferramenta ou equipamento adicional: ______________",
)

_EPIS = (
    "EPIs definidos na análise de risco e vestimenta adequada",
    "Proteção ocular, mãos, pés e auditiva, conforme riscos",
    "Isolamento, sinalização e bloqueio de energias",
    "Extintor e recursos de emergência exigidos na área",
)

_MATERIAIS = (
    "Óleo lubrificante: especificação / volume a confirmar",
    "Filtro de óleo: referência e quantidade a confirmar",
    "Filtro de combustível: referência e quantidade a confirmar",
    "Filtro de ar: referência e quantidade a confirmar",
    "Fluido de arrefecimento: especificação a confirmar",
    "Juntas, anéis, abraçadeiras e vedantes compatíveis",
    "Produtos de limpeza e absorventes / contenção",
    "Materiais adicionais conforme escopo e fabricante",
)


def _tabela_grade(titulos, linhas, larguras, estilos):
    """Cabeçalho repetido e linhas imprimíveis em páginas A4."""
    dados = [[Paragraph(t, estilos["cab"]) for t in titulos]]
    dados.extend([
        [Paragraph(str(celula), estilos["pequeno"]) for celula in linha]
        for linha in linhas
    ])
    tabela = LongTable(
        dados, colWidths=larguras, repeatRows=1, hAlign="LEFT",
    )
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, FUNDO]),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDA),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDA),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return tabela


def gerar_pdf_modelo_generico(tipo):
    """Retorna bytes de um formulário genérico, sem consultar registros reais."""
    try:
        modelo = obter_modelo(tipo)
    except ChecklistDominioError as exc:
        raise PDFChecklistError("Tipo de manutenção inválido.") from exc

    estilos = _estilos()
    memoria = BytesIO()
    documento = SimpleDocTemplate(
        memoria, pagesize=A4,
        leftMargin=MARGEM, rightMargin=MARGEM,
        topMargin=40 * mm, bottomMargin=20 * mm,
        title=f"JSP G5 | Checklist genérico {modelo['tipo']}",
        author="JSP Elétrica Industrial & Solar",
        subject="Preparação de manutenção e inspeção manual, sem OS",
    )
    historia = [
        Paragraph("CHECKLIST GENÉRICO | GRUPOS GERADORES", estilos["titulo"]),
        Paragraph(
            "MODELO PARA PLANEJAMENTO E PREENCHIMENTO MANUAL "
            "| SEM COMPROVAÇÃO DE EXECUÇÃO",
            estilos["aviso"],
        ),
        Spacer(1, 3 * mm),
        _tabela_dados([
            ("Tipo de manutenção", modelo["tipo"]),
            ("Catálogo técnico", modelo["versao"]),
            ("Cliente / unidade", "__________________________________________________"),
            ("Local de instalação", "__________________________________________________"),
            ("Gerador / identificação", "__________________________________________________"),
            ("Motor / alternador", "__________________________________________________"),
            ("Controladora / QTA", "__________________________________________________"),
            ("OS (se houver)", "__________________________________________________"),
            ("Data e hora", "____/____/________  ______:______"),
            ("Técnico / equipe", "__________________________________________________"),
        ], estilos),
        Paragraph("01. Planejamento e segurança antes da saída", estilos["sub"]),
        Paragraph(
            "[ ] Escopo e tipo de manutenção conferidos. "
            "[ ] Acesso e responsável do cliente confirmados.",
            estilos["texto"],
        ),
        Spacer(1, 2 * mm),
        Paragraph(
            "[ ] Procedimento, riscos e autorizações verificados. "
            "[ ] Manuais e referências técnicas disponíveis.",
            estilos["texto"],
        ),
        Spacer(1, 2 * mm),
        Paragraph(
            "[ ] Parada, testes de carga, trips e transferências "
            "somente quando autorizados e planejados.",
            estilos["texto"],
        ),
        Paragraph("02. Equipamentos de proteção e segurança", estilos["sub"]),
        _tabela_grade(
            ("Conferência de segurança / EPI", "Separado", "Retorno"),
            [
                (item, "[ ]", "[ ]") for item in _EPIS
            ],
            [LARGURA_UTIL - 54 * mm, 27 * mm, 27 * mm],
            estilos,
        ),
        Paragraph("03. Ferramentas e instrumentos para manutenção", estilos["sub"]),
        Paragraph(
            "A relação é orientativa: conferir adequação, calibração, "
            "isolação e necessidade de cada instrumento antes de separar.",
            estilos["pequeno"],
        ),
        Spacer(1, 2 * mm),
        _tabela_grade(
            ("Ferramenta / equipamento", "Qtde", "Saída", "Confer.", "Retorno"),
            [(nome, "____", "[ ]", "[ ]", "[ ]") for nome in _FERRAMENTAS],
            [89 * mm, 18 * mm, 25 * mm, 25 * mm, 25 * mm],
            estilos,
        ),
        Paragraph("04. Materiais, filtros e consumíveis", estilos["sub"]),
        Paragraph(
            "Nenhum código, óleo, quantidade ou compatibilidade foi presumido. "
            "Conferir com a placa, o manual e o escopo contratado.",
            estilos["pequeno"],
        ),
        Spacer(1, 2 * mm),
        _tabela_grade(
            ("Material / referência a confirmar", "Espec./código", "Qtde", "Separado"),
            [(nome, "____________", "____", "[ ]") for nome in _MATERIAIS],
            [93 * mm, 48 * mm, 17 * mm, 24 * mm],
            estilos,
        ),
        Paragraph("05. Conferência logística", estilos["sub"]),
        Paragraph(
            "[ ] Insumos e volumes separados. "
            "[ ] Transporte, acondicionamento e contenção verificados.",
            estilos["texto"],
        ),
        Spacer(1, 2 * mm),
        Paragraph(
            "[ ] Ferramentas entregues à equipe. "
            "[ ] Resíduos e materiais usados terão destinação adequada.",
            estilos["texto"],
        ),
        Spacer(1, 4 * mm),
        Paragraph(
            "Saída - responsável: _____________________ "
            "  Data/hora: ____/____/______  ______:______",
            estilos["texto"],
        ),
        Spacer(1, 3 * mm),
        Paragraph(
            "Retorno - responsável: __________________ "
            "  Data/hora: ____/____/______  ______:______",
            estilos["texto"],
        ),
        Paragraph("06. Checklist técnico de manutenção G5", estilos["sub"]),
        Paragraph(
            "Assinalar C = conforme, NC = não conforme, NA = não aplicável "
            "ou NR = não realizado. Registrar medições e justificar NC, NA e NR. "
            "Comparar os valores aos limites do fabricante; o formulário "
            "não realiza aprovação automática.",
            estilos["pequeno"],
        ),
    ]
    for secao in modelo["secoes"]:
        for indice, item in enumerate(secao["itens"]):
            historia.append(_item_documento(
                item, None, "branco", estilos,
                titulo_secao=secao["titulo"] if indice == 0 else None,
            ))
    historia.extend([
        Paragraph("07. Materiais efetivamente aplicados / resíduos", estilos["sub"]),
        _tabela_grade(
            ("Referência real / lote (se houver)", "Quantidade", "Observação"),
            [("_________________________________", "_________", "__________________")
             for _ in range(4)],
            [88 * mm, 28 * mm, LARGURA_UTIL - 116 * mm],
            estilos,
        ),
        Paragraph("08. Ocorrências, pendências e recomendações", estilos["sub"]),
        Paragraph(
            "___________________________________________________________________________",
            estilos["texto"],
        ),
        Paragraph(
            "___________________________________________________________________________",
            estilos["texto"],
        ),
        Paragraph(
            "___________________________________________________________________________",
            estilos["texto"],
        ),
        Spacer(1, 6 * mm),
        KeepTogether([
            Paragraph(
                "Técnico: ______________________________  "
                "Cliente: ______________________________",
                estilos["texto"],
            ),
            Spacer(1, 2 * mm),
            Paragraph(
                "Assinaturas manuais, quando aplicáveis. Documento genérico "
                "não substitui OS, procedimentos de segurança, manuais ou "
                "registros de execução no ERP.",
                estilos["pequeno"],
            ),
        ]),
    ])
    documento.build(
        historia, onFirstPage=_cabecalho, onLaterPages=_cabecalho,
    )
    pdf = memoria.getvalue()
    if not pdf.startswith(b"%PDF-") or b"%%EOF" not in pdf[-100:]:
        raise PDFChecklistError("Falha na geração do PDF genérico.")
    return pdf
