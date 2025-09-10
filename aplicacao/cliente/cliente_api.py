from flask import Blueprint, jsonify, request, current_app
from .cliente_model import Cliente
from aplicacao.extensoes import db
from sqlalchemy import or_

cliente_api_bp = Blueprint('cliente_api', __name__, url_prefix='/clientes/api')


@cliente_api_bp.route('/', methods=['GET'])
def listar_clientes_json():
    clientes = Cliente.query.order_by(Cliente.nome).all()
    return jsonify([c.to_dict() for c in clientes])


@cliente_api_bp.route('/buscar', methods=['GET'])
def buscar_clientes():
    nome = request.args.get('nome', '').strip()
    query = Cliente.query
    if nome:
        like = f"%{nome}%"
        query = query.filter(or_(Cliente.nome.ilike(like), Cliente.apelido.ilike(like), Cliente.cpf_cnpj.ilike(like)))
    resultados = query.order_by(Cliente.nome).limit(30).all()
    return jsonify([c.to_dict() for c in resultados])


@cliente_api_bp.route('/<int:id>', methods=['GET'])
def detalhe_cliente_json(id):
    c = Cliente.query.get_or_404(id)
    return jsonify(c.to_dict())


@cliente_api_bp.route('/', methods=['POST'])
def criar_cliente_json():
    data = request.get_json() or {}
    nome = data.get('nome')
    if not nome:
        return jsonify({'error': 'nome obrigatório'}), 400
    c = Cliente()
    c.nome = nome
    c.apelido = data.get('apelido')
    c.cpf_cnpj = data.get('cpf_cnpj')
    c.email = data.get('email')
    c.telefone = data.get('telefone')
    c.pais = data.get('pais') or 'Brasil'
    c.ativo = True
    db.session.add(c)
    db.session.commit()
    return jsonify({'id': c.id}), 201
