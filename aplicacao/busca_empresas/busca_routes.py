"""
Rotas para busca de empresas
"""

import requests
import json
import re
import time
import random
from datetime import datetime
from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
import os
from urllib.parse import urlencode
from aplicacao.extensoes import db
from aplicacao.busca_empresas.empresa_model import EmpresaEncontrada
import sqlite3
import csv

# Simple file-based cache for BrasilAPI CNPJ responses
BRASILAPI_CACHE_DIR = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')), 'data', 'cache', 'brasilapi')
os.makedirs(BRASILAPI_CACHE_DIR, exist_ok=True)

def _cache_path_for_cnpj(cnpj: str) -> str:
    norm = re.sub(r"\D", "", cnpj or "")
    return os.path.join(BRASILAPI_CACHE_DIR, f"{norm}.json")

def _cache_get(cnpj: str, max_age_days: int = 30):
    path = _cache_path_for_cnpj(cnpj)
    if not os.path.exists(path):
        return None
    try:
        stat = os.stat(path)
        age_seconds = time.time() - stat.st_mtime
        if age_seconds > max_age_days * 86400:
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro lendo cache BrasilAPI ({path}): {e}")
        return None

def _cache_set(cnpj: str, data: dict):
    path = _cache_path_for_cnpj(cnpj)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Falha ao gravar cache BrasilAPI ({path}): {e}")

def http_get_with_retries(url: str, params: dict = None, headers: dict = None, retries: int = 3, backoff: float = 0.5, timeout: int = 10):
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            if params:
                resp = requests.get(url, params=params, headers=headers or {}, timeout=timeout)
            else:
                resp = requests.get(url, headers=headers or {}, timeout=timeout)
            resp.raise_for_status()
            return resp
        except Exception as e:
            last_exc = e
            sleep_time = backoff * (2 ** (attempt - 1))
            print(f"Request failed (attempt {attempt}/{retries}) to {url}: {e}; sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
    print(f"All retries failed for {url}: {last_exc}")
    raise last_exc


def buscar_paginas_amarelas(cidade, atividade):
    """Busca empresas no site Páginas Amarelas"""
    empresas = []
    
    try:
        # Mapear atividades para termos de busca mais específicos
        termos_busca = mapear_termo_busca(atividade)
        
        for termo in termos_busca[:2]:  # Limitar a 2 termos para não sobrecarregar
            url = f"https://www.paginasamarelas.com.br/busca/{quote_plus(termo)}/{quote_plus(cidade)}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Parser específico para Páginas Amarelas (estrutura pode mudar)
                empresas_encontradas = extrair_empresas_paginas_amarelas(soup, cidade, atividade)
                empresas.extend(empresas_encontradas)
            
            time.sleep(random.uniform(1, 2))  # Rate limiting aleatório
            
    except Exception as e:
        print(f"Erro ao buscar em Páginas Amarelas: {e}")
    
    return empresas


def buscar_google_places(cidade, atividade):
    """Busca empresas usando Google Places API (simulado por enquanto)"""
    # Se houver configuração de API, implementar chamada real aqui.
    # Por enquanto, não usamos fallback simulado — retornar lista vazia.
    # Em produção: usar chave em configuração/variável de ambiente e implementar consulta.
    api_key = None
    try:
        api_key = None  # substituir pela leitura de config se disponível
    except Exception:
        api_key = None

    if not api_key:
        print(f"Google Places não configurado — nenhum fallback. Pulando busca para: {atividade} em {cidade}")
        return []

    # Implementação futura com API key
    return []


def buscar_guia_mais(cidade, atividade):
    """Busca empresas no GuiaMais"""
    empresas = []
    
    try:
        termo = f"{atividade} {cidade}"
        url = f"https://www.guiamais.com.br/busca/{quote_plus(termo)}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            empresas_encontradas = extrair_empresas_guia_mais(soup, cidade, atividade)
            empresas.extend(empresas_encontradas)
            
    except Exception as e:
        print(f"Erro ao buscar no GuiaMais: {e}")
    
    return empresas


def extrair_empresas_paginas_amarelas(soup, cidade, atividade):
    """Extrai informações de empresas do HTML das Páginas Amarelas"""
    empresas = []
    
    try:
        # Seletores comuns para páginas de listagem
        # Nota: Estes seletores podem precisar ser ajustados conforme o site atual
        cards_empresa = soup.find_all(['div', 'article'], class_=re.compile(r'result|card|item|listing', re.I))
        
        for card in cards_empresa[:10]:  # Limitar a 10 resultados por página
            try:
                # Extrair nome da empresa
                nome_elem = card.find(['h1', 'h2', 'h3', 'h4'], class_=re.compile(r'name|title|empresa', re.I))
                if not nome_elem:
                    nome_elem = card.find('a', class_=re.compile(r'name|title', re.I))
                
                nome = nome_elem.get_text(strip=True) if nome_elem else "Empresa não identificada"
                
                # Extrair endereço
                endereco_elem = card.find(['div', 'span', 'p'], class_=re.compile(r'address|endereco|local', re.I))
                endereco = endereco_elem.get_text(strip=True) if endereco_elem else f"Endereço em {cidade}"
                
                # Extrair telefone / email com heurísticas: tel: mailto: e regex no texto
                telefone = None
                email = None
                # procurar links tel: e mailto:
                a_tags = card.find_all('a', href=True)
                for a in a_tags:
                    href = a['href']
                    if href.startswith('tel:') and not telefone:
                        telefone = href.split(':', 1)[1].strip()
                    if href.startswith('mailto:') and not email:
                        email = href.split(':', 1)[1].strip()

                # selecionar elementos que possam conter telefone/email (textos soltos)
                possible_text = ' '.join([t.get_text(' ', strip=True) for t in card.find_all(['div', 'span', 'p', 'li'])])

                # regex para telefone (brasileiro simples) e email
                if not telefone:
                    m_tel = re.search(r"(\(?\d{2}\)?\s?9?\d{4}[-\s]?\d{4})", possible_text)
                    if m_tel:
                        telefone = m_tel.group(1)
                if not email:
                    m_email = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", possible_text)
                    if m_email:
                        email = m_email.group(0)
                
                empresa = {
                    'cnpj': 'Não informado',
                    'razao_social': nome,
                    'nome_fantasia': nome,
                    'cidade': cidade.title(),
                    'uf': 'SP',  # Assumir SP
                    'atividade_principal': f"{atividade.title()} - {nome}",
                    'situacao': 'ATIVA',
                    'telefone': telefone,
                    'email': email,
                    'endereco_completo': endereco,
                    'fonte': 'Páginas Amarelas'
                }
                
                empresas.append(empresa)
                
            except Exception as e:
                print(f"Erro ao processar empresa individual: {e}")
                continue
                
    except Exception as e:
        print(f"Erro ao extrair empresas das Páginas Amarelas: {e}")
    
    return empresas


def extrair_empresas_guia_mais(soup, cidade, atividade):
    """Extrai informações de empresas do HTML do GuiaMais"""
    empresas = []
    
    try:
        # Seletores para GuiaMais
        cards_empresa = soup.find_all(['div', 'li'], class_=re.compile(r'result|item|card', re.I))
        
        for card in cards_empresa[:8]:  # Limitar resultados
            try:
                nome_elem = card.find(['h2', 'h3', 'a'], class_=re.compile(r'name|title', re.I))
                nome = nome_elem.get_text(strip=True) if nome_elem else f"{atividade.title()} em {cidade}"
                
                endereco_elem = card.find(['div', 'span'], class_=re.compile(r'address|endereco', re.I))
                endereco = endereco_elem.get_text(strip=True) if endereco_elem else f"{cidade}"
                # Extrair telefone/email usando heurísticas: tel/mailto e regex no texto do card
                telefone = None
                email = None
                a_tags = card.find_all('a', href=True)
                for a in a_tags:
                    href = a['href']
                    if href.startswith('tel:') and not telefone:
                        telefone = href.split(':', 1)[1].strip()
                    if href.startswith('mailto:') and not email:
                        email = href.split(':', 1)[1].strip()

                possible_text = ' '.join([t.get_text(' ', strip=True) for t in card.find_all(['div', 'span', 'p', 'li'])])
                if not telefone:
                    m_tel = re.search(r"(\(?\d{2}\)?\s?9?\d{4}[-\s]?\d{4})", possible_text)
                    if m_tel:
                        telefone = m_tel.group(1)
                if not email:
                    m_email = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", possible_text)
                    if m_email:
                        email = m_email.group(0)

                empresa = {
                    'cnpj': 'Não informado',
                    'razao_social': nome,
                    'nome_fantasia': nome,
                    'cidade': cidade.title(),
                    'uf': 'SP',
                    'atividade_principal': f"{atividade.title()}",
                    'situacao': 'ATIVA',
                    'endereco_completo': endereco,
                    'telefone': telefone,
                    'email': email,
                    'fonte': 'GuiaMais'
                }
                
                empresas.append(empresa)
                
            except Exception:
                continue
                
    except Exception as e:
        print(f"Erro ao extrair empresas do GuiaMais: {e}")
    
    return empresas


def mapear_termo_busca(atividade):
    """Mapeia atividades para termos de busca mais específicos"""
    mapeamento = {
        'restaurante': ['restaurante', 'comida', 'alimentação'],
        'supermercado': ['supermercado', 'mercado', 'hipermercado'],
        'farmacia': ['farmácia', 'drogaria', 'medicamentos'],
        'loja': ['loja', 'comércio', 'varejo'],
        'hotel': ['hotel', 'pousada', 'hospedagem'],
        'posto': ['posto de gasolina', 'combustível'],
        'academia': ['academia', 'ginástica', 'fitness'],
        'salao': ['salão de beleza', 'cabelereiro', 'estética'],
        'clinica': ['clínica', 'médico', 'consultório'],
        'industria': ['indústria', 'fábrica', 'manufatura'],
        'oficina': ['oficina', 'mecânica', 'auto center']
    }
    
    return mapeamento.get(atividade.lower(), [atividade])


def remover_duplicatas(empresas):
    """Remove empresas duplicadas da lista"""
    empresas_unicas = []
    nomes_vistos = set()
    
    for empresa in empresas:
        nome_key = empresa.get('razao_social', '').lower().strip()
        if nome_key and nome_key not in nomes_vistos:
            nomes_vistos.add(nome_key)
            empresas_unicas.append(empresa)
    
    return empresas_unicas


def is_trusted_company(empresa: dict) -> bool:
    """Determina se a empresa possui dados de contato suficientes para ser considerada confiável.

    Critérios mínimos:
    - CNPJ válido (14 dígitos) OU
    - Telefone informado OU
    - Email informado
    """
    if not empresa:
        return False

    cnpj = normalize_cnpj(empresa.get('cnpj', '') or '')
    telefone = (empresa.get('telefone') or '').strip()
    email = (empresa.get('email') or '').strip()

    if cnpj and len(cnpj) == 14 and cnpj.isdigit():
        return True

    if telefone and telefone.lower() != 'não informado' and telefone.lower() != 'nao informado':
        return True

    if email and email.lower() != 'não informado' and email.lower() != 'nao informado':
        return True

    return False

# Blueprint
busca_bp = Blueprint('busca_empresas', __name__, template_folder='templates')

@busca_bp.route('/busca-empresas')
def index():
    """Página inicial de busca de empresas"""
    return render_template('busca_empresas/index.html')

@busca_bp.route('/buscar-empresas', methods=['GET', 'POST'])
def buscar():
    """Formulário e processamento de busca"""
    
    if request.method == 'GET':
        return render_template('busca_empresas/buscar.html')
    
    # POST - processar busca
    cidade = request.form.get('cidade', '').strip()
    tipo_atividade = request.form.get('tipo_atividade', '').strip()
    
    if not cidade or not tipo_atividade:
        flash('Por favor, preencha cidade e tipo de atividade', 'error')
        return render_template('busca_empresas/buscar.html')
    
    # Buscar empresas via múltiplas fontes (web scraping + APIs)
    try:
        empresas = buscar_empresas_api(cidade, tipo_atividade)

        if not empresas:
            flash(f'Não foi possível localizar estabelecimentos/indústrias do tipo "{tipo_atividade}" em {cidade}. Tente termos mais específicos.', 'warning')
            return render_template('busca_empresas/buscar.html')

        # Salvar no banco
        termo_busca = f"{cidade} - {tipo_atividade}"
        # Salvar também uma exportação JSON no servidor para auditoria/uso posterior
        try:
            exports_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'static', 'exports')
            exports_dir = os.path.abspath(exports_dir)
            os.makedirs(exports_dir, exist_ok=True)
            filename = f"empresas_{cidade.replace(' ', '_')}_{tipo_atividade}.json"
            filepath = os.path.join(exports_dir, filename)
            empresas_serializaveis = []
            for e in empresas:
                empresas_serializaveis.append({
                    'cnpj': e.get('cnpj', 'Não informado'),
                    'razao_social': e.get('razao_social', 'Não informado'),
                    'nome_fantasia': e.get('nome_fantasia', 'Não informado'),
                    'atividade_principal': e.get('atividade_principal', 'Não informado'),
                    'cidade': e.get('cidade', cidade),
                    'uf': e.get('uf', 'Não informado'),
                    'telefone': e.get('telefone', 'Não informado'),
                    'email': e.get('email', 'Não informado'),
                    'endereco_completo': e.get('endereco_completo', 'Não informado'),
                    'fonte': e.get('fonte', 'Não informado')
                })
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({'cidade': cidade, 'tipo_atividade': tipo_atividade, 'empresas': empresas_serializaveis}, f, ensure_ascii=False, indent=2)
            export_file_url = url_for('static', filename=f'exports/{filename}')
        except Exception as e:
            print(f"Erro ao salvar exportação JSON no servidor: {e}")
            export_file_url = None
        empresas_salvas = []
        
        for empresa_data in empresas:
            # Verificar se já existe
            empresa_existente = EmpresaEncontrada.query.filter_by(cnpj=empresa_data['cnpj']).first()
            
            if not empresa_existente:
                # Criar nova empresa
                empresa = EmpresaEncontrada(
                    cnpj=empresa_data['cnpj'],
                    razao_social=empresa_data['razao_social'],
                    nome_fantasia=empresa_data.get('nome_fantasia'),
                    cep=empresa_data.get('cep'),
                    logradouro=empresa_data.get('logradouro'),
                    numero=empresa_data.get('numero'),
                    complemento=empresa_data.get('complemento'),
                    bairro=empresa_data.get('bairro'),
                    cidade=empresa_data.get('cidade'),
                    uf=empresa_data.get('uf'),
                    atividade_principal=empresa_data.get('atividade_principal'),
                    atividades_secundarias=json.dumps(empresa_data.get('atividades_secundarias', [])),
                    telefone=empresa_data.get('telefone'),
                    email=empresa_data.get('email'),
                    situacao=empresa_data.get('situacao'),
                    data_abertura=empresa_data.get('data_abertura'),
                    termo_busca=termo_busca
                )
                db.session.add(empresa)
                empresas_salvas.append(empresa)
            else:
                # Atualizar termo de busca
                empresa_existente.termo_busca = termo_busca
                empresa_existente.data_busca = datetime.utcnow()
                empresas_salvas.append(empresa_existente)
            # definir atributos transitórios para uso na template
            try:
                last = empresas_salvas[-1]
                setattr(last, 'fonte', empresa_data.get('fonte'))
                # marcar enriquecido se tiver CNPJ válido ou endereço completo
                cnpj_clean = normalize_cnpj(empresa_data.get('cnpj') or '')
                enriquecido = (cnpj_clean and len(cnpj_clean) == 14) or bool(empresa_data.get('endereco_completo'))
                setattr(last, 'enriquecido', enriquecido)
            except Exception:
                pass
        
        db.session.commit()

        flash(f'Encontradas {len(empresas_salvas)} empresas para "{tipo_atividade}" em {cidade}', 'success')

        return render_template('busca_empresas/resultados.html', 
                     empresas=empresas_salvas, 
                     cidade=cidade, 
                     tipo_atividade=tipo_atividade,
                     export_file_url=export_file_url)

    except Exception as e:
        flash(f'Erro ao buscar empresas: {str(e)}', 'error')
        return render_template('busca_empresas/buscar.html')


@busca_bp.route('/buscar-empresas/json', methods=['POST'])
def buscar_json():
    """Endpoint que recebe `cidade` e `tipo_atividade` e retorna JSON com empresas encontradas."""
    cidade = request.form.get('cidade', '').strip()
    tipo_atividade = request.form.get('tipo_atividade', '').strip()

    if not cidade or not tipo_atividade:
        return jsonify({'error': 'Por favor, preencha cidade e tipo de atividade'}), 400

    try:
        empresas = buscar_empresas_api(cidade, tipo_atividade)
        # Garantir estrutura serializável e campos mínimos
        empresas_serializaveis = []
        for e in empresas:
            empresas_serializaveis.append({
                'cnpj': e.get('cnpj', 'Não informado'),
                'razao_social': e.get('razao_social', 'Não informado'),
                'nome_fantasia': e.get('nome_fantasia', 'Não informado'),
                'atividade_principal': e.get('atividade_principal', 'Não informado'),
                'cidade': e.get('cidade', cidade),
                'uf': e.get('uf', 'Não informado'),
                'telefone': e.get('telefone', 'Não informado'),
                'email': e.get('email', 'Não informado'),
                'endereco_completo': e.get('endereco_completo', 'Não informado'),
                'fonte': e.get('fonte', 'Não informado')
            })

        # Salvar também no servidor para auditoria/uso posterior
        try:
            exports_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'static', 'exports')
            exports_dir = os.path.abspath(exports_dir)
            os.makedirs(exports_dir, exist_ok=True)
            filename = f"empresas_{cidade.replace(' ', '_')}_{tipo_atividade}.json"
            filepath = os.path.join(exports_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({'cidade': cidade, 'tipo_atividade': tipo_atividade, 'empresas': empresas_serializaveis}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao salvar exportação JSON no servidor: {e}")

        if not empresas_serializaveis:
            return jsonify({'error': f'Não foi possível localizar estabelecimentos/indústrias do tipo "{tipo_atividade}" em {cidade}.'}), 404

        return jsonify({'cidade': cidade, 'tipo_atividade': tipo_atividade, 'empresas': empresas_serializaveis})

    except Exception as e:
        return jsonify({'error': f'Erro ao buscar empresas: {str(e)}'}), 500

@busca_bp.route('/historico-buscas')
def historico():
    """Histórico de buscas realizadas"""
    # Buscar empresas agrupadas por termo de busca
    page = request.args.get('page', 1, type=int)
    
    empresas = EmpresaEncontrada.query\
        .order_by(EmpresaEncontrada.data_busca.desc())\
        .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('busca_empresas/historico.html', empresas=empresas)

@busca_bp.route('/empresa/<int:empresa_id>')
def detalhes_empresa(empresa_id):
    """Detalhes de uma empresa específica"""
    empresa = EmpresaEncontrada.query.get_or_404(empresa_id)
    return render_template('busca_empresas/detalhes.html', empresa=empresa)

@busca_bp.route('/api/empresas/buscar')
def api_buscar():
    """API para busca ajax"""
    cidade = request.args.get('cidade', '').strip()
    tipo_atividade = request.args.get('tipo_atividade', '').strip()
    
    if not cidade or not tipo_atividade:
        return jsonify({'error': 'Parâmetros obrigatórios: cidade e tipo_atividade'}), 400

    try:
        empresas = buscar_empresas_api(cidade, tipo_atividade)
        return jsonify({'empresas': empresas, 'total': len(empresas)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def buscar_empresas_api(cidade, tipo_atividade):
    """
    Busca empresas por cidade e atividade usando múltiplas fontes
    
    Args:
        cidade (str): Nome da cidade
        tipo_atividade (str): Tipo de atividade da empresa
    
    Returns:
        list: Lista de empresas encontradas
    """
    
    # Se for CNPJ, usar busca específica
    possible_cnpj = (cidade or '') + ' ' + (tipo_atividade or '')
    if is_cnpj(possible_cnpj):
        try:
            empresa = buscar_por_cnpj(possible_cnpj)
            return [empresa] if empresa else []
        except Exception:
            pass
    
    # Busca por região e atividade usando web scraping
    empresas = []
    
    try:
        # Estratégia 0: APIs especializadas (Listacnae / Dados.gov.br) - habilitar se configuradas
        try:
            empresas_api = buscar_api_externa(cidade, tipo_atividade)
            if empresas_api:
                empresas.extend(empresas_api)
        except Exception as e:
            print(f"Erro na busca por APIs externas (ignorada): {e}")

        # Estratégia 1: Páginas Amarelas (reativada com tratamento)
        try:
            print(f"Buscando em Páginas Amarelas: {tipo_atividade} em {cidade}")
            empresas_pa = buscar_paginas_amarelas(cidade, tipo_atividade)
            if empresas_pa:
                empresas.extend(empresas_pa)
            time.sleep(1)
        except Exception as e:
            print(f"Falha na busca Páginas Amarelas (ignorada): {e}")
        
        # Estratégia 2: Google Maps (simulado - usar API quando disponível)
        print(f"Buscando via Google Places API: {tipo_atividade} em {cidade}")
        empresas_google = buscar_google_places(cidade, tipo_atividade)
        empresas.extend(empresas_google)
        
        # Estratégia 3: Guia Mais (fonte adicional)
        print(f"Buscando em Guia Mais: {tipo_atividade} em {cidade}")
        empresas_guia = buscar_guia_mais(cidade, tipo_atividade)
        empresas.extend(empresas_guia)
        time.sleep(1)  # Rate limiting

        # Estratégia 4: Dados Abertos locais (pasta data_abertos/ com CSV/JSON)
        try:
            empresas_abertos = buscar_dados_abertos(cidade, tipo_atividade)
            if empresas_abertos:
                empresas.extend(empresas_abertos)
        except Exception as e:
            print(f"Erro ao buscar dados abertos: {e}")
        
        # Estratégia 5: Overpass (OpenStreetMap)
        try:
            print(f"Buscando via Overpass: {tipo_atividade} em {cidade}")
            empresas_overpass = buscar_overpass(cidade, tipo_atividade, limit=200)
            if empresas_overpass:
                empresas.extend(empresas_overpass)
        except Exception as e:
            print(f"Erro ao buscar via Overpass: {e}")
        
    except Exception as e:
        print(f"Erro na busca por scraping: {e}")
    
    # Remover duplicatas por CNPJ (se disponível) ou nome
    empresas_unicas = remover_duplicatas(empresas)

    # Enriquecer empresas que possuam CNPJ válido via BrasilAPI
    empresas_enriquecidas = []
    for e in empresas_unicas:
        cnpj = normalize_cnpj(e.get('cnpj', '') or '')
        if cnpj and len(cnpj) == 14:
            try:
                brasil = buscar_por_cnpj(cnpj)
                if brasil:
                    # Mesclar: priorizar dados da BrasilAPI quando disponíveis
                    merged = {**e, **{k: v for k, v in brasil.items() if v}}
                    empresas_enriquecidas.append(merged)
                    continue
            except Exception as ex:
                print(f"Erro enriquecimento BrasilAPI para {cnpj}: {ex}")

        empresas_enriquecidas.append(e)

    # Filtrar apenas empresas com dados de contato confiáveis
    empresas_trusted = [e for e in empresas_enriquecidas if is_trusted_company(e)]

    print(f"Total de empresas encontradas: {len(empresas_unicas)} (após enriquecimento confiáveis: {len(empresas_trusted)})")
    return empresas_trusted


def buscar_dados_abertos(cidade, atividade):
    """Procura por arquivos CSV/JSON em `data_abertos/` no workspace e retorna correspondências.

    Formato esperado (flexível): cada registro deve ter pelo menos nome/razao_social e, se possível, cnpj, telefone, endereco.
    """
    resultados = []
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data_abertos'))
    if not os.path.exists(base_dir):
        return resultados

    for fname in os.listdir(base_dir):
        path = os.path.join(base_dir, fname)
        try:
            if fname.lower().endswith('.csv'):
                import csv
                with open(path, encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        cidade_row = (row.get('cidade') or row.get('municipio') or '').strip().lower()
                        if cidade.lower() in cidade_row and atividade.lower() in ' '.join(row.values()).lower():
                            resultados.append({
                                'cnpj': row.get('cnpj') or 'Não informado',
                                'razao_social': row.get('razao_social') or row.get('nome') or 'Não informado',
                                'nome_fantasia': row.get('nome_fantasia') or 'Não informado',
                                'cidade': row.get('cidade') or 'Não informado',
                                'uf': row.get('uf') or 'Não informado',
                                'telefone': row.get('telefone') or 'Não informado',
                                'email': row.get('email') or 'Não informado',
                                'endereco_completo': row.get('endereco') or 'Não informado',
                                'fonte': f'Dados Abertos ({fname})'
                            })
            elif fname.lower().endswith('.json'):
                with open(path, encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for row in data:
                            cidade_row = (row.get('cidade') or row.get('municipio') or '').strip().lower()
                            if cidade.lower() in cidade_row and atividade.lower() in ' '.join([str(v) for v in row.values()]).lower():
                                resultados.append({
                                    'cnpj': row.get('cnpj') or 'Não informado',
                                    'razao_social': row.get('razao_social') or row.get('nome') or 'Não informado',
                                    'nome_fantasia': row.get('nome_fantasia') or 'Não informado',
                                    'cidade': row.get('cidade') or 'Não informado',
                                    'uf': row.get('uf') or 'Não informado',
                                    'telefone': row.get('telefone') or 'Não informado',
                                    'email': row.get('email') or 'Não informado',
                                    'endereco_completo': row.get('endereco') or 'Não informado',
                                    'fonte': f'Dados Abertos ({fname})'
                                })
        except Exception as e:
            print(f"Erro lendo dados abertos {path}: {e}")

    return resultados


def buscar_api_externa(cidade: str, atividade: str) -> list:
    """Adaptador genérico para chamadas a APIs externas configuráveis.

    Atualmente implementa dois adaptadores mínimos:
    - Listacnae (se `LISTACNAE_BASE` estiver definido)
    - Dados.gov.br (se `DADOS_GOV_BASE` estiver definido)

    A configuração é feita por variáveis de ambiente opcionais. Se não houver
    configuração, a função retorna lista vazia.
    """
    resultados = []

    # Leitura de configurações via variáveis de ambiente (opcional)
    LISTACNAE_BASE = os.environ.get('LISTACNAE_BASE')
    LISTACNAE_KEY = os.environ.get('LISTACNAE_KEY')
    DADOS_GOV_BASE = os.environ.get('DADOS_GOV_BASE')

    # Tentar Listacnae primeiro (mais direcionado)
    if LISTACNAE_BASE:
        try:
            r = buscar_listacnae(LISTACNAE_BASE, LISTACNAE_KEY, cidade, atividade)
            if r:
                resultados.extend(r)
        except Exception as e:
            print(f"Erro ao consultar Listacnae: {e}")

    # Em seguida tentar Dados.gov.br (se houver base/endpoint configurado)
    if DADOS_GOV_BASE:
        try:
            r2 = buscar_dados_gov(DADOS_GOV_BASE, cidade, atividade)
            if r2:
                resultados.extend(r2)
        except Exception as e:
            print(f"Erro ao consultar Dados.gov.br: {e}")

    return resultados


def buscar_listacnae(base_url: str, api_key: str, cidade: str, atividade: str) -> list:
    """Adapter mínimo para Listacnae API. Retorna lista de empresas no formato do sistema.

    Documentação/URL e key devem ser colocadas em `LISTACNAE_BASE` e `LISTACNAE_KEY`.
    Esta função tenta montar uma query simples e mapear campos básicos.
    """
    empresas = []
    try:
        params = {
            'cidade': cidade,
            'q': atividade,
            'limit': 50
        }
        headers = {'User-Agent': 'ERP-JSP-bot/1.0'}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        url = base_url.rstrip('/') + '/search'
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # Assumir que `data` é uma lista de objetos com pelo menos `name` e `cidade`
        for item in (data or []):
            empresas.append({
                'cnpj': item.get('cnpj') or 'Não informado',
                'razao_social': item.get('razao_social') or item.get('name') or 'Não informado',
                'nome_fantasia': item.get('nome_fantasia') or item.get('name') or 'Não informado',
                'cidade': item.get('cidade') or cidade,
                'uf': item.get('uf') or 'Não informado',
                'atividade_principal': item.get('atividade') or atividade,
                'telefone': item.get('telefone'),
                'email': item.get('email'),
                'endereco_completo': item.get('endereco') or 'Não informado',
                'fonte': 'Listacnae'
            })

    except Exception as e:
        print(f"Erro no adapter Listacnae: {e}")

    return empresas


def buscar_dados_gov(base_url: str, cidade: str, atividade: str) -> list:
    """Adapter mínimo para endpoints do Dados.gov.br que retornen listas públicas.

    `base_url` deve ser um endpoint público que aceita `cidade` e `q` como parâmetros.
    """
    empresas = []
    try:
        # Se `base_url` for um CSV (URL ou caminho local), faça download/índice e consulte SQLite
        if isinstance(base_url, str) and base_url.lower().endswith('.csv'):
            sqlite_path = _ensure_csv_indexed(base_url)
            if sqlite_path:
                rows = _query_dados_gov_sqlite(sqlite_path, cidade, atividade)
                for item in rows:
                    empresas.append({
                        'cnpj': item.get('cnpj') or item.get('CNPJ') or 'Não informado',
                        'razao_social': item.get('razao_social') or item.get('razao') or item.get('nome') or 'Não informado',
                        'nome_fantasia': item.get('nome_fantasia') or item.get('nome') or 'Não informado',
                        'cidade': item.get('cidade') or item.get('municipio') or cidade,
                        'uf': item.get('uf') or item.get('estado') or 'Não informado',
                        'atividade_principal': item.get('atividade') or atividade,
                        'telefone': item.get('telefone') or item.get('fone') or 'Não informado',
                        'email': item.get('email') or 'Não informado',
                        'endereco_completo': item.get('endereco') or 'Não informado',
                        'fonte': f'Dados.gov.br (CSV)'
                    })
                return empresas

        # Caso contrário, tentar tratar `base_url` como endpoint que retorne JSON com `results`
        params = {'cidade': cidade, 'q': atividade, 'limit': 100}
        headers = {'User-Agent': 'ERP-JSP-bot/1.0'}
        url = base_url.rstrip('/') + '/search'
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        for item in (data.get('results') if isinstance(data, dict) else data or []):
            empresas.append({
                'cnpj': item.get('cnpj') or 'Não informado',
                'razao_social': item.get('razao') or item.get('razao_social') or item.get('nome') or 'Não informado',
                'nome_fantasia': item.get('nome_fantasia') or item.get('nome') or 'Não informado',
                'cidade': item.get('cidade') or cidade,
                'uf': item.get('uf') or 'Não informado',
                'atividade_principal': item.get('atividade') or atividade,
                'telefone': item.get('telefone') or item.get('fone'),
                'email': item.get('email'),
                'endereco_completo': item.get('endereco') or 'Não informado',
                'fonte': 'Dados.gov.br'
            })

    except Exception as e:
        print(f"Erro no adapter Dados.gov.br: {e}")

    return empresas


def _ensure_csv_indexed(csv_source: str) -> str:
    """Garante que o CSV seja baixado (se URL) e indexado em um SQLite local.

    Retorna o caminho para o arquivo sqlite criado, ou None em caso de falha.
    """
    try:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'data_abertos'))
        os.makedirs(base_dir, exist_ok=True)

        # Determinar local do CSV
        if csv_source.startswith('http://') or csv_source.startswith('https://'):
            csv_fname = os.path.join(base_dir, 'dados_gov_remote.csv')
            # Baixar apenas se não existir ou estiver desatualizado (simples)
            if not os.path.exists(csv_fname):
                headers = {'User-Agent': 'ERP-JSP-bot/1.0'}
                r = requests.get(csv_source, headers=headers, timeout=30)
                r.raise_for_status()
                with open(csv_fname, 'wb') as f:
                    f.write(r.content)
        else:
            # caminho local
            csv_fname = os.path.abspath(csv_source)
            if not os.path.exists(csv_fname):
                return None

        # Criar sqlite path
        sqlite_path = os.path.join(base_dir, 'dados_gov_cache.sqlite')
        conn = sqlite3.connect(sqlite_path)
        cur = conn.cursor()

        # Ler CSV e criar tabela
        with open(csv_fname, encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            headers = [h.strip().replace(' ', '_') for h in reader.fieldnames if h]

            # Criar tabela dinâmica
            cols = ', '.join([f'"{h}" TEXT' for h in headers])
            cur.execute('DROP TABLE IF EXISTS dados_gov')
            cur.execute(f'CREATE TABLE dados_gov ({cols})')

            insert_sql = f"INSERT INTO dados_gov ({', '.join([f'"{h}"' for h in headers])}) VALUES ({', '.join(['?']*len(headers))})"
            batch = []
            for row in reader:
                values = [row.get(h, '') for h in reader.fieldnames]
                batch.append(values)
                if len(batch) >= 500:
                    cur.executemany(insert_sql, batch)
                    batch = []
            if batch:
                cur.executemany(insert_sql, batch)

        conn.commit()
        conn.close()
        return sqlite_path
    except Exception as e:
        print(f"Erro ao indexar CSV para Dados.gov.br: {e}")
        return None


def _query_dados_gov_sqlite(sqlite_path: str, cidade: str, atividade: str, limit: int = 200) -> list:
    """Consulta a base sqlite criada a partir do CSV e retorna dicionários correspondentes."""
    results = []
    try:
        conn = sqlite3.connect(sqlite_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Obter colunas
        cur.execute("PRAGMA table_info(dados_gov)")
        cols = [r[1] for r in cur.fetchall()]

        # Construir WHERE dinâmico (procurar cidade em colunas comuns e atividade em todo texto concatenado)
        cidade_like = f"%{cidade.lower()}%"
        atividade_like = f"%{atividade.lower()}%"

        cidade_clauses = []
        for c in cols:
            if c.lower() in ('cidade', 'municipio', 'municipio_nome'):
                cidade_clauses.append(f"lower(\"{c}\") LIKE ?")

        if not cidade_clauses:
            # fallback: procurar cidade em qualquer coluna
            cidade_clauses = [f"lower(\"{c}\") LIKE ?" for c in cols]

        # atividade: procurar no concatenado de colunas
        concat_cols = " || ' ' || ".join([f"ifnull(\"{c}\", '')" for c in cols])

        sql = f"SELECT * FROM dados_gov WHERE ({' OR '.join(cidade_clauses)}) AND lower({concat_cols}) LIKE ? LIMIT {limit}"
        params = [cidade_like] * len(cidade_clauses)
        params.append(atividade_like)

        cur.execute(sql, params)
        rows = cur.fetchall()
        for r in rows:
            results.append({k: r[k] for k in r.keys()})

        conn.close()
    except Exception as e:
        print(f"Erro ao consultar sqlite Dados.gov.br: {e}")

    return results


def buscar_overpass(cidade: str, atividade: str, limit: int = 200) -> list:
    """Consulta a Overpass API para POIs comerciais/industriais dentro do bbox do município.

    Usa Nominatim para obter a bbox do município e em seguida executa query Overpass.
    Retorna lista de dicionários com campos mapeados para o formato do sistema.
    """
    resultados = []
    try:
        # Obter bbox via Nominatim
        nominatim_url = 'https://nominatim.openstreetmap.org/search'
        params = {'q': cidade + ', Brazil', 'format': 'json', 'limit': 1}
        headers = {'User-Agent': 'ERP-JSP-bot/1.0 (+https://example.com)'}
        r = requests.get(nominatim_url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        hits = r.json()
        if not hits:
            return resultados

        hit = hits[0]
        # boundingbox: [south, north, west, east]
        bbox = hit.get('boundingbox')
        if not bbox or len(bbox) != 4:
            return resultados

        south, north, west, east = bbox[0], bbox[1], bbox[2], bbox[3]
        bbox_str = f"{south},{west},{north},{east}"

        # Montar query Overpass — pesquisar por shop, landuse=industrial, craft, office, amenity=market
        overpass_query = f"""
[out:json][timeout:60];
(
  node["shop"]({bbox_str});
  way["shop"]({bbox_str});
  relation["shop"]({bbox_str});

  node["landuse"="industrial"]({bbox_str});
  way["landuse"="industrial"]({bbox_str});
  relation["landuse"="industrial"]({bbox_str});

  node["craft"]({bbox_str});
  way["craft"]({bbox_str});
  relation["craft"]({bbox_str});

  node["office"]({bbox_str});
  way["office"]({bbox_str});
  relation["office"]({bbox_str});

  node["amenity"="market"]({bbox_str});
  way["amenity"="market"]({bbox_str});
  relation["amenity"="market"]({bbox_str});
);
out center {limit};
"""

        overpass_url = 'https://overpass-api.de/api/interpreter'
        resp = requests.post(overpass_url, data={'data': overpass_query}, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        elements = data.get('elements', [])
        for el in elements:
            tags = el.get('tags', {}) or {}
            name = tags.get('name') or tags.get('operator') or tags.get('brand') or 'Não informado'
            telefone = tags.get('phone') or tags.get('contact:phone') or tags.get('telephone') or 'Não informado'
            email = tags.get('email') or tags.get('contact:email') or 'Não informado'
            city = tags.get('addr:city') or cidade
            uf = tags.get('addr:state') or 'Não informado'
            endereco_parts = []
            if tags.get('addr:street'):
                endereco_parts.append(tags.get('addr:street'))
            if tags.get('addr:housenumber'):
                endereco_parts.append(tags.get('addr:housenumber'))
            if tags.get('addr:postcode'):
                endereco_parts.append(tags.get('addr:postcode'))
            endereco = ', '.join(endereco_parts) if endereco_parts else (tags.get('address') or 'Não informado')

            atividade_tag = tags.get('shop') or tags.get('craft') or tags.get('industrial') or tags.get('amenity') or 'Não informado'

            # Coordenadas
            lat = None
            lon = None
            if 'center' in el:
                lat = el['center'].get('lat')
                lon = el['center'].get('lon')
            else:
                lat = el.get('lat')
                lon = el.get('lon')

            empresa = {
                'cnpj': 'Não informado',
                'razao_social': name,
                'nome_fantasia': name,
                'cidade': city,
                'uf': uf,
                'atividade_principal': atividade_tag,
                'situacao': 'ATIVA',
                'telefone': telefone,
                'email': email,
                'endereco_completo': endereco,
                'fonte': 'Overpass',
                'osm_id': el.get('id'),
                'osm_type': el.get('type'),
                'lat': lat,
                'lon': lon
            }
            resultados.append(empresa)

    except Exception as e:
        print(f"Erro na consulta Overpass: {e}")

    return resultados


def normalize_cnpj(value: str) -> str:
    """Remove qualquer formatação e retorna somente dígitos."""
    if not value:
        return ''
    return re.sub(r"\D", "", value)


def is_cnpj(value: str) -> bool:
    """Detecta se a string contém um possível CNPJ (14 dígitos)."""
    cleaned = normalize_cnpj(value)
    return len(cleaned) == 14 and cleaned.isdigit()


def buscar_por_cnpj(valor_cnpj: str):
    """Consulta o BrasilAPI para obter dados do CNPJ.

    Retorna um dicionário no mesmo formato esperado por `buscar_empresas_api`.
    """
    cnpj = normalize_cnpj(valor_cnpj)
    if not cnpj:
        return None

    # Check cache first
    cached = _cache_get(cnpj)
    if cached:
        data = cached
    else:
        url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
        try:
            resp = http_get_with_retries(url, retries=3, backoff=0.5, timeout=8)
            if resp.status_code == 404:
                return None
            data = resp.json()
            _cache_set(cnpj, data)
        except Exception as e:
            print(f"Erro ao consultar BrasilAPI para CNPJ {cnpj}: {e}")
            return None

    # Mapear atividade principal a partir dos campos da BrasilAPI
    atividade_principal = ""
    if data.get('cnae_fiscal') and data.get('cnae_fiscal_descricao'):
        atividade_principal = f"{data['cnae_fiscal']} - {data['cnae_fiscal_descricao']}"

    # Mapear atividades secundárias
    atividades_sec_format = []
    cnaes_sec = data.get('cnaes_secundarios', []) or []
    for cnae in cnaes_sec:
        if isinstance(cnae, dict) and cnae.get('codigo') and cnae.get('descricao'):
            atividades_sec_format.append(f"{cnae['codigo']} - {cnae['descricao']}")

    # Mapear telefone (campo pode variar entre versões da API)
    telefone = None
    for key in ('ddd_telefone_1', 'ddd_telefone1', 'telefone', 'telefones'):
        val = data.get(key)
        if val:
            telefone = val
            break
    if telefone and isinstance(telefone, str):
        just_digits = re.sub(r"\D", "", telefone)
        if len(just_digits) >= 10:
            ddd = just_digits[:2]
            if len(just_digits) == 10:
                num = f"{just_digits[2:6]}-{just_digits[6:]}"
            else:
                num = f"{just_digits[2:7]}-{just_digits[7:]}"
            telefone = f"({ddd}) {num}"

    # Mapear situação cadastral
    situacao = "ATIVA" if data.get('situacao_cadastral') == 2 or data.get('situacao_cadastral') == '2' else data.get('descricao_situacao_cadastral', 'INATIVA')

    empresa = {
        'cnpj': data.get('cnpj'),
        'razao_social': data.get('razao_social'),
        'nome_fantasia': data.get('nome_fantasia'),
        'cep': data.get('cep'),
        'logradouro': data.get('logradouro'),
        'numero': data.get('numero'),
        'complemento': data.get('complemento'),
        'bairro': data.get('bairro'),
        'cidade': data.get('municipio') or data.get('municipio_nome') or data.get('cidade'),
        'uf': data.get('uf'),
        'atividade_principal': atividade_principal,
        'atividades_secundarias': atividades_sec_format,
        'telefone': telefone,
        'email': data.get('email'),
        'situacao': situacao,
        'data_abertura': data.get('data_inicio_atividade') or data.get('data_abertura')
    }

    return empresa

def buscar_via_brasil_api(cidade, tipo_atividade):
    """Placeholder: BrasilAPI NÃO fornece busca por cidade+atividade.

    Esta função não retorna dados fictícios quando o modo 'apenas API real' está ativo.
    Para buscas por CNPJ use `buscar_por_cnpj()`.
    """
    return []

def buscar_dados_exemplo(cidade, tipo_atividade):
    """Fallback com dados de exemplo"""
    return [{
        'cnpj': '12.345.678/0001-90',
        'razao_social': f'{tipo_atividade.title()} {cidade.title()} Exemplo LTDA',
        'nome_fantasia': f'{tipo_atividade.title()} do Centro',
        'cidade': cidade.title(),
        'uf': 'SP',
        'atividade_principal': f'{tipo_atividade.title()} - Atividade Principal',
        'situacao': 'ATIVA',
        'telefone': '(11) 99999-9999',
        'email': f'contato@{tipo_atividade.lower()}.com.br'
    }]