"""
Rotas para o módulo de prospecção de clientes.

Este módulo define uma Blueprint responsável por exibir um formulário de
busca de empresas (prospecção) e listar os resultados obtidos a partir
de filtros fornecidos pelo usuário. O design segue o padrão
futurista do ERP JSP, com tema escuro e detalhes em azul ciano.

Para integrar com APIs reais, edite a função ``buscar_empresas`` em
``prospeccao_model.py`` para realizar chamadas HTTP de acordo com as
credenciais disponíveis. Os resultados são exibidos em uma tabela
responsiva.
"""

from flask import Blueprint, render_template, request
from .prospeccao_model import buscar_empresas, Prospect, db


prospeccao_bp = Blueprint(
    "prospeccao",
    __name__,
    template_folder="templates",
    url_prefix="/prospeccao",
)


@prospeccao_bp.route("/", methods=["GET", "POST"])
def buscar():
    """
    Exibe o formulário de prospecção e, quando enviado via POST,
    realiza a busca de empresas com base nos filtros informados.

    Filtros disponíveis: CNAE, cidade, CNPJ e estado. Os resultados
    retornados pela função ``buscar_empresas`` são passados ao template
    para exibição.
    """
    resultados = []
    filtros = {"cnae": "", "cidade": "", "cnpj": "", "estado": ""}
    if request.method == "POST":
        cnae = request.form.get("cnae", "").strip()
        cidade = request.form.get("cidade", "").strip()
        cnpj = request.form.get("cnpj", "").strip()
        estado = request.form.get("estado", "").strip()
        filtros.update(
            {"cnae": cnae, "cidade": cidade, "cnpj": cnpj, "estado": estado}
        )
        resultados = buscar_empresas(
            cnpj=cnpj or None,
            cnae=cnae or None,
            cidade=cidade or None,
            estado=estado or None,
        )
    return render_template(
        "prospeccao/busca.html",
        resultados=resultados,
        filtros=filtros,
    )


@prospeccao_bp.route("/salvar/<string:cnpj>", methods=["POST"])
def salvar(cnpj: str):
    """
    Persiste um prospecto no banco de dados.

    Esta rota recebe um CNPJ selecionado pelo usuário e cria um
    registro em ``Prospect`` caso ainda não exista. Os dados enviados
    via formulário devem incluir nome, razão social, CNAE, cidade,
    estado, telefone e email. Após salvar, retorna uma resposta vazia
    com status 204 para permitir o refresh da lista via JavaScript se
    desejado.
    """
    # Coleta dados do formulário para salvar
    razao_social = request.form.get("razao_social")
    nome_fantasia = request.form.get("nome_fantasia")
    cnae = request.form.get("cnae")
    cidade = request.form.get("cidade")
    estado = request.form.get("estado")
    telefone = request.form.get("telefone")
    email = request.form.get("email")
    # Verifica se o CNPJ já existe
    prospecto = Prospect.query.filter_by(cnpj=cnpj).first()
    if not prospecto:
        prospecto = Prospect(
            cnpj=cnpj,
            razao_social=razao_social or "",
            nome_fantasia=nome_fantasia or "",
            cnae=cnae or "",
            cidade=cidade or "",
            estado=estado or "",
            telefone=telefone or "",
            email=email or "",
        )
        db.session.add(prospecto)
        db.session.commit()
    return ("", 204)