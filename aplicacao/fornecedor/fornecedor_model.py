# fornecedor_model.py
from aplicacao.extensoes import db
from datetime import datetime

class Fornecedor(db.Model):
    __tablename__ = 'fornecedores'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf_cnpj = db.Column(db.String(20), unique=True, nullable=True)  # Renomeado de cnpj para cpf_cnpj
    telefone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=True)
    cep = db.Column(db.String(10), nullable=True)
    endereco = db.Column(db.String(150), nullable=True)
    numero = db.Column(db.String(20), nullable=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    complemento = db.Column(db.String(100), nullable=True)
    bairro = db.Column(db.String(100), nullable=True)
    cidade = db.Column(db.String(100), nullable=True)
    uf = db.Column(db.String(2), nullable=True)
    pais = db.Column(db.String(50), nullable=True)
    inscricao_estadual = db.Column(db.String(30), nullable=True)
    inscricao_municipal = db.Column(db.String(30), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    nome_fantasia = db.Column(db.String(100), nullable=True)
    logradouro = db.Column(db.String(150), nullable=True)
    apelido = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f'<Fornecedor {self.nome}>'

    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nome': self.nome,
            'cpf_cnpj': self.cpf_cnpj,
            'telefone': self.telefone,
            'email': self.email,
            'cep': self.cep,
            'endereco': self.endereco,
            'numero': self.numero,
            'complemento': self.complemento,
            'bairro': self.bairro,
            'cidade': self.cidade,
            'uf': self.uf,
            'pais': self.pais,
            'inscricao_estadual': self.inscricao_estadual,
            'inscricao_municipal': self.inscricao_municipal,
            'observacoes': self.observacoes,
            'ativo': self.ativo,
            'nome_fantasia': self.nome_fantasia,
            'logradouro': self.logradouro,
            'apelido': self.apelido,
            'data_cadastro': self.data_cadastro.isoformat() if self.data_cadastro else None
        }
