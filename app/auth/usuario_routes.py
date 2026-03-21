# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Routes de Gerenciamento de Usuários
===========================================

Rotas para CRUD de usuários (apenas admin).

Autor: JSP Soluções
Data: 2026
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from app.extensoes import db
from app.auth.usuario_model import Usuario

# Cria o blueprint
usuario_bp = Blueprint('usuario', __name__, url_prefix='/usuarios', template_folder='templates')


# Decorador admin_required
def admin_required(f):
    """Decorador para rotas que requerem permissão de admin."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.tipo_usuario != 'admin':
            flash('Acesso negado. Apenas administradores podem acessar esta página.', 'error')
            return redirect(url_for('painel.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@usuario_bp.route('/')
@admin_required
def listar():
    """Lista todos os usuários do sistema."""
    busca = request.args.get('busca', '').strip()
    
    query = Usuario.query
    
    if busca:
        query = query.filter(
            db.or_(
                Usuario.nome.ilike(f'%{busca}%'),
                Usuario.email.ilike(f'%{busca}%'),
                Usuario.usuario.ilike(f'%{busca}%')
            )
        )
    
    usuarios = query.order_by(Usuario.nome).all()
    stats = Usuario.estatisticas()
    
    return render_template('auth/usuarios/listar.html', 
                         usuarios=usuarios,
                         stats=stats,
                         busca=busca)


@usuario_bp.route('/novo', methods=['GET', 'POST'])
@admin_required
def novo():
    """Cadastra novo usuário."""
    if request.method == 'POST':
        try:
            # Validação de campos obrigatórios
            nome = request.form.get('nome', '').strip()
            email = request.form.get('email', '').strip()
            usuario = request.form.get('usuario', '').strip()
            senha = request.form.get('senha', '').strip()
            tipo_usuario = request.form.get('tipo_usuario', 'usuario')
            
            if not all([nome, email, usuario, senha]):
                flash('Preencha todos os campos obrigatórios.', 'error')
                return render_template('auth/usuarios/form.html')
            
            # Verifica se email já existe
            if Usuario.query.filter_by(email=email).first():
                flash('Email já cadastrado.', 'error')
                return render_template('auth/usuarios/form.html')
            
            # Verifica se username já existe
            if Usuario.query.filter_by(usuario=usuario).first():
                flash('Nome de usuário já cadastrado.', 'error')
                return render_template('auth/usuarios/form.html')
            
            # Cria novo usuário
            novo_usuario = Usuario(
                nome=nome,
                email=email,
                usuario=usuario,
                tipo_usuario=tipo_usuario,
                telefone=request.form.get('telefone', '').strip(),
                cargo=request.form.get('cargo', '').strip(),
                departamento=request.form.get('departamento', '').strip(),
                ativo=True,
                email_confirmado=True,
                primeiro_login=False
            )
            novo_usuario.set_senha(senha)
            novo_usuario.save()
            
            flash(f'Usuário {nome} cadastrado com sucesso!', 'success')
            return redirect(url_for('usuario.listar'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar usuário: {str(e)}', 'error')
            return render_template('auth/usuarios/form.html')
    
    # GET - exibe formulário
    return render_template('auth/usuarios/form.html', usuario=None)


@usuario_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@admin_required
def editar(id):
    """Edita usuário existente."""
    usuario = Usuario.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Atualiza dados
            usuario.nome = request.form.get('nome', '').strip()
            usuario.email = request.form.get('email', '').strip()
            usuario.usuario = request.form.get('usuario', '').strip()
            usuario.tipo_usuario = request.form.get('tipo_usuario', 'usuario')
            usuario.telefone = request.form.get('telefone', '').strip()
            usuario.cargo = request.form.get('cargo', '').strip()
            usuario.departamento = request.form.get('departamento', '').strip()
            
            # Atualiza senha se fornecida
            nova_senha = request.form.get('senha', '').strip()
            if nova_senha:
                usuario.set_senha(nova_senha)
            
            usuario.save()
            
            flash(f'Usuário {usuario.nome} atualizado com sucesso!', 'success')
            return redirect(url_for('usuario.listar'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar usuário: {str(e)}', 'error')
    
    # GET - exibe formulário
    return render_template('auth/usuarios/form.html', usuario=usuario)


@usuario_bp.route('/<int:id>/toggle-status', methods=['POST'])
@admin_required
def toggle_status(id):
    """Ativa ou desativa usuário."""
    usuario = Usuario.query.get_or_404(id)
    
    # Não permite desativar o próprio usuário
    if usuario.id == current_user.id:
        flash('Você não pode desativar seu próprio usuário.', 'error')
        return redirect(url_for('usuario.listar'))
    
    try:
        usuario.ativo = not usuario.ativo
        usuario.save()
        
        status = 'ativado' if usuario.ativo else 'desativado'
        flash(f'Usuário {usuario.nome} {status} com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao alterar status: {str(e)}', 'error')
    
    return redirect(url_for('usuario.listar'))


@usuario_bp.route('/<int:id>/resetar-senha', methods=['POST'])
@admin_required
def resetar_senha(id):
    """Reseta senha do usuário para padrão."""
    usuario = Usuario.query.get_or_404(id)
    
    try:
        senha_padrao = '123456'  # Senha padrão
        usuario.set_senha(senha_padrao)
        usuario.primeiro_login = True
        usuario.save()
        
        flash(f'Senha do usuário {usuario.nome} resetada para: {senha_padrao}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao resetar senha: {str(e)}', 'error')
    
    return redirect(url_for('usuario.listar'))
