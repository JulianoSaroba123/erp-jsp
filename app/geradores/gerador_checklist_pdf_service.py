# -*- coding: utf-8 -*-
"""G5-F4: gera PDFs A4 em memória a partir dos snapshots do checklist.

Não acessa banco, não modifica OS/estoque/financeiro e não consulta o
cadastro técnico atual. O documento preenchido exige execução concluída.
ReportLab já é dependência do ERP, sem HTML externo nem recursos de rede.
"""
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether, LongTable, Paragraph, SimpleDocTemplate, Spacer, Table,
    TableStyle,
)

from app.geradores.gerador_checklist_catalogo import (
    STATUS_ROTULOS, STATUS_VALIDOS,
)

AZUL = colors.HexColor("#082b55")
CIANO = colors.HexColor("#0891b2")
CINZA = colors.HexColor("#4b5563")
BORDA = colors.HexColor("#cbd5e1")
FUNDO = colors.HexColor("#eef6fb")
LARGURA, ALTURA = A4
MARGEM = 14 * mm
LARGURA_UTIL = LARGURA - 2 * MARGEM
LOGO = Path(__file__).resolve().parents[1] / "static" / "img" / "JSP_relatorios_oficial.png"


class PDFChecklistError(ValueError):
    """PDF não permitido ou registro técnico inválido."""


def _seguro(valor, padrao="-"):
    if valor is None or valor == "":
        return padrao
    return escape(str(valor)).replace("\n", "<br/>")


def _campo(objeto, nome, padrao="-"):
    if not isinstance(objeto, dict):
        return padrao
    return _seguro(objeto.get(nome), padrao)


def _estilos():
    base = dict(fontName="Helvetica", leading=11, textColor=CINZA)
    return {
        "titulo": ParagraphStyle(
            "G5Titulo", fontName="Helvetica-Bold", fontSize=14,
            leading=18, textColor=AZUL, spaceAfter=6,
        ),
        "sub": ParagraphStyle(
            "G5Sub", fontName="Helvetica-Bold", fontSize=9.5,
            leading=12, textColor=AZUL, spaceBefore=11, spaceAfter=5,
            keepWithNext=True,
        ),
        "texto": ParagraphStyle(
            "G5Texto", fontSize=8.5, **base,
        ),
        "pequeno": ParagraphStyle(
            "G5Pequeno", fontSize=7.5, leading=10, textColor=CINZA,
            fontName="Helvetica",
        ),
        "item": ParagraphStyle(
            "G5Item", fontName="Helvetica-Bold", fontSize=8.4,
            leading=11, textColor=AZUL,
        ),
        "aviso": ParagraphStyle(
            "G5Aviso", fontName="Helvetica-Bold", fontSize=8.3,
            leading=11, textColor=AZUL, alignment=TA_CENTER,
        ),
        "cab": ParagraphStyle(
            "G5Cab", fontName="Helvetica-Bold", fontSize=8.2,
            leading=11, textColor=colors.white,
        ),
    }


def _tabela_dados(linhas, estilos):
    celulas = [
        [
            Paragraph(f"<b>{_seguro(rotulo)}</b>", estilos["pequeno"]),
            Paragraph(_seguro(valor), estilos["texto"]),
        ]
        for rotulo, valor in linhas
    ]
    tabela = Table(celulas, colWidths=[38 * mm, LARGURA_UTIL - 38 * mm], hAlign="LEFT")
    tabela.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDA),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDA),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, FUNDO]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return tabela


def _verificar_snapshot(execucao, modo):
    if modo not in {"branco", "preenchido"}:
        raise PDFChecklistError("Modo de impressão inválido.")

    modelo = getattr(execucao, "modelo_snapshot", None)
    identificacao = getattr(execucao, "identificacao_snapshot", None)
    if not isinstance(modelo, dict) or not isinstance(identificacao, dict):
        raise PDFChecklistError("Identificação técnica não disponível.")
    if modelo.get("versao") != getattr(execucao, "versao_catalogo", None):
        raise PDFChecklistError("Versão do modelo inconsistente.")
    if modelo.get("tipo") != getattr(execucao, "tipo_plano", None):
        raise PDFChecklistError("Tipo de manutenção inconsistente.")
    secoes = modelo.get("secoes")
    if not isinstance(secoes, list) or not secoes:
        raise PDFChecklistError("Itens do checklist não encontrados.")

    itens = []
    for secao in secoes:
        if not isinstance(secao, dict) or not isinstance(secao.get("itens"), list):
            raise PDFChecklistError("Seção técnica inválida.")
        for item in secao["itens"]:
            if not isinstance(item, dict) or not item.get("id") or not item.get("descricao"):
                raise PDFChecklistError("Item técnico inválido.")
            itens.append(item["id"])
    if len(set(itens)) != len(itens):
        raise PDFChecklistError("Modelo com itens duplicados.")

    if modo == "branco":
        return modelo, identificacao, {}

    if getattr(execucao, "estado", None) != "CONCLUIDO":
        raise PDFChecklistError(
            "PDF preenchido disponível somente após conclusão do checklist."
        )
    resultado = getattr(execucao, "respostas_snapshot", None)
    if not isinstance(resultado, dict):
        raise PDFChecklistError("Resultados do checklist indisponíveis.")
    if (
        resultado.get("versao_modelo") != getattr(execucao, "versao_catalogo", None)
        or resultado.get("tipo") != getattr(execucao, "tipo_plano", None)
        or resultado.get("apto_para_encerramento") is not True
    ):
        raise PDFChecklistError("Resultados não correspondem ao modelo concluído.")
    respostas = resultado.get("respostas")
    if not isinstance(respostas, list):
        raise PDFChecklistError("Respostas inválidas.")

    mapa = {}
    for registro in respostas:
        if not isinstance(registro, dict):
            raise PDFChecklistError("Resposta inválida.")
        item_id = registro.get("item_id")
        if item_id in mapa or item_id not in itens:
            raise PDFChecklistError("Respostas duplicadas ou desconhecidas.")
        if registro.get("status") not in STATUS_VALIDOS:
            raise PDFChecklistError("Status de item inválido.")
        mapa[item_id] = registro
    if set(mapa) != set(itens):
        raise PDFChecklistError("Checklist concluído possui itens sem resposta.")
    return modelo, identificacao, mapa


def _cabecalho(canvas, documento):
    canvas.saveState()
    canvas.setFillColor(AZUL)
    canvas.rect(0, ALTURA - 6 * mm, LARGURA, 6 * mm, stroke=0, fill=1)
    canvas.setStrokeColor(CIANO)
    canvas.setLineWidth(1.6)
    canvas.line(MARGEM, ALTURA - 34 * mm, LARGURA - MARGEM, ALTURA - 34 * mm)
    if LOGO.is_file():
        try:
            canvas.drawImage(
                str(LOGO), MARGEM, ALTURA - 30 * mm,
                width=23 * mm, height=22 * mm,
                preserveAspectRatio=True, anchor="c", mask="auto",
            )
        except Exception:
            pass
    canvas.setFillColor(AZUL)
    canvas.setFont("Helvetica-Bold", 12)
    canvas.drawString(41 * mm, ALTURA - 17 * mm, "JSP ELÉTRICA INDUSTRIAL & SOLAR")
    canvas.setFillColor(CINZA)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(41 * mm, ALTURA - 23 * mm, "Atendendo com excelência e honestidade")
    canvas.setStrokeColor(BORDA)
    canvas.line(MARGEM, 15 * mm, LARGURA - MARGEM, 15 * mm)
    canvas.setFillColor(CINZA)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(MARGEM, 10 * mm, "G5 | Registro de manutenção de grupo gerador")
    canvas.drawRightString(
        LARGURA - MARGEM, 10 * mm, f"Página {documento.page}"
    )
    canvas.restoreState()


def _consumiveis(identificacao, estilos):
    registro = identificacao.get("consumiveis", [])
    if not isinstance(registro, list) or not registro:
        return []
    conteudo = [[
        Paragraph("Tipo", estilos["cab"]),
        Paragraph("Referência / fabricante", estilos["cab"]),
        Paragraph("Quantidade cadastrada", estilos["cab"]),
    ]]
    for item in registro[:150]:
        if not isinstance(item, dict):
            continue
        conteudo.append([
            Paragraph(_campo(item, "tipo"), estilos["pequeno"]),
            Paragraph(
                f"{_campo(item, 'referencia')} / {_campo(item, 'fabricante')}",
                estilos["pequeno"],
            ),
            Paragraph(
                f"{_campo(item, 'quantidade')} {_campo(item, 'unidade', '')}",
                estilos["pequeno"],
            ),
        ])
    tabela = LongTable(
        conteudo, colWidths=[42 * mm, 87 * mm, LARGURA_UTIL - 129 * mm],
        repeatRows=1, hAlign="LEFT",
    )
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, FUNDO]),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, BORDA),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDA),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return [
        Paragraph("Referências técnicas cadastradas", estilos["sub"]),
        tabela,
        Spacer(1, 4 * mm),
        Paragraph(
            "Esta tabela apresenta a especificação cadastrada. "
            "Não comprova instalação, substituição ou baixa no estoque.",
            estilos["pequeno"],
        ),
    ]


def _item_documento(item, resposta, modo, estilos):
    descricao = _campo(item, "descricao")
    unidade = _campo(item, "unidade", "")
    cabecalho = Paragraph(
        f"{_campo(item, 'id')} | {descricao}", estilos["item"],
    )
    if modo == "branco":
        texto = (
            "<b>Resultado:</b> [ ] Conforme &nbsp;&nbsp; "
            "[ ] Não conforme &nbsp;&nbsp; [ ] Não aplicável &nbsp;&nbsp; "
            "[ ] Não realizado"
        )
        if item.get("unidade"):
            texto += f"<br/><b>Medição ({unidade}):</b> ____________________________"
        texto += (
            "<br/><b>Observações / justificativa:</b>"
            " _____________________________________________________________"
            "<br/>____________________________________________________________________________"
        )
    else:
        status = resposta["status"]
        texto = f"<b>Resultado:</b> {_seguro(STATUS_ROTULOS[status])}"
        if item.get("unidade"):
            texto += (
                f" &nbsp;&nbsp; <b>Medição ({unidade}):</b> "
                f"{_seguro(resposta.get('medicao'))}"
            )
        texto += (
            "<br/><b>Observações / justificativa:</b> "
            f"{_seguro(resposta.get('observacao'), 'Sem observações.')}"
        )
    tabela = Table(
        [[cabecalho], [Paragraph(texto, estilos["pequeno"])]],
        colWidths=[LARGURA_UTIL], hAlign="LEFT",
    )
    tabela.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.55, BORDA),
        ("BACKGROUND", (0, 0), (-1, 0), FUNDO),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return KeepTogether([tabela, Spacer(1, 2.4 * mm)])


def gerar_pdf_checklist(execucao, *, modo):
    """Retorna bytes de PDF para envio HTTP; sem gravação em disco."""
    modelo, identificacao, resultados = _verificar_snapshot(execucao, modo)
    os = identificacao.get("os") or {}
    cliente = identificacao.get("cliente") or {}
    gerador = identificacao.get("gerador") or {}
    if not all(isinstance(x, dict) for x in (os, cliente, gerador)):
        raise PDFChecklistError("Identificação do documento inválida.")

    estilos = _estilos()
    buffer = BytesIO()
    documento = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=MARGEM, rightMargin=MARGEM,
        topMargin=40 * mm, bottomMargin=20 * mm,
        title=f"Checklist JSP G5 #{getattr(execucao, 'id', '')} - {modo}",
        author="JSP Elétrica Industrial & Solar",
        subject="Checklist de manutenção de grupo gerador",
    )
    historia = [
        Paragraph("CHECKLIST TÉCNICO DE MANUTENÇÃO", estilos["titulo"]),
        Paragraph(
            (
                "FORMULÁRIO EM BRANCO | SEM COMPROVAÇÃO DE EXECUÇÃO"
                if modo == "branco" else
                "REGISTRO CONCLUÍDO | RESULTADOS INFORMADOS NA MANUTENÇÃO"
            ),
            estilos["aviso"],
        ),
        Spacer(1, 4 * mm),
        _tabela_dados([
            ("Checklist", f"#{getattr(execucao, 'id', '-')} | "
                           f"{getattr(execucao, 'versao_catalogo', '-')}"),
            ("Plano", getattr(execucao, "tipo_plano", "-")),
            ("OS", f"{os.get('numero', '-')} | {os.get('titulo', '-')}"),
            ("Cliente", cliente.get("nome") or "-"),
            ("Gerador", f"{gerador.get('codigo', '-')} | "
                        f"{gerador.get('fabricante') or '-'} "
                        f"{gerador.get('modelo') or ''}"),
            ("Nº de série", gerador.get("numero_serie") or "-"),
            ("Potência / tensão", f"{gerador.get('potencia_kva') or '-'} kVA | "
                                 f"{gerador.get('tensao') or '-'}"),
            ("Local", gerador.get("local_instalado") or "-"),
            ("Data da manutenção",
             "____/____/________" if modo == "branco" else
             getattr(execucao, "data_servico", None) or "-"),
        ], estilos),
        Paragraph("Conjunto técnico cadastrado", estilos["sub"]),
        _tabela_dados([
            ("Motor", f"{_campo(identificacao.get('motor'), 'fabricante')} "
                      f"{_campo(identificacao.get('motor'), 'modelo')} "
                      f"| Série: {_campo(identificacao.get('motor'), 'numero_serie')}"),
            ("Alternador", f"{_campo(identificacao.get('alternador'), 'fabricante')} "
                           f"{_campo(identificacao.get('alternador'), 'modelo')} "
                           f"| Série: {_campo(identificacao.get('alternador'), 'numero_serie')}"),
            ("Controladora", f"{_campo(identificacao.get('controladora'), 'fabricante')} "
                             f"{_campo(identificacao.get('controladora'), 'modelo')}"),
            ("QTA/ATS", f"{_campo(identificacao.get('qta'), 'fabricante')} "
                        f"{_campo(identificacao.get('qta'), 'modelo')}"),
            ("Bateria", f"{_campo(identificacao.get('bateria'), 'fabricante')} "
                        f"{_campo(identificacao.get('bateria'), 'modelo')}"),
            ("Carregador", f"{_campo(identificacao.get('carregador'), 'fabricante')} "
                           f"{_campo(identificacao.get('carregador'), 'modelo')}"),
        ], estilos),
    ]
    historia.extend(_consumiveis(identificacao, estilos))
    historia.append(Paragraph("Itens de inspeção e manutenção", estilos["sub"]))

    for secao in modelo["secoes"]:
        historia.append(
            Paragraph(_campo(secao, "titulo"), estilos["sub"])
        )
        for item in secao["itens"]:
            historia.append(
                _item_documento(item, resultados.get(item["id"]), modo, estilos)
            )

    historia.append(Paragraph("Observações gerais e recomendações", estilos["sub"]))
    observacoes = (
        "________________________________________________________________________________"
        "<br/>________________________________________________________________________________"
        "<br/>________________________________________________________________________________"
        if modo == "branco" else
        _seguro(getattr(execucao, "observacoes_gerais", None), "Não informadas.")
    )
    historia.append(Paragraph(observacoes, estilos["texto"]))
    historia.append(Spacer(1, 8 * mm))

    if modo == "preenchido":
        finalizado = getattr(execucao, "concluido_em", None)
        historia.append(Paragraph(
            f"<b>Checklist concluído em:</b> "
            f"{_seguro(finalizado.strftime('%d/%m/%Y %H:%M') if finalizado else '-')}"
            f" &nbsp;&nbsp; <b>Usuário responsável (ID):</b> "
            f"{_seguro(getattr(execucao, 'concluido_por_id', None))}",
            estilos["pequeno"],
        ))
        historia.append(Spacer(1, 8 * mm))

    assinatura = Table([
        [
            Paragraph("________________________________________", estilos["texto"]),
            Paragraph("________________________________________", estilos["texto"]),
        ],
        [
            Paragraph("Técnico responsável (assinatura manual)", estilos["pequeno"]),
            Paragraph("Recebimento pelo cliente (assinatura manual)", estilos["pequeno"]),
        ],
    ], colWidths=[LARGURA_UTIL / 2, LARGURA_UTIL / 2])
    assinatura.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    historia.append(KeepTogether([
        assinatura, Spacer(1, 5 * mm),
        Paragraph(
            "Este documento registra as informações fornecidas pela equipe. "
            "Não substitui procedimentos de segurança, manuais de fabricantes, "
            "ensaios contratados nem responsabilidade técnica aplicável.",
            estilos["pequeno"],
        ),
    ]))
    documento.build(
        historia, onFirstPage=_cabecalho, onLaterPages=_cabecalho,
    )
    pdf = buffer.getvalue()
    if not pdf.startswith(b"%PDF-") or len(pdf) < 1000:
        raise PDFChecklistError("Falha ao gerar PDF íntegro.")
    return pdf
