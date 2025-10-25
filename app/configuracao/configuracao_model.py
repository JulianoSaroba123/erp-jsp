# Prompt: Crie o model de configurações conforme descrito no prompt completo do usuário.
# Modelo de Configurações do Sistema - ERP JSP
# Uso: armazena informações da empresa e preferências do sistema. Registro único (id=1).

from datetime import datetime
from app.extensoes import db
from app.models import BaseModel


class Configuracao(BaseModel):
    """Model que armazena as configurações da empresa e do sistema.

    Este model tem um único registro (id=1). Use o método `get_solo()` para obter
    a instância global de configuração.
    """

    __tablename__ = 'configuracao'

    # Identificação da empresa
    nome_fantasia = db.Column(db.String(200), nullable=False)
    razao_social = db.Column(db.String(200))
    cnpj = db.Column(db.String(20))
    inscricao_estadual = db.Column(db.String(50))
    telefone = db.Column(db.String(50))
    email = db.Column(db.String(150))
    site = db.Column(db.String(150))
    logo = db.Column(db.String(255))  # caminho/URL para a imagem

    # Endereço
    cep = db.Column(db.String(20))
    logradouro = db.Column(db.String(200))
    numero = db.Column(db.String(20))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    uf = db.Column(db.String(2))

    # Dados bancários
    banco = db.Column(db.String(100))
    agencia = db.Column(db.String(50))
    conta = db.Column(db.String(50))
    pix = db.Column(db.String(100))

    # Textos institucionais
    missao = db.Column(db.Text)
    visao = db.Column(db.Text)
    valores = db.Column(db.Text)
    frase_assinatura = db.Column(db.String(255))

    # Preferências do sistema
    tema = db.Column(db.String(50), default='claro')  # claro, escuro, futurista
    cor_principal = db.Column(db.String(7), default='#00aaff')  # hex
    exibir_logo_em_pdfs = db.Column(db.Boolean, default=True)
    exibir_rodape_padrao = db.Column(db.Boolean, default=True)

    # Meta: BaseModel já traz campos como id, data_criacao, data_atualizacao, ativo

    def __repr__(self):
        return f"<Configuracao: {self.nome_fantasia}>"

    @classmethod
    def get_solo(cls):
        """Retorna a configuração única (id=1). Se não existir, cria com valores padrões."""
        conf = cls.query.get(1)
        if not conf:
            conf = cls(id=1, nome_fantasia='Minha Empresa')
            db.session.add(conf)
            db.session.commit()
        return conf
