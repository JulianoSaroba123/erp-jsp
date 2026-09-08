# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Routes de Ordem de Serviço
=========================================

Rotas para gerenciamento de ordens de serviço.
CRUD completo com controle de status.

Autor: JSP Soluções
Data: 2025
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, make_response
from flask_login import current_user
from app.extensoes import db
from app.ordem_servico.ordem_servico_model import (
    OrdemServico, OrdemServicoItem, OrdemServicoProduto, OrdemServicoParcela, OrdemServicoAnexo
)
from app.cliente.cliente_model import Cliente
from app.colaborador.colaborador_model import OrdemServicoColaborador, Colaborador
from app.produto.produto_model import Produto
from decimal import Decimal
import decimal
import os
import base64
from datetime import datetime as dt, datetime, time, date, timedelta
from calendar import monthrange
from werkzeug.utils import secure_filename
import uuid


FORMAS_PAGAMENTO_VALIDAS = frozenset({
    'dinheiro', 'cartao_credito', 'cartao_debito',
    'transferencia', 'pix', 'boleto', 'cheque',
})


def validar_forma_pagamento(valor):
    """Normaliza uma forma enviada pelo formulário ou retorna None."""
    valor_normalizado = (valor or '').strip() or None
    if valor_normalizado is not None and valor_normalizado not in FORMAS_PAGAMENTO_VALIDAS:
        return None, False
    return valor_normalizado, True

# === FUNÇÃO UTILITÁRIA PARA BUSCAR CLIENTES ===
def buscar_clientes_ativos():
    """
    Função simples e confiável para buscar clientes ativos.
    Retorna APENAS clientes ativos com nome válido.
    Garante consistência entre todos os módulos.
    """
    try:
        # Busca básica e segura
        # FIX: Usar text() para queries problemáticas com PostgreSQL
        from sqlalchemy import select
        
        clientes = Cliente.query.filter(
            Cliente.ativo == True
        ).order_by(Cliente.nome).all()
        
        # Filtrar em Python para evitar problemas de SQL
        clientes_validos = []
        for cliente in clientes:
            if cliente and cliente.nome and cliente.nome.strip():
                clientes_validos.append(cliente)
        
        return clientes_validos
        
    except Exception as e:
        print(f"❌ ERRO na busca de clientes: {e}")
        print(f"❌ Tentando busca alternativa...")
        # Fallback: busca direta sem filtros complexos
        try:
            clientes = Cliente.query.all()
            clientes_validos = [
                c for c in clientes 
                if c.ativo and c.nome and c.nome.strip()
            ]
            return clientes_validos
        except Exception as e2:
            print(f"❌ ERRO CRÍTICO na busca de clientes: {e2}")
            return []

# Configurações de upload
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads', 'ordem_servico', 'anexos')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size(file):
    """Obtém o tamanho do arquivo"""
    file.seek(0, 2)  # Move para o final
    size = file.tell()
    file.seek(0)  # Volta para o início
    return size

def generate_unique_filename(original_filename):
    """Gera nome único para o arquivo"""
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    unique_name = str(uuid.uuid4())
    return f"{unique_name}.{ext}" if ext else unique_name

# Função auxiliar para conversão segura de inteiros
def safe_int_convert(value, default=None):
    """
    Converte string para int de forma segura.
    
    Args:
        value: Valor a ser convertido
        default: Valor padrão se conversão falhar
        
    Returns:
        int ou None/default
    """
    if not value:
        return default
        
    if isinstance(value, str):
        value = value.strip()
        if not value or not value.isdigit():
            return default
    
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_decimal_convert(value, default=0):
    """
    Converte string para Decimal de forma segura.
    
    Args:
        value: Valor a ser convertido  
        default: Valor padrão se conversão falhar (pode ser None)
        
    Returns:
        Decimal ou None
    """
    if not value or (isinstance(value, str) and value.strip() == ''):
        return Decimal(str(default)) if default is not None else None
        
    try:
        s = str(value).strip()
        # Remove currency symbol and spaces
        s = s.replace('R$', '').replace(' ', '')

        # Se contém vírgula, assumimos formato brasileiro: pontos como milhares e vírgula como decimal
        if ',' in s:
            # Remover pontos (separadores de milhares) e trocar vírgula por ponto
            clean_value = s.replace('.', '').replace(',', '.')
        else:
            # Não há vírgula. Pode ser `1.23` (ponto decimal) ou `1.000` (milhares) dependendo do contexto.
            # Neste caso, NÃO removemos pontos automaticamente — assumimos que ponto é separador decimal.
            clean_value = s

        if clean_value == '' or clean_value == '.':
            return Decimal(str(default)) if default is not None else None
        return Decimal(clean_value)
    except (ValueError, TypeError, decimal.InvalidOperation):
        return Decimal(str(default)) if default is not None else None


def usuario_eh_admin():
    """Retorna se o usuário logado é administrador."""
    return getattr(current_user, 'tipo_usuario', None) == 'admin'


def usuario_eh_colaborador():
    return getattr(current_user, 'tipo_usuario', None) == 'colaborador'


def colaborador_do_usuario_atual():
    """Resolve o colaborador do login por e-mail, sempre de forma fail-closed."""
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


def normalizar_modo_operacional(tipo_os, modo_informado):
    """Padroniza o modo operacional da OS."""
    if tipo_os != 'operacional':
        return 'atendimento'

    return 'diaria' if (modo_informado or '').strip().lower() == 'diaria' else 'atendimento'


def aplicar_descricao_por_modo(ordem, form_data, tipo_os):
    """Aplica os campos de descrição conforme o modo da OS."""
    modo_operacional = normalizar_modo_operacional(tipo_os, form_data.get('tipo_servico'))
    ordem.tipo_servico = modo_operacional

    if modo_operacional == 'diaria':
        ordem.descricao_problema = form_data.get('descricao_problema_diaria', '').strip()
        ordem.diagnostico_tecnico = ''
        ordem.solucao = ''
        ordem.observacoes = ''
    else:
        ordem.descricao_problema = form_data.get('descricao_problema', '').strip()
        ordem.diagnostico_tecnico = form_data.get('diagnostico_tecnico', '').strip()
        ordem.solucao = form_data.get('solucao', '').strip()
        ordem.observacoes = form_data.get('observacoes', '').strip()

    return modo_operacional


def _somar_meses_data(data_base, meses):
    """Soma meses preservando o dia quando possível."""
    indice_mes = (data_base.month - 1) + meses
    ano = data_base.year + (indice_mes // 12)
    mes = (indice_mes % 12) + 1
    dia = min(data_base.day, monthrange(ano, mes)[1])
    return date(ano, mes, dia)


def _montar_parcelas_automaticas(valor_total, numero_parcelas, valor_entrada, data_primeira):
    """Monta o cronograma completo; a entrada, quando existe, é a parcela nº 1."""
    total = Decimal(str(valor_total or 0)).quantize(Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)
    entrada = Decimal(str(valor_entrada or 0)).quantize(Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)
    quantidade = int(numero_parcelas or 0)

    if quantidade < 1:
        raise ValueError('O número de parcelas deve ser maior que zero.')
    if entrada < 0 or entrada > total:
        raise ValueError('O valor da entrada deve estar entre zero e o valor total da OS.')
    if entrada > 0 and quantidade == 1 and entrada != total:
        raise ValueError('Com 1 parcela, a entrada precisa ser igual ao valor total da OS.')

    valores = []
    restante = total
    qtd_restante = quantidade

    if entrada > 0:
        valores.append(entrada)
        restante -= entrada
        qtd_restante -= 1

    if qtd_restante > 0:
        valor_base = (restante / qtd_restante).quantize(Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)
        diferenca = restante - (valor_base * qtd_restante)

        for indice in range(qtd_restante):
            valor = valor_base
            if indice == qtd_restante - 1:
                valor = (valor + diferenca).quantize(Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)
            valores.append(valor)

    if len(valores) != quantidade:
        raise ValueError('Não foi possível distribuir o valor total entre as parcelas.')

    return [
        (indice + 1, _somar_meses_data(data_primeira, indice), valor)
        for indice, valor in enumerate(valores)
    ]


def _parse_parcelas_manuais(parcelas_datas, parcelas_valores, data_base):
    """Converte as linhas do editor de parcelas para valores tipados."""
    parsed = []
    for indice, valor_raw in enumerate(parcelas_valores):
        if not str(valor_raw or '').strip():
            raise ValueError(f'Informe o valor da parcela #{indice + 1}.')

        valor = safe_decimal_convert(valor_raw, None)
        if valor is None or valor < 0:
            raise ValueError(f'Valor inválido na parcela #{indice + 1}.')

        data_vencimento = data_base
        if indice < len(parcelas_datas) and parcelas_datas[indice]:
            try:
                data_vencimento = datetime.strptime(parcelas_datas[indice], '%Y-%m-%d').date()
            except Exception as exc:
                raise ValueError(f'Data inválida na parcela #{indice + 1}.') from exc

        parsed.append((
            indice + 1,
            data_vencimento,
            Decimal(str(valor)).quantize(Decimal('0.01'), rounding=decimal.ROUND_HALF_UP),
        ))
    return parsed


def _lancamentos_da_parcela(parcela):
    """Busca lançamentos financeiros vinculados a uma parcela."""
    from app.financeiro.financeiro_model import LancamentoFinanceiro

    if not parcela.id:
        return []

    return LancamentoFinanceiro.query.filter_by(
        ordem_servico_parcela_id=parcela.id
    ).all()


def _parcela_tem_baixa_confirmada(parcela):
    """Protege parcelas e lançamentos já pagos/recebidos."""
    if bool(getattr(parcela, 'pago', False)) or getattr(parcela, 'data_pagamento', None):
        return True

    for lancamento in _lancamentos_da_parcela(parcela):
        if lancamento.status in {'pago', 'recebido'} or lancamento.data_pagamento is not None:
            return True
    return False


def _remover_parcela_segura(parcela):
    """Remove parcela e lançamentos não quitados sem commit intermediário."""
    lancamentos = _lancamentos_da_parcela(parcela)

    if _parcela_tem_baixa_confirmada(parcela):
        raise ValueError(
            f'A parcela #{parcela.numero_parcela} possui pagamento/recebimento confirmado e não pode ser removida.'
        )

    for lancamento in lancamentos:
        db.session.delete(lancamento)
    db.session.delete(parcela)


def _reconciliar_parcelas_ordem(ordem, novas_parcelas):
    """Atualiza parcelas in-place, cria excedentes e remove sobras com segurança."""
    existentes = sorted(
        list(getattr(ordem, 'parcelas', []) or []),
        key=lambda parcela: (parcela.numero_parcela or 0, parcela.id or 0),
    )
    for indice, (numero, data_vencimento, valor) in enumerate(novas_parcelas):
        valor = Decimal(str(valor)).quantize(Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)

        if indice < len(existentes):
            parcela = existentes[indice]
            mudanca_destrutiva = (
                parcela.numero_parcela != numero
                or parcela.data_vencimento != data_vencimento
                or Decimal(str(parcela.valor or 0)).quantize(
                    Decimal('0.01'), rounding=decimal.ROUND_HALF_UP
                ) != valor
            )
            if mudanca_destrutiva and _parcela_tem_baixa_confirmada(parcela):
                raise ValueError(
                    f'A parcela #{parcela.numero_parcela} já possui pagamento/recebimento confirmado e não pode ser alterada.'
                )

            parcela.numero_parcela = numero
            parcela.data_vencimento = data_vencimento
            parcela.valor = valor
            parcela.ativo = True

            # Mantém o financeiro pendente sincronizado com a parcela preservada.
            # Lançamentos quitados não chegam aqui quando há mudança, pois a
            # validação acima bloqueia alterações destrutivas nesses casos.
            if mudanca_destrutiva:
                total_parcelas = len(novas_parcelas)
                for lancamento in _lancamentos_da_parcela(parcela):
                    if lancamento.status in {'pago', 'recebido'} or lancamento.data_pagamento is not None:
                        continue
                    lancamento.valor = valor
                    lancamento.data_vencimento = data_vencimento
                    lancamento.numero_parcela = f'{numero}/{total_parcelas}'
        else:
            db.session.add(OrdemServicoParcela(
                ordem_servico=ordem,
                numero_parcela=numero,
                data_vencimento=data_vencimento,
                valor=valor,
                ativo=True,
            ))

    for parcela in existentes[len(novas_parcelas):]:
        _remover_parcela_segura(parcela)


def limpar_itens_e_parcelas(ordem):
    """Remove serviços, produtos e parcelas vinculados à OS."""
    for item in list(getattr(ordem, 'servicos', []) or []):
        db.session.delete(item)

    for produto in list(getattr(ordem, 'produtos_utilizados', []) or []):
        db.session.delete(produto)

    for parcela in list(getattr(ordem, 'parcelas', []) or []):
        _remover_parcela_segura(parcela)


def limpar_dados_financeiros(ordem):
    """Reseta dados financeiros quando a OS não permite gestão financeira."""
    ordem.valor_servico = Decimal('0')
    ordem.valor_pecas = Decimal('0')
    ordem.valor_desconto = Decimal('0')
    ordem.valor_total = Decimal('0')
    ordem.condicao_pagamento = 'a_vista'
    ordem.status_pagamento = 'pendente'
    ordem.numero_parcelas = 1
    ordem.valor_entrada = Decimal('0')
    ordem.data_primeira_parcela = None
    ordem.data_vencimento_pagamento = None
    ordem.descricao_pagamento = ''
    ordem.prazo_garantia = 0


def extrair_colaboradores_form(form_data):
    """Extrai os registros de colaboradores enviados pelo formulário."""
    colaboradores = {}

    for key in form_data.keys():
        match = re.match(r'^colaboradores\[(\d+)\]\[(.+)\]$', key)
        if match:
            index, campo = match.groups()
            valor = form_data.get(key, '').strip()
            colaboradores.setdefault(index, {})[campo] = valor

    return [colaboradores[index] for index in sorted(colaboradores.keys(), key=int)]


def processar_colaboradores_os(ordem, form_data):
    """Salva os apontamentos de colaboradores da OS."""
    for item in list(getattr(ordem, 'colaboradores_trabalho', []) or []):
        db.session.delete(item)

    total_horas = Decimal('0')
    total_horas_normais = Decimal('0')
    total_horas_extras = Decimal('0')
    total_km = 0

    for colaborador_data in extrair_colaboradores_form(form_data):
        colaborador_id = safe_int_convert(colaborador_data.get('colaborador_id'))
        if not colaborador_id:
            continue

        data_trabalho = date.today()
        if colaborador_data.get('data_trabalho'):
            try:
                data_trabalho = datetime.strptime(colaborador_data.get('data_trabalho'), '%Y-%m-%d').date()
            except Exception:
                data_trabalho = date.today()

        def parse_hora(campo):
            if colaborador_data.get(campo):
                try:
                    return datetime.strptime(colaborador_data.get(campo), '%H:%M').time()
                except Exception:
                    return None
            return None

        hora_entrada_manha = parse_hora('hora_entrada_manha')
        hora_saida_manha = parse_hora('hora_saida_manha')
        hora_entrada_tarde = parse_hora('hora_entrada_tarde')
        hora_saida_tarde = parse_hora('hora_saida_tarde')
        hora_entrada_extra = parse_hora('hora_entrada_extra')
        hora_saida_extra = parse_hora('hora_saida_extra')
        hora_inicio = hora_entrada_manha or hora_entrada_tarde or hora_entrada_extra or parse_hora('hora_inicio')
        hora_fim = hora_saida_extra or hora_saida_tarde or hora_saida_manha or parse_hora('hora_fim')
        
        # Extrair percentual de adicional customizado (se fornecido)
        percentual_adicional_cobranca = colaborador_data.get('percentual_adicional_cobranca')
        if percentual_adicional_cobranca:
            try:
                percentual_adicional_cobranca = Decimal(str(percentual_adicional_cobranca))
            except:
                percentual_adicional_cobranca = None

        trabalho = OrdemServicoColaborador(
            ordem_servico_id=ordem.id,
            colaborador_id=colaborador_id,
            data_trabalho=data_trabalho,
            hora_inicio=hora_inicio,
            hora_fim=hora_fim,
            hora_entrada_manha=hora_entrada_manha,
            hora_saida_manha=hora_saida_manha,
            hora_entrada_tarde=hora_entrada_tarde,
            hora_saida_tarde=hora_saida_tarde,
            hora_entrada_extra=hora_entrada_extra,
            hora_saida_extra=hora_saida_extra,
            km_inicial=safe_int_convert(colaborador_data.get('km_inicial')),
            km_final=safe_int_convert(colaborador_data.get('km_final')),
            descricao_atividade=colaborador_data.get('descricao_atividade', ''),
            observacoes=colaborador_data.get('observacoes', ''),
            percentual_adicional_cobranca=percentual_adicional_cobranca
        )

        # Sempre calcular automaticamente a partir dos horários detalhados
        trabalho.calcular_horas_automatico()
        
        # Calcular valores com adicionais (custo e receita por hora)
        colaborador_obj = Colaborador.query.get(colaborador_id)
        if colaborador_obj:
            salario = colaborador_obj.salario_mensal or Decimal('0')
            valor_hora = colaborador_obj.valor_hora or Decimal('0')
            if salario > 0 or valor_hora > 0:
                trabalho.atualizar_valores_com_adicional(salario, valor_hora)

        total_horas += Decimal(str(trabalho.total_horas or 0))
        total_horas_normais += Decimal(str(trabalho.horas_normais or 0))
        total_horas_extras += Decimal(str(trabalho.horas_extras or 0))
        total_km += trabalho.km_total
        db.session.add(trabalho)

    if ordem.tipo_os == 'operacional':
        if total_horas > 0:
            horas_inteiras = int(total_horas)
            minutos = int(round((float(total_horas) - horas_inteiras) * 60))
            ordem.total_horas = f'{horas_inteiras}h {minutos:02d}min'
        else:
            ordem.total_horas = ''

        # Salvar horas como Decimal (formato numérico no banco)
        ordem.horas_normais = total_horas_normais if total_horas_normais > 0 else None

        ordem.horas_extras = total_horas_extras if total_horas_extras > 0 else None

        ordem.total_km = f'{total_km} km' if total_km > 0 else ''

from werkzeug.utils import secure_filename
import re
import os
import uuid
import tempfile
import base64

# Cria o blueprint
ordem_servico_bp = Blueprint('ordem_servico', __name__, template_folder='templates')


@ordem_servico_bp.before_request
def restringir_rotas_colaborador():
    """Colaborador acessa apenas lista, visualização e seu próprio apontamento."""
    if not usuario_eh_colaborador():
        return None
    permitidas = {
        'ordem_servico.listar',
        'ordem_servico.visualizar',
        'ordem_servico.apontamento_colaborador',
        'ordem_servico.novo_operacional',
        'ordem_servico.editar_operacional',
    }
    if request.endpoint not in permitidas:
        flash('Seu perfil possui acesso somente à execução das suas Ordens de Serviço.', 'error')
        return redirect(url_for('ordem_servico.listar'))
    return None

# Configurações de upload
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'app', 'static', 'uploads')
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar'
}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# ===== ROTA DE AUTOCOMPLETE =====
@ordem_servico_bp.route('/autocomplete/<campo>')
def autocomplete_campo(campo):
    """
    Retorna valores únicos já usados para autocomplete.
    
    Campos suportados:
    - solicitante
    - tecnico_responsavel
    - titulo
    - equipamento
    - marca_modelo
    """
    from sqlalchemy import distinct
    
    campos_permitidos = {
        'solicitante': OrdemServico.solicitante,
        'tecnico_responsavel': OrdemServico.tecnico_responsavel,
        'titulo': OrdemServico.titulo,
        'equipamento': OrdemServico.equipamento,
        'marca_modelo': OrdemServico.marca_modelo
    }
    
    if campo not in campos_permitidos:
        return jsonify({'error': 'Campo não permitido'}), 400
    
    try:
        coluna = campos_permitidos[campo]
        
        # Busca valores únicos e remove nulos/vazios
        valores = db.session.query(distinct(coluna))\
            .filter(coluna.isnot(None), coluna != '')\
            .order_by(coluna)\
            .limit(50)\
            .all()
        
        # Extrai os valores da tupla
        resultado = [v[0] for v in valores if v[0]]
        
        return jsonify(resultado)
        
    except Exception as e:
        print(f"Erro ao buscar autocomplete para {campo}: {e}")
        return jsonify([])

def get_logo_base64():
    """Retorna o logo configurado no sistema em base64 para o PDF"""
    try:
        from app.configuracao.configuracao_model import Configuracao
        import base64
        
        print("🔍 DEBUG LOGO: Iniciando busca da logo...")
        
        # Busca a configuração do sistema
        config = Configuracao.get_solo()
        
        # Se há logo em base64 armazenado no banco (para cloud/Render), usa ele primeiro
        if config and config.logo_base64:
            print(f"✅ DEBUG LOGO: Logo encontrada no banco (base64) - {len(config.logo_base64)} chars")
            # Remove prefixo data:image se houver
            logo_b64 = config.logo_base64
            if logo_b64.startswith('data:'):
                # Extrai apenas o base64 depois da vírgula
                logo_b64 = logo_b64.split(',', 1)[1] if ',' in logo_b64 else logo_b64
                print(f"   🔧 Removido prefixo data:image, tamanho agora: {len(logo_b64)} chars")
            return logo_b64
        
        # Se há logo configurado como arquivo, usa ele
        if config and config.logo:
            print(f"🔍 DEBUG LOGO: Tentando carregar logo do arquivo: {config.logo}")
            # Verifica se é caminho absoluto ou relativo
            if os.path.isabs(config.logo):
                logo_path = config.logo
            else:
                # Caminho relativo ao diretório static
                logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'uploads', config.logo)
            
            print(f"   📁 Caminho completo: {logo_path}")
            # Lê o arquivo da imagem e converte para base64
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as img_file:
                    img_data = img_file.read()
                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                    print(f"   ✅ Logo carregada do arquivo - {len(img_base64)} chars base64")
                    return img_base64
            else:
                print(f"   ❌ Arquivo não encontrado: {logo_path}")
        
        # Fallback: tenta usar a logo padrão JSP.jpg
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'img', 'JSP.jpg')
        print(f"🔍 DEBUG LOGO: Tentando logo padrão: {logo_path}")
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as img_file:
                img_data = img_file.read()
                img_base64 = base64.b64encode(img_data).decode('utf-8')
                print(f"   ✅ Logo padrão carregada - {len(img_base64)} chars base64")
                return img_base64
        else:
            print(f"   ❌ Logo padrão não encontrada: {logo_path}")
                
    except Exception as e:
        print(f"❌ DEBUG LOGO: Erro ao carregar logo: {e}")
        import traceback
        traceback.print_exc()
    
    # Fallback final: retorna None para usar o SVG no template
    print("⚠️ DEBUG LOGO: Nenhuma logo encontrada, retornando None (usará placeholder)")
    return None

@ordem_servico_bp.route('/teste_os')
def teste_os():
    """Endpoint de teste para verificar se as OS estão acessíveis"""
    from app.ordem_servico.ordem_servico_model import OrdemServico
    
    todas = OrdemServico.query.all()
    ativas = OrdemServico.query.filter_by(ativo=True).all()
    
    resultado = {
        'total_os': len(todas),
        'os_ativas': len(ativas),
        'lista_os': [{'numero': os.numero, 'titulo': os.titulo, 'ativo': os.ativo} for os in todas]
    }
    
    return jsonify(resultado)

@ordem_servico_bp.route('/debug_banco')
def debug_banco():
    """🔍 Endpoint de DEBUG - Verifica banco de dados"""
    from sqlalchemy import text, inspect
    from app.extensoes import db
    import os
    
    resultado = {
        'status': 'iniciando',
        'erros': [],
        'dados': {}
    }
    
    try:
        # 1. Conexão
        resultado['dados']['database_url_exists'] = bool(os.getenv('DATABASE_URL'))
        resultado['dados']['sqlalchemy_uri'] = str(db.engine.url)[:80]
        
        # 2. Tabelas
        inspector = inspect(db.engine)
        tabelas = inspector.get_table_names()
        resultado['dados']['total_tabelas'] = len(tabelas)
        resultado['dados']['ordem_servico_existe'] = 'ordem_servico' in tabelas
        resultado['dados']['lista_tabelas'] = tabelas
        
        # 3. Schema
        try:
            schema_result = db.session.execute(text("SELECT current_schema()"))
            resultado['dados']['schema_atual'] = schema_result.scalar()
        except:
            resultado['dados']['schema_atual'] = 'N/A (SQLite)'
        
        # 4. Query SQL direta
        sql_result = db.session.execute(text("SELECT COUNT(*) FROM ordem_servico"))
        resultado['dados']['count_sql'] = sql_result.scalar()
        
        # 4.1 Status SQL direta
        sql_status = db.session.execute(text("SELECT status, COUNT(*) FROM ordem_servico GROUP BY status"))
        resultado['dados']['status_sql'] = {row[0]: row[1] for row in sql_status.fetchall()}
        
        # 4.2 Campo ativo SQL direta
        sql_ativo = db.session.execute(text("SELECT ativo, COUNT(*) FROM ordem_servico GROUP BY ativo"))
        resultado['dados']['ativo_sql'] = {str(row[0]): row[1] for row in sql_ativo.fetchall()}
        
        if resultado['dados']['count_sql'] > 0:
            sql_result2 = db.session.execute(text("SELECT id, numero, titulo, status, ativo FROM ordem_servico LIMIT 5"))
            resultado['dados']['primeiras_os_sql'] = [
                {'id': row[0], 'numero': row[1], 'titulo': row[2], 'status': row[3], 'ativo': row[4]} 
                for row in sql_result2.fetchall()
            ]
        
        # 5. Query ORM
        total_orm = OrdemServico.query.count()
        total_orm_ativas = OrdemServico.query.filter(OrdemServico.ativo == True).count()
        resultado['dados']['count_orm'] = total_orm
        resultado['dados']['count_orm_ativas'] = total_orm_ativas
        resultado['dados']['model_tablename'] = OrdemServico.__tablename__
        
        if total_orm > 0:
            primeiras_orm = OrdemServico.query.limit(5).all()
            resultado['dados']['primeiras_os_orm'] = [
                {'id': os.id, 'numero': os.numero, 'titulo': os.titulo, 'status': os.status, 'ativo': os.ativo}
                for os in primeiras_orm
            ]
        
        resultado['status'] = 'sucesso'
        
    except Exception as e:
        resultado['status'] = 'erro'
        resultado['erros'].append(str(e))
        import traceback
        resultado['traceback'] = traceback.format_exc()
    
    return jsonify(resultado)

@ordem_servico_bp.route('/')
@ordem_servico_bp.route('/listar')
def listar():
    """
    Lista todas as ordens de serviço ativas com filtros avançados.
    
    Filtros disponíveis:
    - busca: número, título, equipamento ou nome do cliente
    - status: status da OS
    - cliente_id: ID do cliente
    - data_inicio/data_fim: range de datas de abertura
    """
    try:
        # Parâmetros de busca
        busca = request.args.get('busca', '').strip()
        status = request.args.get('status', '').strip()
        prioridade = request.args.get('prioridade', '').strip()
        cliente_id = request.args.get('cliente_id', '').strip()
        data_inicio = request.args.get('data_inicio', '').strip()
        data_fim = request.args.get('data_fim', '').strip()
        
        # Query principal - filtra OS ativas
        query = OrdemServico.query.filter(OrdemServico.ativo.is_(True))
        
        # Colaborador: somente OS operacional em que ele esteja realmente escalado.
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
        
        # Aplica filtros
        if busca:
            query = query.join(Cliente, isouter=True).filter(
                db.or_(
                    OrdemServico.numero.ilike(f'%{busca}%'),
                    OrdemServico.titulo.ilike(f'%{busca}%'),
                    OrdemServico.equipamento.ilike(f'%{busca}%'),
                    Cliente.nome.ilike(f'%{busca}%')
                )
            )
        
        if status:
            query = query.filter(OrdemServico.status == status)
        
        if prioridade:
            query = query.filter(OrdemServico.prioridade == prioridade)
        
        if cliente_id:
            try:
                query = query.filter(OrdemServico.cliente_id == int(cliente_id))
            except ValueError:
                pass
        
        # Filtro por range de datas
        if data_inicio:
            try:
                data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                query = query.filter(OrdemServico.data_abertura >= data_inicio_obj)
            except ValueError:
                flash('Data de início inválida', 'warning')
        
        if data_fim:
            try:
                data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
                query = query.filter(OrdemServico.data_abertura <= data_fim_obj)
            except ValueError:
                flash('Data de fim inválida', 'warning')
        
        ordens = query.order_by(OrdemServico.data_abertura.desc()).all()
        
        if usuario_eh_colaborador():
            return render_template(
                'os/listar_colaborador.html',
                ordens=ordens,
                busca=busca,
                status_filtro=status,
                colaborador_vinculado=colaborador_vinculado,
            )

        # Lista de clientes para filtro dropdown
        clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
        
        # Estatísticas
        stats = OrdemServico.estatisticas_dashboard()
        
        return render_template('os/listar.html', 
                             ordens=ordens, 
                             clientes=clientes,
                             stats=stats,
                             busca=busca,
                             status_filtro=status,
                             prioridade_filtro=prioridade,
                             cliente_filtro=cliente_id)
    
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"\n❌ ERRO NA ROTA /listar: {error_msg}")
        traceback.print_exc()
        
        # Verifica se é erro de coluna inexistente
        if 'column' in error_msg.lower() or 'does not exist' in error_msg.lower():
            flash('⚠️ Banco de dados desatualizado. Execute as migrations: python migrate_db.py', 'error')
            return render_template('os/erro_db.html', 
                                 erro=error_msg,
                                 solucao='Execute: python migrate_db.py'), 500
        
        flash(f'Erro ao carregar ordens: {error_msg}', 'error')
        return redirect(url_for('painel.index'))

def _parse_data_operacional_campo(valor):
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


@ordem_servico_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    """
    Cria uma nova ordem de serviço.
    
    GET: Exibe formulário
    POST: Processa criação
    """
    if request.method == 'POST':
        try:
            print("🔍 DEBUG: Iniciando processamento POST...")
            
            # Converte valores
            print("🔍 DEBUG: Convertendo valores...")
            valor_servico = safe_decimal_convert(request.form.get('valor_servico', '0'), 0)
            valor_pecas = safe_decimal_convert(request.form.get('valor_pecas', '0'), 0)
            valor_desconto = safe_decimal_convert(request.form.get('valor_desconto', '0'), 0)
            valor_entrada = safe_decimal_convert(request.form.get('valor_entrada', '0'), 0)
            
            print("🔍 DEBUG: Convertendo datas...")
            # Converte datas
            data_prevista = None
            data_primeira_parcela = None
            data_vencimento_pagamento = None
            if request.form.get('data_prevista'):
                data_prevista = datetime.strptime(request.form.get('data_prevista'), '%Y-%m-%d').date()
            if request.form.get('data_primeira_parcela'):
                data_primeira_parcela = datetime.strptime(request.form.get('data_primeira_parcela'), '%Y-%m-%d').date()
            if request.form.get('data_vencimento_pagamento'):
                data_vencimento_pagamento = datetime.strptime(request.form.get('data_vencimento_pagamento'), '%Y-%m-%d').date()
            
            # Converte horas (sistema antigo - mantido para compatibilidade)
            hora_inicial = None
            hora_final = None
            
            if request.form.get('hora_inicial'):
                hora_inicial = datetime.strptime(request.form.get('hora_inicial'), '%H:%M').time()
            if request.form.get('hora_final'):
                hora_final = datetime.strptime(request.form.get('hora_final'), '%H:%M').time()
            
            # Converte horas detalhadas (sistema novo - 6 campos)
            hora_entrada_manha = None
            hora_saida_almoco = None
            hora_retorno_almoco = None
            hora_saida = None
            hora_entrada_extra = None
            hora_saida_extra = None
            
            if request.form.get('hora_entrada_manha'):
                hora_entrada_manha = datetime.strptime(request.form.get('hora_entrada_manha'), '%H:%M').time()
            if request.form.get('hora_saida_almoco'):
                hora_saida_almoco = datetime.strptime(request.form.get('hora_saida_almoco'), '%H:%M').time()
            if request.form.get('hora_retorno_almoco'):
                hora_retorno_almoco = datetime.strptime(request.form.get('hora_retorno_almoco'), '%H:%M').time()
            if request.form.get('hora_saida'):
                hora_saida = datetime.strptime(request.form.get('hora_saida'), '%H:%M').time()
            if request.form.get('hora_entrada_extra'):
                hora_entrada_extra = datetime.strptime(request.form.get('hora_entrada_extra'), '%H:%M').time()
            if request.form.get('hora_saida_extra'):
                hora_saida_extra = datetime.strptime(request.form.get('hora_saida_extra'), '%H:%M').time()
            
            # Define tipo_os: colaboradores sempre criam operacional
            if hasattr(current_user, 'tipo_usuario') and current_user.tipo_usuario == 'colaborador':
                tipo_os_final = 'operacional'
                print("👷 DEBUG: Colaborador criando OS - forçando tipo_os='operacional'")
            else:
                tipo_os_final = request.form.get('tipo_os', 'comercial')
                print(f"👤 DEBUG: Usuário padrão criando OS - tipo_os='{tipo_os_final}'")

            modo_operacional = normalizar_modo_operacional(tipo_os_final, request.form.get('tipo_servico'))
            pode_gerir_financeiro = usuario_eh_admin() and modo_operacional == 'atendimento'
            forma_pagamento, forma_pagamento_valida = validar_forma_pagamento(
                request.form.get('forma_pagamento')
            )
            if not forma_pagamento_valida:
                flash('Forma de pagamento inválida. Selecione uma opção válida.', 'error')
                clientes = buscar_clientes_ativos()
                return render_template(
                    'os/form.html', ordem=None, clientes=clientes,
                    numero_os=OrdemServico.gerar_proximo_numero(),
                    today=date.today(), forma_pagamento_atual='',
                )
            
            # Cria ordem de serviço
            ordem = OrdemServico(
                numero=OrdemServico.gerar_proximo_numero(),
                cliente_id=int(request.form.get('cliente_id')),
                titulo=request.form.get('titulo', request.form.get('equipamento', 'OS sem título')).strip(),
                descricao=request.form.get('descricao', '').strip(),
                observacoes='',
                # Novos campos de solicitação
                solicitante=request.form.get('solicitante', '').strip(),
                descricao_problema='',
                status=request.form.get('status', 'aberta'),
                prioridade=request.form.get('prioridade', 'normal'),
                data_prevista=data_prevista,
                # Data de abertura (editável)
                data_abertura=(datetime.strptime(request.form.get('data_abertura'), '%Y-%m-%d').date() if request.form.get('data_abertura') else date.today()),
                # Data de início (editável)
                data_inicio=(datetime.strptime(request.form.get('data_inicio'), '%Y-%m-%dT%H:%M') if request.form.get('data_inicio') else None),
                # Data de conclusão (editável)
                data_conclusao=(datetime.strptime(request.form.get('data_conclusao'), '%Y-%m-%dT%H:%M') if request.form.get('data_conclusao') else None),
                # Data de vencimento do pagamento (editável)
                data_vencimento_pagamento=(datetime.strptime(request.form.get('data_vencimento_pagamento'), '%Y-%m-%d').date() if pode_gerir_financeiro and request.form.get('data_vencimento_pagamento') else None),
                tecnico_responsavel=request.form.get('tecnico_responsavel', '').strip(),
                valor_servico=Decimal(str(valor_servico)) if pode_gerir_financeiro and valor_servico else Decimal('0'),
                valor_pecas=Decimal(str(valor_pecas)) if pode_gerir_financeiro and valor_pecas else Decimal('0'),
                valor_desconto=Decimal(str(valor_desconto)) if pode_gerir_financeiro and valor_desconto else Decimal('0'),
                prazo_garantia=int(request.form.get('prazo_garantia', 0)) if pode_gerir_financeiro else 0,
                equipamento=request.form.get('equipamento', '').strip(),
                marca_modelo=request.form.get('marca_modelo', '').strip(),
                numero_serie=request.form.get('numero_serie', '').strip(),
                diagnostico=request.form.get('diagnostico', '').strip(),
                diagnostico_tecnico='',
                solucao='',
                # Tipo de OS (comercial ou operacional)
                tipo_os=tipo_os_final,
                tipo_servico=modo_operacional,
                # Novos campos - Tratamento seguro
                km_inicial=safe_int_convert(request.form.get('km_inicial', '')),
                km_final=safe_int_convert(request.form.get('km_final', '')),
                total_km=request.form.get('total_km', '').strip(),
                hora_inicial=hora_inicial,
                hora_final=hora_final,
                intervalo_almoco=safe_int_convert(request.form.get('intervalo_almoco', '60'), default=60),
                # Sistema de horários detalhado (6 campos)
                hora_entrada_manha=hora_entrada_manha,
                hora_saida_almoco=hora_saida_almoco,
                hora_retorno_almoco=hora_retorno_almoco,
                hora_saida=hora_saida,
                hora_entrada_extra=hora_entrada_extra,
                hora_saida_extra=hora_saida_extra,
                # Converter horas para Decimal ou None
                horas_normais=safe_decimal_convert(request.form.get('horasNormais', ''), default=None),
                horas_extras=safe_decimal_convert(request.form.get('horasExtras', ''), default=None),
                total_horas=request.form.get('total_horas', '').strip(),
                condicao_pagamento=request.form.get('condicao_pagamento', 'a_vista') if pode_gerir_financeiro else 'a_vista',
                status_pagamento=request.form.get('status_pagamento', 'pendente') if pode_gerir_financeiro else 'pendente',
                numero_parcelas=safe_int_convert(request.form.get('numero_parcelas', '1'), default=1) if pode_gerir_financeiro else 1,
                valor_entrada=Decimal(str(valor_entrada)) if pode_gerir_financeiro and valor_entrada else Decimal('0'),
                data_primeira_parcela=data_primeira_parcela if pode_gerir_financeiro else None,
                # Novos campos para anexos e descrição de pagamento
                descricao_pagamento=request.form.get('descricao_pagamento', '').strip() if pode_gerir_financeiro else '',
                observacoes_anexos=request.form.get('observacoes_anexos', '').strip(),
                # Assinaturas digitais
                assinatura_cliente=request.form.get('assinatura_cliente', '').strip() or None,
                assinatura_cliente_nome=request.form.get('assinatura_cliente_nome', '').strip() or None,
                assinatura_cliente_data=datetime.fromisoformat(request.form.get('assinatura_cliente_data')) if request.form.get('assinatura_cliente_data') else None,
                assinatura_tecnico=request.form.get('assinatura_tecnico', '').strip() or None,
                assinatura_tecnico_nome=request.form.get('assinatura_tecnico_nome', '').strip() or None,
                assinatura_tecnico_data=datetime.fromisoformat(request.form.get('assinatura_tecnico_data')) if request.form.get('assinatura_tecnico_data') else None
            )

            aplicar_descricao_por_modo(ordem, request.form, tipo_os_final)
            
            # Validações
            print(f"DEBUG: Validando título: '{ordem.titulo}'")
            if not ordem.titulo or ordem.titulo == 'OS sem título':
                # Se não há título, usar equipamento como referência
                if request.form.get('equipamento', '').strip():
                    ordem.titulo = f"OS - {request.form.get('equipamento', '').strip()}"
                else:
                    ordem.titulo = f"OS #{ordem.numero}"
            
            print(f"DEBUG: Validando cliente_id: '{ordem.cliente_id}'")
            if not ordem.cliente_id:
                flash('Cliente é obrigatório!', 'error')
                print(" DEBUG: Cliente é obrigatório")
                clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
                numero_os = OrdemServico.gerar_proximo_numero()
                return render_template('os/form.html', ordem=None, clientes=clientes, numero_os=numero_os, today=date.today())
            
            # Adiciona ordem à sessão (transação será confirmada no final)
            try:
                print("🔍 DEBUG: Iniciando processo de adicionar ordem...")
                db.session.add(ordem)
                # Flush para garantir que ordem.id seja populado antes de criar os itens
                print("🔍 DEBUG: Fazendo flush da ordem...")
                db.session.flush()
                print(f"✅ DEBUG: Ordem adicionada com sucesso, ID: {ordem.id}")
            except Exception as e:
                print(f"❌ DEBUG: Erro ao adicionar ordem: {e}")
                db.session.rollback()
                flash(f'Erro ao criar ordem: {str(e)}', 'error')
                clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
                numero_os = OrdemServico.gerar_proximo_numero()
                return render_template('os/form.html', ordem=None, clientes=clientes, numero_os=numero_os, today=date.today())
            
            # Processa itens de serviço
            print("🔍 DEBUG: Processando itens de serviço com nova estrutura de tipos")
            
            servicos_data = []
            if pode_gerir_financeiro:
                print("🔍 DEBUG: Coletando dados de serviços...")
                servicos_desc_array = request.form.getlist('servico_descricao[]')
                servicos_tipo_array = request.form.getlist('servico_tipo[]')
                servicos_quantidade_array = request.form.getlist('servico_quantidade[]')
                servicos_valor_array = request.form.getlist('servico_valor[]')

                print(f"DEBUG: Arrays simples encontrados - desc: {len(servicos_desc_array)}, tipo: {len(servicos_tipo_array)}, qtd: {len(servicos_quantidade_array)}, valor: {len(servicos_valor_array)}")

                if servicos_desc_array:
                    print("DEBUG: Usando estrutura de arrays simples para serviços (novo)")
                    for i, desc in enumerate(servicos_desc_array):
                        if desc and desc.strip():
                            tipo = servicos_tipo_array[i] if i < len(servicos_tipo_array) else 'Serviço Fechado'
                            quantidade = servicos_quantidade_array[i] if i < len(servicos_quantidade_array) else '1'
                            valor_unitario = servicos_valor_array[i] if i < len(servicos_valor_array) else '0'

                            servicos_data.append({
                                'descricao': desc.strip(),
                                'tipo': tipo,
                                'quantidade': float(safe_decimal_convert(quantidade, 1.0)),
                                'valor_unitario': float(safe_decimal_convert(valor_unitario, 0.0))
                            })
                else:
                    print("DEBUG: Usando estrutura indexada para serviços (fallback)")
                    index = 0
                    while True:
                        desc_key = f'servicos[{index}][descricao]'
                        if desc_key not in request.form:
                            break

                        tipo_key = f'servicos[{index}][tipo]'
                        quantidade_key = f'servicos[{index}][quantidade]'
                        valor_key = f'servicos[{index}][valor_unitario]'

                        desc = request.form.get(desc_key, '').strip()
                        if desc:
                            tipo = request.form.get(tipo_key, 'Serviço Fechado')
                            quantidade = request.form.get(quantidade_key, '1')
                            valor_unitario = request.form.get(valor_key, '0')

                            servicos_data.append({
                                'descricao': desc,
                                'tipo': tipo,
                                'quantidade': float(safe_decimal_convert(quantidade, 1.0)),
                                'valor_unitario': float(safe_decimal_convert(valor_unitario, 0.0))
                            })

                        index += 1
            
            print(f"🔍 DEBUG: Coletados {len(servicos_data)} serviços: {servicos_data}")
            
            # Criar itens de serviço E ACUMULAR TOTAL
            print("="*80)
            print("🚀 VERSÃO NOVA DO CÓDIGO RODANDO - ACUMULAÇÃO DECIMAL")
            print("="*80)
            total_servicos_acumulado = Decimal('0.00')
            
            for servico_data in servicos_data:
                item = OrdemServicoItem(
                    ordem_servico_id=ordem.id,
                    descricao=servico_data['descricao'],
                    tipo_servico=servico_data['tipo'],
                    quantidade=Decimal(str(servico_data['quantidade'])),
                    valor_unitario=Decimal(str(servico_data['valor_unitario']))
                )
                item.calcular_total()
                total_servicos_acumulado += item.valor_total
                db.session.add(item)
                print(f"➕ Serviço adicionado: {item.descricao} - {item.quantidade} {item.tipo_servico} = R$ {item.valor_total}")
            
            # Processa produtos utilizados
            # Aceita tanto produto_id (novos produtos cadastrados) quanto produto_descricao (produtos antigos ou personalizados)
            produtos_id = request.form.getlist('produto_id[]') if pode_gerir_financeiro else []
            produtos_desc = request.form.getlist('produto_descricao[]') if pode_gerir_financeiro else []
            produtos_desc_custom = request.form.getlist('produto_descricao_custom[]') if pode_gerir_financeiro else []
            produtos_qtd = request.form.getlist('produto_quantidade[]') if pode_gerir_financeiro else []
            produtos_valor = request.form.getlist('produto_valor[]') if pode_gerir_financeiro else []
            
            # ACUMULAR TOTAL DE PRODUTOS
            total_produtos_acumulado = Decimal('0.00')
            
            # Determinar qual lista tem mais itens para processar
            max_produtos = max(len(produtos_id) if produtos_id else 0,
                              len(produtos_desc) if produtos_desc else 0)
            
            for i in range(max_produtos):
                descricao = None
                produto_cadastrado_id = None
                
                # Prioridade: produto_id (novo sistema)
                if i < len(produtos_id) and produtos_id[i] and produtos_id[i] != '':
                    if produtos_id[i] == 'custom':
                        # Produto personalizado - usar descrição custom
                        if i < len(produtos_desc_custom) and produtos_desc_custom[i].strip():
                            descricao = produtos_desc_custom[i].strip()
                    else:
                        # Produto cadastrado
                        try:
                            produto_cadastrado_id = int(produtos_id[i])
                            produto_obj = Produto.query.get(produto_cadastrado_id)
                            if produto_obj:
                                descricao = produto_obj.nome
                        except (ValueError, TypeError):
                            pass
                
                # Fallback: produto_descricao (antigo sistema - para OS antigas)
                if not descricao and i < len(produtos_desc) and produtos_desc[i].strip():
                    descricao = produtos_desc[i].strip()
                
                # Se tem descrição, adiciona o produto
                if descricao:
                    produto = OrdemServicoProduto(
                        ordem_servico_id=ordem.id,
                        descricao=descricao,
                        produto_id=produto_cadastrado_id,  # Referência ao produto cadastrado (se houver)
                        quantidade=Decimal(produtos_qtd[i].replace(',', '.')) if i < len(produtos_qtd) and produtos_qtd[i] else 1,
                        valor_unitario=Decimal(produtos_valor[i].replace(',', '.')) if i < len(produtos_valor) and produtos_valor[i] else 0
                    )
                    produto.calcular_total()
                    total_produtos_acumulado += produto.valor_total
                    db.session.add(produto)
                    print(f"➕ Produto adicionado: {descricao} (ID: {produto_cadastrado_id}) - {produto.quantidade} x R$ {produto.valor_unitario} = R$ {produto.valor_total}")
            
            
            # CALCULAR TOTAIS DIRETO DOS VALORES ACUMULADOS (tudo já é Decimal)
            total_final = total_servicos_acumulado + total_produtos_acumulado - ordem.valor_desconto

            ordem.valor_servico = total_servicos_acumulado
            ordem.valor_pecas = total_produtos_acumulado
            ordem.valor_total = total_final

            if not pode_gerir_financeiro:
                limpar_dados_financeiros(ordem)
            
            print("="*80)
            print(f"✅ TOTAIS CALCULADOS (DECIMAL PURO):")
            print(f"   Serviços: {ordem.valor_servico} (tipo: {type(ordem.valor_servico)})")
            print(f"   Produtos: {ordem.valor_pecas} (tipo: {type(ordem.valor_pecas)})")
            print(f"   Desconto: {ordem.valor_desconto} (tipo: {type(ordem.valor_desconto)})")
            print(f"   TOTAL: {ordem.valor_total} (tipo: {type(ordem.valor_total)})")
            print("="*80)
            
            # NOTE: parcelas processing moved to after total calculation (see below)

            # Preferência: incluir imagens no relatório
            ordem.incluir_imagens_relatorio = True if request.form.get('incluir_imagens_relatorio') in ('1', 'on', 'true') else False
            
            # Processa arquivos anexados
            if 'anexos' in request.files or 'anexos[]' in request.files:
                # Pega os arquivos usando o nome correto
                if 'anexos' in request.files:
                    files = request.files.getlist('anexos')
                else:
                    files = request.files.getlist('anexos[]')
                for file in files:
                    if file and file.filename and allowed_file(file.filename):
                        try:
                            # Verifica tamanho
                            if get_file_size(file) > MAX_FILE_SIZE:
                                flash(f'Arquivo {file.filename} é muito grande (máximo 16MB)', 'warning')
                                continue
                                
                            # Gera nome único
                            filename = generate_unique_filename(file.filename)
                            filepath = os.path.join(UPLOAD_FOLDER, filename)
                            
                            # Cria diretório se não existe
                            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                            
                            # Lê o conteúdo do arquivo para salvar no banco (Render precisa)
                            file.seek(0)  # Volta ao início do arquivo
                            file_content = file.read()
                            file.seek(0)  # Volta novamente para salvar em disco
                            
                            # Salva arquivo em disco também (para desenvolvimento local)
                            file.save(filepath)
                            
                            # Detecta tipo do arquivo
                            content_type = file.content_type or 'application/octet-stream'
                            tipo_arquivo = 'image' if content_type.startswith('image/') else 'document'
                            
                            # Cria registro no banco (com conteúdo em BLOB para Render)
                            try:
                                anexo = OrdemServicoAnexo(
                                    ordem_servico_id=ordem.id,
                                    nome_original=file.filename,
                                    nome_arquivo=filename,
                                    tipo_arquivo=tipo_arquivo,
                                    mime_type=content_type,
                                    tamanho=len(file_content),
                                    caminho=filepath,
                                    conteudo=file_content  # Salva no banco para persistir no Render
                                )
                            except TypeError:
                                # Se a coluna conteudo não existir ainda, cria sem ela
                                print(f"⚠️ Coluna 'conteudo' não existe, criando anexo sem BLOB")
                                anexo = OrdemServicoAnexo(
                                    ordem_servico_id=ordem.id,
                                    nome_original=file.filename,
                                    nome_arquivo=filename,
                                    tipo_arquivo=tipo_arquivo,
                                    mime_type=content_type,
                                    tamanho=len(file_content),
                                    caminho=filepath
                                )
                            db.session.add(anexo)
                            
                        except Exception as e:
                            flash(f'Erro ao salvar arquivo {file.filename}: {str(e)}', 'warning')
                    elif file and file.filename and not allowed_file(file.filename):
                        flash(f'Tipo de arquivo não permitido: {file.filename}', 'warning')

            processar_colaboradores_os(ordem, request.form)
            
            # Processa parcelas (validação + criação)
            if pode_gerir_financeiro and ordem.condicao_pagamento == 'parcelado' and ordem.numero_parcelas and ordem.numero_parcelas > 0:
                entrada = safe_decimal_convert(request.form.get('valor_entrada', '0'), 0)
                parcelas_datas = request.form.getlist('parcela_data[]')
                parcelas_valores = request.form.getlist('parcela_valor[]')

                base_date = (
                    ordem.data_primeira_parcela
                    or ordem.data_prevista
                    or ordem.data_abertura
                    or date.today()
                )
                tolerancia = Decimal('0.02')

                if parcelas_valores and any(str(valor).strip() for valor in parcelas_valores):
                    parsed_parcelas = _parse_parcelas_manuais(parcelas_datas, parcelas_valores, base_date)

                    if len(parsed_parcelas) != ordem.numero_parcelas:
                        raise ValueError(
                            f'Foram informadas {len(parsed_parcelas)} parcelas, mas o Nº Parcelas está como {ordem.numero_parcelas}.'
                        )

                    soma_parcelas = sum((parcela[2] for parcela in parsed_parcelas), Decimal('0'))
                    total_os_decimal = Decimal(str(total_final))
                    if abs(soma_parcelas - total_os_decimal) > tolerancia:
                        raise ValueError('A soma das parcelas deve corresponder exatamente ao valor total da OS.')

                    if entrada > 0 and abs(parsed_parcelas[0][2] - entrada) > tolerancia:
                        raise ValueError(
                            'Quando existe entrada, o valor da parcela #1 deve ser igual ao Valor Entrada.'
                        )
                else:
                    parsed_parcelas = _montar_parcelas_automaticas(
                        total_final,
                        ordem.numero_parcelas,
                        entrada,
                        base_date,
                    )

                ordem.data_primeira_parcela = parsed_parcelas[0][1] if parsed_parcelas else None
                _reconciliar_parcelas_ordem(ordem, parsed_parcelas)

            try:
                print("🔄 DEBUG: Tentando fazer commit da ordem...")
                db.session.commit()
                print("✅ DEBUG: Commit realizado com sucesso!")
                ordem.valor_total = total_final
                
                # === INTEGRAÇÃO FINANCEIRA ===
                try:
                    from app.financeiro.financeiro_utils import gerar_lancamento_ordem_servico
                    print("🔄 DEBUG: Gerando lançamento financeiro...")
                    gerar_lancamento_ordem_servico(ordem, forma_pagamento=forma_pagamento)
                    print("✅ DEBUG: Integração financeira concluída!")
                except Exception as financeiro_error:
                    print(f"⚠️ DEBUG: Erro na integração financeira: {financeiro_error}")
                    # Não interrompe o fluxo - ordem já foi criada
                
            except Exception as commit_error:
                print(f"❌ DEBUG: Erro no commit: {commit_error}")
                print(f"❌ DEBUG: Tipo do erro: {type(commit_error)}")
                import traceback
                traceback.print_exc()
                db.session.rollback()
                flash(f'Erro ao salvar ordem de serviço no banco de dados: {str(commit_error)}', 'error')
                clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
                numero_os = OrdemServico.gerar_proximo_numero()
                return render_template('os/form.html', ordem=None, clientes=clientes, numero_os=numero_os, today=date.today())

            flash(f'✅ Ordem de Serviço #{ordem.numero} criada com sucesso!', 'success')
            print(f"✅ DEBUG: Redirecionando para visualizar OS #{ordem.numero} (ID: {ordem.id})")
            return redirect(url_for('ordem_servico.visualizar', id=ordem.id))
            
        except Exception as e:
            # Em caso de erro, desfaz qualquer alteração pendente na sessão
            print(f"❌ DEBUG: Erro geral ao criar OS: {str(e)}")
            print(f"❌ DEBUG: Tipo do erro: {type(e)}")
            import traceback
            traceback.print_exc()
            try:
                db.session.rollback()
            except Exception:
                pass
            flash(f'❌ Erro ao criar ordem de serviço: {str(e)}', 'error')
            clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
            numero_os = OrdemServico.gerar_proximo_numero()
            return render_template('os/form.html', ordem=None, clientes=clientes, numero_os=numero_os, today=date.today())
    
    # GET - exibe formulário vazio
    clientes = buscar_clientes_ativos()
    numero_os = OrdemServico.gerar_proximo_numero()
    return render_template('os/form.html', ordem=None, clientes=clientes, numero_os=numero_os, today=date.today())

@ordem_servico_bp.route('/<int:id>')
def visualizar(id):
    """
    Visualiza detalhes de uma ordem de serviço.
    
    Args:
        id: ID da ordem de serviço
    """
    from sqlalchemy.orm import joinedload
    
    # Carregar OS com todos os relacionamentos necessários
    ordem = OrdemServico.query.options(
        joinedload(OrdemServico.servicos),
        joinedload(OrdemServico.produtos_utilizados),
        joinedload(OrdemServico.parcelas),
        joinedload(OrdemServico.anexos)
    ).filter_by(id=id, ativo=True).first()
    
    if not ordem:
        flash('Ordem de serviço não encontrada!', 'error')
        return redirect(url_for('ordem_servico.listar'))
    
    if usuario_eh_colaborador():
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
    print(f"📋 OS #{ordem.numero}: {len(ordem.servicos)} serviços, {len(ordem.produtos_utilizados)} produtos")
    print(f"💰 Valores: Serviços={ordem.valor_total_servicos}, Produtos={ordem.valor_total_produtos}")
    
    return render_template('os/visualizar.html', ordem=ordem, today=date.today())

@ordem_servico_bp.route('/<int:id>/apontamento', methods=['GET', 'POST'])
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
def editar(id):
    """
    Edita uma ordem de serviço existente.
    
    Args:
        id: ID da ordem de serviço
    """
    print(f"DEBUG: Iniciando edição para ID {id}")
    
    # Carregar OS com eager loading de parcelas e colaboradores
    from sqlalchemy.orm import joinedload
    ordem = OrdemServico.query.options(
        joinedload(OrdemServico.parcelas),
        joinedload(OrdemServico.colaboradores_trabalho)
    ).filter_by(id=id, ativo=True).first()
    
    if not ordem:
        print(f" DEBUG: Ordem com ID {id} não encontrada")
        flash('Ordem de serviço não encontrada!', 'error')
        return redirect(url_for('ordem_servico.listar'))
    
    # Colaboradores só podem editar ordens operacionais
    if hasattr(current_user, 'tipo_usuario') and current_user.tipo_usuario == 'colaborador' and ordem.tipo_os != 'operacional':
        flash('Você não tem permissão para editar esta ordem de serviço.', 'error')
        return redirect(url_for('ordem_servico.listar'))
    
    print(f"✅ DEBUG: Ordem encontrada: {ordem.numero}")
    print(f"💳 DEBUG PARCELAS: {len(ordem.parcelas) if hasattr(ordem, 'parcelas') and ordem.parcelas else 0} parcelas carregadas")
    print(f"👷 DEBUG COLABORADORES: {len(ordem.colaboradores_trabalho) if hasattr(ordem, 'colaboradores_trabalho') and ordem.colaboradores_trabalho else 0} colaboradores carregados")
    if hasattr(ordem, 'colaboradores_trabalho') and ordem.colaboradores_trabalho:
        for c in ordem.colaboradores_trabalho:
            if c.ativo:
                print(f"   Colaborador {c.colaborador_id}: Manhã {c.hora_entrada_manha}-{c.hora_saida_manha}, Tarde {c.hora_entrada_tarde}-{c.hora_saida_tarde}, Extra {c.hora_entrada_extra}-{c.hora_saida_extra}")
    if hasattr(ordem, 'parcelas') and ordem.parcelas:
        for p in ordem.parcelas:
            print(f"   Parcela {p.numero_parcela}: R$ {p.valor} - Venc: {p.data_vencimento}")
    
    if request.method == 'POST':
        try:
            print(f"DEBUG: Processando POST para ordem {id}")
            print(f"DEBUG: Form data keys: {list(request.form.keys())}")
            
            # Debug específico para serviços e produtos
            servicos_desc = request.form.getlist('servico_descricao[]')
            produtos_desc = request.form.getlist('produto_descricao[]')
            print(f"DEBUG: Serviços encontrados: {len(servicos_desc)} - {servicos_desc}")
            print(f"DEBUG: Produtos encontrados: {len(produtos_desc)} - {produtos_desc}")
            usuario_admin = usuario_eh_admin()
            parcelamento_original = {
                'condicao': ordem.condicao_pagamento,
                'numero': len(ordem.parcelas) if getattr(ordem, 'parcelas', None) else (ordem.numero_parcelas or 1),
                'entrada': Decimal(str(ordem.valor_entrada or 0)),
                'data_primeira': ordem.data_primeira_parcela,
            }
            
            # ===== DEFINE pode_gerir_financeiro NO INÍCIO =====
            # Determina tipo_os primeiro para calcular modo operacional
            tipo_os_preliminar = request.form.get('tipo_os', ordem.tipo_os or 'comercial')
            if hasattr(current_user, 'tipo_usuario') and current_user.tipo_usuario == 'colaborador':
                tipo_os_preliminar = 'operacional'  # Forçar operacional para colaboradores
            
            modo_operacional = aplicar_descricao_por_modo(ordem, request.form, tipo_os_preliminar)
            pode_gerir_financeiro = usuario_admin and modo_operacional == 'atendimento'
            print(f"🔑 DEBUG: usuario_admin={usuario_admin}, modo_operacional='{modo_operacional}', pode_gerir_financeiro={pode_gerir_financeiro}")
            # ===================================================
            
            # Converte valores
            valor_servico = safe_decimal_convert(request.form.get('valor_servico', '0'), 0)
            valor_pecas = safe_decimal_convert(request.form.get('valor_pecas', '0'), 0)
            valor_desconto = safe_decimal_convert(request.form.get('valor_desconto', '0'), 0)
            
            # Converte datas
            data_prevista = None
            if request.form.get('data_prevista'):
                data_prevista = datetime.strptime(request.form.get('data_prevista'), '%Y-%m-%d').date()
            
            # Atualiza dados
            ordem.cliente_id = int(request.form.get('cliente_id'))
            ordem.titulo = request.form.get('titulo', request.form.get('equipamento', ordem.titulo or 'OS sem título')).strip()
            ordem.descricao = request.form.get('descricao', '').strip()
            # Novos campos de solicitação
            ordem.solicitante = request.form.get('solicitante', '').strip()
            
            # Controla mudança de status
            novo_status = request.form.get('status', 'aberta')
            # Permite sobrescrever data_abertura e data_conclusao manualmente
            if request.form.get('data_abertura'):
                try:
                    ordem.data_abertura = datetime.strptime(request.form.get('data_abertura'), '%Y-%m-%d').date()
                except Exception:
                    pass

            if request.form.get('data_conclusao'):
                try:
                    ordem.data_conclusao = datetime.strptime(request.form.get('data_conclusao'), '%Y-%m-%dT%H:%M').replace(tzinfo=None)
                except Exception:
                    try:
                        ordem.data_conclusao = datetime.strptime(request.form.get('data_conclusao'), '%Y-%m-%d')
                    except Exception as e:
                        print(f"⚠️ Erro ao converter data_conclusao='{request.form.get('data_conclusao')}': {e}")
            else:
                # Campo enviado vazio = limpar data de conclusão
                ordem.data_conclusao = None

            # Permite sobrescrever data_inicio manualmente
            if request.form.get('data_inicio'):
                try:
                    ordem.data_inicio = datetime.strptime(request.form.get('data_inicio'), '%Y-%m-%dT%H:%M').replace(tzinfo=None)
                except Exception:
                    try:
                        ordem.data_inicio = datetime.strptime(request.form.get('data_inicio'), '%Y-%m-%d')
                    except Exception as e:
                        print(f"⚠️ Erro ao converter data_inicio='{request.form.get('data_inicio')}': {e}")
            else:
                ordem.data_inicio = None

            if novo_status != ordem.status:
                if novo_status == 'em_andamento' and ordem.status == 'aberta':
                    ordem.data_inicio = dt.now()
                elif novo_status == 'concluida' and ordem.status != 'concluida' and not ordem.data_conclusao:
                    ordem.data_conclusao = dt.now()
            ordem.status = novo_status
            
            ordem.prioridade = request.form.get('prioridade', 'normal')
            ordem.data_prevista = data_prevista
            ordem.tecnico_responsavel = request.form.get('tecnico_responsavel', '').strip()
            # valor_servico e valor_pecas serão recalculados após processar itens
            if pode_gerir_financeiro:
                ordem.valor_desconto = safe_decimal_convert(request.form.get('valor_desconto', '0'), 0)
                ordem.prazo_garantia = int(request.form.get('prazo_garantia', 0))
            ordem.equipamento = request.form.get('equipamento', '').strip()
            ordem.marca_modelo = request.form.get('marca_modelo', '').strip()
            ordem.numero_serie = request.form.get('numero_serie', '').strip()
            ordem.diagnostico = request.form.get('diagnostico', '').strip()
            
            # Tipo de OS: colaboradores não podem alterar, sempre operacional
            if hasattr(current_user, 'tipo_usuario') and current_user.tipo_usuario == 'colaborador':
                ordem.tipo_os = 'operacional'  # Forçar operacional para colaboradores
                print("👷 DEBUG: Colaborador editando OS - mantendo tipo_os='operacional'")
            else:
                ordem.tipo_os = request.form.get('tipo_os', ordem.tipo_os or 'comercial')
                print(f"👤 DEBUG: Usuário padrão editando OS - tipo_os='{ordem.tipo_os}'")
            
            # Recalcula modo_operacional com o tipo_os final
            modo_operacional = aplicar_descricao_por_modo(ordem, request.form, ordem.tipo_os)
            pode_gerir_financeiro = usuario_admin and modo_operacional == 'atendimento'
            print(f"🔄 DEBUG: Recalculado - modo_operacional='{modo_operacional}', pode_gerir_financeiro={pode_gerir_financeiro}")
            
            # Controle de KM e Tempo - Tratamento seguro de conversão
            ordem.km_inicial = safe_int_convert(request.form.get('km_inicial', ''))
            ordem.km_final = safe_int_convert(request.form.get('km_final', ''))
            ordem.total_km = request.form.get('total_km', '').strip()
            
            # Processa horários (sistema antigo - compatibilidade)
            hora_inicial = None
            hora_final = None
            
            if request.form.get('hora_inicial'):
                hora_inicial = datetime.strptime(request.form.get('hora_inicial'), '%H:%M').time()
            if request.form.get('hora_final'):
                hora_final = datetime.strptime(request.form.get('hora_final'), '%H:%M').time()
            
            ordem.hora_inicial = hora_inicial
            ordem.hora_final = hora_final
            
            # Processa horários detalhados (sistema novo - 6 campos)
            if request.form.get('hora_entrada_manha'):
                ordem.hora_entrada_manha = datetime.strptime(request.form.get('hora_entrada_manha'), '%H:%M').time()
            else:
                ordem.hora_entrada_manha = None
                
            if request.form.get('hora_saida_almoco'):
                ordem.hora_saida_almoco = datetime.strptime(request.form.get('hora_saida_almoco'), '%H:%M').time()
            else:
                ordem.hora_saida_almoco = None
                
            if request.form.get('hora_retorno_almoco'):
                ordem.hora_retorno_almoco = datetime.strptime(request.form.get('hora_retorno_almoco'), '%H:%M').time()
            else:
                ordem.hora_retorno_almoco = None
                
            if request.form.get('hora_saida'):
                ordem.hora_saida = datetime.strptime(request.form.get('hora_saida'), '%H:%M').time()
            else:
                ordem.hora_saida = None
                
            if request.form.get('hora_entrada_extra'):
                ordem.hora_entrada_extra = datetime.strptime(request.form.get('hora_entrada_extra'), '%H:%M').time()
            else:
                ordem.hora_entrada_extra = None
                
            if request.form.get('hora_saida_extra'):
                ordem.hora_saida_extra = datetime.strptime(request.form.get('hora_saida_extra'), '%H:%M').time()
            else:
                ordem.hora_saida_extra = None
            
            # Campos de horas calculadas - converter para Decimal
            try:
                hn = request.form.get('horasNormais', '').strip()
                ordem.horas_normais = Decimal(str(hn)) if hn and hn != '' else None
            except:
                ordem.horas_normais = None
            
            try:
                he = request.form.get('horasExtras', '').strip()
                ordem.horas_extras = Decimal(str(he)) if he and he != '' else None
            except:
                ordem.horas_extras = None
            ordem.intervalo_almoco = safe_int_convert(request.form.get('intervalo_almoco', '60'), default=60)
            ordem.total_horas = request.form.get('total_horas', '').strip()
            
            # Condições de Pagamento
            forma_pagamento = None
            if pode_gerir_financeiro:
                forma_pagamento, forma_pagamento_valida = validar_forma_pagamento(
                    request.form.get('forma_pagamento')
                )
                if not forma_pagamento_valida:
                    flash('Forma de pagamento inválida. Selecione uma opção válida.', 'error')
                    db.session.rollback()
                    clientes = buscar_clientes_ativos()
                    return render_template(
                        'os/form.html', ordem=ordem, clientes=clientes,
                        today=date.today(), forma_pagamento_atual='',
                    )
                ordem.condicao_pagamento = request.form.get('condicao_pagamento', 'a_vista')
                ordem.status_pagamento = request.form.get('status_pagamento', 'pendente')
                ordem.numero_parcelas = int(request.form.get('numero_parcelas', 1)) if request.form.get('numero_parcelas') else 1
                ordem.valor_entrada = safe_decimal_convert(request.form.get('valor_entrada', '0'), 0)
            
            # Data da primeira parcela
            if pode_gerir_financeiro:
                if request.form.get('data_primeira_parcela'):
                    try:
                        ordem.data_primeira_parcela = datetime.strptime(
                            request.form.get('data_primeira_parcela'),
                            '%Y-%m-%d'
                        ).date()
                    except Exception:
                        ordem.data_primeira_parcela = None
                else:
                    ordem.data_primeira_parcela = None

            # Data de vencimento do pagamento
            if pode_gerir_financeiro:
                if request.form.get('data_vencimento_pagamento'):
                    try:
                        ordem.data_vencimento_pagamento = datetime.strptime(
                            request.form.get('data_vencimento_pagamento'),
                            '%Y-%m-%d'
                        ).date()
                    except Exception:
                        ordem.data_vencimento_pagamento = None
                else:
                    ordem.data_vencimento_pagamento = None

            if pode_gerir_financeiro:
                ordem.descricao_pagamento = request.form.get('descricao_pagamento', '').strip()
            ordem.observacoes_anexos = request.form.get('observacoes_anexos', '').strip()
            
            # Atualizar assinaturas digitais
            assinatura_cliente = request.form.get('assinatura_cliente', '').strip()
            if assinatura_cliente:
                ordem.assinatura_cliente = assinatura_cliente
                ordem.assinatura_cliente_nome = request.form.get('assinatura_cliente_nome', '').strip() or None
                assinatura_cliente_data_str = request.form.get('assinatura_cliente_data', '').strip()
                if assinatura_cliente_data_str:
                    try:
                        ordem.assinatura_cliente_data = datetime.fromisoformat(assinatura_cliente_data_str)
                    except:
                        ordem.assinatura_cliente_data = None
            elif not assinatura_cliente and not request.form.get('assinatura_cliente_nome'):
                # Se não tem assinatura e não tem nome, limpar tudo
                ordem.assinatura_cliente = None
                ordem.assinatura_cliente_nome = None
                ordem.assinatura_cliente_data = None
            
            assinatura_tecnico = request.form.get('assinatura_tecnico', '').strip()
            if assinatura_tecnico:
                ordem.assinatura_tecnico = assinatura_tecnico
                ordem.assinatura_tecnico_nome = request.form.get('assinatura_tecnico_nome', '').strip() or None
                assinatura_tecnico_data_str = request.form.get('assinatura_tecnico_data', '').strip()
                if assinatura_tecnico_data_str:
                    try:
                        ordem.assinatura_tecnico_data = datetime.fromisoformat(assinatura_tecnico_data_str)
                    except:
                        ordem.assinatura_tecnico_data = None
            elif not assinatura_tecnico and not request.form.get('assinatura_tecnico_nome'):
                # Se não tem assinatura e não tem nome, limpar tudo
                ordem.assinatura_tecnico = None
                ordem.assinatura_tecnico_nome = None
                ordem.assinatura_tecnico_data = None
            
            # Validações
            if not ordem.titulo or ordem.titulo == 'OS sem título':
                # Se não há título, usar equipamento como referência
                if request.form.get('equipamento', '').strip():
                    ordem.titulo = f"OS - {request.form.get('equipamento', '').strip()}"
                else:
                    ordem.titulo = f"OS #{ordem.numero}"

            if modo_operacional != 'atendimento':
                limpar_itens_e_parcelas(ordem)
                limpar_dados_financeiros(ordem)
            elif pode_gerir_financeiro:
                print(f"DEBUG: Removendo {len(ordem.servicos)} serviços antigos via loop delete")
                servicos_removidos = 0
                for item_existente in list(ordem.servicos):
                    print(f"  🗑️ Removendo serviço: {item_existente.descricao}")
                    db.session.delete(item_existente)
                    servicos_removidos += 1
                print(f" {servicos_removidos} serviços removidos")

                print("DEBUG: Processando itens de serviço com nova estrutura de tipos (edição)")
                servicos_desc_array = request.form.getlist('servico_descricao[]')
                servicos_tipo_array = request.form.getlist('servico_tipo[]')
                servicos_quantidade_array = request.form.getlist('servico_quantidade[]')
                servicos_valor_array = request.form.getlist('servico_valor[]')

                print(f"DEBUG: Arrays simples encontrados - desc: {len(servicos_desc_array)}, tipo: {len(servicos_tipo_array)}, qtd: {len(servicos_quantidade_array)}, valor: {len(servicos_valor_array)}")

                servicos_data = []
                if servicos_desc_array:
                    print("DEBUG: Usando estrutura de arrays simples para serviços")
                    for i, desc in enumerate(servicos_desc_array):
                        if desc and desc.strip():
                            tipo = servicos_tipo_array[i] if i < len(servicos_tipo_array) else 'Serviço Fechado'
                            quantidade = servicos_quantidade_array[i] if i < len(servicos_quantidade_array) else '1'
                            valor_unitario = servicos_valor_array[i] if i < len(servicos_valor_array) else '0'

                            servicos_data.append({
                                'descricao': desc.strip(),
                                'tipo': tipo,
                                'quantidade': float(safe_decimal_convert(quantidade, 1.0)),
                                'valor_unitario': float(safe_decimal_convert(valor_unitario, 0.0))
                            })
                else:
                    print("DEBUG: Usando estrutura indexada para serviços (fallback)")
                    index = 0
                    while True:
                        desc_key = f'servicos[{index}][descricao]'
                        if desc_key not in request.form:
                            break

                        tipo_key = f'servicos[{index}][tipo]'
                        quantidade_key = f'servicos[{index}][quantidade]'
                        valor_key = f'servicos[{index}][valor_unitario]'

                        desc = request.form.get(desc_key, '').strip()
                        if desc:
                            tipo = request.form.get(tipo_key, 'Serviço Fechado')
                            quantidade = request.form.get(quantidade_key, '1')
                            valor_unitario = request.form.get(valor_key, '0')

                            servicos_data.append({
                                'descricao': desc,
                                'tipo': tipo,
                                'quantidade': float(safe_decimal_convert(quantidade, 1.0)),
                                'valor_unitario': float(safe_decimal_convert(valor_unitario, 0.0))
                            })

                        index += 1

                print(f"DEBUG: Coletados {len(servicos_data)} serviços para edição: {servicos_data}")

                servicos_adicionados = 0
                for servico_data in servicos_data:
                    item = OrdemServicoItem(
                        ordem_servico_id=ordem.id,
                        descricao=servico_data['descricao'],
                        tipo_servico=servico_data['tipo'],
                        quantidade=Decimal(str(servico_data['quantidade'])),
                        valor_unitario=Decimal(str(servico_data['valor_unitario']))
                    )
                    item.calcular_total()
                    db.session.add(item)
                    servicos_adicionados += 1
                    print(f"  ➕ Adicionado serviço: {item.descricao} - {item.quantidade} {item.tipo_servico} = R$ {item.valor_total}")
                print(f" {servicos_adicionados} serviços adicionados")

                print(f"DEBUG: Removendo {len(ordem.produtos_utilizados)} produtos antigos via loop delete")
                produtos_removidos = 0
                for produto_existente in list(ordem.produtos_utilizados):
                    print(f"  🗑️ Removendo produto: {produto_existente.descricao}")
                    db.session.delete(produto_existente)
                    produtos_removidos += 1
                print(f" {produtos_removidos} produtos removidos")

                produtos_id = request.form.getlist('produto_id[]')
                produtos_desc = request.form.getlist('produto_descricao[]')
                produtos_desc_custom = request.form.getlist('produto_descricao_custom[]')
                produtos_qtd = request.form.getlist('produto_quantidade[]')
                produtos_valor = request.form.getlist('produto_valor[]')

                max_produtos = max(len(produtos_id) if produtos_id else 0,
                                  len(produtos_desc) if produtos_desc else 0)

                print(f"DEBUG: Processando {max_produtos} produtos do formulário")
                print(f"  📝 IDs: {produtos_id if produtos_id else []}")
                print(f"  📝 Descrições: {produtos_desc if produtos_desc else []}")
                print(f"  📝 Custom: {produtos_desc_custom if produtos_desc_custom else []}")

                produtos_adicionados = 0
                for i in range(max_produtos):
                    descricao = None
                    produto_cadastrado_id = None

                    if i < len(produtos_id) and produtos_id[i] and produtos_id[i] != '':
                        if produtos_id[i] == 'custom':
                            if i < len(produtos_desc_custom) and produtos_desc_custom[i].strip():
                                descricao = produtos_desc_custom[i].strip()
                        else:
                            try:
                                produto_cadastrado_id = int(produtos_id[i])
                                produto_obj = Produto.query.get(produto_cadastrado_id)
                                if produto_obj:
                                    descricao = produto_obj.nome
                            except (ValueError, TypeError):
                                pass

                    if not descricao and i < len(produtos_desc) and produtos_desc[i].strip():
                        descricao = produtos_desc[i].strip()

                    if descricao:
                        qtd_value = produtos_qtd[i] if i < len(produtos_qtd) else ''
                        valor_value = produtos_valor[i] if i < len(produtos_valor) else ''

                        produto = OrdemServicoProduto(
                            ordem_servico_id=ordem.id,
                            descricao=descricao,
                            produto_id=produto_cadastrado_id,
                            quantidade=safe_decimal_convert(qtd_value, 1),
                            valor_unitario=safe_decimal_convert(valor_value, 0)
                        )
                        produto.calcular_total()
                        db.session.add(produto)
                        produtos_adicionados += 1
                        print(f"  ➕ Adicionado produto: {descricao} (ID: {produto_cadastrado_id})")
                print(f" {produtos_adicionados} produtos adicionados")

                ordem.valor_servico = ordem.valor_total_servicos
                ordem.valor_pecas = ordem.valor_total_produtos
                ordem.valor_total = ordem.valor_total_calculado_novo
                print(f"🧮 DEBUG: Valor serviço: R$ {ordem.valor_servico} | Valor peças: R$ {ordem.valor_pecas} | Valor total: R$ {ordem.valor_total}")

            # Processa parcelas da ordem com reconciliação segura
            tem_parcelas_existentes = bool(
                hasattr(ordem, 'parcelas') and ordem.parcelas and len(ordem.parcelas) > 0
            )

            if pode_gerir_financeiro and ordem.condicao_pagamento == 'parcelado' and ordem.numero_parcelas > 0:
                entrada = safe_decimal_convert(request.form.get('valor_entrada', '0'), 0)
                parcelas_datas = request.form.getlist('parcela_data[]')
                parcelas_valores = request.form.getlist('parcela_valor[]')
                recalcular_solicitado = request.form.get('recalcular_parcelas') == '1'

                base_date = (
                    ordem.data_primeira_parcela
                    or ordem.data_prevista
                    or ordem.data_abertura
                    or date.today()
                )
                tolerancia = Decimal('0.02')

                if parcelas_valores and any(str(valor).strip() for valor in parcelas_valores):
                    parsed_parcelas = _parse_parcelas_manuais(parcelas_datas, parcelas_valores, base_date)

                    if len(parsed_parcelas) != ordem.numero_parcelas:
                        raise ValueError(
                            f'Foram informadas {len(parsed_parcelas)} parcelas, mas o Nº Parcelas está como {ordem.numero_parcelas}.'
                        )

                    soma_parcelas = sum((parcela[2] for parcela in parsed_parcelas), Decimal('0'))
                    if abs(soma_parcelas - Decimal(str(ordem.valor_total))) > tolerancia:
                        raise ValueError('A soma das parcelas deve corresponder exatamente ao valor total da OS.')

                    if entrada > 0 and abs(parsed_parcelas[0][2] - entrada) > tolerancia:
                        raise ValueError(
                            'Quando existe entrada, o valor da parcela #1 deve ser igual ao Valor Entrada.'
                        )

                    ordem.data_primeira_parcela = parsed_parcelas[0][1] if parsed_parcelas else None
                    _reconciliar_parcelas_ordem(ordem, parsed_parcelas)

                elif recalcular_solicitado or not tem_parcelas_existentes:
                    parsed_parcelas = _montar_parcelas_automaticas(
                        ordem.valor_total,
                        ordem.numero_parcelas,
                        entrada,
                        base_date,
                    )
                    ordem.data_primeira_parcela = parsed_parcelas[0][1] if parsed_parcelas else None
                    _reconciliar_parcelas_ordem(ordem, parsed_parcelas)

                else:
                    configuracao_alterada = (
                        ordem.numero_parcelas != parcelamento_original['numero']
                        or Decimal(str(ordem.valor_entrada or 0)) != parcelamento_original['entrada']
                        or ordem.data_primeira_parcela != parcelamento_original['data_primeira']
                    )
                    if configuracao_alterada:
                        raise ValueError(
                            'Os campos do parcelamento foram alterados. Clique em "Refazer Parcelamento", '
                            'revise a tabela gerada e salve novamente.'
                        )

                    print(
                        f"✅ Preservando {len(ordem.parcelas)} parcelas existentes "
                        "(nenhuma refação solicitada)"
                    )

            elif pode_gerir_financeiro and ordem.condicao_pagamento != 'parcelado':
                if tem_parcelas_existentes:
                    _reconciliar_parcelas_ordem(ordem, [])

                ordem.numero_parcelas = 1
                if ordem.condicao_pagamento in {'a_vista', '30_dias'}:
                    ordem.data_primeira_parcela = None
                    ordem.valor_entrada = Decimal('0')

            # Processa arquivos anexados
            print(f"🔍 DEBUG ANEXOS EDITAR: Verificando anexos em request.files...")
            print(f"🔍 DEBUG ANEXOS EDITAR: request.files keys: {list(request.files.keys())}")
            print(f"🔍 DEBUG ANEXOS EDITAR: request.form keys: {list(request.form.keys())}")
            print(f"🔍 DEBUG ANEXOS EDITAR: Tem campo 'anexos'? {'anexos' in request.files}")
            print(f"🔍 DEBUG ANEXOS EDITAR: Tem campo 'anexos[]'? {'anexos[]' in request.files}")
            print(f"🔍 DEBUG ANEXOS EDITAR: Valor de request.files.get('anexos'): {request.files.get('anexos')}")
            print(f"🔍 DEBUG ANEXOS EDITAR: Valor de request.files.get('anexos[]'): {request.files.get('anexos[]')}")

            # Atualiza preferência: incluir imagens no PDF
            ordem.incluir_imagens_relatorio = True if request.form.get('incluir_imagens_relatorio') in ('1', 'on', 'true') else False
            
            # Verifica tanto 'anexos' quanto 'anexos[]'
            if 'anexos' in request.files or 'anexos[]' in request.files:
                # Pega os arquivos usando o nome correto
                if 'anexos' in request.files:
                    files = request.files.getlist('anexos')
                    campo_usado = 'anexos'
                else:
                    files = request.files.getlist('anexos[]')
                    campo_usado = 'anexos[]'
                    
                print(f"🔍 DEBUG ANEXOS EDITAR: {len(files)} arquivos encontrados usando campo '{campo_usado}'")
                
                for i, file in enumerate(files):
                    print(f"🔍 DEBUG ANEXOS EDITAR: Arquivo {i+1}: filename='{file.filename}', content_type='{file.content_type}', size={get_file_size(file) if file else 0}")
                    
                    if file and file.filename and allowed_file(file.filename):
                        try:
                            print(f"🔍 DEBUG ANEXOS EDITAR: Processando arquivo válido: {file.filename}")
                            
                            # Verifica tamanho
                            file_size = get_file_size(file)
                            print(f"🔍 DEBUG ANEXOS EDITAR: Tamanho do arquivo: {file_size} bytes")
                            
                            if file_size > MAX_FILE_SIZE:
                                flash(f'Arquivo {file.filename} é muito grande (máximo 16MB)', 'warning')
                                print(f"❌ DEBUG ANEXOS EDITAR: Arquivo muito grande: {file.filename}")
                                continue
                                
                            # Gera nome único
                            filename = generate_unique_filename(file.filename)
                            filepath = os.path.join(UPLOAD_FOLDER, filename)
                            print(f"🔍 DEBUG ANEXOS EDITAR: Salvando em: {filepath}")
                            
                            # Cria diretório se não existe
                            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                            
                            # Lê o conteúdo do arquivo para salvar no banco (Render precisa)
                            file.seek(0)  # Volta ao início do arquivo
                            file_content = file.read()
                            file.seek(0)  # Volta novamente para salvar em disco
                            
                            # Salva arquivo em disco (para desenvolvimento local)
                            file.save(filepath)
                            print(f"✅ DEBUG ANEXOS EDITAR: Arquivo salvo fisicamente: {filepath}")
                            
                            # Detecta tipo do arquivo
                            content_type = file.content_type or 'application/octet-stream'
                            tipo_arquivo = 'image' if content_type.startswith('image/') else 'document'
                            print(f"🔍 DEBUG ANEXOS EDITAR: Tipo detectado: {tipo_arquivo}, MIME: {content_type}")
                            
                            # Cria registro no banco (com conteúdo em BLOB para Render)
                            try:
                                anexo = OrdemServicoAnexo(
                                    ordem_servico_id=ordem.id,
                                    nome_original=file.filename,
                                    nome_arquivo=filename,
                                    tipo_arquivo=tipo_arquivo,
                                    mime_type=content_type,
                                    tamanho=len(file_content),
                                    caminho=filepath,
                                    conteudo=file_content  # Salva no banco para persistir no Render
                                )
                            except TypeError:
                                # Se a coluna conteudo não existir ainda, cria sem ela
                                print(f"⚠️ Coluna 'conteudo' não existe, criando anexo sem BLOB")
                                anexo = OrdemServicoAnexo(
                                    ordem_servico_id=ordem.id,
                                    nome_original=file.filename,
                                    nome_arquivo=filename,
                                    tipo_arquivo=tipo_arquivo,
                                    mime_type=content_type,
                                    tamanho=len(file_content),
                                    caminho=filepath
                                )
                            db.session.add(anexo)
                            print(f"✅ DEBUG ANEXOS EDITAR: Registro criado no banco: {anexo}")
                            
                        except Exception as e:
                            print(f"❌ DEBUG ANEXOS EDITAR: Erro ao processar {file.filename}: {str(e)}")
                            flash(f'Erro ao salvar arquivo {file.filename}: {str(e)}', 'warning')
                    elif file and file.filename and not allowed_file(file.filename):
                        print(f"❌ DEBUG ANEXOS EDITAR: Tipo não permitido: {file.filename}")
                        flash(f'Tipo de arquivo não permitido: {file.filename}', 'warning')
                    elif file and file.filename == '':
                        print(f"🔍 DEBUG ANEXOS EDITAR: Arquivo vazio ignorado")
                    else:
                        print(f"🔍 DEBUG ANEXOS EDITAR: Arquivo inválido: file={file}, filename='{file.filename if file else None}'")
            else:
                print("🔍 DEBUG ANEXOS EDITAR: Nenhum campo 'anexos' encontrado nos arquivos")

            processar_colaboradores_os(ordem, request.form)
            
            # Recalcula valor total novamente antes do commit final
            ordem.valor_total = ordem.valor_total_calculado
            valor_total_sincronizacao = ordem.valor_total or sum(
                (Decimal(str(parcela.valor or 0)) for parcela in ordem.parcelas),
                Decimal('0'),
            )

            # Commit final: salva novas linhas de serviços/produtos/parcelas/anexos
            try:
                db.session.commit()
                print(f"🏁 DEBUG: Ordem de Serviço salva com sucesso! Total final: R$ {ordem.valor_total}")
                ordem.valor_total = valor_total_sincronizacao
                
                # Integração financeira - gerar/atualizar lançamento
                from app.financeiro.financeiro_utils import gerar_lancamento_ordem_servico
                try:
                    gerar_lancamento_ordem_servico(ordem, forma_pagamento=forma_pagamento)
                    print(f"💰 DEBUG: Lançamento financeiro atualizado para OS {ordem.numero}")
                except Exception as fin_err:
                    print(f"⚠️ DEBUG: Erro na integração financeira: {fin_err}")
                    # Não falha a operação principal
                    
            except Exception as commit_err:
                try:
                    db.session.rollback()
                except Exception:
                    pass
                raise

            flash(f'Ordem de Serviço {ordem.numero} atualizada com sucesso!', 'success')
            return redirect(url_for('ordem_servico.visualizar', id=ordem.id))
            
        except Exception as e:
            flash(f'Erro ao atualizar ordem de serviço: {str(e)}', 'error')
            # Busca clientes com função robusta
            db.session.rollback()
            clientes = buscar_clientes_ativos()
            return render_template('os/form.html', ordem=ordem, clientes=clientes, today=date.today())
    
    # GET - exibe formulário preenchido
    print("DEBUG: Buscando clientes...")
    clientes = buscar_clientes_ativos()
    
    from app.financeiro.financeiro_model import LancamentoFinanceiro
    formas_pagamento = [l.forma_pagamento for l in LancamentoFinanceiro.query.filter_by(
        ordem_servico_id=ordem.id,
    ).all() if l.forma_pagamento]
    formas_pagamento_unicas = set(formas_pagamento)
    forma_pagamento_atual = (
        next(iter(formas_pagamento_unicas))
        if len(formas_pagamento_unicas) == 1
        else '__multiplas__' if formas_pagamento_unicas else ''
    )

    print("DEBUG: Renderizando template...")
    try:
        return render_template('os/form.html', 
                             ordem=ordem, 
                             clientes=clientes or [], 
                              today=date.today(),
                              forma_pagamento_atual=forma_pagamento_atual)
    except Exception as e:
        print(f" DEBUG: Erro ao renderizar template: {e}")
        import traceback
        traceback.print_exc()
        raise

@ordem_servico_bp.route('/<int:id>/excluir', methods=['GET', 'POST'])
def excluir(id):
    """
    Exclui (desativa) uma ordem de serviço.
    
    Args:
        id: ID da ordem de serviço
    """
    ordem = OrdemServico.get_by_id(id)
    if not ordem:
        flash('Ordem de serviço não encontrada!', 'error')
        return redirect(url_for('ordem_servico.listar'))
    
    if request.method == 'GET':
        # Exibe página de confirmação
        return render_template('ordem_servico/confirmar_exclusao.html', ordem=ordem)
    
    try:
        # Soft delete
        ordem.delete()
        
        # Integração financeira - remover/cancelar lançamento
        from app.financeiro.financeiro_utils import cancelar_lancamento_ordem_servico
        try:
            cancelar_lancamento_ordem_servico(ordem)
            print(f"💰 DEBUG: Lançamento financeiro cancelado para OS {ordem.numero}")
        except Exception as fin_err:
            print(f"⚠️ DEBUG: Erro ao cancelar lançamento financeiro: {fin_err}")
            # Não falha a operação principal
            
        flash(f'Ordem de Serviço "{ordem.numero}" excluída com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir ordem de serviço: {str(e)}', 'error')
    
    return redirect(url_for('ordem_servico.listar'))

@ordem_servico_bp.route('/<int:id>/iniciar', methods=['POST'])
def iniciar_servico(id):
    """
    Inicia o serviço (muda status para em_andamento).
    
    Args:
        id: ID da ordem de serviço
    """
    ordem = OrdemServico.get_by_id(id)
    if not ordem:
        flash('Ordem de serviço não encontrada!', 'error')
        return redirect(url_for('ordem_servico.listar'))
    
    try:
        ordem.iniciar_servico()
        flash(f'Serviço da OS "{ordem.numero}" iniciado!', 'success')
    except Exception as e:
        flash(f'Erro ao iniciar serviço: {str(e)}', 'error')
    
    return redirect(url_for('ordem_servico.visualizar', id=id))

@ordem_servico_bp.route('/<int:id>/concluir', methods=['POST'])
def concluir_servico(id):
    """
    Conclui o serviço (muda status para concluida).
    
    Args:
        id: ID da ordem de serviço
    """
    ordem = OrdemServico.get_by_id(id)
    if not ordem:
        flash('Ordem de serviço não encontrada!', 'error')
        return redirect(url_for('ordem_servico.listar'))
    
    try:
        ordem.concluir_servico()
        flash(f'Serviço da OS "{ordem.numero}" concluído!', 'success')
    except Exception as e:
        flash(f'Erro ao concluir serviço: {str(e)}', 'error')
    
    return redirect(url_for('ordem_servico.visualizar', id=id))

@ordem_servico_bp.route('/<int:id>/cancelar', methods=['POST'])
def cancelar_servico(id):
    """
    Cancela o serviço (muda status para cancelada).
    
    Args:
        id: ID da ordem de serviço
    """
    ordem = OrdemServico.get_by_id(id)
    if not ordem:
        flash('Ordem de serviço não encontrada!', 'error')
        return redirect(url_for('ordem_servico.listar'))
    
    try:
        ordem.cancelar_servico()
        flash(f'Serviço da OS "{ordem.numero}" cancelado!', 'warning')
    except Exception as e:
        flash(f'Erro ao cancelar serviço: {str(e)}', 'error')
    
    return redirect(url_for('ordem_servico.visualizar', id=id))

@ordem_servico_bp.route('/api/buscar')
def api_buscar():
    """
    API para busca de ordens de serviço via AJAX.
    
    Parâmetros:
        q: termo de busca
        status: filtro por status
        cliente_id: filtro por cliente
    """
    try:
        termo = request.args.get('q', '').strip()
        status = request.args.get('status', '').strip()
        cliente_id = request.args.get('cliente_id', '').strip()
        
        query = OrdemServico.query.filter_by(ativo=True)
        
        if termo:
            query = query.join(Cliente).filter(
                db.or_(
                    OrdemServico.numero.ilike(f'%{termo}%'),
                    OrdemServico.titulo.ilike(f'%{termo}%'),
                    Cliente.nome.ilike(f'%{termo}%')
                )
            )
        
        if status:
            query = query.filter(OrdemServico.status == status)
        
        if cliente_id:
            query = query.filter(OrdemServico.cliente_id == int(cliente_id))
        
        ordens = query.limit(20).all()
        
        resultado = []
        for ordem in ordens:
            resultado.append({
                'id': ordem.id,
                'numero': ordem.numero,
                'titulo': ordem.titulo,
                'cliente': ordem.cliente.nome if ordem.cliente else '',
                'status': ordem.status_formatado,
                'status_cor': ordem.status_cor,
                'valor_total': f"R$ {ordem.valor_total:.2f}".replace('.', ','),
                'data_abertura': ordem.data_abertura.strftime('%d/%m/%Y')
            })
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@ordem_servico_bp.route('/anexo/<int:anexo_id>')
def baixar_anexo(anexo_id):
    """
    Serve um arquivo anexado à ordem de serviço.
    Serve do BLOB primeiro, depois tenta disco físico.
    
    Args:
        anexo_id: ID do anexo
    """
    from flask import Response
    import io
    
    anexo = OrdemServicoAnexo.query.get_or_404(anexo_id)
    
    # 1. Tenta servir do BLOB (se disponível)
    if hasattr(anexo, 'conteudo') and anexo.conteudo:
        return Response(
            io.BytesIO(anexo.conteudo),
            mimetype=anexo.mime_type,
            headers={'Content-Disposition': f'attachment; filename="{anexo.nome_original}"'}
        )
    
    # 2. Fallback: tenta servir do disco
    try:
        return send_from_directory(
            UPLOAD_FOLDER,
            anexo.nome_arquivo,
            as_attachment=True,
            download_name=anexo.nome_original
        )
    except FileNotFoundError:
        flash('Arquivo não encontrado!', 'error')
        return redirect(url_for('ordem_servico.visualizar', id=anexo.ordem_servico_id))

@ordem_servico_bp.route('/anexo/<int:anexo_id>/visualizar')
def visualizar_anexo(anexo_id):
    """
    Visualiza um arquivo anexado (para imagens principalmente).
    Serve do BLOB primeiro, depois tenta disco físico.
    """
    from flask import send_file
    import io

    anexo = OrdemServicoAnexo.query.get_or_404(anexo_id)

    # 1. Tenta servir do BLOB (funciona no Render)
    if hasattr(anexo, 'conteudo') and anexo.conteudo:
        conteudo = bytes(anexo.conteudo) if not isinstance(anexo.conteudo, bytes) else anexo.conteudo
        return send_file(
            io.BytesIO(conteudo),
            mimetype=anexo.mime_type or 'image/jpeg',
            as_attachment=False,
            download_name=anexo.nome_original
        )

    # 2. Fallback: tenta disco
    possible_paths = [
        os.path.join(UPLOAD_FOLDER, anexo.nome_arquivo),
        os.path.join('app', 'static', 'uploads', anexo.nome_arquivo),
        os.path.join(current_app.root_path, 'static', 'uploads', anexo.nome_arquivo),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return send_file(
                    io.BytesIO(f.read()),
                    mimetype=anexo.mime_type or 'image/jpeg',
                    as_attachment=False,
                    download_name=anexo.nome_original
                )

    return ('Imagem não encontrada', 404)

@ordem_servico_bp.route('/anexo/<int:anexo_id>/excluir', methods=['POST'])
def excluir_anexo(anexo_id):
    """
    Exclui um anexo da ordem de serviço.
    
    Args:
        anexo_id: ID do anexo
    """
    anexo = OrdemServicoAnexo.query.get_or_404(anexo_id)
    ordem_id = anexo.ordem_servico_id
    nome_arquivo = anexo.nome_original
    
    try:
        # Remove arquivo físico (se existir)
        filepath = os.path.join(UPLOAD_FOLDER, anexo.nome_arquivo)
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Remove registro do banco (BLOB também será removido automaticamente)
        anexo.delete()
        
        return jsonify({
            'success': True,
            'message': f'Anexo "{nome_arquivo}" excluído com sucesso!'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao excluir anexo: {str(e)}'
        }), 500

@ordem_servico_bp.route('/<int:id>/anexos')
def listar_anexos(id):
    """
    Lista anexos de uma ordem de serviço em formato JSON.
    
    Args:
        id: ID da ordem de serviço
    """
    ordem = OrdemServico.query.get_or_404(id)
    anexos = OrdemServicoAnexo.query.filter_by(ordem_servico_id=id).order_by(OrdemServicoAnexo.data_upload, OrdemServicoAnexo.id).all()
    
    resultado = []
    for anexo in anexos:
        resultado.append({
            'id': anexo.id,
            'nome_original': anexo.nome_original,
            'tipo_arquivo': anexo.tipo_arquivo,
            'tamanho': anexo.tamanho,
            'data_upload': anexo.data_upload.strftime('%d/%m/%Y %H:%M') if anexo.data_upload else ''
        })
    
    return jsonify(resultado)

@ordem_servico_bp.route('/anexo/<int:anexo_id>/download')
def download_anexo(anexo_id):
    """
    Faz download de um arquivo anexado.
    Tenta BLOB primeiro (funciona no Render), depois disco.
    """
    from flask import send_file
    import io

    anexo = OrdemServicoAnexo.query.get_or_404(anexo_id)

    # 1. Tenta BLOB (Render)
    if hasattr(anexo, 'conteudo') and anexo.conteudo:
        conteudo = bytes(anexo.conteudo) if not isinstance(anexo.conteudo, bytes) else anexo.conteudo
        return send_file(
            io.BytesIO(conteudo),
            mimetype=anexo.mime_type or 'application/octet-stream',
            as_attachment=True,
            download_name=anexo.nome_original
        )

    # 2. Fallback: disco
    try:
        return send_from_directory(
            UPLOAD_FOLDER,
            anexo.nome_arquivo,
            as_attachment=True,
            download_name=anexo.nome_original
        )
    except FileNotFoundError:
        flash('Arquivo não encontrado!', 'error')
        return redirect(url_for('ordem_servico.visualizar', id=anexo.ordem_servico_id))

@ordem_servico_bp.route('/api/test')
def api_test():
    """Rota de teste básico."""
    return {'message': 'API funcionando!', 'success': True}

@ordem_servico_bp.route('/api/clientes')
def api_clientes():
    """API para buscar clientes ativos (para atualização dinâmica do select)."""
    try:
        print(" API /api/clientes chamada!")
        
        # Usa a função robusta para buscar clientes
        clientes = buscar_clientes_ativos()
        
        # Debug: listar primeiros clientes
        cliente11_encontrado = False
        for i, cliente in enumerate(clientes[:5]):
            print(f"  Cliente {i+1}: ID={cliente.id}, Nome='{cliente.nome}', Ativo={cliente.ativo}")
            if cliente.id == 11:
                cliente11_encontrado = True
        
        # Verificar especificamente Cliente 11
        if not cliente11_encontrado:
            c11_direto = Cliente.query.filter_by(id=11).first()
            if c11_direto:
                print(f"  ⚠️ Cliente 11 existe mas não aparece na lista: Nome='{c11_direto.nome}', Ativo={c11_direto.ativo}")
            else:
                print(f"   Cliente 11 não existe no banco")
        else:
            print(f"   Cliente 11 encontrado na lista!")
        
        # Formato para atualização do select
        clientes_validos = []
        for c in clientes:
            if c.nome and c.nome.strip():  # Mesmo filtro do template
                clientes_validos.append({
                    'id': c.id,
                    'nome': c.nome.strip(),
                    'cpf_cnpj': c.cpf_cnpj or '',
                    'cidade': c.cidade or ''
                })
        
        resultado = {
            'success': True,
            'clientes': clientes_validos,
            'total': len(clientes_validos),
            'debug_info': {
                'total_no_banco': len(clientes),
                'com_nome_valido': len(clientes_validos),
                'timestamp': str(dt.now())
            }
        }
        
        print(f" Retornando {resultado['total']} clientes válidos de {len(clientes)} no banco")
        return jsonify(resultado)
        
    except Exception as e:
        print(f" Erro na API de clientes: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@ordem_servico_bp.route('/api/clientes/test')
def api_clientes_test():
    """Rota de teste para debug."""
    return jsonify({
        'message': 'API de clientes funcionando!',
        'timestamp': str(dt.now()),
        'blueprint': 'ordem_servico',
        'success': True
    })

@ordem_servico_bp.route('/api/clientes/refresh')
def api_clientes_refresh():
    """API para forçar refresh dos clientes com função robusta."""
    try:
        print(" API /api/clientes/refresh chamada - REFRESH FORÇADO!")
        
        # Usar função robusta para buscar clientes
        clientes = buscar_clientes_ativos()
        
        # Debug: listar TODOS os clientes
        print("LISTA COMPLETA DE CLIENTES:")
        for i, cliente in enumerate(clientes):
            print(f"  📝 Cliente {i+1}: ID={cliente.id}, Nome='{cliente.nome}', Ativo={cliente.ativo}")
        
        # Aplicar mesmo filtro do template
        clientes_validos = []
        
        for c in clientes:
            if c.nome and c.nome.strip():  # Mesmo filtro do template
                clientes_validos.append({
                    'id': c.id,
                    'nome': c.nome.strip(),
                    'cpf_cnpj': c.cpf_cnpj or '',
                    'cidade': c.cidade or ''
                })
            else:
                print(f"⚠️ Cliente ignorado: ID={c.id}, Nome='{c.nome or 'SEM_NOME'}'")
        
        print(f" CLIENTES VÁLIDOS: {len(clientes_validos)}")
        
        resultado = {
            'success': True,
            'clientes': clientes_validos,
            'total': len(clientes_validos),
            'debug_info': {
                'total_no_banco': len(clientes),
                'com_nome_valido': len(clientes_validos),
                'timestamp': str(dt.now()),
                'refresh': True
            },
            'message': f'Lista atualizada! {len(clientes_validos)} clientes encontrados.'
        }
        
        print(f" RETORNANDO: {len(clientes_validos)} clientes válidos de {len(clientes)} totais")
        return jsonify(resultado)
        
    except Exception as e:
        print(f" Erro na API de clientes REFRESH: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@ordem_servico_bp.route('/api/produtos')
def api_produtos():
    """
    API para buscar produtos cadastrados.
    Retorna lista de produtos ativos com seus dados.
    """
    try:
        print("🔍 API /api/produtos chamada!")
        
        # Primeiro, verificar TODOS os produtos
        todos_produtos = Produto.query.all()
        print(f"📦 Total de produtos no banco (todos): {len(todos_produtos)}")
        
        # Mostrar todos para debug
        for p in todos_produtos:
            ativo_status = getattr(p, 'ativo', 'SEM_CAMPO_ATIVO')
            print(f"  🔍 Produto ID {p.id}: {p.nome} | Ativo: {ativo_status}")
        
        # Buscar apenas produtos ativos (se o campo existir)
        if hasattr(Produto, 'ativo'):
            produtos = Produto.query.filter_by(ativo=True).order_by(Produto.nome).all()
            print(f"📦 Produtos com ativo=True: {len(produtos)}")
        else:
            # Se não existe campo ativo, buscar todos
            produtos = Produto.query.order_by(Produto.nome).all()
            print(f"📦 Produtos (sem filtro de ativo): {len(produtos)}")
        
        produtos_list = []
        for produto in produtos:
            # Pega o preço de venda ou custo (o que estiver disponível)
            preco = produto.preco_venda if hasattr(produto, 'preco_venda') and produto.preco_venda else (produto.preco_custo if hasattr(produto, 'preco_custo') and produto.preco_custo else 0)
            
            produto_data = {
                'id': produto.id,
                'nome': produto.nome,
                'descricao': produto.descricao if hasattr(produto, 'descricao') and produto.descricao else '',
                'preco': float(preco) if preco else 0,
                'codigo': produto.codigo if hasattr(produto, 'codigo') and produto.codigo else '',
                'estoque': produto.estoque_atual if hasattr(produto, 'estoque_atual') else 0
            }
            produtos_list.append(produto_data)
            print(f"  ✅ Produto: {produto.nome} (ID: {produto.id}) - R$ {preco}")
        
        print(f"✅ Retornando {len(produtos_list)} produtos")
        return jsonify({
            'success': True,
            'produtos': produtos_list,
            'total': len(produtos_list),
            'debug': {
                'total_no_banco': len(todos_produtos),
                'total_retornados': len(produtos_list)
            }
        })
        
    except Exception as e:
        print(f"❌ Erro ao buscar produtos: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@ordem_servico_bp.route('/api/equipamentos-cliente/<int:cliente_id>')
def api_equipamentos_cliente(cliente_id):
    """
    API para buscar histórico de equipamentos de um cliente.
    Retorna equipamentos únicos com seus detalhes das OS anteriores.
    """
    try:
        # Busca todas as OS do cliente (ativas, concluídas, etc)
        ordens = OrdemServico.query.filter_by(
            cliente_id=cliente_id,
            ativo=True
        ).order_by(OrdemServico.data_abertura.desc()).all()
        
        # Dicionário para armazenar equipamentos únicos
        # Chave: nome do equipamento (normalizado)
        # Valor: dados completos do equipamento mais recente
        equipamentos_dict = {}
        
        for ordem in ordens:
            if ordem.equipamento and ordem.equipamento.strip():
                # Normaliza o nome para comparação (minúsculas, sem espaços extras)
                nome_normalizado = ordem.equipamento.strip().lower()
                
                # Se ainda não temos este equipamento, ou se esta OS é mais recente
                if nome_normalizado not in equipamentos_dict:
                    equipamentos_dict[nome_normalizado] = {
                        'equipamento': ordem.equipamento.strip(),
                        'modelo': ordem.modelo or '',
                        'marca': ordem.marca or '',
                        'numero_serie': ordem.numero_serie or '',
                        'ultima_os': ordem.numero,
                        'data_ultima_os': ordem.data_abertura.strftime('%d/%m/%Y') if ordem.data_abertura else '',
                        'total_os': 1
                    }
                else:
                    # Incrementa contador de OS para este equipamento
                    equipamentos_dict[nome_normalizado]['total_os'] += 1
        
        # Converte para lista ordenada por nome
        equipamentos_lista = sorted(
            equipamentos_dict.values(),
            key=lambda x: x['equipamento']
        )
        
        return jsonify({
            'success': True,
            'equipamentos': equipamentos_lista,
            'total': len(equipamentos_lista)
        })
        
    except Exception as e:
        print(f"❌ Erro ao buscar equipamentos do cliente: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@ordem_servico_bp.route('/<int:id>/relatorio-pdf')
def gerar_relatorio_pdf(id):
    """
    Gera relatório em PDF da ordem de serviço.
    
    Args:
        id: ID da ordem de serviço
        com_imagens: parâmetro opcional para forçar inclusão/exclusão de imagens (0 ou 1)
        
    Returns:
        PDF file: Relatório da ordem de serviço em PDF
    """
    print(f"DEBUG PDF: Iniciando geração de PDF para OS ID: {id}")
    
    try:
        # Busca a ordem de serviço
        ordem = OrdemServico.query.get_or_404(id)
        print(f" DEBUG PDF: Ordem encontrada: {ordem.numero}")
        
        # Verifica se deve incluir imagens (parâmetro da URL ou configuração da OS)
        com_imagens_param = request.args.get('com_imagens')
        if com_imagens_param is not None:
            # Parâmetro da URL tem prioridade
            incluir_imagens = com_imagens_param == '1'
            print(f"DEBUG PDF: Incluir imagens (via URL): {incluir_imagens}")
        else:
            # Usa configuração salva na OS
            incluir_imagens = ordem.incluir_imagens_relatorio if hasattr(ordem, 'incluir_imagens_relatorio') else False
            print(f"DEBUG PDF: Incluir imagens (via config OS): {incluir_imagens}")
        
        # Verifica se deve incluir seção de custos de mão de obra
        com_custos = request.args.get('com_custos') == '1'
        # PDF de fechamento interno (o que pagar a cada colaborador)
        fechamento = request.args.get('fechamento') == '1'
        
        # Temporariamente define o valor para renderização
        ordem_incluir_imagens_original = getattr(ordem, 'incluir_imagens_relatorio', False)
        ordem.incluir_imagens_relatorio = incluir_imagens
        
        # Calcula totais se necessário
        if not ordem.valor_servico:
            total_servicos = sum(item.valor_total for item in ordem.servicos) if hasattr(ordem, 'servicos') and ordem.servicos else 0
            ordem.valor_servico = Decimal(str(total_servicos))
            
        if not ordem.valor_pecas:
            total_produtos = sum(produto.valor_total for produto in ordem.produtos_utilizados) if hasattr(ordem, 'produtos_utilizados') and ordem.produtos_utilizados else 0
            ordem.valor_pecas = Decimal(str(total_produtos))
            
        # Debug dos produtos
        if hasattr(ordem, 'produtos_utilizados') and ordem.produtos_utilizados:
            print(f"DEBUG PDF: Produtos encontrados:")
            for i, produto in enumerate(ordem.produtos_utilizados, 1):
                print(f"  {i}. {produto.descricao}: Qtd={produto.quantidade} x R${produto.valor_unitario} = R${produto.valor_total}")
            print(f"DEBUG PDF: Total calculado: R$ {ordem.valor_pecas}")
        else:
            print(f"⚠️ DEBUG PDF: Nenhum produto encontrado!")
            
        if not ordem.valor_total:
            valor_servico = Decimal(str(ordem.valor_servico or 0))
            valor_pecas = Decimal(str(ordem.valor_pecas or 0))
            valor_desconto = Decimal(str(ordem.valor_desconto or 0))
            ordem.valor_total = valor_servico + valor_pecas - valor_desconto
        
        print(f"DEBUG PDF: Importando configurações...")
        # Importar configurações da empresa
        from app.configuracao.configuracao_utils import get_config
        config = get_config()
        
        print(f"DEBUG PDF: Renderizando template HTML...")
        print(f"🔍 TEMPLATE SENDO USADO: 'os/pdf_ordem_servico.html'")
        print(f"🔍 CAMINHO ABSOLUTO: {os.path.abspath(os.path.join('app', 'ordem_servico', 'templates', 'os', 'pdf_ordem_servico.html'))}")
        
        # Converter imagens anexadas para base64 (sempre para PDF normal e do cliente; nunca para fechamento)
        anexos_base64 = {}
        if not fechamento and hasattr(ordem, 'anexos') and ordem.anexos:
            import base64
            print(f"🖼️ DEBUG PDF: Convertendo {len(ordem.anexos)} anexos para base64...")
            for anexo in ordem.anexos:
                print(f"  📁 Processando: {anexo.nome_original}")
                print(f"     - Tipo: {anexo.tipo_arquivo}")
                print(f"     - MIME: {anexo.mime_type}")
                print(f"     - Caminho salvo: {anexo.caminho}")
                
                if anexo.tipo_arquivo == 'image' or (anexo.mime_type and 'image' in anexo.mime_type):
                    try:
                        # PRIORIDADE 1: Usar conteúdo BLOB salvo no banco (funciona no Render)
                        if hasattr(anexo, 'conteudo') and anexo.conteudo:
                            print(f"     ✅ Usando conteúdo do BLOB no banco ({len(anexo.conteudo)} bytes)")
                            img_base64 = base64.b64encode(anexo.conteudo).decode('utf-8')
                            anexos_base64[str(anexo.id)] = img_base64
                            print(f"     ✅ Convertido do BLOB: {len(img_base64)} chars base64")
                        else:
                            # PRIORIDADE 2: Tentar ler do disco (desenvolvimento local)
                            print(f"     ⚠️ BLOB vazio, tentando ler do disco...")
                            possible_paths = [
                                anexo.caminho,  # Caminho completo salvo no banco
                                os.path.join(UPLOAD_FOLDER, anexo.nome_arquivo),  # Usando UPLOAD_FOLDER
                                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads', 'ordem_servico', 'anexos', anexo.nome_arquivo),
                                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'app', 'static', 'uploads', anexo.nome_arquivo),  # Caminho usado atualmente
                            ]
                            
                            arquivo_encontrado = None
                            for caminho_teste in possible_paths:
                                if os.path.exists(caminho_teste):
                                    arquivo_encontrado = caminho_teste
                                    print(f"     ✅ Arquivo encontrado em: {arquivo_encontrado}")
                                    break
                                else:
                                    print(f"     ❌ Não encontrado em: {caminho_teste}")
                            
                            if arquivo_encontrado:
                                # Lê o arquivo e converte para base64
                                with open(arquivo_encontrado, 'rb') as img_file:
                                    img_data = img_file.read()
                                    img_base64 = base64.b64encode(img_data).decode('utf-8')
                                    anexos_base64[str(anexo.id)] = img_base64
                                    print(f"     ✅ Convertido do disco: {len(img_base64)} chars base64 | {len(img_data)} bytes")
                            else:
                                print(f"     ⚠️ ARQUIVO NÃO ENCONTRADO em nenhum caminho testado!")
                            
                    except Exception as e:
                        print(f"     ⚠️ ERRO ao converter {anexo.nome_original}: {str(e)}")
                        import traceback
                        print(f"     Stack: {traceback.format_exc()}")
            print(f"🖼️ DEBUG PDF: Total de imagens convertidas com sucesso: {len(anexos_base64)}/{len(ordem.anexos)}")
        
        # Renderiza o template HTML com timestamp para evitar cache
        html_content = render_template(
            'os/pdf_ordem_servico.html',
            ordem=ordem,
            now=dt.now,
            logo_base64=get_logo_base64(),  # Função para obter logo em base64
            config=config,  # Adicionar configurações
            timedelta=timedelta,  # Para cálculo de garantia
            timestamp=dt.now().isoformat(),  # Timestamp único para evitar cache
            anexos_base64=anexos_base64,  # Imagens em base64
            com_custos=com_custos,  # Seção de custo de M.O. (admin)
            fechamento=fechamento   # PDF de fechamento - o que pagar ao colaborador
        )
        print(f"🔍 PRIMEIROS 200 CHARS DO HTML: {html_content[:200]}...")
        print(f" DEBUG PDF: Template renderizado com sucesso")
        
        # Configurações do WeasyPrint
        base_url = request.url_root
        css_string = '''
            @page {
                size: A4;
                margin: 1cm;
            }
            body {
                font-family: Arial, sans-serif;
                font-size: 12px;
                line-height: 1.4;
            }
        '''
        
        # Retorna HTML otimizado para impressão com script de auto-download
        print(f"DEBUG PDF: Retornando HTML para impressão com auto-download...")
        
        # Adiciona script para forçar diálogo de impressão (salvar como PDF)
        script_auto_print = '''
        <script>
            window.onload = function() {
                // Abre automaticamente o diálogo de impressão
                window.print();
            };
        </script>
        '''
        
        # Injeta o script antes do </body>
        if '</body>' in html_content:
            html_content = html_content.replace('</body>', f'{script_auto_print}</body>')
        else:
            html_content += script_auto_print
        
        response = make_response(html_content)
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        # Sugere nome do arquivo para quando o usuário escolher "Salvar como PDF"
        # Formato: "Ordem de Serviço OS16012026007" (data + número da OS)
        data_str = dt.now().strftime("%d%m%Y")  # Formato: 16012026
        numero_str = str(ordem.numero).zfill(4)  # Formato: 0007
        response.headers['Content-Disposition'] = f'inline; filename="Ordem de Servico OS{data_str}{numero_str}.pdf"'
        
        print(f" DEBUG PDF: HTML retornado com sucesso (com auto-print)")
        return response
        
    except Exception as e:
        print(f" DEBUG PDF: Erro geral na geração de PDF: {str(e)}")
        print(f" DEBUG PDF: Tipo do erro geral: {type(e)}")
        import traceback
        print(f" DEBUG PDF: Stack trace: {traceback.format_exc()}")
        flash(f'Erro ao gerar relatório PDF: {str(e)}', 'error')
        return redirect(url_for('ordem_servico.visualizar', id=id))
