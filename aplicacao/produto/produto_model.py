from aplicacao.extensoes import db
from datetime import datetime

class Produto(db.Model):
    __tablename__ = 'produtos'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(30), unique=True, nullable=False)
    nome = db.Column(db.String(200), nullable=False)
    sku = db.Column(db.String(100), unique=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'))
    preco = db.Column(db.Numeric(12,2), default=0.00)
    custo = db.Column(db.Numeric(12,2), default=0.00)
    markup = db.Column(db.Numeric(5,2), default=0.00)  # Markup em percentual (ex: 50.00 para 50%)
    estoque = db.Column(db.Float, default=0.0)
    unidade = db.Column(db.String(20), default='un')
    categoria = db.Column(db.String(100))
    descricao = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relacionamento opcional para facilitar buscas
    fornecedor = db.relationship('Fornecedor', backref=db.backref('produtos', lazy='dynamic'))

    def __repr__(self):
        return f'<Produto {self.nome}>'

    def calcular_preco_venda(self):
        """Calcula o preço de venda baseado no custo e markup"""
        if self.custo and self.markup:
            return float(self.custo) * (1 + float(self.markup) / 100)
        return float(self.custo) if self.custo else 0.00

    def atualizar_preco_por_markup(self):
        """Atualiza o preço baseado no markup atual"""
        self.preco = self.calcular_preco_venda()

    def calcular_markup_por_preco(self):
        """Calcula o markup baseado no custo e preço atual"""
        if self.custo and self.preco and float(self.custo) > 0:
            return ((float(self.preco) / float(self.custo)) - 1) * 100
        return 0.00

    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nome': self.nome,
            'sku': self.sku,
            'categoria': self.categoria,
            'descricao': self.descricao,
            'preco': float(self.preco) if self.preco else None,
            'custo': float(self.custo) if self.custo else None,
            'markup': float(self.markup) if self.markup else None,
            'estoque': self.estoque,
            'unidade': self.unidade,
            'fornecedor_id': self.fornecedor_id,
            'fornecedor_nome': self.fornecedor.nome if self.fornecedor else None,
            'ativo': self.ativo,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }
