"""
Módulo de modelagem para Prospeção de Clientes.

Este módulo define a estrutura de dados para armazenar leads
capturados a partir de pesquisas por CNAE, cidade e CNPJ. Ele também
inclui uma função utilitária que demonstra como consultar uma API
externa para obter empresas com base em filtros informados. A função
``buscar_empresas`` deve ser adaptada para utilizar um serviço real
conforme as necessidades do projeto (por exemplo, APIs de CNPJá,
ListaCNAE ou ReceitaWS). Para fins de demonstração, retorna uma lista
estática de dicionários.
"""

from flask_sqlalchemy import SQLAlchemy
from flask import current_app
import requests
from typing import List, Dict, Optional

db = SQLAlchemy()


class Prospect(db.Model):
    """Modelo de lead/prospecto armazenado localmente.

    Este modelo representa uma empresa prospectada. Ele pode ser
    armazenado para histórico ou importado posteriormente como
    cliente efetivo. Os campos cobrem as informações básicas
    retornadas por APIs externas de consulta de empresas.
    """

    __tablename__ = "prospects"

    id = db.Column(db.Integer, primary_key=True)
    cnpj = db.Column(db.String(18), unique=True, nullable=False)
    razao_social = db.Column(db.String(200), nullable=False)
    nome_fantasia = db.Column(db.String(200))
    cnae = db.Column(db.String(20))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    telefone = db.Column(db.String(25))
    email = db.Column(db.String(120))

    def __repr__(self) -> str:
        return f"<Prospect {self.cnpj} - {self.razao_social}>"


def buscar_empresas(
    cnpj: Optional[str] = None,
    cnae: Optional[str] = None,
    cidade: Optional[str] = None,
    estado: Optional[str] = None,
) -> List[Dict[str, str]]:
    """
    Busca empresas utilizando filtros de CNPJ, CNAE, cidade e estado.

    Esta função serve de exemplo e demonstra como integrar com APIs
    externas. Para produção, substitua a lógica interna por chamadas
    reais ao serviço escolhido (por exemplo, CNPJá ou ListaCNAE),
    configurando tokens em current_app.config conforme necessário.

    :param cnpj: Número do CNPJ a ser consultado (opcional).
    :param cnae: Código CNAE a ser filtrado (opcional).
    :param cidade: Nome da cidade para filtrar (opcional).
    :param estado: Sigla do estado (UF) (opcional).
    :return: Lista de dicionários representando empresas encontradas.
    """
    # Exemplo de integração com uma API externa. Se você possui uma
    # chave de API configurada em current_app.config, pode fazer
    # requisições reais aqui. Descomente e ajuste conforme o serviço
    # utilizado.
    #
    # token = current_app.config.get("LISTACNAE_API_KEY")
    # url = "https://api.listacnae.com.br/search"
    # params = {
    #     "cnpj": cnpj,
    #     "cnae": cnae,
    #     "cidade": cidade,
    #     "estado": estado,
    #     "token": token,
    # }
    # try:
    #     resp = requests.get(url, params=params, timeout=15)
    #     resp.raise_for_status()
    #     data = resp.json()
    #     return data.get("empresas", [])
    # except Exception as exc:
    #     current_app.logger.error(f"Erro ao buscar empresas: {exc}")
    #     return []

    # Enquanto não for integrado a um serviço real, retorna alguns
    # registros fictícios para teste.
    dados_teste = [
        {
            "cnpj": "12.345.678/0001-90",
            "razao_social": "Fábrica de Componentes Elétricos LTDA",
            "nome_fantasia": "Eletronix",
            "cnae": cnae or "2721-0/00",
            "cidade": cidade or "Tietê",
            "estado": estado or "SP",
            "telefone": "(11) 99999-0001",
            "email": "contato@eletronix.com.br",
        },
        {
            "cnpj": "98.765.432/0001-10",
            "razao_social": "Usinagem de Metais São Paulo SA",
            "nome_fantasia": "Metallis",
            "cnae": cnae or "2592-8/00",
            "cidade": cidade or "Tietê",
            "estado": estado or "SP",
            "telefone": "(11) 98888-0022",
            "email": "vendas@metallis.com.br",
        },
    ]
    # Filtra dados de teste por CNPJ, CNAE, cidade e estado, caso informados
    resultados: List[Dict[str, str]] = []
    for empresa in dados_teste:
        if cnpj and cnpj not in empresa["cnpj"]:
            continue
        if cnae and cnae not in empresa["cnae"]:
            continue
        if cidade and cidade.lower() != empresa["cidade"].lower():
            continue
        if estado and estado.lower() != empresa["estado"].lower():
            continue
        resultados.append(empresa)
    return resultados