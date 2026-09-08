# -*- coding: utf-8 -*-
"""Aplica o hotfix de UX/consistencia do cadastro de fornecedor.

Escopo:
- remove a Inscricao Estadual duplicada do bloco superior;
- mantem uma unica IE/RG no bloco Documentos;
- padroniza novo/editar para usar rg_ie como fonte unica;
- troca Data de Fundacao nativa por DD/MM/AAAA com mascara;
- faz o parser aceitar DD/MM/AAAA e AAAA-MM-DD;
- garante que a edicao salve data_fundacao;
- separa nome PF e razao social PJ no POST;
- torna a resposta da consulta CNPJ explicita para razao_social.

Uso local somente na branch fix/fornecedor-data-ie.
"""
from pathlib import Path

FORM = Path('app/fornecedor/templates/fornecedor/form.html')
ROUTES = Path('app/fornecedor/fornecedor_routes.py')
API = Path('app/fornecedor/consultas_api.py')


def replace_once(texto, antigo, novo, marcador):
    qtd = texto.count(antigo)
    if qtd != 1:
        raise SystemExit(f'ABORTADO: esperado 1 marcador para {marcador}, encontrado {qtd}.')
    return texto.replace(antigo, novo, 1)


def limpar_trailing_whitespace(texto):
    """Remove espacos/tabs no fim das linhas e preserva newline final."""
    return '\n'.join(linha.rstrip() for linha in texto.splitlines()) + '\n'


def main():
    form = FORM.read_text(encoding='utf-8')
    routes = ROUTES.read_text(encoding='utf-8')
    api = API.read_text(encoding='utf-8')

    # Nomes distintos no HTML: PF e PJ nao podem compartilhar name="nome".
    form = replace_once(
        form,
        '''                                           id="nome" \n                                           name="nome" ''',
        '''                                           id="nome" \n                                           name="nome_pf" ''',
        'name do Nome PF',
    )
    form = replace_once(
        form,
        '''                                                   id="razao_social_pj" \n                                                   name="nome" ''',
        '''                                                   id="razao_social_pj" \n                                                   name="razao_social" ''',
        'name da Razao Social PJ',
    )

    bloco_ie = '''                                        <div class="col-md-6">\n                                            <label for="nome_fantasia" class="form-label">Nome Fantasia *</label>\n                                            <input type="text" \n                                                   class="form-control" \n                                                   id="nome_fantasia" \n                                                   name="nome_fantasia" \n                                                   value="{{ fornecedor.nome_fantasia or '' }}"\n                                                   maxlength="150"\n                                                   placeholder="Nome fantasia da empresa">\n                                        </div>\n                                        <div class="col-md-6">\n                                            <label for="inscricao_estadual" class="form-label">Inscrição Estadual</label>\n                                            <input type="text" \n                                                   class="form-control" \n                                                   id="inscricao_estadual" \n                                                   name="inscricao_estadual" \n                                                   value="{{ fornecedor.inscricao_estadual or '' }}"\n                                                   maxlength="20"\n                                                   placeholder="Inscrição Estadual">\n                                        </div>'''

    bloco_ie_novo = '''                                        <div class="col-md-12">\n                                            <label for="nome_fantasia" class="form-label">Nome Fantasia *</label>\n                                            <input type="text"\n                                                   class="form-control"\n                                                   id="nome_fantasia"\n                                                   name="nome_fantasia"\n                                                   value="{{ fornecedor.nome_fantasia or '' }}"\n                                                   maxlength="150"\n                                                   placeholder="Nome fantasia da empresa">\n                                        </div>'''

    form = replace_once(form, bloco_ie, bloco_ie_novo, 'IE duplicada no bloco PJ')

    data_antiga = '''                                <input type="date" \n                                       class="form-control" \n                                       id="data_fundacao" \n                                       name="data_fundacao" \n                                       value="{{ fornecedor.data_fundacao or '' }}">'''

    data_nova = '''                                <input type="text"\n                                       class="form-control"\n                                       id="data_fundacao"\n                                       name="data_fundacao"\n                                       value="{{ fornecedor.data_fundacao.strftime('%d/%m/%Y') if fornecedor.data_fundacao else '' }}"\n                                       inputmode="numeric"\n                                       maxlength="10"\n                                       autocomplete="off"\n                                       placeholder="DD/MM/AAAA">'''

    form = replace_once(form, data_antiga, data_nova, 'campo data_fundacao')

    mascara_cep = '''        function mascaraCep(value) {\n            value = value.replace(/\\D/g, '');\n            value = value.replace(/(\\d{5})(\\d)/, '$1-$2');\n            return value;\n        }\n        \n        // Máscara para telefone'''

    mascara_data = '''        function mascaraCep(value) {\n            value = value.replace(/\\D/g, '');\n            value = value.replace(/(\\d{5})(\\d)/, '$1-$2');\n            return value;\n        }\n\n        function mascaraData(value) {\n            value = value.replace(/\\D/g, '').slice(0, 8);\n            value = value.replace(/(\\d{2})(\\d)/, '$1/$2');\n            value = value.replace(/(\\d{2})(\\d)/, '$1/$2');\n            return value;\n        }\n        \n        // Máscara para telefone'''

    form = replace_once(form, mascara_cep, mascara_data, 'funcao mascaraData')

    listener_cep = '''        document.getElementById('cep').addEventListener('input', function() {\n            this.value = mascaraCep(this.value);\n        });\n        \n        ['telefone', 'celular', 'whatsapp', 'contato_telefone'].forEach(id => {'''

    listener_data = '''        document.getElementById('cep').addEventListener('input', function() {\n            this.value = mascaraCep(this.value);\n        });\n\n        const dataFundacaoInput = document.getElementById('data_fundacao');\n        if (dataFundacaoInput) {\n            dataFundacaoInput.addEventListener('input', function() {\n                this.value = mascaraData(this.value);\n            });\n        }\n        \n        ['telefone', 'celular', 'whatsapp', 'contato_telefone'].forEach(id => {'''

    form = replace_once(form, listener_cep, listener_data, 'listener data_fundacao')

    # Frontend aceita chave explicita razao_social e mantem compatibilidade com nome.
    form = replace_once(
        form,
        '''                            if (data.data.nome) {\n                                const razaoSocial = document.getElementById('razao_social_pj');\n                                if (razaoSocial) {\n                                    razaoSocial.value = data.data.nome;\n                                    camposPreenchidos.push('Razão Social');\n                                }\n                            }''',
        '''                            const razaoSocialApi = data.data.razao_social || data.data.nome;\n                            if (razaoSocialApi) {\n                                const razaoSocial = document.getElementById('razao_social_pj');\n                                if (razaoSocial) {\n                                    razaoSocial.value = razaoSocialApi;\n                                    camposPreenchidos.push('Razão Social');\n                                }\n                            }''',
        'preenchimento da Razao Social',
    )

    parser_antigo = '''def _parse_date(value):\n    """Converte string para date."""\n    if not value or value.strip() == '':\n        return None\n    try:\n        from datetime import datetime\n        return datetime.strptime(value, '%Y-%m-%d').date()\n    except (ValueError, AttributeError):\n        return None'''

    parser_novo = '''def _parse_date(value):\n    """Converte datas em AAAA-MM-DD ou DD/MM/AAAA para date."""\n    if not value or value.strip() == '':\n        return None\n    from datetime import datetime\n    valor = value.strip()\n    for formato in ('%Y-%m-%d', '%d/%m/%Y'):\n        try:\n            return datetime.strptime(valor, formato).date()\n        except ValueError:\n            continue\n    return None'''

    routes = replace_once(routes, parser_antigo, parser_novo, 'parser de data')

    # Novo fornecedor: resolve nome canonico conforme tipo.
    routes = replace_once(
        routes,
        '''        try:\n            # Coleta TODOS os dados profissionais do formulário\n            fornecedor = Fornecedor(\n                nome=request.form.get('nome', '').strip(),''',
        '''        try:\n            # Coleta TODOS os dados profissionais do formulário\n            tipo_fornecedor = request.form.get('tipo', 'PJ')\n            nome_fornecedor = (\n                request.form.get('razao_social', '').strip()\n                if tipo_fornecedor == 'PJ'\n                else request.form.get('nome_pf', '').strip()\n            )\n            fornecedor = Fornecedor(\n                nome=nome_fornecedor,''',
        'nome canonico no novo fornecedor',
    )
    routes = replace_once(
        routes,
        '''                tipo=request.form.get('tipo', 'PJ'),''',
        '''                tipo=tipo_fornecedor,''',
        'tipo canonico no novo fornecedor',
    )

    novo_docs_antigo = '''                rg_ie=request.form.get('rg_ie', '').strip(),\n                inscricao_estadual=request.form.get('rg_ie', '').strip(),\n                inscricao_municipal=request.form.get('inscricao_municipal', '').strip(),\n                im=request.form.get('im', '').strip(),'''

    novo_docs_novo = '''                rg_ie=request.form.get('rg_ie', '').strip(),\n                inscricao_estadual=(request.form.get('rg_ie', '').strip() if tipo_fornecedor == 'PJ' else ''),\n                inscricao_municipal=(request.form.get('im', '').strip() if tipo_fornecedor == 'PJ' else ''),\n                im=request.form.get('im', '').strip(),'''

    routes = replace_once(routes, novo_docs_antigo, novo_docs_novo, 'documentos no novo fornecedor')

    # Edicao: mesma regra de nome canonico e mesma fonte de documentos.
    editar_nome_antigo = '''            # Atualiza dados\n            fornecedor.nome = request.form.get('nome', '').strip()\n            fornecedor.nome_fantasia = request.form.get('nome_fantasia', '').strip()\n            fornecedor.tipo = request.form.get('tipo', 'PJ')'''

    editar_nome_novo = '''            # Atualiza dados\n            fornecedor.tipo = request.form.get('tipo', 'PJ')\n            fornecedor.nome = (\n                request.form.get('razao_social', '').strip()\n                if fornecedor.tipo == 'PJ'\n                else request.form.get('nome_pf', '').strip()\n            )\n            fornecedor.nome_fantasia = request.form.get('nome_fantasia', '').strip()'''

    routes = replace_once(routes, editar_nome_antigo, editar_nome_novo, 'nome canonico na edicao')

    # A substituicao acima ja moveu fornecedor.tipo para antes do nome. Por isso
    # este marcador comeca em novo_doc, sem esperar novamente a linha do tipo.
    editar_docs_antigo = '''            novo_doc = ''.join(filter(str.isdigit, request.form.get('cnpj_cpf', '')))\n            fornecedor.inscricao_estadual = request.form.get('inscricao_estadual', '').strip()\n            fornecedor.inscricao_municipal = request.form.get('inscricao_municipal', '').strip()'''

    editar_docs_novo = '''            novo_doc = ''.join(filter(str.isdigit, request.form.get('cnpj_cpf', '')))\n            fornecedor.rg_ie = request.form.get('rg_ie', '').strip()\n            fornecedor.inscricao_estadual = fornecedor.rg_ie if fornecedor.tipo == 'PJ' else ''\n            fornecedor.im = request.form.get('im', '').strip()\n            fornecedor.inscricao_municipal = fornecedor.im if fornecedor.tipo == 'PJ' else ''\n            fornecedor.data_fundacao = _parse_date(request.form.get('data_fundacao'))'''

    routes = replace_once(routes, editar_docs_antigo, editar_docs_novo, 'documentos/data na edicao')

    # API CNPJ: chave explicita e fallback de compatibilidade.
    api = replace_once(
        api,
        '''        # Formata os dados para retornar\n        resultado = {\n            'success': True,\n            'data': {\n                'nome': data.get('nome', ''),''',
        '''        # Formata os dados para retornar\n        razao_social = (\n            data.get('nome')\n            or data.get('razao_social')\n            or data.get('razaoSocial')\n            or ''\n        )\n        resultado = {\n            'success': True,\n            'data': {\n                'nome': razao_social,\n                'razao_social': razao_social,''',
        'razao_social na API CNPJ',
    )

    form = limpar_trailing_whitespace(form)
    routes = limpar_trailing_whitespace(routes)
    api = limpar_trailing_whitespace(api)

    FORM.write_text(form, encoding='utf-8')
    ROUTES.write_text(routes, encoding='utf-8')
    API.write_text(api, encoding='utf-8')
    print('OK - Cadastro de fornecedor corrigido: nome/razao social, Data de Fundacao e IE padronizados.')


if __name__ == '__main__':
    main()
