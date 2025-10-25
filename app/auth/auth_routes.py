# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Routes de Autenticação
=====================================

Rotas para login, logout e gerenciamento de sessões.
Integrado com Flask-Login para controle de acesso.

Autor: JSP Soluções
Data: 2025
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.extensoes import db
from app.auth.usuario_model import Usuario, LogLogin
from urllib.parse import urlparse, urljoin
from datetime import datetime
import re

# Cria o blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth', template_folder='templates')


def get_client_ip():
    """Obtém o IP do cliente."""
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ['REMOTE_ADDR']
    else:
        return request.environ['HTTP_X_FORWARDED_FOR']


def is_safe_url(target):
    """Verifica se a URL de redirecionamento é segura."""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Página de login.
    
    GET: Exibe formulário de login
    POST: Processa tentativa de login
    """
    # Busca configurações para logo e dados da empresa
    from app.configuracao.configuracao_utils import get_config
    config = get_config()
    
    # Se já está logado, redireciona para dashboard
    if current_user.is_authenticated:
        return redirect(url_for('painel.dashboard'))
    
    if request.method == 'POST':
        identificador = request.form.get('identificador', '').strip().lower()
        senha = request.form.get('senha', '')
        lembrar = bool(request.form.get('lembrar'))
        
        # Validações básicas
        if not identificador or not senha:
            flash('Por favor, preencha todos os campos.', 'error')
            return render_template('auth/login.html', identificador=identificador)
        
        # Busca usuário
        usuario = Usuario.buscar_para_login(identificador)
        
        # Variáveis para log
        usuario_id = usuario.id if usuario else None
        motivo_falha = None
        sucesso = False
        
        try:
            if not usuario:
                motivo_falha = 'usuario_nao_encontrado'
                flash('Usuário ou senha incorretos.', 'error')
                
            elif not usuario.pode_fazer_login:
                if not usuario.ativo:
                    motivo_falha = 'conta_inativa'
                    flash('Conta desativada. Entre em contato com o administrador.', 'error')
                elif usuario.esta_bloqueado:
                    motivo_falha = 'conta_bloqueada'
                    flash('Conta temporariamente bloqueada devido a múltiplas tentativas de login. Tente novamente mais tarde.', 'error')
                else:
                    motivo_falha = 'conta_sem_permissao'
                    flash('Conta sem permissão para login.', 'error')
                    
            elif not usuario.verificar_senha(senha):
                motivo_falha = 'senha_incorreta'
                usuario.registrar_tentativa_falha()
                flash('Usuário ou senha incorretos.', 'error')
                
            else:
                # Login bem-sucedido
                login_user(usuario, remember=lembrar)
                usuario.registrar_login()
                sucesso = True
                
                # Mensagem de boas-vindas
                if usuario.primeiro_login:
                    flash(f'Bem-vindo ao ERP JSP, {usuario.nome}! Este é seu primeiro login.', 'info')
                else:
                    flash(f'Bem-vindo de volta, {usuario.nome}!', 'success')
                
                # Redireciona para página solicitada ou dashboard
                next_page = request.args.get('next')
                if not next_page or not is_safe_url(next_page):
                    next_page = url_for('painel.dashboard')
                
                return redirect(next_page)
                
        except Exception as e:
            current_app.logger.error(f'Erro durante login: {str(e)}')
            motivo_falha = 'erro_sistema'
            flash('Erro interno do sistema. Tente novamente.', 'error')
        
        finally:
            # Registra tentativa de login
            LogLogin.registrar_tentativa(
                identificador=identificador,
                sucesso=sucesso,
                usuario_id=usuario_id,
                motivo_falha=motivo_falha,
                ip_address=get_client_ip(),
                user_agent=request.user_agent.string
            )
        
        # Se chegou até aqui, houve falha
        return render_template('auth/login.html', identificador=identificador, config=config)
    
    # GET - exibe formulário
    return render_template('auth/login.html', config=config)


@auth_bp.route('/logout')
@login_required
def logout():
    """
    Faz logout do usuário.
    """
    nome = current_user.nome
    logout_user()
    flash(f'Logout realizado com sucesso. Até logo, {nome}!', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/perfil')
@login_required
def perfil():
    """
    Página de perfil do usuário.
    """
    return render_template('auth/perfil.html', usuario=current_user)


@auth_bp.route('/alterar-senha', methods=['GET', 'POST'])
@login_required
def alterar_senha():
    """
    Página para alterar senha.
    
    GET: Exibe formulário
    POST: Processa alteração
    """
    if request.method == 'POST':
        senha_atual = request.form.get('senha_atual', '')
        nova_senha = request.form.get('nova_senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')
        
        # Validações
        if not senha_atual or not nova_senha or not confirmar_senha:
            flash('Por favor, preencha todos os campos.', 'error')
            return render_template('auth/alterar_senha.html')
        
        if not current_user.verificar_senha(senha_atual):
            flash('Senha atual incorreta.', 'error')
            return render_template('auth/alterar_senha.html')
        
        if nova_senha != confirmar_senha:
            flash('Nova senha e confirmação não coincidem.', 'error')
            return render_template('auth/alterar_senha.html')
        
        if len(nova_senha) < 6:
            flash('Nova senha deve ter pelo menos 6 caracteres.', 'error')
            return render_template('auth/alterar_senha.html')
        
        # Altera senha
        try:
            current_user.set_senha(nova_senha)
            current_user.primeiro_login = False
            current_user.save()
            
            flash('Senha alterada com sucesso!', 'success')
            return redirect(url_for('auth.perfil'))
            
        except Exception as e:
            current_app.logger.error(f'Erro ao alterar senha: {str(e)}')
            flash('Erro ao alterar senha. Tente novamente.', 'error')
    
    # GET - exibe formulário
    return render_template('auth/alterar_senha.html')


@auth_bp.route('/primeiro-login', methods=['GET', 'POST'])
@login_required
def primeiro_login():
    """
    Página para primeiro login (alteração obrigatória de senha).
    """
    # Se não é primeiro login, redireciona
    if not current_user.primeiro_login:
        return redirect(url_for('painel.dashboard'))
    
    if request.method == 'POST':
        nova_senha = request.form.get('nova_senha', '')
        confirmar_senha = request.form.get('confirmar_senha', '')
        
        # Validações
        if not nova_senha or not confirmar_senha:
            flash('Por favor, preencha todos os campos.', 'error')
            return render_template('auth/primeiro_login.html')
        
        if nova_senha != confirmar_senha:
            flash('Nova senha e confirmação não coincidem.', 'error')
            return render_template('auth/primeiro_login.html')
        
        if len(nova_senha) < 6:
            flash('Senha deve ter pelo menos 6 caracteres.', 'error')
            return render_template('auth/primeiro_login.html')
        
        # Verifica força da senha
        if not validar_forca_senha(nova_senha):
            flash('Senha deve conter pelo menos: 1 letra maiúscula, 1 minúscula, 1 número.', 'error')
            return render_template('auth/primeiro_login.html')
        
        # Altera senha
        try:
            current_user.set_senha(nova_senha)
            current_user.primeiro_login = False
            current_user.save()
            
            flash('Senha definida com sucesso! Bem-vindo ao ERP JSP.', 'success')
            return redirect(url_for('painel.dashboard'))
            
        except Exception as e:
            current_app.logger.error(f'Erro no primeiro login: {str(e)}')
            flash('Erro ao definir senha. Tente novamente.', 'error')
    
    # GET - exibe formulário
    return render_template('auth/primeiro_login.html')


def validar_forca_senha(senha):
    """
    Valida a força da senha.
    
    Args:
        senha (str): Senha a ser validada
        
    Returns:
        bool: True se a senha atende aos critérios
    """
    if len(senha) < 6:
        return False
    
    # Pelo menos uma maiúscula
    if not re.search(r'[A-Z]', senha):
        return False
    
    # Pelo menos uma minúscula
    if not re.search(r'[a-z]', senha):
        return False
    
    # Pelo menos um número
    if not re.search(r'\d', senha):
        return False
    
    return True


# Handlers de contexto global
@auth_bp.app_context_processor
def inject_auth_vars():
    """
    Injeta variáveis de autenticação em todos os templates.
    """
    return {
        'current_user': current_user,
        'is_authenticated': current_user.is_authenticated if current_user else False
    }


# Decorador personalizado para verificar permissões
def permissao_required(permissao):
    """
    Decorador para verificar se o usuário tem uma permissão específica.
    
    Args:
        permissao (str): Nome da permissão necessária
    """
    def decorator(f):
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.tem_permissao(permissao):
                flash('Você não tem permissão para acessar esta página.', 'error')
                return redirect(url_for('painel.dashboard'))
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator