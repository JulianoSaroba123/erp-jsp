# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Modelo de Prospecção
===================================

Módulo de modelagem para Prospeção de Clientes.

Este módulo define a estrutura de dados para armazenar leads
capturados a partir de pesquisas por CNAE, cidade e CNPJ. Ele também
inclui uma função utilitária que demonstra como consultar uma API
externa para obter empresas com base em filtros informados.

Autor: JSP Soluções
Data: 2025
"""

from app.extensoes import db
from datetime import datetime, date
from flask import current_app
import requests
from typing import List, Dict, Optional


class Prospect(db.Model):
    """Modelo de lead/prospecto armazenado localmente.

    Este modelo representa uma empresa prospectada. Ele pode ser
    armazenado para histórico ou importado posteriormente como
    cliente efetivo. Os campos cobrem as informações básicas
    retornadas por APIs externas de consulta de empresas.
    """

    __tablename__ = "prospects"

    id = db.Column(db.Integer, primary_key=True)
    cnpj = db.Column(db.String(18), unique=True, nullable=False, index=True)
    razao_social = db.Column(db.String(200), nullable=False)
    nome_fantasia = db.Column(db.String(200))
    cnae = db.Column(db.String(20))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    telefone = db.Column(db.String(25))
    email = db.Column(db.String(120))
    
    # Status do prospect
    status = db.Column(db.String(20), default='ativo')  # ativo, convertido, inativo
    observacoes = db.Column(db.Text)
    
    # Controle de origem
    origem = db.Column(db.String(50), default='busca_cnae')  # busca_cnae, manual, importacao
    
    # Timestamps
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __repr__(self) -> str:
        return f"<Prospect {self.cnpj} - {self.razao_social}>"
    
    def to_dict(self):
        """Converte o prospect para dicionário"""
        return {
            'id': self.id,
            'cnpj': self.cnpj,
            'razao_social': self.razao_social,
            'nome_fantasia': self.nome_fantasia,
            'cnae': self.cnae,
            'cidade': self.cidade,
            'estado': self.estado,
            'telefone': self.telefone,
            'email': self.email,
            'status': self.status,
            'observacoes': self.observacoes,
            'origem': self.origem,
            'criado_em': self.criado_em,
            'atualizado_em': self.atualizado_em
        }
    
    @classmethod
    def buscar_por_cnpj(cls, cnpj):
        """Busca prospect por CNPJ"""
        return cls.query.filter_by(cnpj=cnpj, ativo=True).first()
    
    @classmethod
    def listar_ativos(cls):
        """Lista todos os prospects ativos"""
        return cls.query.filter_by(ativo=True, status='ativo').order_by(cls.criado_em.desc()).all()


def buscar_empresas(
    cnpj: Optional[str] = None,
    cnae: Optional[str] = None,
    cidade: Optional[str] = None,
    estado: Optional[str] = None,
) -> List[Dict[str, str]]:
    """
    Busca empresas utilizando APIs gratuitas (ReceitaWS e BrasilAPI).

    IMPORTANTE: As APIs gratuitas apenas permitem consulta por CNPJ específico.
    Para busca por CNAE, cidade ou estado, seria necessária uma API paga.

    :param cnpj: Número do CNPJ a ser consultado (obrigatório para APIs gratuitas).
    :param cnae: Código CNAE (não suportado pelas APIs gratuitas).
    :param cidade: Nome da cidade (não suportado pelas APIs gratuitas).
    :param estado: Sigla do estado (não suportado pelas APIs gratuitas).
    :return: Lista de dicionários representando empresas encontradas.
    """
    
    current_app.logger.info(f"Busca iniciada - CNPJ: {cnpj}, CNAE: {cnae}, Cidade: {cidade}, Estado: {estado}")
    
    # Se CNPJ não foi informado, retorna lista vazia
    if not cnpj:
        current_app.logger.info("Busca por empresa requer CNPJ para APIs gratuitas")
        return []
    
    # Limpa o CNPJ (remove pontos, barras e hífens)
    cnpj_limpo = cnpj.replace('.', '').replace('/', '').replace('-', '').strip()
    current_app.logger.info(f"CNPJ limpo para busca: {cnpj_limpo}")
    
    # Valida se o CNPJ tem 14 dígitos
    if len(cnpj_limpo) != 14 or not cnpj_limpo.isdigit():
        current_app.logger.warning(f"CNPJ inválido fornecido: {cnpj} (limpo: {cnpj_limpo})")
        return []
    
    # Tenta buscar primeiro na ReceitaWS
    current_app.logger.info("Tentando buscar na ReceitaWS...")
    empresa = _buscar_receita_ws(cnpj_limpo)
    
    # Se não encontrou na ReceitaWS, tenta BrasilAPI
    if not empresa:
        current_app.logger.info("Não encontrado na ReceitaWS, tentando BrasilAPI...")
        empresa = _buscar_brasil_api(cnpj_limpo)
    
    # Log do resultado final
    if empresa:
        current_app.logger.info(f"Empresa encontrada: {empresa['razao_social']}")
        return [empresa]
    else:
        current_app.logger.warning(f"Empresa não encontrada em nenhuma API para CNPJ: {cnpj}")
        return []


def _buscar_receita_ws(cnpj: str) -> Optional[Dict[str, str]]:
    """
    Busca empresa na API ReceitaWS.
    
    :param cnpj: CNPJ limpo (apenas números).
    :return: Dicionário com dados da empresa ou None.
    """
    try:
        url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Verifica se a consulta foi bem-sucedida
        if data.get('status') == 'ERROR':
            current_app.logger.warning(f"ReceitaWS: {data.get('message', 'Erro desconhecido')}")
            return None
        
        # Mapeia os dados para o formato esperado
        return {
            'cnpj': _formatar_cnpj(cnpj),
            'razao_social': data.get('nome', ''),
            'nome_fantasia': data.get('fantasia', '') or data.get('nome', ''),
            'cnae': data.get('atividade_principal', [{}])[0].get('code', '') if data.get('atividade_principal') else '',
            'cidade': data.get('municipio', ''),
            'estado': data.get('uf', ''),
            'telefone': data.get('telefone', ''),
            'email': data.get('email', ''),
            'situacao': data.get('situacao', ''),
            'abertura': data.get('abertura', ''),
        }
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Erro ao consultar ReceitaWS: {e}")
        return None
    except (KeyError, ValueError, IndexError) as e:
        current_app.logger.error(f"Erro ao processar resposta da ReceitaWS: {e}")
        return None


def _buscar_brasil_api(cnpj: str) -> Optional[Dict[str, str]]:
    """
    Busca empresa na API BrasilAPI.
    
    :param cnpj: CNPJ limpo (apenas números).
    :return: Dicionário com dados da empresa ou None.
    """
    try:
        url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Mapeia os dados para o formato esperado
        return {
            'cnpj': _formatar_cnpj(cnpj),
            'razao_social': data.get('razao_social', ''),
            'nome_fantasia': data.get('nome_fantasia', '') or data.get('razao_social', ''),
            'cnae': data.get('cnae_fiscal', ''),
            'cidade': data.get('municipio', ''),
            'estado': data.get('uf', ''),
            'telefone': data.get('ddd_telefone_1', ''),
            'email': data.get('email', ''),
            'situacao': data.get('situacao_cadastral', ''),
            'abertura': data.get('data_inicio_atividade', ''),
        }
        
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Erro ao consultar BrasilAPI: {e}")
        return None
    except (KeyError, ValueError) as e:
        current_app.logger.error(f"Erro ao processar resposta da BrasilAPI: {e}")
        return None


def _formatar_cnpj(cnpj: str) -> str:
    """
    Formata CNPJ para o padrão XX.XXX.XXX/XXXX-XX.
    
    :param cnpj: CNPJ limpo (apenas números).
    :return: CNPJ formatado.
    """
    if len(cnpj) != 14:
        return cnpj
    
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"