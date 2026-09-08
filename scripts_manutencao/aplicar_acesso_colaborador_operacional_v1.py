# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OS_ROUTES = ROOT / "app/ordem_servico/ordem_servico_routes.py"
FIN_ROUTES = ROOT / "app/financeiro/financeiro_routes.py"
NFSE_ROUTES = ROOT / "app/financeiro/nfse_routes.py"
BASE = ROOT / "app/templates/base.html"


def replace_once(texto, antigo, novo, nome):
    qtd = texto.count(antigo)
    if qtd != 1:
        raise SystemExit(f"ABORTADO: esperado 1 marcador para {nome}, encontrado {qtd}.")
    return texto.replace(antigo, novo, 1)


# -----------------------------------------------------------------------------
# Financeiro: proteção do blueprint inteiro
# -----------------------------------------------------------------------------
fin = FIN_ROUTES.read_text(encoding="utf-8")
if "def restringir_acesso_financeiro():" not in fin:
    fin = replace_once(
        fin,
        "from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file\n",
        "from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file\nfrom flask_login import current_user\n",
        "import current_user financeiro",
    )
    fin = replace_once(
        fin,
        "bp_financeiro = Blueprint('financeiro', __name__, template_folder='templates')\n\n",
        """bp_financeiro = Blueprint('financeiro', __name__, template_folder='templates')


@bp_financeiro.before_request
def restringir_acesso_financeiro():
    \"\"\"Bloqueia todo o módulo financeiro para perfis sem permissão.\"\"\"
    if not getattr(current_user, 'is_authenticated', False):
        return redirect(url_for('auth.login'))
    if not current_user.tem_permissao('visualizar_financeiro'):
        flash('Acesso ao Financeiro restrito ao perfil autorizado.', 'error')
        return redirect(url_for('painel.dashboard'))

""",
        "guard financeiro",
    )
FIN_ROUTES.write_text(fin, encoding="utf-8")


# -----------------------------------------------------------------------------
# NFS-e: também pertence ao domínio financeiro
# -----------------------------------------------------------------------------
nfse = NFSE_ROUTES.read_text(encoding="utf-8")
if "def restringir_acesso_nfse_financeiro():" not in nfse:
    nfse = replace_once(
        nfse,
        "bp_nfse = Blueprint('nfse', __name__, url_prefix='/financeiro/nfse')\n\n",
        """bp_nfse = Blueprint('nfse', __name__, url_prefix='/financeiro/nfse')


@bp_nfse.before_request
def restringir_acesso_nfse_financeiro():
    \"\"\"NFS-e é informação financeira/fiscal e exige permissão financeira.\"\"\"
    if not getattr(current_user, 'is_authenticated', False):
        return redirect(url_for('auth.login'))
    if not current_user.tem_permissao('visualizar_financeiro'):
        flash('Acesso fiscal/financeiro restrito ao perfil autorizado.', 'error')
        return redirect(url_for('painel.dashboard'))

""",
        "guard nfse",
    )
NFSE_ROUTES.write_text(nfse, encoding="utf-8")


# -----------------------------------------------------------------------------
# OS: vínculo fail-closed por e-mail e rota dedicada de apontamento
# -----------------------------------------------------------------------------
os_routes = OS_ROUTES.read_text(encoding="utf-8")

if "def usuario_eh_colaborador():" not in os_routes:
    os_routes = replace_once(
        os_routes,
        """def usuario_eh_admin():
    \"\"\"Retorna se o usuário logado é administrador.\"\"\"
    return getattr(current_user, 'tipo_usuario', None) == 'admin'


""",
        """def usuario_eh_admin():
    \"\"\"Retorna se o usuário logado é administrador.\"\"\"
    return getattr(current_user, 'tipo_usuario', None) == 'admin'


def usuario_eh_colaborador():
    return getattr(current_user, 'tipo_usuario', None) == 'colaborador'


def colaborador_do_usuario_atual():
    \"\"\"Resolve o colaborador do login por e-mail, sempre de forma fail-closed.\"\"\"
    if not usuario_eh_colaborador():
        return None
    email = (getattr(current_user, 'email', None) or '').strip().lower()
    if not email:
        return None
    encontrados = Colaborador.query.filter(
        db.func.lower(Colaborador.email) == email,
        Colaborador.ativo.is_(True),
    ).all()
    return encontrados[0] if len(encontrados) == 1 else None


def ordem_pertence_ao_colaborador(ordem_id, colaborador_id):
    if not ordem_id or not colaborador_id:
        return False
    return OrdemServicoColaborador.query.filter_by(
        ordem_servico_id=ordem_id,
        colaborador_id=colaborador_id,
        ativo=True,
    ).first() is not None


def _hora_apontamento(valor):
    texto = (valor or '').strip()
    if not texto:
        return None
    return datetime.strptime(texto, '%H:%M').time()


def _recalcular_resumo_apontamentos(ordem):
    trabalhos = OrdemServicoColaborador.query.filter_by(
        ordem_servico_id=ordem.id,
        ativo=True,
    ).all()
    total_normais = sum((Decimal(str(t.horas_normais or 0)) for t in trabalhos), Decimal('0'))
    total_extras = sum((Decimal(str(t.horas_extras or 0)) for t in trabalhos), Decimal('0'))
    total = sum((Decimal(str(t.total_horas or 0)) for t in trabalhos), Decimal('0'))
    total_km = sum((t.km_total for t in trabalhos), 0)

    ordem.horas_normais = total_normais if total_normais > 0 else None
    ordem.horas_extras = total_extras if total_extras > 0 else None
    if total > 0:
        horas = int(total)
        minutos = int(round((float(total) - horas) * 60))
        ordem.total_horas = f'{horas}h {minutos:02d}min'
    else:
        ordem.total_horas = ''
    ordem.total_km = f'{total_km} km' if total_km > 0 else ''


""",
        "helpers colaborador OS",
    )

if "def restringir_rotas_colaborador():" not in os_routes:
    os_routes = replace_once(
        os_routes,
        "ordem_servico_bp = Blueprint('ordem_servico', __name__, template_folder='templates')\n\n",
        """ordem_servico_bp = Blueprint('ordem_servico', __name__, template_folder='templates')


@ordem_servico_bp.before_request
def restringir_rotas_colaborador():
    \"\"\"Colaborador acessa apenas lista, visualização e seu próprio apontamento.\"\"\"
    if not usuario_eh_colaborador():
        return None
    permitidas = {
        'ordem_servico.listar',
        'ordem_servico.visualizar',
        'ordem_servico.apontamento_colaborador',
    }
    if request.endpoint not in permitidas:
        flash('Seu perfil possui acesso somente à execução das suas Ordens de Serviço.', 'error')
        return redirect(url_for('ordem_servico.listar'))
    return None

""",
        "guard blueprint OS colaborador",
    )

os_routes = replace_once(
    os_routes,
    """        # Se o usuário for colaborador, mostra apenas ordens operacionais
        if hasattr(current_user, 'tipo_usuario') and current_user.tipo_usuario == 'colaborador':
            query = query.filter(OrdemServico.tipo_os == 'operacional')
""",
    """        # Colaborador: somente OS operacional em que ele esteja realmente escalado.
        colaborador_vinculado = None
        if usuario_eh_colaborador():
            colaborador_vinculado = colaborador_do_usuario_atual()
            if colaborador_vinculado is None:
                query = query.filter(OrdemServico.id == -1)  # fail-closed
            else:
                query = query.join(
                    OrdemServicoColaborador,
                    OrdemServicoColaborador.ordem_servico_id == OrdemServico.id,
                ).filter(
                    OrdemServico.tipo_os == 'operacional',
                    OrdemServicoColaborador.colaborador_id == colaborador_vinculado.id,
                    OrdemServicoColaborador.ativo.is_(True),
                ).distinct()
""",
    "filtro OS próprias",
)

os_routes = replace_once(
    os_routes,
    """        # Lista de clientes para filtro dropdown
        clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
""",
    """        if usuario_eh_colaborador():
            return render_template(
                'os/listar_colaborador.html',
                ordens=ordens,
                busca=busca,
                status_filtro=status,
                colaborador_vinculado=colaborador_vinculado,
            )

        # Lista de clientes para filtro dropdown
        clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
""",
    "render lista colaborador",
)

os_routes = replace_once(
    os_routes,
    """    # Colaboradores só podem visualizar ordens operacionais
    if hasattr(current_user, 'tipo_usuario') and current_user.tipo_usuario == 'colaborador' and ordem.tipo_os != 'operacional':
        flash('Você não tem permissão para visualizar esta ordem de serviço.', 'error')
        return redirect(url_for('ordem_servico.listar'))
    
    # Debug: verificar se os itens foram carregados
""",
    """    if usuario_eh_colaborador():
        colaborador = colaborador_do_usuario_atual()
        if (
            colaborador is None
            or ordem.tipo_os != 'operacional'
            or not ordem_pertence_ao_colaborador(ordem.id, colaborador.id)
        ):
            flash('Esta Ordem de Serviço não está atribuída ao seu usuário.', 'error')
            return redirect(url_for('ordem_servico.listar'))
        trabalho = OrdemServicoColaborador.query.filter_by(
            ordem_servico_id=ordem.id,
            colaborador_id=colaborador.id,
            ativo=True,
        ).order_by(OrdemServicoColaborador.id.desc()).first()
        return render_template(
            'os/visualizar_colaborador.html',
            ordem=ordem,
            trabalho=trabalho,
            today=date.today(),
        )
    
    # Debug: verificar se os itens foram carregados
""",
    "visualização operacional colaborador",
)

if "def apontamento_colaborador(id):" not in os_routes:
    os_routes = replace_once(
        os_routes,
        "@ordem_servico_bp.route('/<int:id>/editar', methods=['GET', 'POST'])\ndef editar(id):",
        """@ordem_servico_bp.route('/<int:id>/apontamento', methods=['GET', 'POST'])
def apontamento_colaborador(id):
    if not usuario_eh_colaborador():
        flash('Apontamento individual disponível apenas para o perfil Colaborador.', 'error')
        return redirect(url_for('ordem_servico.visualizar', id=id))

    colaborador = colaborador_do_usuario_atual()
    ordem = OrdemServico.query.filter_by(id=id, ativo=True).first()
    if (
        colaborador is None
        or ordem is None
        or ordem.tipo_os != 'operacional'
        or not ordem_pertence_ao_colaborador(id, colaborador.id)
    ):
        flash('Esta Ordem de Serviço não está atribuída ao seu usuário.', 'error')
        return redirect(url_for('ordem_servico.listar'))

    trabalho = OrdemServicoColaborador.query.filter_by(
        ordem_servico_id=id,
        colaborador_id=colaborador.id,
        ativo=True,
    ).order_by(OrdemServicoColaborador.id.desc()).first()
    if trabalho is None:
        flash('Apontamento do colaborador não encontrado para esta OS.', 'error')
        return redirect(url_for('ordem_servico.listar'))

    if request.method == 'POST':
        try:
            data_texto = (request.form.get('data_trabalho') or '').strip()
            trabalho.data_trabalho = datetime.strptime(data_texto, '%Y-%m-%d').date() if data_texto else date.today()
            trabalho.hora_entrada_manha = _hora_apontamento(request.form.get('hora_entrada_manha'))
            trabalho.hora_saida_manha = _hora_apontamento(request.form.get('hora_saida_manha'))
            trabalho.hora_entrada_tarde = _hora_apontamento(request.form.get('hora_entrada_tarde'))
            trabalho.hora_saida_tarde = _hora_apontamento(request.form.get('hora_saida_tarde'))
            trabalho.hora_entrada_extra = _hora_apontamento(request.form.get('hora_entrada_extra'))
            trabalho.hora_saida_extra = _hora_apontamento(request.form.get('hora_saida_extra'))
            trabalho.km_inicial = safe_int_convert(request.form.get('km_inicial'))
            trabalho.km_final = safe_int_convert(request.form.get('km_final'))
            if (
                trabalho.km_inicial is not None
                and trabalho.km_final is not None
                and trabalho.km_final < trabalho.km_inicial
            ):
                raise ValueError('KM final não pode ser menor que o KM inicial.')
            trabalho.descricao_atividade = (request.form.get('descricao_atividade') or '').strip()
            trabalho.observacoes = (request.form.get('observacoes') or '').strip()

            trabalho.calcular_horas_automatico()
            _recalcular_resumo_apontamentos(ordem)
            db.session.commit()
            flash('Apontamento salvo com sucesso.', 'success')
            return redirect(url_for('ordem_servico.visualizar', id=ordem.id))
        except Exception as exc:
            db.session.rollback()
            flash(f'Erro ao salvar apontamento: {exc}', 'error')

    return render_template(
        'os/apontamento_colaborador.html',
        ordem=ordem,
        trabalho=trabalho,
        today=date.today(),
    )


@ordem_servico_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):""",
        "rota apontamento colaborador",
    )

OS_ROUTES.write_text(os_routes, encoding="utf-8")


# -----------------------------------------------------------------------------
# Sidebar: colaborador enxerga somente sua operação
# -----------------------------------------------------------------------------
base = BASE.read_text(encoding="utf-8")
if "MINHA OPERAÇÃO" not in base:
    base = replace_once(
        base,
        """            {% endif %}

            {% endif %}

            <!-- Usuário -->
""",
        """            {% endif %}

            {% else %}
            <div class="nav-section-header">
                <i class="fas fa-toolbox me-2"></i>
                <span>MINHA OPERAÇÃO</span>
            </div>
            <div class="nav-item">
                <a href="{{ url_for('ordem_servico.listar') }}" class="nav-link">
                    <i class="nav-icon fas fa-wrench"></i>
                    <span class="nav-text">Minhas OS</span>
                </a>
            </div>
            {% endif %}

            <!-- Usuário -->
""",
        "menu colaborador",
    )
BASE.write_text(base, encoding="utf-8")

print("OK - Acesso operacional do colaborador V1 aplicado.")
