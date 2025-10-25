# Rotas para gerenciar Configurações do Sistema (único registro id=1)
# Inclui upload de logo, busca CNPJ (BrasilAPI) e CEP (ViaCEP)

import os
import requests
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory
from werkzeug.utils import secure_filename
from app.extensoes import db
from app.configuracao.configuracao_model import Configuracao
from app.configuracao.configuracao_utils import get_config

bp_config = Blueprint('configuracao', __name__, template_folder='templates')

# Pasta para uploads - usa a pasta 'uploads/configuracao'
UPLOAD_FOLDER = os.path.join('uploads', 'configuracao')
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


@bp_config.route('/configuracao')
def visualizar():
    conf = Configuracao.get_solo()
    return render_template('configuracao/form_configuracao.html', configuracao=conf)


@bp_config.route('/configuracao/editar', methods=['GET', 'POST'])
def editar():
    conf = Configuracao.get_solo()

    if request.method == 'POST':
        # Campos básicos
        conf.nome_fantasia = request.form.get('nome_fantasia', conf.nome_fantasia)
        conf.razao_social = request.form.get('razao_social', conf.razao_social)
        conf.cnpj = request.form.get('cnpj', conf.cnpj)
        conf.inscricao_estadual = request.form.get('inscricao_estadual', conf.inscricao_estadual)
        conf.telefone = request.form.get('telefone', conf.telefone)
        conf.email = request.form.get('email', conf.email)
        conf.site = request.form.get('site', conf.site)

        # Endereço
        conf.cep = request.form.get('cep', conf.cep)
        conf.logradouro = request.form.get('logradouro', conf.logradouro)
        conf.numero = request.form.get('numero', conf.numero)
        conf.bairro = request.form.get('bairro', conf.bairro)
        conf.cidade = request.form.get('cidade', conf.cidade)
        conf.uf = request.form.get('uf', conf.uf)

        # Bancários
        conf.banco = request.form.get('banco', conf.banco)
        conf.agencia = request.form.get('agencia', conf.agencia)
        conf.conta = request.form.get('conta', conf.conta)
        conf.pix = request.form.get('pix', conf.pix)

        # Textos institucionais
        conf.missao = request.form.get('missao', conf.missao)
        conf.visao = request.form.get('visao', conf.visao)
        conf.valores = request.form.get('valores', conf.valores)
        conf.frase_assinatura = request.form.get('frase_assinatura', conf.frase_assinatura)

        # Preferências
        conf.tema = request.form.get('tema', conf.tema)
        conf.cor_principal = request.form.get('cor_principal', conf.cor_principal)
        conf.exibir_logo_em_pdfs = bool(request.form.get('exibir_logo_em_pdfs'))
        conf.exibir_rodape_padrao = bool(request.form.get('exibir_rodape_padrao'))

        # Logo upload
        if 'logo' in request.files:
            file = request.files['logo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                save_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(save_path)
                conf.logo = save_path

        db.session.commit()
        # Invalidate cache
        try:
            from app.configuracao.configuracao_utils import _cached as _c
            _c = None
        except Exception:
            pass

        flash('Configurações atualizadas com sucesso.', 'success')
        return redirect(url_for('configuracao.visualizar'))

    return render_template('configuracao/form_configuracao.html', configuracao=conf)


@bp_config.route('/configuracao/lookup/cnpj')
def lookup_cnpj():
    cnpj = request.args.get('cnpj')
    if not cnpj:
        return {'error': 'cnpj required'}, 400

    # Limpa o CNPJ
    cnpj_only = ''.join(filter(str.isdigit, cnpj))
    try:
        resp = requests.get(f'https://brasilapi.com.br/api/cnpj/v1/{cnpj_only}', timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            return data
        return {'error': 'not found'}, 404
    except Exception as e:
        return {'error': str(e)}, 500


@bp_config.route('/configuracao/lookup/cep')
def lookup_cep():
    cep = request.args.get('cep')
    if not cep:
        return {'error': 'cep required'}, 400
    cep_only = ''.join(filter(str.isdigit, cep))
    try:
        resp = requests.get(f'https://viacep.com.br/ws/{cep_only}/json/', timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            return data
        return {'error': 'not found'}, 404
    except Exception as e:
        return {'error': str(e)}, 500


@bp_config.route('/uploads/configuracao/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)
