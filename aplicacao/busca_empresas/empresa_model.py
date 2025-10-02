"""
Modelo para armazenar empresas encontradas
"""

from datetime import datetime
from aplicacao.extensoes import db

class EmpresaEncontrada(db.Model):
    """Model para empresas encontradas via API"""
    __tablename__ = 'empresas_encontradas'
    
    id = db.Column(db.Integer, primary_key=True)
    cnpj = db.Column(db.String(18), nullable=False, unique=True)
    razao_social = db.Column(db.String(200), nullable=False)
    nome_fantasia = db.Column(db.String(200))
    
    # Endereço
    cep = db.Column(db.String(10))
    logradouro = db.Column(db.String(200))
    numero = db.Column(db.String(10))
    complemento = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    uf = db.Column(db.String(2))
    
    # Atividade
    atividade_principal = db.Column(db.String(500))
    atividades_secundarias = db.Column(db.Text)  # JSON string
    
    # Contato
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    
    # Situação
    situacao = db.Column(db.String(50))
    data_abertura = db.Column(db.Date)
    
    # Controle
    data_busca = db.Column(db.DateTime, default=datetime.utcnow)
    termo_busca = db.Column(db.String(200))  # cidade + tipo de atividade
    foi_convertida_cliente = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<EmpresaEncontrada {self.cnpj}: {self.razao_social}>'
    
    @property
    def endereco_completo(self):
        """Retorna endereço formatado"""
        partes = [
            self.logradouro,
            self.numero,
            self.complemento,
            self.bairro,
            self.cidade,
            self.uf
        ]
        return ', '.join(filter(None, partes))
    
    def to_dict(self):
        """Converte para dicionário"""
        return {
            'id': self.id,
            'cnpj': self.cnpj,
            'razao_social': self.razao_social,
            'nome_fantasia': self.nome_fantasia,
            'endereco': self.endereco_completo,
            'atividade_principal': self.atividade_principal,
            'cidade': self.cidade,
            'uf': self.uf,
            'situacao': self.situacao,
            'telefone': self.telefone,
            'email': self.email
        }