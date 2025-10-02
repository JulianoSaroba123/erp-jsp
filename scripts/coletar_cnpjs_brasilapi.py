"""
Script: coletar_cnpjs_brasilapi.py
- Consulta a BrasilAPI para uma lista de CNPJs
- Extrai campos relevantes e salva em Excel

Como usar:
python scripts\coletar_cnpjs_brasilapi.py

Instalação de dependências (se necessário):
pip install requests pandas openpyxl
"""

import requests
import pandas as pd
import time
from typing import List, Dict

BRASILAPI_URL = "https://brasilapi.com.br/api/cnpj/v1/{}"


def consultar_cnpj(cnpj: str) -> Dict[str, str]:
    """Faz requisição GET para BrasilAPI e retorna dicionário com campos desejados.
    Em caso de erro, retorna um dicionário com valores "Não informado" e uma chave "_erro" com a mensagem.
    """
    url = BRASILAPI_URL.format(cnpj)
    try:
        resp = requests.get(url, timeout=10)
    except requests.RequestException as e:
        # Erro de conexão
        return {
            'cnpj': cnpj,
            'razao_social': 'Não informado',
            'nome_fantasia': 'Não informado',
            'descricao_atividade_principal': 'Não informado',
            'municipio': 'Não informado',
            'uf': 'Não informado',
            'telefone': 'Não informado',
            'email': 'Não informado',
            'data_inicio_atividade': 'Não informado',
            '_erro': f'Erro de conexão: {e}'
        }

    if resp.status_code == 200:
        try:
            data = resp.json()
        except ValueError:
            return {
                'cnpj': cnpj,
                'razao_social': 'Não informado',
                'nome_fantasia': 'Não informado',
                'descricao_atividade_principal': 'Não informado',
                'municipio': 'Não informado',
                'uf': 'Não informado',
                'telefone': 'Não informado',
                'email': 'Não informado',
                'data_inicio_atividade': 'Não informado',
                '_erro': 'Resposta inválida JSON'
            }

        # Extrair campos com fallback para 'Não informado'
        razao_social = data.get('razao_social') or data.get('razao_social') or 'Não informado'
        nome_fantasia = data.get('nome_fantasia') or 'Não informado'

        # Atividade principal pode estar em estrutura: 'atividade_principal': {'code': '47.11-3', 'text': 'Comércio varejista de mercadorias'}
        atividade_principal = data.get('atividade_principal') or data.get('atividade_principal') or {}
        descricao_atividade_principal = 'Não informado'
        if isinstance(atividade_principal, dict):
            descricao_atividade_principal = atividade_principal.get('text') or atividade_principal.get('descricao') or atividade_principal.get('descricao_secundaria') or 'Não informado'
        elif isinstance(atividade_principal, list) and len(atividade_principal) > 0:
            # Alguns endpoints retornam lista
            primeiro = atividade_principal[0]
            descricao_atividade_principal = primeiro.get('text') or primeiro.get('descricao') or 'Não informado'

        municipio = data.get('municipio') or data.get('municipio_descricao') or 'Não informado'
        uf = data.get('uf') or data.get('estado') or 'Não informado'

        telefone = data.get('telefone') or data.get('ddd_telefone_1') or data.get('telefone1') or 'Não informado'

        # Email pode vir em diferentes campos
        email = data.get('email') or data.get('emails') or 'Não informado'
        if isinstance(email, list):
            email = email[0] if email else 'Não informado'

        data_inicio_atividade = data.get('data_inicio_atividade') or data.get('abertura') or 'Não informado'

        return {
            'cnpj': data.get('cnpj') or cnpj,
            'razao_social': razao_social,
            'nome_fantasia': nome_fantasia,
            'descricao_atividade_principal': descricao_atividade_principal,
            'municipio': municipio,
            'uf': uf,
            'telefone': telefone,
            'email': email,
            'data_inicio_atividade': data_inicio_atividade
        }

    elif resp.status_code == 404:
        # CNPJ não encontrado
        return {
            'cnpj': cnpj,
            'razao_social': 'Não informado',
            'nome_fantasia': 'Não informado',
            'descricao_atividade_principal': 'Não informado',
            'municipio': 'Não informado',
            'uf': 'Não informado',
            'telefone': 'Não informado',
            'email': 'Não informado',
            'data_inicio_atividade': 'Não informado',
            '_erro': 'CNPJ não encontrado'
        }
    else:
        # Outros erros HTTP
        return {
            'cnpj': cnpj,
            'razao_social': 'Não informado',
            'nome_fantasia': 'Não informado',
            'descricao_atividade_principal': 'Não informado',
            'municipio': 'Não informado',
            'uf': 'Não informado',
            'telefone': 'Não informado',
            'email': 'Não informado',
            'data_inicio_atividade': 'Não informado',
            '_erro': f'HTTP {resp.status_code}'
        }


def coletar_lista(cnpjs: List[str]) -> List[Dict[str, str]]:
    """Itera sobre lista de CNPJs e retorna lista de dicionários com dados.
    Pausa entre requisições para não sobrecarregar a API (rate limit friendly).
    """
    resultados = []
    for cnpj in cnpjs:
        c = cnpj.strip()
        if not c:
            continue
        print(f"Consultando CNPJ: {c}")
        res = consultar_cnpj(c)
        resultados.append(res)
        # Pausa curta para evitar throttling
        time.sleep(0.5)
    return resultados


def salvar_excel(lista: List[Dict[str, str]], caminho: str = 'empresas_coletadas.xlsx') -> None:
    """Salva a lista de dicionários em um arquivo Excel utilizando pandas/openpyxl"""
    df = pd.DataFrame(lista)
    # Garantir ordem de colunas desejada
    cols = ['cnpj', 'razao_social', 'nome_fantasia', 'descricao_atividade_principal', 'municipio', 'uf', 'telefone', 'email', 'data_inicio_atividade', '_erro']
    # Adicionar colunas faltantes
    for c in cols:
        if c not in df.columns:
            df[c] = 'Não informado'
    df = df[cols]
    df.to_excel(caminho, index=False)
    print(f"Salvo: {caminho}")


if __name__ == '__main__':
    # Exemplo de CNPJs. Substitua por sua lista real ou leia de arquivo.
    exemplo = [
        '27865757000102',  # Exemplo real
        '00000000000191',  # CNPJ da Receita (exemplo)
        '11111111000191',  # Provavelmente inválido
    ]

    results = coletar_lista(exemplo)
    salvar_excel(results)
