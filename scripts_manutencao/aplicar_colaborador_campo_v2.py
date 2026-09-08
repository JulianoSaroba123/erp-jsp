# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app/app.py"
CLIENTE = ROOT / "app/cliente/cliente_routes.py"
OS = ROOT / "app/ordem_servico/ordem_servico_routes.py"


def replace_once(texto, antigo, novo, nome):
    qtd = texto.count(antigo)
    if qtd != 1:
        raise SystemExit(f"ABORTADO: esperado 1 marcador para {nome}, encontrado {qtd}.")
    return texto.replace(antigo, novo, 1)


# -----------------------------------------------------------------------------
# Whitelist global do colaborador: cadastro operacional + OS de campo.
# -----------------------------------------------------------------------------
app = APP.read_text(encoding="utf-8")
if "'ordem_servico.novo_operacional'" not in app:
    app = replace_once(
        app,
        """            'ordem_servico.apontamento_colaborador',\n            'cliente.listar',\n            'cliente.visualizar',\n""",
        """            'ordem_servico.apontamento_colaborador',\n            'ordem_servico.novo_operacional',\n            'ordem_servico.editar_operacional',\n            'cliente.listar',\n            'cliente.visualizar',\n            'cliente.novo_operacional',\n""",
        "whitelist de campo",
    )
APP.write_text(app, encoding="utf-8")


# -----------------------------------------------------------------------------
# Cliente de campo: somente dados operacionais. Nenhum campo financeiro/comercial
# é lido do POST. Ao salvar, segue direto para a criação da OS.
# -----------------------------------------------------------------------------
cliente = CLIENTE.read_text(encoding="utf-8")
if "def novo_operacional():" not in cliente:
    marcador_cliente = """@cliente_bp.route('/novo', methods=['GET', 'POST'])\ndef novo():\n"""
    bloco_cliente = r'''@cliente_bp.route('/novo-operacional', methods=['GET', 'POST'])
def novo_operacional():
    """Cadastro de cliente em campo pelo perfil Colaborador, sem dados financeiros."""
    if not getattr(current_user, 'is_authenticated', False) or getattr(current_user, 'tipo_usuario', None) != 'colaborador':
        flash('Cadastro operacional disponível apenas para o perfil Colaborador.', 'error')
        return redirect(url_for('cliente.listar'))

    form_data = request.form.to_dict(flat=True) if request.method == 'POST' else {}
    if request.method == 'POST':
        limits = _get_clientes_column_limits()
        truncated_fields = []
        tipo = (_sanitize_text('tipo', request.form.get('tipo'), limits, truncated_fields) or 'PF').upper()
        if tipo not in {'PF', 'PJ'}:
            tipo = 'PF'

        nome = _sanitize_text('nome', request.form.get('nome'), limits, truncated_fields)
        nome_fantasia = _sanitize_text('nome_fantasia', request.form.get('nome_fantasia'), limits, truncated_fields)
        razao_social = _sanitize_text('razao_social', request.form.get('razao_social'), limits, truncated_fields)
        if tipo == 'PJ' and not nome:
            nome = nome_fantasia or razao_social
        if not nome:
            flash('Informe o nome do cliente.', 'error')
            return render_template('cliente/form_operacional_colaborador.html', form_data=form_data)

        cpf_cnpj = _sanitize_text('cpf_cnpj', request.form.get('cpf_cnpj'), limits, truncated_fields)
        if cpf_cnpj:
            documento_numerico = re.sub(r'[^0-9]', '', cpf_cnpj)
            for existente in Cliente.query.filter(Cliente.cpf_cnpj.isnot(None)).all():
                if re.sub(r'[^0-9]', '', existente.cpf_cnpj or '') == documento_numerico:
                    if existente.ativo:
                        flash(f'Cliente {existente.nome_display} já cadastrado. Usei o cadastro existente para abrir a OS.', 'info')
                        return redirect(url_for('ordem_servico.novo_operacional', cliente_id=existente.id))
                    flash('Este documento pertence a um cliente inativo. Solicite a reativação à administração.', 'warning')
                    return render_template('cliente/form_operacional_colaborador.html', form_data=form_data)

        try:
            novo_cliente = Cliente(
                nome=nome,
                nome_fantasia=nome_fantasia,
                razao_social=razao_social,
                tipo=tipo,
                cpf_cnpj=cpf_cnpj,
                rg_ie=_sanitize_text('rg_ie', request.form.get('rg_ie'), limits, truncated_fields),
                email=_sanitize_text('email', request.form.get('email'), limits, truncated_fields),
                telefone=_sanitize_text('telefone', request.form.get('telefone'), limits, truncated_fields),
                celular=_sanitize_text('celular', request.form.get('celular'), limits, truncated_fields),
                whatsapp=_sanitize_text('whatsapp', request.form.get('whatsapp'), limits, truncated_fields),
                contato_nome=_sanitize_text('contato_nome', request.form.get('contato_nome'), limits, truncated_fields),
                contato_cargo=_sanitize_text('contato_cargo', request.form.get('contato_cargo'), limits, truncated_fields),
                contato_telefone=_sanitize_text('contato_telefone', request.form.get('contato_telefone'), limits, truncated_fields),
                contato_email=_sanitize_text('contato_email', request.form.get('contato_email'), limits, truncated_fields),
                cep=_sanitize_text('cep', request.form.get('cep'), limits, truncated_fields),
                endereco=_sanitize_text('endereco', request.form.get('endereco'), limits, truncated_fields),
                numero=_sanitize_text('numero', request.form.get('numero'), limits, truncated_fields),
                complemento=_sanitize_text('complemento', request.form.get('complemento'), limits, truncated_fields),
                bairro=_sanitize_text('bairro', request.form.get('bairro'), limits, truncated_fields),
                cidade=_sanitize_text('cidade', request.form.get('cidade'), limits, truncated_fields),
                estado=(_sanitize_text('estado', request.form.get('estado'), limits, truncated_fields) or '').upper() or None,
                pais='Brasil',
                observacoes=request.form.get('observacoes', '').strip() or None,
                observacoes_internas=None,
                limite_credito=0,
                forma_pagamento_padrao=None,
                prazo_pagamento_padrao=30,
                desconto_padrao=0,
                status='ativo',
                ativo=True,
            )
            db.session.add(novo_cliente)
            db.session.commit()
            _flash_truncation_warning(truncated_fields)
            flash(f'Cliente {novo_cliente.nome_display} cadastrado. Agora preencha a Ordem de Serviço.', 'success')
            return redirect(url_for('ordem_servico.novo_operacional', cliente_id=novo_cliente.id))
        except Exception:
            db.session.rollback()
            flash('Não foi possível cadastrar o cliente. Confira os dados e tente novamente.', 'error')

    return render_template('cliente/form_operacional_colaborador.html', form_data=form_data)


'''
    cliente = replace_once(
        cliente,
        marcador_cliente,
        bloco_cliente + marcador_cliente,
        "rota cliente operacional",
    )
CLIENTE.write_text(cliente, encoding="utf-8")


# -----------------------------------------------------------------------------
# OS de campo: criação e edição técnica próprias. Criação zera valores e
# autoescala o colaborador logado. Edição não toca em nenhum campo monetário.
# -----------------------------------------------------------------------------
os_texto = OS.read_text(encoding="utf-8")
if "def novo_operacional():" not in os_texto:
    marcador_os = """@ordem_servico_bp.route('/novo', methods=['GET', 'POST'])\ndef novo():\n"""
    bloco_os = r'''def _parse_data_operacional_campo(valor):
    if not (valor or '').strip():
        return None
    try:
        return datetime.strptime(valor, '%Y-%m-%d').date()
    except Exception:
        return None


def _aplicar_campos_tecnicos_colaborador(ordem, form_data):
    prioridade = (form_data.get('prioridade') or 'normal').strip().lower()
    if prioridade not in {'baixa', 'normal', 'alta', 'urgente'}:
        prioridade = 'normal'
    ordem.titulo = (form_data.get('titulo') or '').strip()
    ordem.solicitante = (form_data.get('solicitante') or '').strip() or None
    ordem.prioridade = prioridade
    ordem.data_prevista = _parse_data_operacional_campo(form_data.get('data_prevista'))
    ordem.equipamento = (form_data.get('equipamento') or '').strip() or None
    ordem.marca_modelo = (form_data.get('marca_modelo') or '').strip() or None
    ordem.numero_serie = (form_data.get('numero_serie') or '').strip() or None
    ordem.descricao_problema = (form_data.get('descricao_problema') or '').strip() or None
    ordem.descricao = ordem.descricao_problema
    ordem.defeito_relatado = (form_data.get('defeito_relatado') or '').strip() or None
    ordem.diagnostico_tecnico = (form_data.get('diagnostico_tecnico') or '').strip() or None
    ordem.solucao = (form_data.get('solucao') or '').strip() or None
    ordem.observacoes = (form_data.get('observacoes') or '').strip() or None


@ordem_servico_bp.route('/novo-operacional', methods=['GET', 'POST'])
def novo_operacional():
    """Cria OS operacional pelo colaborador, sem qualquer valor financeiro."""
    if not usuario_eh_colaborador():
        flash('Criação de OS de campo disponível apenas para Colaborador.', 'error')
        return redirect(url_for('ordem_servico.listar'))

    colaborador = colaborador_do_usuario_atual()
    if not colaborador:
        flash('Seu login precisa estar vinculado a um colaborador ativo antes de criar uma OS.', 'warning')
        return redirect(url_for('ordem_servico.listar'))

    clientes = buscar_clientes_ativos()
    cliente_selecionado = safe_int_convert(request.args.get('cliente_id'))
    form_data = request.form.to_dict(flat=True) if request.method == 'POST' else {}

    if request.method == 'POST':
        cliente_id = safe_int_convert(request.form.get('cliente_id'))
        cliente = Cliente.query.filter_by(id=cliente_id, ativo=True).first() if cliente_id else None
        if not cliente:
            flash('Selecione um cliente ativo.', 'error')
            return render_template('os/form_operacional_colaborador.html', ordem=None, clientes=clientes, cliente_selecionado=cliente_id, form_data=form_data)

        titulo = (request.form.get('titulo') or '').strip()
        if not titulo:
            flash('Informe o título ou serviço da OS.', 'error')
            return render_template('os/form_operacional_colaborador.html', ordem=None, clientes=clientes, cliente_selecionado=cliente_id, form_data=form_data)

        try:
            ordem = OrdemServico(
                numero=OrdemServico.gerar_proximo_numero(),
                cliente_id=cliente.id,
                titulo=titulo,
                tipo_os='operacional',
                tipo_servico='atendimento',
                status='em_execucao',
                prioridade='normal',
                data_abertura=date.today(),
                tecnico_responsavel=colaborador.nome,
                valor_servico=Decimal('0.00'),
                valor_pecas=Decimal('0.00'),
                valor_desconto=Decimal('0.00'),
                valor_total=Decimal('0.00'),
                valor_entrada=Decimal('0.00'),
                condicao_pagamento='a_vista',
                numero_parcelas=1,
                status_pagamento='pendente',
            )
            _aplicar_campos_tecnicos_colaborador(ordem, request.form)
            db.session.add(ordem)
            db.session.flush()

            trabalho = OrdemServicoColaborador(
                ordem_servico_id=ordem.id,
                colaborador_id=colaborador.id,
                data_trabalho=date.today(),
            )
            db.session.add(trabalho)
            db.session.commit()
            flash(f'OS {ordem.numero} criada e atribuída a você.', 'success')
            return redirect(url_for('ordem_servico.visualizar', id=ordem.id))
        except Exception as exc:
            db.session.rollback()
            print(f'ERRO ao criar OS operacional do colaborador: {exc}')
            flash('Não foi possível criar a Ordem de Serviço.', 'error')

    if cliente_selecionado and not Cliente.query.filter_by(id=cliente_selecionado, ativo=True).first():
        cliente_selecionado = None
    return render_template(
        'os/form_operacional_colaborador.html',
        ordem=None,
        clientes=clientes,
        cliente_selecionado=cliente_selecionado,
        form_data=form_data,
    )


@ordem_servico_bp.route('/<int:id>/editar-operacional', methods=['GET', 'POST'])
def editar_operacional(id):
    """Permite ao colaborador editar apenas os dados técnicos de uma OS própria."""
    if not usuario_eh_colaborador():
        flash('Edição operacional disponível apenas para Colaborador.', 'error')
        return redirect(url_for('ordem_servico.listar'))

    colaborador = colaborador_do_usuario_atual()
    ordem = OrdemServico.query.filter_by(id=id, ativo=True).first()
    if not colaborador or not ordem or ordem.tipo_os != 'operacional' or not ordem_pertence_ao_colaborador(id, colaborador.id):
        flash('Você não tem permissão para editar esta OS.', 'error')
        return redirect(url_for('ordem_servico.listar'))

    if ordem.status in {'concluida', 'finalizada', 'cancelada'}:
        flash('OS concluída/cancelada não pode ser alterada pelo colaborador.', 'warning')
        return redirect(url_for('ordem_servico.visualizar', id=ordem.id))

    form_data = request.form.to_dict(flat=True) if request.method == 'POST' else {}
    if request.method == 'POST':
        if not (request.form.get('titulo') or '').strip():
            flash('Informe o título ou serviço da OS.', 'error')
        else:
            try:
                _aplicar_campos_tecnicos_colaborador(ordem, request.form)
                db.session.commit()
                flash('Dados técnicos atualizados com sucesso.', 'success')
                return redirect(url_for('ordem_servico.visualizar', id=ordem.id))
            except Exception as exc:
                db.session.rollback()
                print(f'ERRO ao editar OS operacional do colaborador: {exc}')
                flash('Não foi possível atualizar os dados técnicos.', 'error')

    return render_template(
        'os/form_operacional_colaborador.html',
        ordem=ordem,
        clientes=[],
        cliente_selecionado=ordem.cliente_id,
        form_data=form_data,
    )


'''
    os_texto = replace_once(
        os_texto,
        marcador_os,
        bloco_os + marcador_os,
        "rotas OS operacional de campo",
    )
OS.write_text(os_texto, encoding="utf-8")

print("OK - Colaborador Campo V2 aplicado.")
