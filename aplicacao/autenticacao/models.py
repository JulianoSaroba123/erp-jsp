from aplicacao.extensoes import db

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    nome = db.Column(db.String(120))
    email = db.Column(db.String(120))

    def __repr__(self):
        return f"<Usuario {self.username}>"
