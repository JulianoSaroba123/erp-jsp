# Adicionando as rotas de consulta CNPJ e CEP ao final do arquivo

    return jsonify(resultado)


# === NOVAS ROTAS PARA CONSULTA AUTOMÁTICA ===

@cliente_bp.route('/api/consultar-cnpj/<cnpj>')
def consultar_cnpj(cnpj):
    """
    Consulta dados da empresa via CNPJ usando a API ReceitaWS.
    
    Args:
        cnpj (str): CNPJ da empresa (com ou sem formatação)
    
    Returns:
        json: Dados da empresa ou erro
    """
    try:
        # Remove formatação do CNPJ
        cnpj_limpo = re.sub(r'[^0-9]', '', cnpj)
        
        if len(cnpj_limpo) != 14:
            return jsonify({
                'success': False,
                'error': 'CNPJ deve ter 14 dígitos'
            }), 400
        
        # Consulta API ReceitaWS
        url = f'https://www.receitaws.com.br/v1/cnpj/{cnpj_limpo}'
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return jsonify({
                'success': False,
                'error': 'Erro ao consultar CNPJ'
            }), 500
        
        data = response.json()
        
        if data.get('status') == 'ERROR':
            return jsonify({
                'success': False,
                'error': data.get('message', 'CNPJ não encontrado')
            }), 404
        
        # Formata os dados para retornar
        resultado = {
            'success': True,
            'data': {
                'nome': data.get('nome', ''),
                'fantasia': data.get('fantasia', ''),
                'cnpj': data.get('cnpj', ''),
                'situacao': data.get('situacao', ''),
                'email': data.get('email', ''),
                'telefone': data.get('telefone', ''),
                'endereco': {
                    'logradouro': data.get('logradouro', ''),
                    'numero': data.get('numero', ''),
                    'complemento': data.get('complemento', ''),
                    'bairro': data.get('bairro', ''),
                    'cidade': data.get('municipio', ''),
                    'uf': data.get('uf', ''),
                    'cep': data.get('cep', '')
                }
            }
        }
        
        return jsonify(resultado)
        
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'Timeout ao consultar CNPJ'
        }), 408
        
    except requests.exceptions.RequestException:
        return jsonify({
            'success': False,
            'error': 'Erro de conexão ao consultar CNPJ'
        }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500


@cliente_bp.route('/api/consultar-cep/<cep>')
def consultar_cep(cep):
    """
    Consulta endereço via CEP usando a API ViaCEP.
    
    Args:
        cep (str): CEP (com ou sem formatação)
    
    Returns:
        json: Dados do endereço ou erro
    """
    try:
        # Remove formatação do CEP
        cep_limpo = re.sub(r'[^0-9]', '', cep)
        
        if len(cep_limpo) != 8:
            return jsonify({
                'success': False,
                'error': 'CEP deve ter 8 dígitos'
            }), 400
        
        # Consulta API ViaCEP
        url = f'https://viacep.com.br/ws/{cep_limpo}/json/'
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return jsonify({
                'success': False,
                'error': 'Erro ao consultar CEP'
            }), 500
        
        data = response.json()
        
        if data.get('erro'):
            return jsonify({
                'success': False,
                'error': 'CEP não encontrado'
            }), 404
        
        # Formata os dados para retornar
        resultado = {
            'success': True,
            'data': {
                'cep': data.get('cep', ''),
                'logradouro': data.get('logradouro', ''),
                'complemento': data.get('complemento', ''),
                'bairro': data.get('bairro', ''),
                'cidade': data.get('localidade', ''),
                'uf': data.get('uf', ''),
                'ibge': data.get('ibge', ''),
                'gia': data.get('gia', ''),
                'ddd': data.get('ddd', ''),
                'siafi': data.get('siafi', '')
            }
        }
        
        return jsonify(resultado)
        
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'Timeout ao consultar CEP'
        }), 408
        
    except requests.exceptions.RequestException:
        return jsonify({
            'success': False,
            'error': 'Erro de conexão ao consultar CEP'
        }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500