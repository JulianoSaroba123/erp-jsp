# Endpoint de debug: listar todos os clientes em JSON (ativos e inativos)


from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, abort, send_file, Response
from .cliente_model import Cliente
from aplicacao.extensoes import db
from sqlalchemy import or_
import io
try:
    import pandas as pd
except Exception:
    pd = None

# PDF helpers
try:
    from weasyprint import HTML
    _HAS_WEASY = True
except Exception:
    _HAS_WEASY = False
    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        _HAS_REPORTLAB = True
    except Exception:
        _HAS_REPORTLAB = False
try:
    from aplicacao import csrf
except Exception:
    csrf = None

cliente_bp = Blueprint('cliente', __name__, url_prefix='/clientes', template_folder='templates')

# Helper function for CSRF exemption
def csrf_exempt(f):
    if csrf:
        return csrf.exempt(f)
    return f

def gerar_codigo_cliente():
    ultimo = Cliente.query.order_by(Cliente.id.desc()).first()
    if not ultimo or not ultimo.codigo.startswith("CLI"):
        return "CLI0001"
    numero = int(ultimo.codigo[3:]) + 1
    return f"CLI{numero:04}"

# Listagem com busca e paginação
@cliente_bp.route('')
@cliente_bp.route('/')
def listar_clientes():
    q = request.args.get('q', '').strip()
    page = request.args.get('pagina', type=int, default=1)
    per_page = 20
    
    query = Cliente.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(Cliente.nome.ilike(like),
                Cliente.email.ilike(like),
                Cliente.cpf_cnpj.ilike(like))
        )
    
    pag = query.order_by(Cliente.nome.asc()).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'cliente/lista.html',
        clientes=pag,         # pass the Pagination object so template can use .items and pagination metadata
        paginacao=pag,        # the pagination object (kept for compatibility)
        q=q
    )

# Cadastro
@cliente_bp.route('/cadastrar', methods=['GET', 'POST'])
def novo_cliente():
    if request.method == 'POST':
        try:
            # Verificar se já existe cliente com mesmo CPF/CNPJ
            cpf_cnpj = request.form.get('cpf_cnpj', '')
            # Remove qualquer formatação (pontos, traços, barras)
            cpf_cnpj = ''.join(filter(str.isdigit, cpf_cnpj))
            
            if cpf_cnpj:
                cliente_existente = Cliente.query.filter_by(cpf_cnpj=cpf_cnpj).first()
                if cliente_existente:
                    flash(f'Já existe um cliente cadastrado com este CPF/CNPJ: {cliente_existente.nome}', 'danger')
                    return render_template('cliente/cadastro.html')
            
            # Verificar se já existe cliente com mesmo email
            email = request.form.get('email')
            if email:
                cliente_existente = Cliente.query.filter_by(email=email).first()
                if cliente_existente:
                    flash(f'Já existe um cliente cadastrado com este e-mail: {cliente_existente.nome}', 'danger')
                    return render_template('cliente/cadastro.html')
            
            # Criar novo cliente
            cliente = Cliente()
            cliente.codigo = gerar_codigo_cliente()
            cliente.nome = request.form['nome']
            cliente.cpf_cnpj = cpf_cnpj if cpf_cnpj else None  # Use None em vez de string vazia
            cliente.email = email if email else None  # Use None em vez de string vazia
            cliente.telefone = request.form.get('telefone')
            cliente.apelido = request.form.get('apelido')  # Nome fantasia/apelido
            
            # Salvar campos de endereço separados (com try/except para compatibilidade)
            try:
                cliente.cep = request.form.get('cep', '')
                cliente.logradouro = request.form.get('logradouro', '')
                cliente.numero = request.form.get('numero', '')
                cliente.complemento = request.form.get('complemento', '')
                cliente.bairro = request.form.get('bairro', '')
                cliente.cidade = request.form.get('cidade', '')
                cliente.uf = request.form.get('uf', '')
                cliente.inscricao_estadual = request.form.get('inscricao_estadual', '')
                cliente.inscricao_municipal = request.form.get('inscricao_municipal', '')
                cliente.observacoes = request.form.get('observacoes', '')
            except AttributeError:
                # Se as colunas não existem, ignore
                pass
            
            # Construir endereço completo para compatibilidade
            endereco_partes = []
            logradouro = request.form.get('logradouro', '')
            numero = request.form.get('numero', '')
            complemento = request.form.get('complemento', '')
            bairro = request.form.get('bairro', '')
            cidade = request.form.get('cidade', '')
            uf = request.form.get('uf', '')
            cep = request.form.get('cep', '')
            
            if logradouro:
                endereco_partes.append(logradouro)
            if numero:
                endereco_partes.append(f"nº {numero}")
            if complemento:
                endereco_partes.append(complemento)
            if bairro:
                endereco_partes.append(f"Bairro: {bairro}")
            if cidade:
                endereco_partes.append(cidade)
            if uf:
                endereco_partes.append(uf)
            if cep:
                endereco_partes.append(f"CEP: {cep}")
            
            cliente.endereco = ', '.join(endereco_partes) if endereco_partes else ''
            cliente.pais = request.form.get('pais', 'Brasil')  # Corrigido: país padrão Brasil
            cliente.ativo = True  # Corrigido: sempre ativo por padrão

            # Log dos dados recebidos para debug
            print(f"Salvando novo cliente: {cliente.nome}, CPF/CNPJ: {cliente.cpf_cnpj}, Email: {cliente.email}")
            
            db.session.add(cliente)
            db.session.commit()
            flash('Cliente cadastrado com sucesso!', 'success')
            return redirect(url_for('cliente.listar_clientes'))
        except Exception as e:
            db.session.rollback()
            error_msg = str(e)
            print(f"Erro ao cadastrar cliente: {error_msg}")
            
            # Mensagens de erro mais específicas
            if "cpf_cnpj" in error_msg and "unique" in error_msg.lower():
                flash('Este CPF/CNPJ já está cadastrado para outro cliente.', 'danger')
            elif "email" in error_msg and "unique" in error_msg.lower():
                flash('Este e-mail já está cadastrado para outro cliente.', 'danger')
            else:
                flash(f'Erro ao cadastrar cliente: {error_msg}', 'danger')
    
    return render_template('cliente/cadastro.html')

# Edição
@cliente_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Verificar CPF/CNPJ
            cpf_cnpj = request.form.get('cpf_cnpj', '')
            cpf_cnpj = ''.join(filter(str.isdigit, cpf_cnpj))
            
            if cpf_cnpj:
                cliente_existente = Cliente.query.filter(Cliente.cpf_cnpj == cpf_cnpj, Cliente.id != id).first()
                if cliente_existente:
                    flash(f'Este CPF/CNPJ já está cadastrado para outro cliente: {cliente_existente.nome}', 'danger')
                    return render_template('cliente/cadastro.html', cliente=cliente)
            
            # Verificar e-mail
            email = request.form.get('email')
            if email:
                cliente_existente = Cliente.query.filter(Cliente.email == email, Cliente.id != id).first()
                if cliente_existente:
                    flash(f'Este e-mail já está cadastrado para outro cliente: {cliente_existente.nome}', 'danger')
                    return render_template('cliente/cadastro.html', cliente=cliente)
            
            # Atualizar dados
            cliente.nome = request.form['nome']
            cliente.cpf_cnpj = cpf_cnpj if cpf_cnpj else None
            cliente.email = email if email else None
            cliente.telefone = request.form.get('telefone')
            cliente.apelido = request.form.get('apelido')
            
            # Salvar campos de endereço separados
            try:
                cliente.cep = request.form.get('cep', '')
                cliente.logradouro = request.form.get('logradouro', '')
                cliente.numero = request.form.get('numero', '')
                cliente.complemento = request.form.get('complemento', '')
                cliente.bairro = request.form.get('bairro', '')
                cliente.cidade = request.form.get('cidade', '')
                cliente.uf = request.form.get('uf', '')
                cliente.inscricao_estadual = request.form.get('inscricao_estadual', '')
                cliente.inscricao_municipal = request.form.get('inscricao_municipal', '')
                cliente.observacoes = request.form.get('observacoes', '')
            except AttributeError:
                # Se as colunas não existem, ignore
                pass
            
            # Construir endereço completo para compatibilidade
            endereco_partes = []
            logradouro = request.form.get('logradouro', '')
            numero = request.form.get('numero', '')
            complemento = request.form.get('complemento', '')
            bairro = request.form.get('bairro', '')
            cidade = request.form.get('cidade', '')
            uf = request.form.get('uf', '')
            cep = request.form.get('cep', '')
            
            if logradouro:
                endereco_partes.append(logradouro)
            if numero:
                endereco_partes.append(f"nº {numero}")
            if complemento:
                endereco_partes.append(complemento)
            if bairro:
                endereco_partes.append(f"Bairro: {bairro}")
            if cidade:
                endereco_partes.append(cidade)
            if uf:
                endereco_partes.append(uf)
            if cep:
                endereco_partes.append(f"CEP: {cep}")
            
            cliente.endereco = ', '.join(endereco_partes) if endereco_partes else ''
            cliente.pais = request.form.get('pais', cliente.pais or 'Brasil')
            
            # Garante que o campo codigo exista
            if not hasattr(cliente, 'codigo') or not cliente.codigo:
                cliente.codigo = gerar_codigo_cliente()
            
            # Log das alterações para debug
            print(f"Atualizando cliente ID {id}: {cliente.nome}, CPF/CNPJ: {cliente.cpf_cnpj}, Email: {cliente.email}")
            
            db.session.commit()
            flash('Cliente atualizado com sucesso!', 'success')
            return redirect(url_for('cliente.listar_clientes'))
        except Exception as e:
            db.session.rollback()
            error_msg = str(e)
            print(f"Erro ao atualizar cliente: {error_msg}")
            
            # Mensagens de erro mais específicas
            if "cpf_cnpj" in error_msg and "unique" in error_msg.lower():
                flash('Este CPF/CNPJ já está cadastrado para outro cliente.', 'danger')
            elif "email" in error_msg and "unique" in error_msg.lower():
                flash('Este e-mail já está cadastrado para outro cliente.', 'danger')
            else:
                flash(f'Erro ao atualizar cliente: {error_msg}', 'danger')
    
    # Garante que o campo codigo exista ao renderizar o template
    if not hasattr(cliente, 'codigo') or not cliente.codigo:
        cliente.codigo = gerar_codigo_cliente()
    return render_template('cliente/cadastro.html', cliente=cliente, codigo_gerado=cliente.codigo)

# Simple direct deletion function that works with AJAX and direct requests
@cliente_bp.route('/excluir/<int:id>', methods=['POST', 'GET', 'DELETE'])
@csrf_exempt  # Exempt from CSRF protection
def excluir_cliente(id):
    # For GET requests, redirect to list
    if request.method == 'GET':
        return redirect(url_for('cliente.listar_clientes'))
    
    print(f"Recebida requisição para excluir cliente ID: {id}")
    
    # Get client or 404
    cliente = Cliente.query.get_or_404(id)
    print(f"Cliente encontrado: {cliente.nome}")
    
    # Create connection to handle deletion directly
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError, SQLAlchemyError
    
    # Primeiro verificamos todos os possíveis vínculos
    vinculos = []
    
    try:
        # Verificar orçamentos
        try:
            result = db.session.execute(text("SELECT COUNT(*) FROM orcamentos WHERE cliente_id = :id"), {"id": id})
            count = result.scalar()
            if count and count > 0:
                vinculos.append(f"{count} orçamento(s)")
        except Exception as e:
            # Se a tabela não existir ou ocorrer erro, ignoramos — útil em ambientes de desenvolvimento
            print(f"Erro ao verificar orçamentos (ignorado): {str(e)}")
        
        # Verificar ordens de serviço
        try:
            result = db.session.execute(text("SELECT COUNT(*) FROM ordens_servico WHERE cliente_id = :id"), {"id": id})
            count = result.scalar()
            if count > 0:
                vinculos.append(f"{count} ordem(ns) de serviço")
        except Exception as e:
            print(f"Erro ao verificar ordens de serviço (ignorado): {str(e)}")
            
        # Verificar contas a receber
        try:
            result = db.session.execute(text("SELECT COUNT(*) FROM contas_receber WHERE cliente_id = :id"), {"id": id})
            count = result.scalar()
            if count > 0:
                vinculos.append(f"{count} conta(s) a receber")
        except Exception as e:
            print(f"Erro ao verificar contas a receber (ignorado): {str(e)}")
            
        # Se houver vínculos, informamos e não prosseguimos com a exclusão
        if vinculos:
            vinculos_str = ", ".join(vinculos)
            error_msg = f"Este cliente possui registros vinculados: {vinculos_str}. Não é possível excluir."
            print(f"Clente {id} possui vínculos: {vinculos_str}")
            flash(error_msg, 'danger')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': error_msg, 'vinculos': vinculos}), 400
            else:
                return redirect(url_for('cliente.listar_clientes'))
    
        # Se não houver vínculos, prosseguimos com a exclusão
        print(f"Tentando excluir cliente ID: {id}, Nome: {cliente.nome}")
        
        # Vamos tentar usar o SQLAlchemy primeiro
        try:
            db.session.delete(cliente)
            db.session.commit()
            print(f"Cliente {id} excluído com sucesso via SQLAlchemy")
        except Exception as e:
            print(f"Erro ao excluir via SQLAlchemy, tentando SQL direto: {str(e)}")
            db.session.rollback()
            # Fallback para SQL direto
            result = db.session.execute(text("DELETE FROM clientes WHERE id = :id"), {"id": id})
            db.session.commit()
            print(f"Cliente {id} excluído com SQL direto. Linhas afetadas: {result.rowcount}")
        
        # Success message
        flash('Cliente excluído com sucesso!', 'success')
        
        # AJAX response if needed
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Cliente excluído com sucesso!'})
            
    except IntegrityError as e:
        db.session.rollback()
        error_msg = 'Não é possível excluir este cliente porque ele está vinculado a outros registros no sistema.'
        print(f"Erro de integridade ao excluir cliente ID {id}: {str(e)}")
        flash(error_msg, 'danger')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': error_msg}), 400
            
    except SQLAlchemyError as e:
        db.session.rollback()
        error_msg = f'Erro do banco de dados ao excluir cliente: {str(e)}'
        print(f"Erro SQLAlchemy ao excluir cliente ID {id}: {str(e)}")
        flash(error_msg, 'danger')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': error_msg}), 500
            
    except Exception as e:
        db.session.rollback()
        error_msg = f'Erro ao excluir cliente: {str(e)}'
        print(f"Erro genérico ao excluir cliente ID {id}: {str(e)}")
        flash(error_msg, 'danger')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': error_msg}), 500
    
    # Default response for non-AJAX
    return redirect(url_for('cliente.listar_clientes'))

# Detalhamento
@cliente_bp.route('/detalhar/<int:id>')
def detalhar_cliente(id):
    try:
        cliente = Cliente.query.get_or_404(id)
        return render_template('cliente/detalhar.html', cliente=cliente)
    except Exception as e:
        flash(f'Erro ao carregar detalhes do cliente: {str(e)}', 'danger')
        return redirect(url_for('cliente.listar_clientes'))

# API para busca/autocomplete
@cliente_bp.route('/api/busca', methods=['GET'])
def api_busca_clientes():
    termo = request.args.get('q', '').strip()
    query = Cliente.query
    if termo:
        query = query.filter(or_(Cliente.nome.ilike(f'%{termo}%'), Cliente.cpf_cnpj.ilike(f'%{termo}%')))
    clientes = query.filter(Cliente.ativo == True).order_by(Cliente.nome).limit(20).all()
    resultados = [
        {
            'id': c.id,
            'codigo': c.codigo,
            'nome': c.nome,
            'cpf_cnpj': c.cpf_cnpj or '',
            'telefone': c.telefone or '',
            'email': c.email or '',
            'endereco': c.endereco or ''
        }
        for c in clientes
    ]
    return jsonify(resultados)

# API RESTful básica (GET, POST, PUT, DELETE)
@cliente_bp.route('/api/', methods=['GET'])
@csrf_exempt  # API endpoint - no CSRF needed
def api_listar_clientes():
    clientes = Cliente.query.all()
    return jsonify([
        {
            'id': c.id,
            'codigo': c.codigo,
            'nome': c.nome,
            'cpf_cnpj': c.cpf_cnpj,
            'email': c.email,
            'telefone': c.telefone
        } for c in clientes
    ])


# Exportar lista completa de clientes para Excel
@cliente_bp.route('/exportar/excel')
def exportar_clientes_excel():
    clientes = Cliente.query.order_by(Cliente.nome).all()
    rows = [c.to_dict() for c in clientes]
    if pd is None:
        return jsonify({'error': 'pandas não instalado'}), 500

    df = pd.DataFrame(rows)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Clientes')
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='clientes.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


# Exportar lista completa de clientes para PDF
@cliente_bp.route('/exportar/pdf')
def exportar_clientes_pdf():
    clientes = Cliente.query.order_by(Cliente.nome).all()
    rows = [c.to_dict() for c in clientes]

    # Try weasyprint first
    if _HAS_WEASY:
        # Render a simple HTML table
        html = '<h1>Clientes</h1><table border="1" style="border-collapse:collapse;width:100%">'
        # header
        if rows:
            html += '<tr>' + ''.join(f'<th>{k}</th>' for k in rows[0].keys()) + '</tr>'
        for r in rows:
            html += '<tr>' + ''.join(f'<td>{str(v) if v is not None else ""}</td>' for v in r.values()) + '</tr>'
        html += '</table>'
        pdf = HTML(string=html).write_pdf()
        return Response(pdf, mimetype='application/pdf', headers={"Content-Disposition": "attachment;filename=clientes.pdf"})

    # Fallback to reportlab if available
    if _HAS_REPORTLAB:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph('Clientes', styles['Title']))
        for r in rows:
            story.append(Paragraph(', '.join(f"{k}: {v}" for k, v in r.items()), styles['Normal']))
        doc.build(story)
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name='clientes.pdf', mimetype='application/pdf')

    return jsonify({'error': 'Nenhuma biblioteca de PDF disponível (instale weasyprint ou reportlab)'}), 500

@cliente_bp.route('/api/<int:id>', methods=['GET'])
def api_detalhar_cliente(id):
    c = Cliente.query.get_or_404(id)
    return jsonify({
        'id': c.id,
        'codigo': c.codigo,
        'nome': c.nome,
        'cpf_cnpj': c.cpf_cnpj,
        'email': c.email,
        'telefone': c.telefone
    })

@cliente_bp.route('/api/', methods=['POST'])
@csrf_exempt  # API endpoint - no CSRF needed
def api_criar_cliente():
    data = request.json
    cliente = Cliente(
        codigo=gerar_codigo_cliente(),
        nome=data.get('nome'),
        cpf_cnpj=data.get('cpf_cnpj'),
        email=data.get('email'),
        telefone=data.get('telefone'),
        ativo=True
    )
    db.session.add(cliente)
    db.session.commit()
    return jsonify({'id': cliente.id}), 201

@cliente_bp.route('/api/<int:id>', methods=['PUT'])
@csrf_exempt  # API endpoint - no CSRF needed
def api_editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    data = request.json
    cliente.nome = data.get('nome', cliente.nome)
    cliente.cpf_cnpj = data.get('cpf_cnpj', cliente.cpf_cnpj)
    cliente.email = data.get('email', cliente.email)
    cliente.telefone = data.get('telefone', cliente.telefone)
    db.session.commit()
    return jsonify({'msg': 'Cliente atualizado'})

@cliente_bp.route('/api/<int:id>', methods=['DELETE'])
def api_excluir_cliente(id):
    try:
        cliente = Cliente.query.get_or_404(id)
        db.session.delete(cliente)
        db.session.commit()
        return jsonify({'msg': 'Cliente excluído'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Método alternativo para exclusão com verificação de dependências
@cliente_bp.route('/excluir_alternativo/<int:id>', methods=['POST'])
@csrf_exempt
def excluir_cliente_alternativo(id):
    # Verificar se o cliente existe
    cliente = Cliente.query.get_or_404(id)
    
    # Coletar todas as tabelas com possíveis relações para o cliente
    from sqlalchemy import text, inspect
    
    try:
        # Verificar se há dependências em orçamentos
        result = db.session.execute(text("SELECT COUNT(*) FROM orcamentos WHERE cliente_id = :id"), {"id": id})
        count = result.scalar()
        if count > 0:
            return jsonify({
                'success': False, 
                'message': f'Este cliente possui {count} orçamentos vinculados e não pode ser excluído.'
            }), 400
            
        # Verificar dependências em ordens de serviço
        result = db.session.execute(text("SELECT COUNT(*) FROM ordens_servico WHERE cliente_id = :id"), {"id": id})
        count = result.scalar()
        if count > 0:
            return jsonify({
                'success': False, 
                'message': f'Este cliente possui {count} ordens de serviço vinculadas e não pode ser excluído.'
            }), 400

        # Verificar dependências em contas a receber
        result = db.session.execute(text("SELECT COUNT(*) FROM contas_receber WHERE cliente_id = :id"), {"id": id})
        count = result.scalar()
        if count > 0:
            return jsonify({
                'success': False, 
                'message': f'Este cliente possui {count} contas a receber vinculadas e não pode ser excluído.'
            }), 400
        
        # Se não há dependências, tenta excluir
        db.session.execute(text("DELETE FROM clientes WHERE id = :id"), {"id": id})
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Cliente excluído com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False, 
            'message': f'Erro ao excluir cliente: {str(e)}'
        }), 500

# Rota especial para forçar exclusão (APENAS PARA TESTE/DESENVOLVIMENTO)
@cliente_bp.route('/excluir_teste/<int:id>', methods=['POST'])
@csrf_exempt
def excluir_cliente_teste(id):
    """
    ATENÇÃO: Esta rota é apenas para fins de teste e desenvolvimento.
    Ela força a exclusão de um cliente, removendo todos os seus vínculos primeiro.
    NÃO USE EM PRODUÇÃO pois pode causar perda de dados.
    """
    from flask import current_app

    # Bloqueia em produção
    if not current_app.debug:
        abort(403)

    try:
        # Verificar se o cliente existe
        cliente = Cliente.query.get_or_404(id)
        nome_cliente = cliente.nome
        
        # Coletar informações sobre vínculos para log
        vinculos = []

        # Usar transação para garantir consistência e lidar com tabelas ausentes
        from sqlalchemy import text, exc

        def table_exists(table_name):
            """Verifica se uma tabela existe no schema public (Postgres)."""
            try:
                r = db.session.execute(text("SELECT to_regclass(:t)"), {"t": f"public.{table_name}"}).scalar()
                return r is not None
            except Exception:
                return False

        # Verificar e excluir orçamentos (se existir a tabela)
        try:
            if table_exists('orcamentos'):
                result = db.session.execute(text("SELECT COUNT(*) FROM orcamentos WHERE cliente_id = :id"), {"id": id})
                count = result.scalar()
                if count > 0:
                    vinculos.append(f"{count} orçamento(s)")
                    db.session.execute(text("DELETE FROM orcamentos WHERE cliente_id = :id"), {"id": id})
        except exc.DatabaseError as e:
            print(f"[TESTE] Erro ao operar sobre 'orcamentos' (ignorado): {e}")

        # Verificar e excluir ordens de serviço (se existir a tabela)
        try:
            if table_exists('ordens_servico'):
                result = db.session.execute(text("SELECT COUNT(*) FROM ordens_servico WHERE cliente_id = :id"), {"id": id})
                count = result.scalar()
                if count > 0:
                    vinculos.append(f"{count} ordem(ns) de serviço")

                    # Excluir lançamentos financeiros relacionados às OS (se existir)
                    if table_exists('financeiro_lancamentos_os'):
                        try:
                            db.session.execute(text("""
                                DELETE FROM financeiro_lancamentos_os
                                WHERE os_id IN (SELECT id FROM ordens_servico WHERE cliente_id = :id)
                            """), {"id": id})
                            print(f"[TESTE] Removidos lançamentos financeiros das OS do cliente {id}")
                        except Exception as e:
                            print(f"[TESTE] Erro ao remover lançamentos financeiros (ignorado): {e}")

                    # Excluir parcelas relacionadas às ordens (se existir tabela 'parcelas')
                    if table_exists('parcelas'):
                        try:
                            db.session.execute(text("""
                                DELETE FROM parcelas
                                WHERE ordem_servico_id IN (SELECT id FROM ordens_servico WHERE cliente_id = :id)
                            """), {"id": id})
                            print(f"[TESTE] Removidas parcelas das OS do cliente {id}")
                        except Exception as e:
                            print(f"[TESTE] Erro ao remover parcelas (ignorado): {e}")

                    # Agora excluir as ordens de serviço
                    db.session.execute(text("DELETE FROM ordens_servico WHERE cliente_id = :id"), {"id": id})
        except exc.DatabaseError as e:
            print(f"[TESTE] Erro ao operar sobre 'ordens_servico' (ignorado): {e}")

        # Verificar e excluir contas a receber (se a tabela existir)
        try:
            if table_exists('contas_receber'):
                result = db.session.execute(text("SELECT COUNT(*) FROM contas_receber WHERE cliente_id = :id"), {"id": id})
                count = result.scalar()
                if count > 0:
                    vinculos.append(f"{count} conta(s) a receber")
                    db.session.execute(text("DELETE FROM contas_receber WHERE cliente_id = :id"), {"id": id})
        except exc.DatabaseError as e:
            print(f"[TESTE] Erro ao operar sobre 'contas_receber' (ignorado): {e}")

        # Itens de orçamentos (se existirem)
        try:
            if table_exists('orcamento_itens') and table_exists('orcamentos'):
                db.session.execute(text("""
                    DELETE FROM orcamento_itens
                    WHERE orcamento_id IN (SELECT id FROM orcamentos WHERE cliente_id = :id)
                """), {"id": id})
                print(f"[TESTE] Removidos itens de orçamentos do cliente {id}")
        except Exception as e:
            print(f"[TESTE] Erro ao remover itens de orçamentos (ignorado): {e}")

        # Finalmente, excluir o cliente
        db.session.execute(text("DELETE FROM clientes WHERE id = :id"), {"id": id})
        db.session.commit()
        
        # Registrar no log o que foi excluído
        if vinculos:
            print(f"[TESTE] Cliente {id} ({nome_cliente}) excluído forçadamente. Registros removidos: {', '.join(vinculos)}")
        else:
            print(f"[TESTE] Cliente {id} ({nome_cliente}) excluído (sem vínculos).")
            
        # Retornar resposta de sucesso
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True, 
                'message': 'Cliente excluído com sucesso (modo teste)!',
                'vinculos_removidos': vinculos
            })
        else:
            flash('Cliente excluído com sucesso (modo teste)!', 'warning')
            return redirect(url_for('cliente.listar_clientes'))
            
    except Exception as e:
        db.session.rollback()
        error_msg = f'Erro ao forçar exclusão do cliente: {str(e)}'
        print(f"[ERRO-TESTE] {error_msg}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False, 
                'message': error_msg
            }), 500
        else:
            flash(error_msg, 'danger')
            return redirect(url_for('cliente.listar_clientes'))
