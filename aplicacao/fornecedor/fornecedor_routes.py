from flask import Blueprint, render_template, request, redirect, url_for
from .fornecedor_model import Fornecedor
from aplicacao.extensoes import db
from datetime import datetime

fornecedor_bp = Blueprint(
    'fornecedor',
    __name__,
    url_prefix='/fornecedores',
    template_folder='templates'
)

# Gerador de código automático
def gerar_codigo_fornecedor():
    ultimo = Fornecedor.query.order_by(Fornecedor.id.desc()).first()
    if not ultimo or not ultimo.codigo or not ultimo.codigo.startswith("FOR"):
        return "FOR0001"
    try:
        numero = int(ultimo.codigo[3:]) + 1
    except Exception:
        numero = 1
    return f"FOR{numero:04}"

@fornecedor_bp.route('/')
def listar_fornecedores():
    fornecedores = Fornecedor.query.all()
    return render_template('fornecedor/lista.html', fornecedores=fornecedores)

@fornecedor_bp.route('/cadastrar', methods=['GET', 'POST'])
def novo_fornecedor():
    if request.method == 'POST':
        fornecedor = Fornecedor()
        fornecedor.codigo = gerar_codigo_fornecedor()
        fornecedor.nome = request.form['nome']
        fornecedor.cpf_cnpj = request.form.get('cpf_cnpj')
        fornecedor.telefone = request.form.get('telefone')
        fornecedor.email = request.form.get('email')
        fornecedor.cep = request.form.get('cep')
        fornecedor.endereco = request.form.get('endereco')
        fornecedor.numero = request.form.get('numero')
        fornecedor.complemento = request.form.get('complemento')
        fornecedor.bairro = request.form.get('bairro')
        fornecedor.cidade = request.form.get('cidade')
        fornecedor.uf = request.form.get('uf')
        fornecedor.pais = request.form.get('pais', 'Brasil')
        fornecedor.inscricao_estadual = request.form.get('inscricao_estadual')
        fornecedor.inscricao_municipal = request.form.get('inscricao_municipal')
        fornecedor.observacoes = request.form.get('observacoes')
        fornecedor.ativo = True if request.form.get('ativo') in ('on', '1', 'true') else False
        fornecedor.nome_fantasia = request.form.get('nome_fantasia')
        fornecedor.logradouro = request.form.get('logradouro')
        fornecedor.apelido = request.form.get('apelido')
        fornecedor.data_cadastro = datetime.utcnow()

        db.session.add(fornecedor)
        db.session.commit()
        return redirect(url_for('fornecedor.listar_fornecedores'))
    return render_template('fornecedor/cadastro.html')

@fornecedor_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_fornecedor(id):
    fornecedor = Fornecedor.query.get_or_404(id)
    if request.method == 'POST':
        fornecedor.nome = request.form['nome']
        fornecedor.cpf_cnpj = request.form.get('cpf_cnpj')
        fornecedor.telefone = request.form.get('telefone')
        fornecedor.email = request.form.get('email')
        fornecedor.cep = request.form.get('cep')
        fornecedor.endereco = request.form.get('endereco')
        fornecedor.numero = request.form.get('numero')
        fornecedor.complemento = request.form.get('complemento')
        fornecedor.bairro = request.form.get('bairro')
        fornecedor.cidade = request.form.get('cidade')
        fornecedor.uf = request.form.get('uf')
        fornecedor.pais = request.form.get('pais', 'Brasil')
        fornecedor.inscricao_estadual = request.form.get('inscricao_estadual')
        fornecedor.inscricao_municipal = request.form.get('inscricao_municipal')
        fornecedor.observacoes = request.form.get('observacoes')
        fornecedor.ativo = True if request.form.get('ativo') in ('on', '1', 'true') else False
        fornecedor.nome_fantasia = request.form.get('nome_fantasia')
        fornecedor.logradouro = request.form.get('logradouro')
        fornecedor.apelido = request.form.get('apelido')
        db.session.commit()
        return redirect(url_for('fornecedor.listar_fornecedores'))
    return render_template('fornecedor/cadastro.html', fornecedor=fornecedor)

@fornecedor_bp.route('/excluir/<int:id>', methods=['POST'])
def excluir_fornecedor(id):
    fornecedor = Fornecedor.query.get_or_404(id)
    db.session.delete(fornecedor)
    db.session.commit()
    return redirect(url_for('fornecedor.listar_fornecedores'))

@fornecedor_bp.route('/detalhar/<int:id>', methods=['GET'])
def detalhar_fornecedor(id):
    fornecedor = Fornecedor.query.get_or_404(id)
    return render_template('fornecedor/detalhar.html', fornecedor=fornecedor)

@fornecedor_bp.route('/api/buscar_cep/<cep>')
def buscar_cep(cep):
    """API para buscar endereço pelo CEP usando ViaCEP"""
    import requests
    import re
    from flask import jsonify
    
    # Limpar CEP (remover caracteres especiais)
    cep_limpo = re.sub(r'\D', '', cep)
    
    if len(cep_limpo) != 8:
        return jsonify({'erro': 'CEP deve conter 8 dígitos'}), 400
    
    try:
        # Consultar ViaCEP
        url = f'https://viacep.com.br/ws/{cep_limpo}/json/'
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            dados = response.json()
            
            # Verificar se CEP é válido
            if 'erro' in dados:
                return jsonify({'erro': 'CEP não encontrado'}), 404
            
            return jsonify({
                'cep': dados.get('cep', ''),
                'endereco': dados.get('logradouro', ''),
                'bairro': dados.get('bairro', ''),
                'cidade': dados.get('localidade', ''),
                'uf': dados.get('uf', ''),
                'complemento': dados.get('complemento', '')
            })
        else:
            return jsonify({'erro': 'Erro na consulta do CEP'}), 500
            
    except requests.exceptions.RequestException:
        return jsonify({'erro': 'Erro de conexão com o serviço de CEP'}), 500
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500

@fornecedor_bp.route('/api/buscar_cnpj/<cnpj>')
def buscar_cnpj(cnpj):
    """API para buscar dados da empresa pelo CNPJ usando ReceitaWS"""
    import requests
    import re
    from flask import jsonify
    
    # Limpar CNPJ (remover caracteres especiais)
    cnpj_limpo = re.sub(r'\D', '', cnpj)
    
    if len(cnpj_limpo) != 14:
        return jsonify({'erro': 'CNPJ deve conter 14 dígitos'}), 400
    
    try:
        # Consultar ReceitaWS (API pública gratuita)
        url = f'https://www.receitaws.com.br/v1/cnpj/{cnpj_limpo}'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            
            # Verificar se CNPJ é válido
            if dados.get('status') == 'ERROR':
                return jsonify({'erro': dados.get('message', 'CNPJ não encontrado')}), 404
            
            return jsonify({
                'cnpj': dados.get('cnpj', ''),
                'nome': dados.get('nome', ''),
                'fantasia': dados.get('fantasia', ''),
                'endereco': dados.get('logradouro', ''),
                'numero': dados.get('numero', ''),
                'bairro': dados.get('bairro', ''),
                'cidade': dados.get('municipio', ''),
                'uf': dados.get('uf', ''),
                'cep': dados.get('cep', ''),
                'telefone': dados.get('telefone', ''),
                'email': dados.get('email', ''),
                'situacao': dados.get('situacao', ''),
                'atividade_principal': dados.get('atividade_principal', [{}])[0].get('text', '') if dados.get('atividade_principal') else ''
            })
        else:
            return jsonify({'erro': 'Erro na consulta do CNPJ'}), 500
            
    except requests.exceptions.RequestException:
        return jsonify({'erro': 'Erro de conexão com o serviço de CNPJ'}), 500
    except Exception as e:
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500
