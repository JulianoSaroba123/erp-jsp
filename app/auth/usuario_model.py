# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Model de Usuário
===============================

Model para gerenciamento de usuários e autenticação.
Integrado com Flask-Login para controle de sessões.

Autor: JSP Soluções
Data: 2025
"""

from app.extensoes import db
from app.models import BaseModel
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class Usuario(BaseModel, UserMixin):
    """
    Model para usuários do sistema.
    
    Controla autenticação, permissões e dados pessoais.
    Integrado com Flask-Login (UserMixin).
    """
    
    __tablename__ = 'usuarios'
    
    # Dados básicos
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    usuario = db.Column(db.String(50), unique=True, nullable=False, index=True)  # username
    
    # Autenticação
    senha_hash = db.Column(db.String(255), nullable=False)
    
    # Dados pessoais
    telefone = db.Column(db.String(20))
    cargo = db.Column(db.String(100))
    departamento = db.Column(db.String(100))
    
    # Controle de acesso
    tipo_usuario = db.Column(db.String(20), default='usuario', nullable=False)
    # Tipos: admin, usuario, operador, readonly
    
    # Status da conta
    email_confirmado = db.Column(db.Boolean, default=False)
    primeiro_login = db.Column(db.Boolean, default=True)
    ultimo_login = db.Column(db.DateTime)
    tentativas_login = db.Column(db.Integer, default=0)
    bloqueado_ate = db.Column(db.DateTime)
    
    # Configurações pessoais
    tema_preferido = db.Column(db.String(20), default='light')  # light, dark
    idioma = db.Column(db.String(5), default='pt-BR')
    timezone = db.Column(db.String(50), default='America/Sao_Paulo')
    
    # Meta campos herdados de BaseModel:
    # id, data_criacao, data_atualizacao, ativo, usuario_criacao, usuario_atualizacao
    
    def __repr__(self):
        return f'<Usuario {self.usuario}: {self.nome}>'
    
    def __str__(self):
        return f'{self.nome} ({self.usuario})'
    
    @property
    def tipo_usuario_formatado(self):
        """Retorna tipo de usuário formatado para exibição."""
        tipos = {
            'admin': 'Administrador',
            'usuario': 'Usuário',
            'operador': 'Operador',
            'readonly': 'Apenas Leitura'
        }
        return tipos.get(self.tipo_usuario, self.tipo_usuario.title())
    
    @property
    def status_conta(self):
        """Retorna status da conta."""
        if not self.ativo:
            return 'inativo'
        elif self.esta_bloqueado:
            return 'bloqueado'
        elif not self.email_confirmado:
            return 'pendente_confirmacao'
        else:
            return 'ativo'
    
    @property
    def status_cor(self):
        """Retorna cor do status para exibição."""
        cores = {
            'ativo': 'success',
            'inativo': 'secondary',
            'bloqueado': 'danger',
            'pendente_confirmacao': 'warning'
        }
        return cores.get(self.status_conta, 'secondary')
    
    @property
    def esta_bloqueado(self):
        """Verifica se a conta está bloqueada."""
        if self.bloqueado_ate:
            return datetime.now() < self.bloqueado_ate
        return False
    
    @property
    def pode_fazer_login(self):
        """Verifica se o usuário pode fazer login."""
        return self.ativo and not self.esta_bloqueado
    
    def set_senha(self, senha):
        """
        Define nova senha para o usuário.
        
        Args:
            senha (str): Senha em texto claro
        """
        self.senha_hash = generate_password_hash(senha)
    
    def verificar_senha(self, senha):
        """
        Verifica se a senha está correta.
        
        Args:
            senha (str): Senha em texto claro
            
        Returns:
            bool: True se a senha estiver correta
        """
        return check_password_hash(self.senha_hash, senha)
    
    def registrar_login(self):
        """Registra um login bem-sucedido."""
        self.ultimo_login = datetime.now()
        self.tentativas_login = 0
        self.primeiro_login = False
        self.save()
    
    def registrar_tentativa_falha(self):
        """Registra uma tentativa de login falhada."""
        self.tentativas_login += 1
        
        # Bloqueia após 5 tentativas por 30 minutos
        if self.tentativas_login >= 5:
            from datetime import timedelta
            self.bloqueado_ate = datetime.now() + timedelta(minutes=30)
        
        self.save()
    
    def desbloquear_conta(self):
        """Desbloqueia a conta manualmente."""
        self.tentativas_login = 0
        self.bloqueado_ate = None
        self.save()
    
    def confirmar_email(self):
        """Confirma o email do usuário."""
        self.email_confirmado = True
        self.save()
    
    def tem_permissao(self, permissao):
        """
        Verifica se o usuário tem uma permissão específica.
        
        Args:
            permissao (str): Nome da permissão
            
        Returns:
            bool: True se tiver a permissão
        """
        # Admins têm todas as permissões
        if self.tipo_usuario == 'admin':
            return True
        
        # Permissões por tipo de usuário
        permissoes = {
            'usuario': [
                'visualizar_clientes', 'criar_clientes', 'editar_clientes',
                'visualizar_propostas', 'criar_propostas', 'editar_propostas',
                'visualizar_ordem_servico', 'criar_ordem_servico', 'editar_ordem_servico',
                'visualizar_produtos', 'criar_produtos', 'editar_produtos',
                'visualizar_fornecedores', 'criar_fornecedores', 'editar_fornecedores',
                'visualizar_financeiro', 'criar_financeiro', 'editar_financeiro'
            ],
            'operador': [
                'visualizar_clientes', 'criar_clientes', 'editar_clientes',
                'visualizar_propostas', 'criar_propostas', 'editar_propostas',
                'visualizar_ordem_servico', 'criar_ordem_servico', 'editar_ordem_servico',
                'visualizar_produtos', 'visualizar_fornecedores'
            ],
            'readonly': [
                'visualizar_clientes', 'visualizar_propostas', 'visualizar_ordem_servico',
                'visualizar_produtos', 'visualizar_fornecedores', 'visualizar_financeiro'
            ]
        }
        
        return permissao in permissoes.get(self.tipo_usuario, [])
    
    @classmethod
    def buscar_por_email(cls, email):
        """Busca usuário por email."""
        return cls.query.filter_by(email=email, ativo=True).first()
    
    @classmethod
    def buscar_por_usuario(cls, usuario):
        """Busca usuário por username."""
        return cls.query.filter_by(usuario=usuario, ativo=True).first()
    
    @classmethod
    def buscar_para_login(cls, identificador):
        """
        Busca usuário para login (por email ou username).
        
        Args:
            identificador (str): Email ou username
            
        Returns:
            Usuario: Instância do usuário ou None
        """
        return cls.query.filter(
            db.or_(
                cls.email == identificador,
                cls.usuario == identificador
            ),
            cls.ativo == True
        ).first()
    
    @classmethod
    def criar_admin_padrao(cls):
        """
        Cria usuário administrador padrão se não existir.
        
        Returns:
            Usuario: Instância do admin criado ou existente
        """
        admin = cls.query.filter_by(tipo_usuario='admin', ativo=True).first()
        
        if not admin:
            admin = cls(
                nome='Administrador',
                email='admin@jspsolucoestecnologicas.com',
                usuario='admin',
                tipo_usuario='admin',
                email_confirmado=True,
                primeiro_login=False
            )
            admin.set_senha('admin123')  # Senha padrão - deve ser alterada
            admin.save()
            
        return admin
    
    @classmethod
    def listar_ativos(cls):
        """Lista todos os usuários ativos."""
        return cls.query.filter_by(ativo=True).order_by(cls.nome).all()
    
    @classmethod
    def estatisticas(cls):
        """Retorna estatísticas dos usuários."""
        total = cls.query.count()
        ativos = cls.query.filter_by(ativo=True).count()
        admins = cls.query.filter_by(tipo_usuario='admin', ativo=True).count()
        bloqueados = cls.query.filter(
            cls.bloqueado_ate != None,
            cls.bloqueado_ate > datetime.now(),
            cls.ativo == True
        ).count()
        
        return {
            'total': total,
            'ativos': ativos,
            'admins': admins,
            'bloqueados': bloqueados,
            'inativos': total - ativos
        }


class LogLogin(BaseModel):
    """
    Model para log de tentativas de login.
    
    Registra todas as tentativas de login para auditoria.
    """
    
    __tablename__ = 'log_login'
    
    # Dados da tentativa
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    usuario = db.relationship('Usuario', backref='logs_login')
    
    identificador = db.Column(db.String(120), nullable=False)  # email ou username usado
    ip_address = db.Column(db.String(45))  # IPv4 ou IPv6
    user_agent = db.Column(db.Text)
    
    # Resultado
    sucesso = db.Column(db.Boolean, default=False)
    motivo_falha = db.Column(db.String(100))  # senha_incorreta, usuario_nao_encontrado, conta_bloqueada, etc.
    
    def __repr__(self):
        status = 'SUCESSO' if self.sucesso else 'FALHA'
        return f'<LogLogin {self.identificador}: {status}>'
    
    @classmethod
    def registrar_tentativa(cls, identificador, sucesso, usuario_id=None, motivo_falha=None, ip_address=None, user_agent=None):
        """
        Registra uma tentativa de login.
        
        Args:
            identificador (str): Email ou username usado
            sucesso (bool): Se o login foi bem-sucedido
            usuario_id (int): ID do usuário (se encontrado)
            motivo_falha (str): Motivo da falha (se houver)
            ip_address (str): IP do cliente
            user_agent (str): User agent do navegador
        """
        log = cls(
            usuario_id=usuario_id,
            identificador=identificador,
            ip_address=ip_address,
            user_agent=user_agent,
            sucesso=sucesso,
            motivo_falha=motivo_falha
        )
        log.save()
        return log
    
    @classmethod
    def tentativas_recentes(cls, identificador, minutos=30):
        """
        Conta tentativas de login recentes para um identificador.
        
        Args:
            identificador (str): Email ou username
            minutos (int): Período em minutos
            
        Returns:
            int: Número de tentativas
        """
        from datetime import timedelta
        limite = datetime.now() - timedelta(minutes=minutos)
        
        return cls.query.filter(
            cls.identificador == identificador,
            cls.data_criacao >= limite
        ).count()