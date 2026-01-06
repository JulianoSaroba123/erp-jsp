# -*- coding: utf-8 -*-
"""
Serviço de Integração com API do Distribuidor de Kits Fotovoltaicos
====================================================================

Este módulo fornece funções para consumir a API do distribuidor,
incluindo autenticação via Bearer Token, tratamento de erros e
paginação.

Autor: JSP Soluções
Data: 2026
"""

import requests
from typing import Dict, List, Optional, Any
from flask import current_app
import logging

logger = logging.getLogger(__name__)


class DistribuidorAPIError(Exception):
    """Exceção personalizada para erros da API do distribuidor."""
    pass


class DistribuidorAPIService:
    """Serviço para integração com API do distribuidor."""
    
    def __init__(self):
        """Inicializa o serviço com configurações do app."""
        self.base_url = current_app.config.get('DISTRIBUIDOR_API_URL', '')
        self.token = current_app.config.get('DISTRIBUIDOR_API_TOKEN', '')
        self.timeout = current_app.config.get('DISTRIBUIDOR_API_TIMEOUT', 30)
        
        if not self.token:
            logger.warning("⚠️  DISTRIBUIDOR_API_TOKEN não configurado!")
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Retorna os headers HTTP para as requisições.
        
        Returns:
            Dict com headers incluindo Authorization Bearer
        """
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'ERP-JSP/3.0'
        }
    
    def _make_request(
        self, 
        endpoint: str, 
        method: str = 'GET',
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Faz requisição HTTP para a API do distribuidor.
        
        Args:
            endpoint: Endpoint da API (ex: '/kits', '/kits/123')
            method: Método HTTP (GET, POST, PUT, DELETE)
            params: Parâmetros de query string
            data: Dados para enviar no body (JSON)
        
        Returns:
            Resposta da API em formato dict
            
        Raises:
            DistribuidorAPIError: Se houver erro na requisição
        """
        if not self.token:
            raise DistribuidorAPIError(
                "Token de API não configurado. "
                "Configure DISTRIBUIDOR_API_TOKEN no arquivo .env"
            )
        
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        
        try:
            logger.info(f"API Request: {method} {url}")
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=self.timeout
            )
            
            # Log de resposta
            logger.info(f"API Response: {response.status_code}")
            
            # Tratamento de erros HTTP
            if response.status_code == 401:
                raise DistribuidorAPIError("Token de autenticação inválido ou expirado")
            elif response.status_code == 403:
                raise DistribuidorAPIError("Acesso negado. Verifique as permissões do token")
            elif response.status_code == 404:
                raise DistribuidorAPIError(f"Endpoint não encontrado: {endpoint}")
            elif response.status_code == 429:
                raise DistribuidorAPIError("Limite de requisições excedido. Tente novamente mais tarde")
            elif response.status_code >= 500:
                raise DistribuidorAPIError(f"Erro no servidor do distribuidor: {response.status_code}")
            elif response.status_code != 200:
                raise DistribuidorAPIError(
                    f"Erro na requisição: {response.status_code} - {response.text}"
                )
            
            # Retorna JSON
            return response.json()
            
        except requests.exceptions.Timeout:
            raise DistribuidorAPIError(
                f"Timeout na requisição (limite: {self.timeout}s). "
                "Verifique sua conexão ou aumente o timeout"
            )
        except requests.exceptions.ConnectionError:
            raise DistribuidorAPIError(
                "Erro de conexão com a API do distribuidor. "
                "Verifique sua internet e a URL da API"
            )
        except requests.exceptions.RequestException as e:
            raise DistribuidorAPIError(f"Erro na requisição HTTP: {str(e)}")
        except ValueError as e:
            raise DistribuidorAPIError(f"Erro ao decodificar resposta JSON: {str(e)}")
    
    def listar_kits(
        self,
        page: int = 1,
        per_page: int = 50,
        filtros: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Lista kits fotovoltaicos disponíveis na API.
        
        Args:
            page: Número da página (para paginação)
            per_page: Quantidade de itens por página
            filtros: Filtros adicionais (ex: {'potencia_min': 5000, 'fabricante': 'Canadian'})
        
        Returns:
            Dict com: {
                'kits': [...],  # Lista de kits
                'total': 150,   # Total de kits
                'page': 1,      # Página atual
                'pages': 3      # Total de páginas
            }
        """
        params = {
            'page': page,
            'per_page': per_page
        }
        
        # Adiciona filtros se fornecidos
        if filtros:
            params.update(filtros)
        
        response = self._make_request('/kits', params=params)
        return response
    
    def buscar_kit(self, kit_id: str) -> Dict[str, Any]:
        """
        Busca um kit específico por ID.
        
        Args:
            kit_id: ID do kit na API
        
        Returns:
            Dados do kit
        """
        response = self._make_request(f'/kits/{kit_id}')
        return response
    
    def buscar_kits_por_potencia(
        self,
        potencia_min: Optional[float] = None,
        potencia_max: Optional[float] = None
    ) -> List[Dict]:
        """
        Busca kits filtrando por faixa de potência.
        
        Args:
            potencia_min: Potência mínima em kWp
            potencia_max: Potência máxima em kWp
        
        Returns:
            Lista de kits que atendem aos critérios
        """
        filtros = {}
        if potencia_min is not None:
            filtros['potencia_min'] = potencia_min
        if potencia_max is not None:
            filtros['potencia_max'] = potencia_max
        
        response = self.listar_kits(per_page=100, filtros=filtros)
        return response.get('kits', [])
    
    def buscar_kits_por_fabricante(self, fabricante: str) -> List[Dict]:
        """
        Busca kits de um fabricante específico.
        
        Args:
            fabricante: Nome do fabricante
        
        Returns:
            Lista de kits do fabricante
        """
        filtros = {'fabricante': fabricante}
        response = self.listar_kits(per_page=100, filtros=filtros)
        return response.get('kits', [])
    
    def testar_conexao(self) -> bool:
        """
        Testa a conexão com a API do distribuidor.
        
        Returns:
            True se a conexão estiver OK, False caso contrário
        """
        try:
            self._make_request('/kits', params={'page': 1, 'per_page': 1})
            logger.info("✅ Conexão com API do distribuidor: OK")
            return True
        except DistribuidorAPIError as e:
            logger.error(f"❌ Erro ao conectar com API: {e}")
            return False


def get_api_service() -> DistribuidorAPIService:
    """
    Factory function para obter instância do serviço de API.
    
    Returns:
        Instância de DistribuidorAPIService
    """
    return DistribuidorAPIService()
