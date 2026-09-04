# -*- coding: utf-8 -*-
"""Contrato visual do PDF comercial ativo de propostas."""
import os
import sys
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

os.environ['FLASK_CONFIG'] = 'testing'
os.environ['FLASK_ENV'] = 'testing'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import create_app
from app.configuracao import configuracao_utils


def moeda(valor):
    return f'R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def montar_proposta(**overrides):
    cliente = SimpleNamespace(
        nome='Indústria Exemplo Ltda.', tipo='PJ', cpf_cnpj='12.345.678/0001-90',
        telefone='(11) 99999-0000', email='contato@industriaexemplo.com.br',
        endereco='Rua da Produção, 100', endereco_completo='Rua da Produção, 100 - São Paulo/SP',
    )
    dados = dict(
        codigo='PROPTESTPDF001', cliente=cliente, titulo='Adequação elétrica industrial',
        descricao='Escopo técnico inicial.', observacoes='', vendedor='Equipe Comercial',
        data_emissao=date(2026, 9, 4), valor_produtos=Decimal('0.00'),
        valor_servicos=Decimal('0.00'), desconto=Decimal('0.00'), valor_total=Decimal('0.00'),
        forma_pagamento='a_vista', prazo_execucao='10 dias úteis', garantia='90 dias',
        validade=30, entrada=Decimal('0.00'), intervalo_parcelas=30,
        condicoes_pagamento='Pagamento conforme condições comerciais.',
        valida_ate=date(2026, 10, 4),
    )
    dados.update(overrides)
    return SimpleNamespace(**dados)


def item_produto(indice):
    return SimpleNamespace(descricao=f'Material técnico de instalação {indice}', quantidade=Decimal('2'), valor_unitario=Decimal('125.00'), valor_total=Decimal('250.00'))


def item_servico(indice, descricao=None):
    return SimpleNamespace(descricao=descricao or f'Serviço técnico especializado {indice}', tipo_servico='fechado', quantidade=Decimal('1'), valor_unitario=Decimal('500.00'), valor_total=Decimal('500.00'))


def renderizar(app, proposta, produtos=None, servicos=None, parcelas=None):
    config = SimpleNamespace(nome_fantasia='JSP Elétrica Industrial & Solar', cnpj='41.280.764/0001-65', logradouro='Av. Paulista', numero='1000', bairro='Bela Vista', cidade='São Paulo', uf='SP', cep='01310-100', telefone='(11) 99999-0000', telefone2=None, email='contato@jsp.com.br', site='www.jsp.com.br', inscricao_estadual=None, banco='CORA SCFI - 403', agencia='0001', conta='4633457-0', pix='41.280.764/0001-65', missao=None, visao=None, valores=None, frase_assinatura=None)
    with app.app_context():
        from flask import render_template
        return render_template('proposta/pdf_proposta.html', proposta=proposta, itens_produto=produtos or [], itens_servico=servicos or [], parcelas=parcelas or [], config=config, logo_url='data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==')


def executar_testes():
    configuracao_utils.get_config = lambda *args, **kwargs: None
    app = create_app('testing')
    cenarios = [
        ('curta', montar_proposta()),
        ('produtos', montar_proposta(valor_produtos=Decimal('250.00'), valor_total=Decimal('250.00')), [item_produto(1)], []),
        ('servicos', montar_proposta(valor_servicos=Decimal('500.00'), valor_total=Decimal('500.00')), [], [item_servico(1)]),
        ('misto', montar_proposta(valor_produtos=Decimal('250.00'), valor_servicos=Decimal('500.00'), valor_total=Decimal('750.00')), [item_produto(1)], [item_servico(1)]),
        ('descricao_longa', montar_proposta(descricao='Detalhamento técnico.\n' * 140, valor_servicos=Decimal('500.00'), valor_total=Decimal('500.00')), [], [item_servico(1, 'Descrição técnica extensa com especificações de instalação, segurança e comissionamento. ' * 8)]),
        ('desconto', montar_proposta(valor_produtos=Decimal('1000.00'), desconto=Decimal('10.00'), valor_total=Decimal('900.00')), [item_produto(1)], []),
    ]
    parcelas = [
        SimpleNamespace(numero_parcela=0, valor_parcela=Decimal('100.00'), data_vencimento=date(2026, 9, 4), status='pendente'),
        SimpleNamespace(numero_parcela=1, valor_parcela=Decimal('450.00'), data_vencimento=date(2026, 10, 4), status='pendente'),
        SimpleNamespace(numero_parcela=2, valor_parcela=Decimal('450.00'), data_vencimento=date(2026, 11, 4), status='pendente'),
    ]
    cenarios.append(('parcelada', montar_proposta(forma_pagamento='parcelado', entrada=Decimal('10.00'), valor_total=Decimal('1000.00')), [], [], parcelas))
    cenarios.append(('multipagina', montar_proposta(valor_produtos=Decimal('7500.00'), valor_total=Decimal('7500.00')), [item_produto(indice) for indice in range(1, 31)], []))

    for nome, proposta, *itens in cenarios:
        produtos = itens[0] if itens else []
        servicos = itens[1] if len(itens) > 1 else []
        parcelas_cenario = itens[2] if len(itens) > 2 else []
        html = renderizar(app, proposta, produtos, servicos, parcelas_cenario)
        assert '@page' in html and 'size: A4' in html and 'margin: 12mm 12mm 18mm' in html, nome
        assert 'display: table-header-group' in html, nome
        if produtos or servicos or parcelas_cenario:
            assert '<thead>' in html and '<tbody>' in html, nome
        assert 'TOTAL DA PROPOSTA' not in html or 'Valor total da proposta' in html, nome
        assert 'Página ' in html and 'counter(pages)' in html, nome
        assert '📦' not in html and '🔧' not in html, nome
        if produtos:
            assert produtos[0].descricao in html, nome
            assert moeda(proposta.valor_total) in html, nome
        if servicos:
            assert servicos[0].descricao[:40] in html, nome
        if nome == 'desconto':
            assert 'Desconto comercial (10,00%)' in html and moeda(Decimal('900.00')) in html
        if nome == 'parcelada':
            assert 'Detalhamento do parcelamento (3 parcelas)' in html
            assert moeda(sum(parcela.valor_parcela for parcela in parcelas)) in html, 'Total das parcelas não corresponde à soma exibida'

        import weasyprint
        pdf_bytes = weasyprint.HTML(string=html).write_pdf()
        assert pdf_bytes.startswith(b'%PDF-'), nome
        documento = weasyprint.HTML(string=html).render()
        assert documento.pages, nome
        assert abs(documento.pages[0].width - 793.70) < 1, nome
        assert abs(documento.pages[0].height - 1122.52) < 1, nome
        if nome == 'multipagina':
            assert len(documento.pages) > 1, 'Proposta longa deveria ocupar mais de uma página'
    print('PDF PROPOSTA EXECUTIVE SUITE: OK')


if __name__ == '__main__':
    executar_testes()
