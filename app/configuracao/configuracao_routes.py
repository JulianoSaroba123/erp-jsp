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


@bp_config.route('/')
def visualizar():
    conf = Configuracao.get_solo()
    return render_template('configuracao/form_configuracao.html', configuracao=conf)


@bp_config.route('/editar', methods=['GET', 'POST'])
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
            if file and file.filename and allowed_file(file.filename):
                import base64
                from io import BytesIO
                from PIL import Image
                
                # Salvar arquivo
                filename = secure_filename(file.filename)
                save_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(save_path)
                conf.logo = save_path
                
                # Converter para base64 e salvar também (para consistência e PDFs)
                try:
                    # Abrir a imagem e redimensionar se necessário
                    img = Image.open(save_path)
                    
                    # Redimensionar se a imagem for muito grande (máx 800px)
                    max_size = 800
                    if img.width > max_size or img.height > max_size:
                        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                    
                    # Converte para base64
                    buffer = BytesIO()
                    img_format = img.format or 'PNG'
                    img.save(buffer, format=img_format)
                    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                    
                    # Determinar o MIME type
                    mime_types = {
                        'PNG': 'image/png',
                        'JPEG': 'image/jpeg',
                        'JPG': 'image/jpeg',
                        'GIF': 'image/gif',
                        'WEBP': 'image/webp'
                    }
                    mime_type = mime_types.get(img_format.upper(), 'image/png')
                    
                    # Salva o base64 com prefixo data URI no banco
                    conf.logo_base64 = f"data:{mime_type};base64,{img_base64}"
                    print(f"✅ Logo convertida para base64 e salva no banco (formato: {img_format}, MIME: {mime_type})")
                    
                except Exception as e:
                    print(f"⚠️ Erro ao converter logo para base64: {e}")
                    # Continua mesmo se falhar a conversão para base64
                    pass

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


@bp_config.route('/lookup/cnpj')
def lookup_cnpj():
    cnpj = request.args.get('cnpj')
    print(f"Busca CNPJ recebida: {cnpj}")
    
    if not cnpj:
        print(" CNPJ não fornecido")
        return {'error': 'CNPJ é obrigatório'}, 400

    # Limpa o CNPJ - remove tudo que não é dígito
    cnpj_only = ''.join(filter(str.isdigit, cnpj))
    print(f"🧹 CNPJ limpo: {cnpj_only}")
    
    # Validar se tem pelo menos 11 dígitos
    if len(cnpj_only) < 11:
        print(f" CNPJ muito curto: {len(cnpj_only)} dígitos")
        return {'error': 'CNPJ deve ter pelo menos 11 dígitos'}, 400
    
    try:
        url = f'https://brasilapi.com.br/api/cnpj/v1/{cnpj_only}'
        print(f"📡 Fazendo requisição para: {url}")
        
        resp = requests.get(url, timeout=10)
        print(f" Status da API: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f" Dados recebidos: {data.get('razao_social', 'N/A')}")
            
            # Log dos campos principais
            campos_log = ['razao_social', 'nome_fantasia', 'situacao', 'email']
            for campo in campos_log:
                if campo in data:
                    print(f"    {campo}: {data[campo]}")
            
            return data
        elif resp.status_code == 404:
            print(" CNPJ não encontrado na base de dados")
            return {'error': 'CNPJ não encontrado'}, 404
        else:
            print(f" Erro na API: {resp.status_code} - {resp.text}")
            return {'error': f'Erro na consulta: {resp.status_code}'}, 500
            
    except requests.Timeout:
        print(" Timeout na consulta")
        return {'error': 'Timeout na consulta - tente novamente'}, 500
    except requests.ConnectionError:
        print(" Erro de conexão")
        return {'error': 'Erro de conexão com o serviço de consulta'}, 500
    except Exception as e:
        print(f" Erro inesperado: {str(e)}")
        return {'error': f'Erro interno: {str(e)}'}, 500


@bp_config.route('/lookup/cep')
def lookup_cep():
    cep = request.args.get('cep')
    print(f"Busca CEP recebida: {cep}")
    
    if not cep:
        print(" CEP não fornecido")
        return {'error': 'CEP é obrigatório'}, 400
        
    # Limpa o CEP - remove tudo que não é dígito
    cep_only = ''.join(filter(str.isdigit, cep))
    print(f"🧹 CEP limpo: {cep_only}")
    
    # Validar se tem 8 dígitos
    if len(cep_only) != 8:
        print(f" CEP inválido: {len(cep_only)} dígitos")
        return {'error': 'CEP deve ter exatamente 8 dígitos'}, 400
    
    try:
        url = f'https://viacep.com.br/ws/{cep_only}/json/'
        print(f"📡 Fazendo requisição para: {url}")
        
        resp = requests.get(url, timeout=10)
        print(f" Status da API: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            
            # Verificar se o CEP foi encontrado
            if 'erro' in data:
                print(" CEP não encontrado")
                return {'error': 'CEP não encontrado'}, 404
            
            print(f" Dados recebidos: {data.get('localidade', 'N/A')} - {data.get('uf', 'N/A')}")
            
            # Log dos campos principais
            campos_log = ['logradouro', 'bairro', 'localidade', 'uf']
            for campo in campos_log:
                if campo in data and data[campo]:
                    print(f"    {campo}: {data[campo]}")
            
            return data
        else:
            print(f" Erro na API: {resp.status_code} - {resp.text}")
            return {'error': f'Erro na consulta: {resp.status_code}'}, 500
            
    except requests.Timeout:
        print(" Timeout na consulta")
        return {'error': 'Timeout na consulta - tente novamente'}, 500
    except requests.ConnectionError:
        print(" Erro de conexão")
        return {'error': 'Erro de conexão com o serviço de consulta'}, 500
    except Exception as e:
        print(f" Erro inesperado: {str(e)}")
        return {'error': f'Erro interno: {str(e)}'}, 500


@bp_config.route('/uploads/configuracao/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@bp_config.route('/fix-logo-base64')
def fix_logo_base64():
    """
    Rota administrativa para corrigir logo_base64 sem prefixo data URI.
    Adiciona o prefixo 'data:image/...;base64,' necessário para exibição.
    """
    try:
        conf = Configuracao.get_solo()
        
        if not conf.logo_base64:
            return {
                'status': 'error',
                'message': 'Nenhuma logo encontrada no banco de dados'
            }, 404
        
        # Verificar se já tem o prefixo
        if conf.logo_base64.startswith('data:image'):
            return {
                'status': 'ok',
                'message': 'Logo já está no formato correto!',
                'prefix': conf.logo_base64[:50]
            }
        
        print(f"🔧 Corrigindo logo base64...")
        print(f"   Tamanho atual: {len(conf.logo_base64)} caracteres")
        
        # Detectar formato da imagem
        mime_type = 'image/png'  # padrão
        formato_detectado = 'PNG (padrão)'
        
        if conf.logo_base64.startswith('/9j/'):
            mime_type = 'image/jpeg'
            formato_detectado = 'JPEG'
        elif conf.logo_base64.startswith('iVBOR'):
            mime_type = 'image/png'
            formato_detectado = 'PNG'
        elif conf.logo_base64.startswith('R0lGOD'):
            mime_type = 'image/gif'
            formato_detectado = 'GIF'
        
        print(f"   Formato detectado: {formato_detectado}")
        
        # Adicionar prefixo
        conf.logo_base64 = f"data:{mime_type};base64,{conf.logo_base64}"
        
        # Salvar
        db.session.commit()
        
        # Invalidar cache
        from app.configuracao import configuracao_utils
        configuracao_utils._cached = None
        
        print(f"✅ Logo corrigida com sucesso!")
        print(f"   Novo prefixo: {conf.logo_base64[:50]}...")
        
        return {
            'status': 'success',
            'message': 'Logo corrigida com sucesso!',
            'formato': formato_detectado,
            'mime_type': mime_type,
            'tamanho': len(conf.logo_base64),
            'prefix': conf.logo_base64[:50]
        }
        
    except Exception as e:
        print(f"❌ Erro ao corrigir logo: {e}")
        return {
            'status': 'error',
            'message': f'Erro ao corrigir logo: {str(e)}'
        }, 500
