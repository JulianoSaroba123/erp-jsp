"""
Utilitário para processar templates Word (.docx) com substituição de variáveis
"""
from docx import Document
from docx.shared import Inches
import io
import os


def substituir_variaveis_word(template_path, variaveis):
    """
    Substitui variáveis em um template Word
    
    Args:
        template_path: Caminho do arquivo .docx template
        variaveis: Dict com {variavel: valor} para substituição
        
    Returns:
        Document object com as substituições feitas
    """
    doc = Document(template_path)
    
    # Substituir em parágrafos
    for paragrafo in doc.paragraphs:
        for variavel, valor in variaveis.items():
            if f'[{variavel}]' in paragrafo.text:
                # Substituir no texto completo
                for run in paragrafo.runs:
                    if f'[{variavel}]' in run.text:
                        run.text = run.text.replace(f'[{variavel}]', str(valor))
    
    # Substituir em tabelas
    for tabela in doc.tables:
        for linha in tabela.rows:
            for celula in linha.cells:
                for paragrafo in celula.paragraphs:
                    for variavel, valor in variaveis.items():
                        if f'[{variavel}]' in paragrafo.text:
                            for run in paragrafo.runs:
                                if f'[{variavel}]' in run.text:
                                    run.text = run.text.replace(f'[{variavel}]', str(valor))
    
    # Substituir em cabeçalhos e rodapés
    for secao in doc.sections:
        # Cabeçalho
        for paragrafo in secao.header.paragraphs:
            for variavel, valor in variaveis.items():
                if f'[{variavel}]' in paragrafo.text:
                    for run in paragrafo.runs:
                        if f'[{variavel}]' in run.text:
                            run.text = run.text.replace(f'[{variavel}]', str(valor))
        
        # Rodapé
        for paragrafo in secao.footer.paragraphs:
            for variavel, valor in variaveis.items():
                if f'[{variavel}]' in paragrafo.text:
                    for run in paragrafo.runs:
                        if f'[{variavel}]' in run.text:
                            run.text = run.text.replace(f'[{variavel}]', str(valor))
    
    return doc


def gerar_variaveis_projeto(projeto, cliente=None, config=None, balanco=None):
    """
    Gera dicionário de variáveis a partir de um ProjetoSolar
    
    Args:
        projeto: Instância de ProjetoSolar
        cliente: Instância de Cliente (opcional)
        config: Configuração da empresa
        balanco: Dict com balanço energético
        
    Returns:
        Dict com todas as variáveis disponíveis
    """
    from app.energia_solar.catalogo_model import PlacaSolar, InversorSolar
    
    # Carregar placa e inversor
    placa = PlacaSolar.query.get(projeto.placa_id) if projeto.placa_id else None
    inversor = InversorSolar.query.get(projeto.inversor_id) if projeto.inversor_id else None
    
    variaveis = {
        # Projeto
        'id_projeto': projeto.id or '',
        'projeto_titulo': projeto.nome_cliente or '',
        'nome_cliente': projeto.nome_cliente or '',
        'data_criacao': projeto.data_criacao.strftime('%d/%m/%Y') if projeto.data_criacao else '',
        'status': 'Ativo' if projeto.ativo else 'Inativo',
        
        # Endereço
        'endereco': projeto.endereco or '',
        'cidade': projeto.cidade or '',
        'estado': projeto.estado or '',
        'cep': projeto.cep or '',
        'latitude': projeto.latitude or '',
        'longitude': projeto.longitude or '',
        
        # Irradiação
        'irradiacao_solar_media': f"{projeto.irradiacao_solar:.2f}" if projeto.irradiacao_solar else '',
        
        # Sistema
        'qtd_placas': projeto.qtd_placas or 0,
        'potencia_kwp': f"{projeto.potencia_kwp:.2f}" if projeto.potencia_kwp else '',
        'geracao_estimada_mes': f"{projeto.geracao_estimada_mes:.0f}" if projeto.geracao_estimada_mes else '',
        'area_ocupada': f"{(projeto.qtd_placas or 0) * 2.5:.1f}",
        'peso_total': f"{(projeto.qtd_placas or 0) * 25:.0f}",
        
        # Consumo
        'consumo_kwh_mes': f"{projeto.consumo_kwh_mes:.0f}" if projeto.consumo_kwh_mes else '',
        'simultaneidade': f"{projeto.simultaneidade:.0f}" if projeto.simultaneidade else '35',
        'tarifa_kwh': f"{projeto.tarifa_kwh:.2f}" if projeto.tarifa_kwh else '',
        'tipo_instalacao': (projeto.tipo_instalacao or 'monofasica').capitalize(),
        
        # Placas
        'placa_fabricante': placa.fabricante if placa else '',
        'placa_modelo': placa.modelo if placa else '',
        'placa_potencia': f"{placa.potencia}W" if placa else '',
        'placa_tensao': f"{placa.tensao_max}V" if placa and placa.tensao_max else '',
        'placa_corrente': f"{placa.corrente_max}A" if placa and placa.corrente_max else '',
        'placa_eficiencia': f"{placa.eficiencia}%" if placa and placa.eficiencia else '',
        'placa_garantia': '25 anos',
        'placa_tecnologia': placa.tecnologia if placa else '',
        
        # Inversor
        'inversor_fabricante': inversor.fabricante if inversor else '',
        'inversor_modelo': inversor.modelo if inversor else '',
        'inversor_potencia': f"{inversor.potencia}W" if inversor else '',
        'inversor_tensao_entrada': f"{inversor.tensao_min_mppt}-{inversor.tensao_max_mppt}V" if inversor and inversor.tensao_min_mppt else '',
        'inversor_tensao_saida': '220V',
        'inversor_eficiencia': f"{inversor.eficiencia}%" if inversor and inversor.eficiencia else '',
        'inversor_garantia': '10 anos',
        'inversor_monitoramento': 'WiFi/App',
        
        # Valores
        'valor_total': f"{projeto.preco_final:.2f}" if projeto.preco_final else '',
        'valor_vista': f"{projeto.preco_final * 0.95:.2f}" if projeto.preco_final else '',
        
        # Empresa
        'empresa_nome': config.nome_fantasia if config else 'JSP Elétrica & Solar',
        'empresa_razao': config.razao_social if config else 'JSP Elétrica Industrial Ltda',
        'empresa_cnpj': config.cnpj if config else '41.280.764/0001-65',
        'empresa_endereco': config.logradouro if config else 'Rua Indalécio Costa, 890',
        'empresa_cidade': config.cidade if config else 'Tietê',
        'empresa_estado': config.uf if config else 'SP',
        'empresa_cep': config.cep if config else '18530-170',
        'empresa_telefone': config.telefone if config else '(15) 99670-2036',
        'empresa_email': config.email if config else 'atendimento@eletricasaroba.com.br',
        'empresa_site': 'www.eletricasaroba.com.br',
    }
    
    # Adicionar variáveis do balanço se fornecido
    if balanco:
        variaveis.update({
            'consumo_simultaneo': f"{balanco.get('consumo_simultaneo', 0):.0f}",
            'excedente_kwh': f"{balanco.get('excedente_rede', 0):.0f}",
            'economia_mensal': f"{balanco.get('economia_mensal', 0):.2f}",
            'economia_anual': f"{balanco.get('economia_mensal', 0) * 12:.2f}",
            'economia_25_anos': f"{balanco.get('economia_mensal', 0) * 12 * 25:.2f}",
            'consumo_minimo': balanco.get('consumo_minimo', 30),
        })
    
    return variaveis
