# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Rotas de Notas Fiscais de Serviço (NFS-e)
=========================================================

Rotas e views para gerenciamento de Notas Fiscais de Serviços Eletrônicas.

Autor: JSP Soluções
Data: 2026
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, make_response
from flask_login import login_required, current_user
from datetime import datetime, date
from decimal import Decimal
from app.extensoes import db
from app.financeiro.nfse_model import NotaFiscalServico
from app.cliente.cliente_model import Cliente
from app.ordem_servico.ordem_servico_model import OrdemServico
from app.configuracao.configuracao_model import Configuracao
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

bp_nfse = Blueprint('nfse', __name__, url_prefix='/financeiro/nfse')


@bp_nfse.route('/')
@login_required
def listar():
    """Listar todas as NFS-e."""
    # Filtros
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    status = request.args.get('status')
    cliente_id = request.args.get('cliente_id')
    busca = request.args.get('busca')
    
    query = NotaFiscalServico.query.filter_by(ativo=True)
    
    # Aplicar filtros
    if data_inicio:
        query = query.filter(NotaFiscalServico.data_emissao >= datetime.strptime(data_inicio, '%Y-%m-%d').date())
    if data_fim:
        query = query.filter(NotaFiscalServico.data_emissao <= datetime.strptime(data_fim, '%Y-%m-%d').date())
    if status:
        query = query.filter(NotaFiscalServico.status == status)
    if cliente_id:
        query = query.filter(NotaFiscalServico.cliente_id == cliente_id)
    if busca:
        query = query.filter(
            db.or_(
                NotaFiscalServico.numero.like(f'%{busca}%'),
                NotaFiscalServico.tomador_nome.like(f'%{busca}%'),
                NotaFiscalServico.descricao_servico.like(f'%{busca}%')
            )
        )
    
    notas = query.order_by(NotaFiscalServico.data_emissao.desc()).all()
    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
    
    return render_template('financeiro/nfse/listar.html',
                         notas=notas,
                         clientes=clientes)


@bp_nfse.route('/nova', methods=['GET', 'POST'])
@login_required
def nova():
    """Criar nova NFS-e."""
    if request.method == 'POST':
        try:
            # Pegar configuração da empresa
            config = Configuracao.query.first()
            
            # Criar nova NFS-e
            nota = NotaFiscalServico(
                numero=request.form['numero'],
                numero_rps=request.form.get('numero_rps'),
                serie_rps=request.form.get('serie_rps'),
                data_emissao=datetime.strptime(request.form['data_emissao'], '%Y-%m-%d').date(),
                competencia=datetime.strptime(request.form['competencia'], '%Y-%m-%d').date() if request.form.get('competencia') else None,
                tipo_nfse=request.form.get('tipo_nfse', 'PRESTADOR'),
                status='EMITIDA',
                
                # Prestador (da configuração)
                prestador_nome=config.razao_social if config else '',
                prestador_cnpj=config.cnpj if config else '',
                prestador_im=config.inscricao_municipal if config else '',
                prestador_endereco=f"{config.logradouro}, {config.numero} - {config.bairro} - {config.cidade}/{config.uf}" if config else '',
                prestador_telefone=config.telefone if config else '',
                prestador_email=config.email if config else '',
                
                # Tomador
                tomador_nome=request.form['tomador_nome'],
                tomador_cnpj_cpf=request.form.get('tomador_cnpj_cpf'),
                tomador_im=request.form.get('tomador_im'),
                tomador_endereco=request.form.get('tomador_endereco'),
                tomador_telefone=request.form.get('tomador_telefone'),
                tomador_email=request.form.get('tomador_email'),
                
                # Serviços
                descricao_servico=request.form['descricao_servico'],
                codigo_servico=request.form.get('codigo_servico'),
                codigo_cnae=request.form.get('codigo_cnae'),
                local_prestacao=request.form.get('local_prestacao'),
                
                # Valores
                valor_servicos=Decimal(request.form['valor_servicos']),
                valor_deducoes=Decimal(request.form.get('valor_deducoes', 0)),
                
                # ISS
                aliquota_iss=Decimal(request.form.get('aliquota_iss', 0)),
                iss_retido=request.form.get('iss_retido') == 'on',
                
                # Retenções
                valor_pis=Decimal(request.form.get('valor_pis', 0)),
                valor_cofins=Decimal(request.form.get('valor_cofins', 0)),
                valor_inss=Decimal(request.form.get('valor_inss', 0)),
                valor_ir=Decimal(request.form.get('valor_ir', 0)),
                valor_csll=Decimal(request.form.get('valor_csll', 0)),
                
                # Outras informações
                natureza_operacao=request.form.get('natureza_operacao'),
                optante_simples=request.form.get('optante_simples') == 'on',
                incentivo_fiscal=request.form.get('incentivo_fiscal') == 'on',
                
                # Observações
                observacoes=request.form.get('observacoes'),
                informacoes_complementares=request.form.get('informacoes_complementares'),
                
                # Relacionamentos
                cliente_id=request.form.get('cliente_id') if request.form.get('cliente_id') else None,
                ordem_servico_id=request.form.get('ordem_servico_id') if request.form.get('ordem_servico_id') else None,
            )
            
            # Calcular valores automaticamente
            nota.calcular_valores()
            
            # Salvar
            db.session.add(nota)
            db.session.commit()
            
            # Gerar lançamento financeiro se solicitado
            if request.form.get('gerar_lancamento') == 'on':
                nota.gerar_lancamento_financeiro()
                db.session.commit()
                flash('NFS-e criada e lançamento financeiro gerado com sucesso!', 'success')
            else:
                flash('NFS-e criada com sucesso!', 'success')
            
            return redirect(url_for('nfse.visualizar', id=nota.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar NFS-e: {str(e)}', 'danger')
            print(f"Erro ao criar NFS-e: {str(e)}")
    
    # GET
    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
    ordens_servico = OrdemServico.query.filter_by(ativo=True).order_by(OrdemServico.data_abertura.desc()).limit(50).all()
    config = Configuracao.query.first()
    
    # Gerar próximo número de RPS
    ultima_nota = NotaFiscalServico.query.order_by(NotaFiscalServico.numero_rps.desc()).first()
    proximo_rps = str(int(ultima_nota.numero_rps) + 1) if ultima_nota and ultima_nota.numero_rps else '1'
    
    return render_template('financeiro/nfse/form.html',
                         nota=None,
                         clientes=clientes,
                         ordens_servico=ordens_servico,
                         config=config,
                         proximo_rps=proximo_rps)


@bp_nfse.route('/<int:id>')
@login_required
def visualizar(id):
    """Visualizar NFS-e."""
    nota = NotaFiscalServico.query.get_or_404(id)
    return render_template('financeiro/nfse/visualizar.html', nota=nota)


@bp_nfse.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Editar NFS-e."""
    nota = NotaFiscalServico.query.get_or_404(id)
    
    if nota.status == 'CANCELADA':
        flash('Não é possível editar uma NFS-e cancelada', 'warning')
        return redirect(url_for('nfse.visualizar', id=id))
    
    if request.method == 'POST':
        try:
            # Atualizar campos
            nota.observacoes = request.form.get('observacoes')
            nota.informacoes_complementares = request.form.get('informacoes_complementares')
            
            db.session.commit()
            flash('NFS-e atualizada com sucesso!', 'success')
            return redirect(url_for('nfse.visualizar', id=id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar NFS-e: {str(e)}', 'danger')
    
    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
    config = Configuracao.query.first()
    
    return render_template('financeiro/nfse/form.html',
                         nota=nota,
                         clientes=clientes,
                         config=config)


@bp_nfse.route('/<int:id>/cancelar', methods=['POST'])
@login_required
def cancelar(id):
    """Cancelar NFS-e."""
    nota = NotaFiscalServico.query.get_or_404(id)
    
    if nota.status == 'CANCELADA':
        flash('Esta NFS-e já está cancelada', 'warning')
        return redirect(url_for('nfse.visualizar', id=id))
    
    try:
        nota.status = 'CANCELADA'
        nota.observacoes = (nota.observacoes or '') + f'\n\nCANCELADA em {datetime.now().strftime("%d/%m/%Y %H:%M")} por {current_user.nome}'
        
        # Cancelar lançamento se existir
        if nota.lancamento_id:
            from app.financeiro.financeiro_model import LancamentoFinanceiro
            lancamento = LancamentoFinanceiro.query.get(nota.lancamento_id)
            if lancamento:
                lancamento.status = 'cancelado'
        
        db.session.commit()
        flash('NFS-e cancelada com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao cancelar NFS-e: {str(e)}', 'danger')
    
    return redirect(url_for('nfse.visualizar', id=id))


@bp_nfse.route('/<int:id>/pdf')
@login_required
def gerar_pdf(id):
    """Gerar PDF da NFS-e."""
    nota = NotaFiscalServico.query.get_or_404(id)
    config = Configuracao.query.first()
    
    # Criar buffer para o PDF
    buffer = io.BytesIO()
    
    # Criar PDF
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Cabeçalho
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width/2, height - 2*cm, "NOTA FISCAL DE SERVIÇOS ELETRÔNICA")
    p.drawCentredString(width/2, height - 2.7*cm, f"NFS-e Nº {nota.numero}")
    
    # Dados do prestador
    y = height - 4*cm
    p.setFont("Helvetica-Bold", 12)
    p.drawString(2*cm, y, "PRESTADOR DOS SERVIÇOS")
    y -= 0.7*cm
    p.setFont("Helvetica", 10)
    p.drawString(2*cm, y, f"{nota.prestador_nome}")
    y -= 0.5*cm
    p.drawString(2*cm, y, f"CNPJ: {nota.prestador_cnpj}")
    y -= 0.5*cm
    p.drawString(2*cm, y, f"IM: {nota.prestador_im}")
    y -= 0.5*cm
    p.drawString(2*cm, y, f"{nota.prestador_endereco}")
    
    # Dados do tomador
    y -= 1*cm
    p.setFont("Helvetica-Bold", 12)
    p.drawString(2*cm, y, "TOMADOR DOS SERVIÇOS")
    y -= 0.7*cm
    p.setFont("Helvetica", 10)
    p.drawString(2*cm, y, f"{nota.tomador_nome}")
    y -= 0.5*cm
    p.drawString(2*cm, y, f"CPF/CNPJ: {nota.tomador_cnpj_cpf or 'Não informado'}")
    y -= 0.5*cm
    if nota.tomador_endereco:
        p.drawString(2*cm, y, f"{nota.tomador_endereco}")
        y -= 0.5*cm
    
    # Serviços prestados
    y -= 1*cm
    p.setFont("Helvetica-Bold", 12)
    p.drawString(2*cm, y, "DISCRIMINAÇÃO DOS SERVIÇOS")
    y -= 0.7*cm
    p.setFont("Helvetica", 10)
    
    # Quebrar descrição em linhas
    descricao_linhas = nota.descricao_servico.split('\n')
    for linha in descricao_linhas[:10]:  # Limitar a 10 linhas
        p.drawString(2*cm, y, linha[:80])  # Limitar a 80 caracteres
        y -= 0.5*cm
    
    # Valores
    y -= 1*cm
    p.setFont("Helvetica-Bold", 12)
    p.drawString(2*cm, y, "VALORES")
    y -= 0.7*cm
    p.setFont("Helvetica", 10)
    p.drawString(2*cm, y, f"Valor dos Serviços:")
    p.drawRightString(width - 2*cm, y, f"R$ {nota.valor_servicos:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    y -= 0.5*cm
    
    if nota.valor_deducoes:
        p.drawString(2*cm, y, f"(-) Deduções:")
        p.drawRightString(width - 2*cm, y, f"R$ {nota.valor_deducoes:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        y -= 0.5*cm
    
    p.drawString(2*cm, y, f"Base de Cálculo:")
    p.drawRightString(width - 2*cm, y, f"R$ {nota.valor_base_calculo or 0:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    y -= 0.5*cm
    
    p.drawString(2*cm, y, f"Alíquota ISS:")
    p.drawRightString(width - 2*cm, y, f"{nota.aliquota_iss}%")
    y -= 0.5*cm
    
    p.drawString(2*cm, y, f"Valor ISS:")
    p.drawRightString(width - 2*cm, y, f"R$ {nota.valor_iss:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    y -= 0.7*cm
    
    p.setFont("Helvetica-Bold", 12)
    p.drawString(2*cm, y, f"VALOR LÍQUIDO:")
    p.drawRightString(width - 2*cm, y, f"R$ {nota.valor_liquido or 0:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    # Rodapé
    y = 3*cm
    p.setFont("Helvetica", 8)
    p.drawCentredString(width/2, y, f"Emitida em: {nota.data_emissao.strftime('%d/%m/%Y')}")
    y -= 0.5*cm
    if nota.codigo_verificacao:
        p.drawCentredString(width/2, y, f"Código de Verificação: {nota.codigo_verificacao}")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=nfse_{nota.numero}.pdf'
    
    return response


@bp_nfse.route('/<int:id>/duplicar', methods=['POST'])
@login_required
def duplicar(id):
    """Duplicar NFS-e."""
    nota_original = NotaFiscalServico.query.get_or_404(id)
    
    try:
        # Gerar novo número
        ultima_nota = NotaFiscalServico.query.order_by(NotaFiscalServico.numero.desc()).first()
        novo_numero = str(int(ultima_nota.numero) + 1) if ultima_nota else '1'
        
        # Criar nova nota
        nova_nota = NotaFiscalServico(
            numero=novo_numero,
            data_emissao=date.today(),
            tipo_nfse=nota_original.tipo_nfse,
            status='EMITIDA',
            
            # Copiar dados do prestador
            prestador_nome=nota_original.prestador_nome,
            prestador_cnpj=nota_original.prestador_cnpj,
            prestador_im=nota_original.prestador_im,
            prestador_endereco=nota_original.prestador_endereco,
            prestador_telefone=nota_original.prestador_telefone,
            prestador_email=nota_original.prestador_email,
            
            # Copiar dados do tomador
            tomador_nome=nota_original.tomador_nome,
            tomador_cnpj_cpf=nota_original.tomador_cnpj_cpf,
            tomador_im=nota_original.tomador_im,
            tomador_endereco=nota_original.tomador_endereco,
            tomador_telefone=nota_original.tomador_telefone,
            tomador_email=nota_original.tomador_email,
            
            # Copiar serviços
            descricao_servico=nota_original.descricao_servico,
            codigo_servico=nota_original.codigo_servico,
            codigo_cnae=nota_original.codigo_cnae,
            local_prestacao=nota_original.local_prestacao,
            
            # Copiar valores
            valor_servicos=nota_original.valor_servicos,
            valor_deducoes=nota_original.valor_deducoes,
            aliquota_iss=nota_original.aliquota_iss,
            iss_retido=nota_original.iss_retido,
            
            # Copiar retenções
            valor_pis=nota_original.valor_pis,
            valor_cofins=nota_original.valor_cofins,
            valor_inss=nota_original.valor_inss,
            valor_ir=nota_original.valor_ir,
            valor_csll=nota_original.valor_csll,
            
            # Copiar outras informações
            natureza_operacao=nota_original.natureza_operacao,
            optante_simples=nota_original.optante_simples,
            incentivo_fiscal=nota_original.incentivo_fiscal,
            
            # Relacionamentos
            cliente_id=nota_original.cliente_id,
        )
        
        # Calcular valores
        nova_nota.calcular_valores()
        
        db.session.add(nova_nota)
        db.session.commit()
        
        flash('NFS-e duplicada com sucesso!', 'success')
        return redirect(url_for('nfse.editar', id=nova_nota.id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao duplicar NFS-e: {str(e)}', 'danger')
        return redirect(url_for('nfse.visualizar', id=id))
