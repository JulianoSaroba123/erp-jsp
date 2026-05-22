"""
Serviço de geração de propostas comerciais usando modelo Word (.docx)
Substitui placeholders por dados reais do projeto solar
"""

from pathlib import Path
from datetime import datetime, timedelta
from docx import Document
import subprocess
import os
import logging

logger = logging.getLogger(__name__)


def formatar_moeda(valor):
    """Formata valor numérico para padrão brasileiro R$ 1.234,56"""
    try:
        valor = float(valor or 0)
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def formatar_numero(valor, casas=2):
    """Formata número com vírgula como separador decimal"""
    try:
        return f"{float(valor or 0):.{casas}f}".replace(".", ",")
    except Exception:
        return "0"


def substituir_texto_em_paragrafos(doc, contexto):
    """Substitui placeholders {{CHAVE}} nos parágrafos do documento"""
    for p in doc.paragraphs:
        for chave, valor in contexto.items():
            placeholder = "{{" + chave + "}}"
            if placeholder in p.text:
                # Substitui preservando formatação básica
                for run in p.runs:
                    if placeholder in run.text:
                        run.text = run.text.replace(placeholder, str(valor))


def substituir_texto_em_tabelas(doc, contexto):
    """Substitui placeholders {{CHAVE}} nas tabelas do documento"""
    for tabela in doc.tables:
        for linha in tabela.rows:
            for celula in linha.cells:
                for p in celula.paragraphs:
                    for chave, valor in contexto.items():
                        placeholder = "{{" + chave + "}}"
                        if placeholder in p.text:
                            for run in p.runs:
                                if placeholder in run.text:
                                    run.text = run.text.replace(placeholder, str(valor))


def substituir_em_paragrafo_preservando_basico(paragrafo, contexto):
    """
    Substitui placeholders mesmo quando o Word divide o texto em múltiplos runs.
    Usa abordagem mais robusta que reconstrói o texto completo.
    """
    texto_original = paragrafo.text
    texto_novo = texto_original

    for chave, valor in contexto.items():
        texto_novo = texto_novo.replace("{{" + chave + "}}", str(valor))

    if texto_novo != texto_original:
        # Limpa todos os runs e coloca o texto novo no primeiro
        for run in paragrafo.runs:
            run.text = ""
        if paragrafo.runs:
            paragrafo.runs[0].text = texto_novo
        else:
            paragrafo.add_run(texto_novo)


def montar_contexto_proposta(projeto):
    """
    Monta dicionário com todos os dados do projeto para substituição no Word.
    Usa lógica centralizadora similar à função montar_contexto_proposta_solar.
    """
    
    # Valor total do investimento (prioridade: valor_venda > valor_orcamento > custo_total)
    valor_total = (
        getattr(projeto, "valor_venda", None)
        or getattr(projeto, "valor_orcamento", None)
        or getattr(projeto, "custo_total", None)
        or 0
    )
    valor_total = float(valor_total or 0)

    # Economia mensal e anual
    economia_mensal = float(getattr(projeto, "economia_mensal", None) or 0)
    economia_anual = float(getattr(projeto, "economia_anual", None) or (economia_mensal * 12))

    # Payback
    payback = valor_total / economia_anual if economia_anual > 0 else 0

    # ROI e economia em 25 anos
    economia_25 = economia_anual * 25
    roi_25 = ((economia_25 - valor_total) / valor_total) * 100 if valor_total > 0 else 0

    # Quantidade de módulos (tentar diferentes nomes de campo)
    qtd_modulos = (
        getattr(projeto, "qtd_placas", None)
        or getattr(projeto, "numero_paineis", None)
        or getattr(projeto, "qtd_modulos", None)
        or 0
    )

    # Área necessária (fallback: qtd_modulos * 2.5 m²)
    area = float(getattr(projeto, "area_necessaria", None) or 0)
    if area == 0 and qtd_modulos:
        area = float(qtd_modulos) * 2.5

    # Cliente
    cliente = None
    if hasattr(projeto, 'cliente_id') and projeto.cliente_id:
        from app.cliente.cliente_model import Cliente
        cliente = Cliente.query.get(projeto.cliente_id)
    
    cliente_nome = cliente.nome_razao_social if cliente else "Cliente não informado"
    cliente_cidade = cliente.cidade if cliente else ""
    cliente_estado = cliente.estado if cliente else ""

    # Placa solar
    placa = None
    if hasattr(projeto, 'placa_id') and projeto.placa_id:
        from app.energia_solar.catalogo_model import PlacaSolar
        placa = PlacaSolar.query.get(projeto.placa_id)

    # Inversor
    inversor = None
    if hasattr(projeto, 'inversor_id') and projeto.inversor_id:
        from app.energia_solar.catalogo_model import InversorSolar
        inversor = InversorSolar.query.get(projeto.inversor_id)

    # Montar contexto completo com todos os placeholders
    contexto = {
        # Dados do cliente
        "NOME_CLIENTE": cliente_nome,
        "CPF_CNPJ_CLIENTE": cliente.cpf_cnpj if cliente and cliente.cpf_cnpj else "",
        "CIDADE": cliente_cidade or getattr(projeto, "localidade", "") or "",
        "ESTADO": cliente_estado or "",
        "ENDERECO_CLIENTE": cliente.endereco if cliente and cliente.endereco else "",
        
        # Dados do projeto
        "NUMERO_PROJETO": str(getattr(projeto, "id", "")),
        "DATA_PROPOSTA": datetime.now().strftime("%d/%m/%Y"),
        "VALIDADE_PROPOSTA": (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y"),
        
        # Dados técnicos
        "POTENCIA_SISTEMA": f"{formatar_numero(getattr(projeto, 'potencia_kwp', 0), 2)} kWp",
        "QTD_MODULOS": str(qtd_modulos),
        "POTENCIA_MODULO": f"{placa.potencia}W" if placa else "",
        "MODELO_MODULO": placa.modelo if placa else "",
        "FABRICANTE_MODULO": placa.fabricante if placa else "",
        "MODELO_INVERSOR": inversor.modelo if inversor else "",
        "FABRICANTE_INVERSOR": inversor.fabricante if inversor else "",
        "POTENCIA_INVERSOR": f"{inversor.potencia}W" if inversor else "",
        
        # Geração e consumo
        "GERACAO_MENSAL": f"{formatar_numero(getattr(projeto, 'geracao_estimada_mes', 0), 0)} kWh/mês",
        "GERACAO_ANUAL": f"{formatar_numero(float(getattr(projeto, 'geracao_estimada_mes', 0) or 0) * 12, 0)} kWh/ano",
        "CONSUMO_MENSAL": f"{formatar_numero(getattr(projeto, 'consumo_kwh_mes', 0), 0)} kWh/mês",
        "CONSUMO_ANUAL": f"{formatar_numero(float(getattr(projeto, 'consumo_kwh_mes', 0) or 0) * 12, 0)} kWh/ano",
        "AREA_NECESSARIA": f"{formatar_numero(area, 2)} m²",
        "IRRADIACAO_SOLAR": f"{formatar_numero(getattr(projeto, 'irradiacao_solar', 5.0), 2)} kWh/m².dia",
        
        # Valores financeiros
        "VALOR_INVESTIMENTO": formatar_moeda(valor_total),
        "ECONOMIA_MENSAL": formatar_moeda(economia_mensal),
        "ECONOMIA_ANUAL": formatar_moeda(economia_anual),
        "ECONOMIA_25_ANOS": formatar_moeda(economia_25),
        "PAYBACK": f"{formatar_numero(payback, 1)} anos",
        "ROI_25_ANOS": f"{formatar_numero(roi_25, 0)}%",
        
        # Custos detalhados
        "CUSTO_EQUIPAMENTOS": formatar_moeda(getattr(projeto, 'custo_equipamentos', 0)),
        "CUSTO_INSTALACAO": formatar_moeda(getattr(projeto, 'custo_instalacao', 0)),
        "CUSTO_PROJETO": formatar_moeda(getattr(projeto, 'custo_projeto', 0)),
        
        # Dados da empresa (configuração)
        "NOME_EMPRESA": "JSP Elétrica & Solar",
        "CNPJ_EMPRESA": "",
        "TELEFONE_EMPRESA": "(15) 99670-2036",
        "EMAIL_EMPRESA": "atendimento@eletricasaroba.com.br",
        "SITE_EMPRESA": "",
    }

    # Tentar carregar dados da empresa de configuração
    try:
        from app.configuracao.configuracao_utils import carregar_configuracao
        config = carregar_configuracao()
        if config:
            contexto["NOME_EMPRESA"] = config.nome_fantasia or contexto["NOME_EMPRESA"]
            contexto["CNPJ_EMPRESA"] = config.cnpj or ""
            contexto["TELEFONE_EMPRESA"] = config.telefone or contexto["TELEFONE_EMPRESA"]
            contexto["EMAIL_EMPRESA"] = config.email or contexto["EMAIL_EMPRESA"]
            contexto["SITE_EMPRESA"] = config.site or ""
    except Exception as e:
        logger.warning(f"Não foi possível carregar configurações da empresa: {e}")

    return contexto


def gerar_docx_proposta(projeto, template_path, output_path):
    """
    Carrega template Word, substitui placeholders e salva documento preenchido.
    
    Args:
        projeto: Objeto ProjetoSolar com dados do projeto
        template_path: Caminho para o arquivo .docx modelo
        output_path: Caminho onde salvar o .docx preenchido
        
    Returns:
        Path do arquivo gerado
    """
    logger.info(f"📄 Carregando template Word: {template_path}")
    doc = Document(template_path)
    
    logger.info(f"🔧 Montando contexto do projeto {projeto.id}")
    contexto = montar_contexto_proposta(projeto)
    
    logger.info(f"✏️ Substituindo {len(contexto)} placeholders no documento")
    substituir_texto_em_paragrafos(doc, contexto)
    substituir_texto_em_tabelas(doc, contexto)
    
    logger.info(f"💾 Salvando documento preenchido: {output_path}")
    doc.save(output_path)
    
    logger.info(f"✅ Documento DOCX gerado com sucesso!")
    return output_path


def converter_docx_para_pdf(docx_path, pdf_path):
    """
    Converte DOCX para PDF usando LibreOffice (se disponível).
    
    Args:
        docx_path: Caminho do arquivo .docx
        pdf_path: Caminho desejado para o .pdf
        
    Returns:
        Path do PDF gerado ou None se falhar
    """
    try:
        output_dir = str(Path(pdf_path).parent)
        
        logger.info(f"📝 Convertendo DOCX para PDF usando LibreOffice...")
        
        # Tentar usar LibreOffice para conversão
        subprocess.run([
            "libreoffice",
            "--headless",
            "--convert-to", "pdf",
            "--outdir", output_dir,
            str(docx_path)
        ], check=True, timeout=60, capture_output=True)
        
        # LibreOffice gera o PDF com o mesmo nome do DOCX
        gerado = Path(output_dir) / (Path(docx_path).stem + ".pdf")
        
        if gerado.exists():
            # Renomear se necessário
            if str(gerado) != str(pdf_path):
                gerado.rename(pdf_path)
            
            logger.info(f"✅ PDF gerado com sucesso: {pdf_path}")
            return pdf_path
        else:
            logger.warning(f"⚠️ LibreOffice executou mas PDF não foi encontrado")
            return None

    except FileNotFoundError:
        logger.warning(f"⚠️ LibreOffice não encontrado no sistema. PDF não será gerado.")
        return None
    except subprocess.TimeoutExpired:
        logger.error(f"❌ Timeout ao converter DOCX para PDF (60s)")
        return None
    except Exception as e:
        logger.error(f"❌ Erro ao converter DOCX para PDF: {e}")
        return None
