# ordem_servico/arquivo_model.py

from aplicacao.extensoes import db
from datetime import datetime
import os
from werkzeug.utils import secure_filename

class OSArquivo(db.Model):
    __tablename__ = 'os_arquivos'
    
    id = db.Column(db.Integer, primary_key=True)
    ordem_servico_id = db.Column(db.Integer, db.ForeignKey('ordens_servico.id'), nullable=False)
    
    # Dados do arquivo
    nome_original = db.Column(db.String(255), nullable=False)
    nome_arquivo = db.Column(db.String(255), nullable=False)  # Nome único no servidor
    tipo_arquivo = db.Column(db.String(50))  # pdf, jpg, png, etc
    tamanho = db.Column(db.Integer)  # Tamanho em bytes
    
    # Categorização
    categoria = db.Column(db.String(50))  # 'antes', 'durante', 'depois', 'documento', 'orcamento'
    descricao = db.Column(db.Text)
    
    # URLs e caminhos
    caminho_local = db.Column(db.String(500))  # Caminho no servidor local
    url_s3 = db.Column(db.String(500))  # URL no S3 (se usar)
    url_publica = db.Column(db.String(500))  # URL pública para visualização
    
    # Controle
    ativo = db.Column(db.Boolean, default=True)
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_upload = db.Column(db.String(100))  # Usuário que fez upload
    
    # Relacionamento
    ordem_servico = db.relationship('OrdemServico', backref='arquivos')
    
    def __repr__(self):
        return f'<OSArquivo {self.nome_original}>'
    
    @property
    def extensao(self):
        """Retorna a extensão do arquivo"""
        return os.path.splitext(self.nome_original)[1].lower()
    
    @property
    def is_imagem(self):
        """Verifica se o arquivo é uma imagem"""
        extensoes_imagem = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        return self.extensao in extensoes_imagem
    
    @property
    def is_pdf(self):
        """Verifica se o arquivo é um PDF"""
        return self.extensao == '.pdf'
    
    @property
    def tamanho_formatado(self):
        """Retorna o tamanho formatado em KB/MB"""
        if not self.tamanho:
            return "0 KB"
        
        if self.tamanho < 1024:
            return f"{self.tamanho} bytes"
        elif self.tamanho < 1024 * 1024:
            return f"{self.tamanho / 1024:.1f} KB"
        else:
            return f"{self.tamanho / (1024 * 1024):.1f} MB"
    
    @property
    def icone_arquivo(self):
        """Retorna ícone FontAwesome baseado no tipo de arquivo"""
        if self.is_imagem:
            return 'fa-image'
        elif self.is_pdf:
            return 'fa-file-pdf'
        else:
            return 'fa-file'
    
    @property
    def cor_categoria(self):
        """Retorna cor CSS baseada na categoria"""
        cores = {
            'antes': 'primary',
            'durante': 'warning',
            'depois': 'success',
            'documento': 'info',
            'orcamento': 'secondary'
        }
        return cores.get(self.categoria, 'secondary')
    
    def get_url_visualizacao(self):
        """Retorna URL para visualização do arquivo"""
        if self.url_publica:
            return self.url_publica
        elif self.url_s3:
            return self.url_s3
        else:
            # URL local relativa
            return f"/static/uploads/os/{self.ordem_servico_id}/{self.nome_arquivo}"
    
    def get_url_download(self):
        """Retorna URL para download do arquivo"""
        return f"/ordem-servico/arquivo/{self.id}/download"
    
    def to_dict(self):
        """Converte objeto para dicionário"""
        return {
            'id': self.id,
            'nome_original': self.nome_original,
            'tipo_arquivo': self.tipo_arquivo,
            'tamanho_formatado': self.tamanho_formatado,
            'categoria': self.categoria,
            'descricao': self.descricao,
            'data_upload': self.data_upload.strftime('%d/%m/%Y %H:%M'),
            'url_visualizacao': self.get_url_visualizacao(),
            'url_download': self.get_url_download(),
            'is_imagem': self.is_imagem,
            'is_pdf': self.is_pdf,
            'icone': self.icone_arquivo,
            'cor_categoria': self.cor_categoria
        }
