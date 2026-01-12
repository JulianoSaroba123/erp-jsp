"""
Rotas para o módulo de Cálculo de Energia Solar
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, make_response, send_file
from flask_login import login_required, current_user
from app.extensoes import db
from app.energia_solar.energia_solar_model import CalculoEnergiaSolar
from app.energia_solar.catalogo_model import PlacaSolar, InversorSolar, KitSolar, ProjetoSolar
from app.energia_solar.custo_fixo_model import CustoFixo
from app.cliente.cliente_model import Cliente
from datetime import datetime
from werkzeug.utils import secure_filename
import math
import os
import logging

logger = logging.getLogger(__name__)

energia_solar_bp = Blueprint('energia_solar', __name__, url_prefix='/energia-solar',
                             template_folder='templates')

# Configuração de uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'static', 'uploads', 'datasheets')
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Detectar se está no Render (filesystem efêmero)
IS_RENDER = os.getenv('RENDER') is not None

# Criar pasta de uploads se não existir (apenas local)
if not IS_RENDER:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Verifica se a extensão do arquivo é permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def calcular_geracao_estimada(qtd_placas, placa_id, irradiacao_solar):
    """
    Calcula a geração mensal estimada baseada nas placas
    
    Fórmula: Geração (kWh/mês) = Qtd Placas × Potência Placa (kWp) × Irradiação (h/dia) × 30 dias × 0.75 (perdas)
    
    Args:
        qtd_placas: Quantidade de placas solares
        placa_id: ID da placa solar
        irradiacao_solar: Irradiação solar média (kWh/m².dia)
    
    Returns:
        float: Geração estimada em kWh/mês
    """
    if not qtd_placas or not placa_id or not irradiacao_solar:
        return 0
    
    try:
        placa = PlacaSolar.query.get(placa_id)
        if not placa or not placa.potencia:
            return 0
        
        # Potência em kWp (605W = 0.605 kWp)
        potencia_placa_kwp = placa.potencia / 1000
        
        # Potência total do sistema
        potencia_total_kwp = qtd_placas * potencia_placa_kwp
        
        # Geração mensal (com 75% de eficiência devido a perdas)
        geracao_mensal = potencia_total_kwp * irradiacao_solar * 30 * 0.75
        
        return round(geracao_mensal, 2)
    except Exception as e:
        print(f"❌ Erro ao calcular geração estimada: {str(e)}")
        return 0


def calcular_balanco_energetico(projeto):
    """
    Calcula o balanço energético do projeto para gráficos
    
    Returns:
        dict: {
            'consumo_mensal': float,
            'geracao_mensal': float,
            'consumo_simultaneo': float (kWh usado durante geração solar),
            'excedente_rede': float (kWh injetado na rede),
            'consumo_noturno': float (kWh consumido da rede),
            'consumo_minimo': float (kWh mínimo obrigatório),
            'economia_mensal': float (R$),
            'autossuficiencia': float (% de energia própria)
        }
    """
    consumo = projeto.consumo_kwh_mes or 0
    geracao = projeto.geracao_estimada_mes or 0
    simultaneidade_decimal = (projeto.simultaneidade or 35) / 100  # Converte % para decimal (35% = 0.35)
    tarifa = projeto.tarifa_kwh or 1.04
    
    # Consumo mínimo obrigatório da concessionária
    tipo_instalacao = projeto.tipo_instalacao or 'monofasica'
    consumo_minimo_map = {
        'monofasica': 30,
        'bifasica': 50,
        'trifasica': 100
    }
    consumo_minimo = consumo_minimo_map.get(tipo_instalacao, 30)
    
    # Consumo durante o dia (simultâneo com geração solar)
    consumo_simultaneo = consumo * simultaneidade_decimal
    
    # Consumo à noite (da rede)
    consumo_noturno = consumo * (1 - simultaneidade_decimal)
    
    # Excedente injetado na rede (créditos)
    excedente_rede = max(0, geracao - consumo_simultaneo)
    
    # Déficit (precisa da rede durante o dia)
    deficit_dia = max(0, consumo_simultaneo - geracao)
    
    # Total consumido da rede
    total_da_rede = consumo_noturno + deficit_dia
    
    # Créditos gerados (compensação)
    creditos_kwh = excedente_rede
    
    # Consumo líquido (após compensação) - nunca menor que o mínimo obrigatório
    consumo_liquido = max(consumo_minimo, total_da_rede - creditos_kwh)
    
    # Economia mensal
    custo_sem_solar = consumo * tarifa
    custo_com_solar = consumo_liquido * tarifa
    economia_mensal = custo_sem_solar - custo_com_solar
    
    # Autossuficiência (% de energia própria)
    autossuficiencia = (geracao / consumo * 100) if consumo > 0 else 0
    
    return {
        'consumo_mensal': round(consumo, 2),
        'geracao_mensal': round(geracao, 2),
        'consumo_simultaneo': round(consumo_simultaneo, 2),
        'consumo_noturno': round(consumo_noturno, 2),
        'excedente_rede': round(excedente_rede, 2),
        'deficit_dia': round(deficit_dia, 2),
        'total_da_rede': round(total_da_rede, 2),
        'creditos_kwh': round(creditos_kwh, 2),
        'consumo_minimo': consumo_minimo,
        'tipo_instalacao': tipo_instalacao.capitalize(),
        'consumo_liquido': round(consumo_liquido, 2),
        'economia_mensal': round(economia_mensal, 2),
        'autossuficiencia': round(autossuficiencia, 1),
        'custo_sem_solar': round(custo_sem_solar, 2),
        'custo_com_solar': round(custo_com_solar, 2)
    }


@energia_solar_bp.route('/datasheet/<path:filename>')
@login_required
def ver_datasheet(filename):
    """Serve arquivos de datasheet de forma segura"""
    try:
        # Validar nome do arquivo
        if not filename or '..' in filename:
            flash('❌ Nome de arquivo inválido', 'error')
            return redirect(request.referrer or url_for('energia_solar.dashboard'))
        
        # Verificar se o arquivo existe
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(filepath):
            flash(f'❌ Arquivo não encontrado: {filename}', 'error')
            return redirect(request.referrer or url_for('energia_solar.dashboard'))
        
        # Servir o arquivo
        return send_from_directory(UPLOAD_FOLDER, filename)
    except Exception as e:
        logger.error(f"Erro ao servir datasheet {filename}: {str(e)}")
        flash(f'❌ Erro ao abrir PDF: {str(e)}', 'error')
        return redirect(request.referrer or url_for('energia_solar.dashboard'))


@energia_solar_bp.route('/')
@login_required
def dashboard():
    """Dashboard do módulo de Energia Solar"""
    try:
        calculos = CalculoEnergiaSolar.query.order_by(CalculoEnergiaSolar.data_calculo.desc()).limit(10).all()
        
        # Estatísticas
        total_calculos = CalculoEnergiaSolar.query.count()
        potencia_total = db.session.query(db.func.sum(CalculoEnergiaSolar.potencia_sistema)).scalar() or 0
        economia_total = db.session.query(db.func.sum(CalculoEnergiaSolar.economia_anual)).scalar() or 0
        
        return render_template('energia_solar/dashboard.html',
                             calculos=calculos,
                             total_calculos=total_calculos,
                             potencia_total=potencia_total,
                             economia_total=economia_total)
    except Exception as e:
        logger.error(f"❌ Erro no dashboard energia solar: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Erro ao carregar dashboard de Energia Solar: {str(e)}', 'error')
        return redirect(url_for('painel.dashboard'))


@energia_solar_bp.route('/calculadora')
@login_required
def calculadora():
    """Página da calculadora de energia solar"""
    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
    return render_template('energia_solar/calculadora.html', clientes=clientes)


@energia_solar_bp.route('/calcular', methods=['POST'])
@login_required
def calcular():
    """Realiza o cálculo do sistema de energia solar"""
    try:
        # Dados do formulário
        consumo_mensal = float(request.form.get('consumo_mensal', 0))
        tarifa_energia = float(request.form.get('tarifa_energia', 0))
        irradiacao = float(request.form.get('irradiacao', 5.0))  # padrão 5 kWh/m²/dia
        
        # Validações
        if consumo_mensal <= 0 or tarifa_energia <= 0:
            flash('Consumo e tarifa devem ser maiores que zero', 'error')
            return redirect(url_for('energia_solar.calculadora'))
        
        # Cálculos básicos
        # Considerando eficiência de 80% e fator de correção
        geracao_diaria_necessaria = consumo_mensal / 30  # kWh/dia
        hsp = irradiacao  # Horas de Sol Pico
        
        # Potência do sistema em kWp
        potencia_sistema = (geracao_diaria_necessaria / hsp) / 0.8  # 80% de eficiência
        potencia_sistema = round(potencia_sistema, 2)
        
        # Painéis (assumindo painéis de 550W)
        potencia_painel = 550  # W
        numero_paineis = math.ceil((potencia_sistema * 1000) / potencia_painel)
        potencia_real = (numero_paineis * potencia_painel) / 1000  # kWp real
        
        # Área necessária (2m² por painel de 550W)
        area_necessaria = numero_paineis * 2.0
        
        # Geração estimada
        geracao_mensal = potencia_real * hsp * 30 * 0.8  # kWh/mês
        
        # Economia
        economia_mensal = geracao_mensal * tarifa_energia
        economia_anual = economia_mensal * 12
        
        # Custo estimado (R$ 4,50 por Wp em média)
        custo_por_wp = 4.50
        custo_total = potencia_real * 1000 * custo_por_wp
        
        # Payback
        if economia_anual > 0:
            payback_anos = custo_total / economia_anual
        else:
            payback_anos = 0
        
        # ROI em 25 anos (vida útil dos painéis)
        roi_25anos = ((economia_anual * 25) - custo_total) / custo_total * 100 if custo_total > 0 else 0
        
        # Inversor (assumindo string inversor, 1 para cada 10kWp)
        numero_inversores = math.ceil(potencia_real / 10)
        potencia_inversor = potencia_real / numero_inversores
        
        # Criar registro
        calculo = CalculoEnergiaSolar(
            cliente_id=request.form.get('cliente_id') or None,
            nome_cliente=request.form.get('nome_cliente', 'Cliente Não Identificado'),
            consumo_mensal=consumo_mensal,
            tarifa_energia=tarifa_energia,
            cidade=request.form.get('cidade'),
            estado=request.form.get('estado'),
            irradiacao_media=irradiacao,
            potencia_sistema=potencia_real,
            numero_paineis=numero_paineis,
            potencia_painel=potencia_painel,
            area_necessaria=area_necessaria,
            tipo_inversor='String',
            potencia_inversor=potencia_inversor,
            numero_inversores=numero_inversores,
            geracao_mensal=geracao_mensal,
            economia_mensal=economia_mensal,
            economia_anual=economia_anual,
            custo_total=custo_total,
            payback_anos=payback_anos,
            roi_25anos=roi_25anos,
            observacoes=request.form.get('observacoes'),
            tipo_instalacao=request.form.get('tipo_instalacao', 'Telhado'),
            orientacao=request.form.get('orientacao', 'Norte'),
            inclinacao=float(request.form.get('inclinacao', 15)),
            usuario_id=current_user.id
        )
        
        db.session.add(calculo)
        db.session.commit()
        
        flash(f'✅ Cálculo realizado! Sistema de {potencia_real}kWp com {numero_paineis} painéis', 'success')
        return redirect(url_for('energia_solar.visualizar', id=calculo.id))
        
    except ValueError as e:
        flash(f'Erro nos dados fornecidos: {str(e)}', 'error')
        return redirect(url_for('energia_solar.calculadora'))
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao realizar cálculo: {str(e)}', 'error')
        return redirect(url_for('energia_solar.calculadora'))


@energia_solar_bp.route('/visualizar/<int:id>')
@login_required
def visualizar(id):
    """Visualiza um cálculo específico"""
    calculo = CalculoEnergiaSolar.query.get_or_404(id)
    return render_template('energia_solar/visualizar.html', calculo=calculo)


@energia_solar_bp.route('/listar')
@login_required
def listar():
    """Lista todos os cálculos realizados"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        calculos = CalculoEnergiaSolar.query.order_by(
            CalculoEnergiaSolar.data_calculo.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return render_template('energia_solar/listar.html', calculos=calculos)
    except Exception as e:
        logger.error(f"❌ Erro ao listar cálculos: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Erro ao carregar lista de cálculos: {str(e)}', 'error')
        return redirect(url_for('energia_solar.dashboard'))


@energia_solar_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir(id):
    """Exclui um cálculo"""
    try:
        calculo = CalculoEnergiaSolar.query.get_or_404(id)
        db.session.delete(calculo)
        db.session.commit()
        flash('Cálculo excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir cálculo: {str(e)}', 'error')
    
    return redirect(url_for('energia_solar.listar'))


@energia_solar_bp.route('/api/irradiacao/<estado>')
@login_required
def api_irradiacao(estado):
    """Retorna irradiação média por estado (valores aproximados)"""
    irradiacao_por_estado = {
        'AC': 4.5, 'AL': 5.2, 'AP': 4.8, 'AM': 4.3, 'BA': 5.5,
        'CE': 5.7, 'DF': 5.3, 'ES': 4.9, 'GO': 5.4, 'MA': 5.1,
        'MT': 5.5, 'MS': 5.2, 'MG': 5.0, 'PA': 4.6, 'PB': 5.6,
        'PR': 4.7, 'PE': 5.8, 'PI': 5.5, 'RJ': 4.8, 'RN': 5.9,
        'RS': 4.4, 'RO': 4.7, 'RR': 4.9, 'SC': 4.5, 'SP': 4.6,
        'SE': 5.3, 'TO': 5.2
    }
    
    irradiacao = irradiacao_por_estado.get(estado.upper(), 5.0)
    return jsonify({'irradiacao': irradiacao})


# ==================== ROTAS DOS CATÁLOGOS ====================

# ========== Catálogo de Placas Solares ==========
@energia_solar_bp.route('/placas', methods=['GET'])
@login_required
def placas_listar():
    """Lista todas as placas solares do catálogo"""
    try:
        placas_obj = PlacaSolar.query.order_by(PlacaSolar.fabricante, PlacaSolar.modelo).all()
        placas = [p.to_dict() for p in placas_obj]
        return render_template('energia_solar/placas_crud.html', placas=placas, placas_obj=placas_obj)
    except Exception as e:
        print(f"❌ Erro ao listar placas: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Erro ao carregar placas: {str(e)}', 'error')
        return redirect(url_for('energia_solar.dashboard'))


@energia_solar_bp.route('/placas/criar', methods=['POST'])
@login_required
def placa_criar():
    """Cria uma nova placa solar no catálogo"""
    try:
        # Processar campos opcionais
        comprimento = request.form.get('comprimento')
        largura = request.form.get('largura')
        espessura = request.form.get('espessura')
        eficiencia = request.form.get('eficiencia')
        num_celulas = request.form.get('num_celulas')
        garantia_produto = request.form.get('garantia_produto')
        garantia_desempenho = request.form.get('garantia_desempenho')
        preco_custo = request.form.get('preco_custo')
        
        # Processar datasheets (múltiplos arquivos ou URL)
        datasheets = []
        
        # No Render, bloquear upload de arquivos (filesystem efêmero)
        if 'datasheet_file' in request.files and not IS_RENDER:
            files = request.files.getlist('datasheet_file')
            for file in files:
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Adicionar timestamp para evitar conflitos
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(filepath)
                    datasheets.append(f"/uploads/datasheets/{filename}")
        elif 'datasheet_file' in request.files and IS_RENDER:
            files = request.files.getlist('datasheet_file')
            if any(f.filename for f in files):
                flash('⚠️ Upload de arquivos não disponível no Render. Use um link externo (Google Drive, Dropbox, etc.)', 'warning')
        
        # Se não houver arquivo, usar URL
        if not datasheets:
            url = request.form.get('datasheet_url')
            if url:
                datasheets.append(url)
        
        # Converter lista para string JSON ou usar primeiro item para compatibilidade
        datasheet = datasheets[0] if len(datasheets) == 1 else (';'.join(datasheets) if datasheets else None)
        
        placa = PlacaSolar(
            modelo=request.form.get('modelo'),
            fabricante=request.form.get('fabricante'),
            potencia=float(request.form.get('potencia')),
            eficiencia=float(eficiencia) if eficiencia and eficiencia.strip() else None,
            num_celulas=int(num_celulas) if num_celulas and num_celulas.strip() else None,
            comprimento=float(comprimento) if comprimento and comprimento.strip() else None,
            largura=float(largura) if largura and largura.strip() else None,
            espessura=float(espessura) if espessura and espessura.strip() else None,
            garantia_produto=int(garantia_produto) if garantia_produto and garantia_produto.strip() else 12,
            garantia_desempenho=int(garantia_desempenho) if garantia_desempenho and garantia_desempenho.strip() else 25,
            preco_venda=float(request.form.get('preco_venda')),
            preco_custo=float(preco_custo) if preco_custo and preco_custo.strip() else None,
            datasheet=datasheet
        )
        
        db.session.add(placa)
        db.session.commit()
        flash(f'Placa {placa.modelo} adicionada ao catálogo com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao adicionar placa: {str(e)}', 'error')
    
    return redirect(url_for('energia_solar.placas_listar'))


@energia_solar_bp.route('/placas/excluir/<int:placa_id>', methods=['POST'])
@login_required
def placa_excluir(placa_id):
    """Exclui uma placa solar do catálogo"""
    try:
        placa = PlacaSolar.query.get_or_404(placa_id)
        db.session.delete(placa)
        db.session.commit()
        flash('Placa excluída do catálogo com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir placa: {str(e)}', 'error')
    
    return redirect(url_for('energia_solar.placas_listar'))


@energia_solar_bp.route('/placas/datasheet/excluir/<int:placa_id>/<int:index>', methods=['POST'])
@login_required
def placa_datasheet_excluir(placa_id, index):
    """Exclui um datasheet específico da placa"""
    try:
        placa = PlacaSolar.query.get_or_404(placa_id)
        
        if placa.datasheet:
            # Separar os arquivos
            arquivos = placa.datasheet.split(';')
            
            # Verificar se o índice é válido
            if 0 <= index < len(arquivos):
                arquivo_excluir = arquivos[index].strip()
                
                # Se for arquivo local, excluir do disco
                if arquivo_excluir.startswith('/uploads/') and not IS_RENDER:
                    caminho_arquivo = os.path.join(
                        os.path.dirname(os.path.dirname(__file__)),
                        'static',
                        arquivo_excluir.lstrip('/')
                    )
                    if os.path.exists(caminho_arquivo):
                        os.remove(caminho_arquivo)
                
                # Remover da lista
                arquivos.pop(index)
                
                # Atualizar o campo
                placa.datasheet = ';'.join(arquivos) if arquivos else None
                db.session.commit()
                
                return jsonify({'success': True}), 200
            else:
                return jsonify({'error': 'Índice inválido'}), 400
        else:
            return jsonify({'error': 'Nenhum datasheet encontrado'}), 404
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@energia_solar_bp.route('/placas/editar/<int:placa_id>', methods=['GET', 'POST'])
@login_required
def placa_editar(placa_id):
    """Edita uma placa solar do catálogo"""
    placa = PlacaSolar.query.get_or_404(placa_id)
    
    if request.method == 'POST':
        try:
            # Atualizar dados
            placa.modelo = request.form.get('modelo')
            placa.fabricante = request.form.get('fabricante')
            placa.potencia = float(request.form.get('potencia'))
            placa.preco_venda = float(request.form.get('preco_venda'))
            
            # Campos opcionais
            comprimento = request.form.get('comprimento')
            largura = request.form.get('largura')
            espessura = request.form.get('espessura')
            eficiencia = request.form.get('eficiencia')
            num_celulas = request.form.get('num_celulas')
            garantia_produto = request.form.get('garantia_produto')
            garantia_desempenho = request.form.get('garantia_desempenho')
            preco_custo = request.form.get('preco_custo')
            
            # Tratar campos numéricos opcionais (aceita vazio ou valor válido)
            placa.eficiencia = float(eficiencia) if eficiencia and eficiencia.strip() else None
            placa.num_celulas = int(num_celulas) if num_celulas and num_celulas.strip() else None
            placa.comprimento = float(comprimento) if comprimento and comprimento.strip() else None
            placa.largura = float(largura) if largura and largura.strip() else None
            placa.espessura = float(espessura) if espessura and espessura.strip() else None
            placa.garantia_produto = int(garantia_produto) if garantia_produto and garantia_produto.strip() else 12
            placa.garantia_desempenho = int(garantia_desempenho) if garantia_desempenho and garantia_desempenho.strip() else 25
            placa.preco_custo = float(preco_custo) if preco_custo and preco_custo.strip() else None
            
            # Processar datasheet (arquivo ou URL)
            datasheet_atualizado = False
            
            # Verificar se há arquivo enviado (apenas local, não no Render)
            if 'datasheet_file' in request.files and not IS_RENDER:
                file = request.files['datasheet_file']
                if file and file.filename and allowed_file(file.filename):
                    # Excluir arquivo antigo se existir e for local
                    if placa.datasheet and placa.datasheet.startswith('/static/uploads/'):
                        old_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                              placa.datasheet.lstrip('/'))
                        if os.path.exists(old_file):
                            os.remove(old_file)
                    
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(filepath)
                    placa.datasheet = f"/uploads/datasheets/{filename}"
                    datasheet_atualizado = True
            elif 'datasheet_file' in request.files and IS_RENDER:
                file = request.files['datasheet_file']
                if file and file.filename:
                    flash('⚠️ Upload de arquivos não disponível no Render. Use um link externo na aba "Link Externo".', 'warning')
            
            # Se não enviou arquivo, verificar URL
            if not datasheet_atualizado:
                url_fornecida = request.form.get('datasheet_url', '').strip()
                if url_fornecida:
                    # Excluir arquivo local antigo se houver
                    if placa.datasheet and placa.datasheet.startswith('/static/uploads/'):
                        old_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                              placa.datasheet.lstrip('/'))
                        if os.path.exists(old_file):
                            os.remove(old_file)
                    placa.datasheet = url_fornecida
            
            db.session.commit()
            
            flash(f'✅ Placa {placa.modelo} atualizada com sucesso!', 'success')
            return redirect(url_for('energia_solar.placas_listar'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar placa: {str(e)}', 'error')
            return redirect(url_for('energia_solar.placas_listar'))
    
    # GET: retornar dados em JSON
    return jsonify(placa.to_dict())


# ========== Catálogo de Inversores ==========
@energia_solar_bp.route('/inversores')
@login_required
def inversores_listar():
    """Lista todos os inversores do catálogo"""
    try:
        inversores_obj = InversorSolar.query.order_by(InversorSolar.fabricante, InversorSolar.modelo).all()
        inversores = [i.to_dict() for i in inversores_obj]
        return render_template('energia_solar/inversores_crud.html', inversores=inversores, inversores_obj=inversores_obj)
    except Exception as e:
        logger.error(f"❌ Erro ao listar inversores: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Erro ao carregar inversores: {str(e)}', 'error')
        return redirect(url_for('energia_solar.dashboard'))


@energia_solar_bp.route('/inversores/criar', methods=['POST'])
@login_required
def inversor_criar():
    """Cria um novo inversor no catálogo"""
    try:
        # Processar campos opcionais
        potencia_maxima = request.form.get('potencia_maxima')
        tensao_entrada_min = request.form.get('tensao_entrada_min')
        tensao_entrada_max = request.form.get('tensao_entrada_max')
        tensao_mppt_min = request.form.get('tensao_mppt_min')
        tensao_mppt_max = request.form.get('tensao_mppt_max')
        num_mppt = request.form.get('num_mppt')
        strings_por_mppt = request.form.get('strings_por_mppt')
        eficiencia_maxima = request.form.get('eficiencia_maxima')
        garantia_anos = request.form.get('garantia_anos')
        grau_protecao = request.form.get('grau_protecao')
        
        # Processar datasheets (múltiplos arquivos ou URL)
        datasheets = []
        
        # No Render, bloquear upload de arquivos (filesystem efêmero)
        if 'datasheet_file' in request.files and not IS_RENDER:
            files = request.files.getlist('datasheet_file')
            for file in files:
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(filepath)
                    datasheets.append(f"/uploads/datasheets/{filename}")
        elif 'datasheet_file' in request.files and IS_RENDER:
            files = request.files.getlist('datasheet_file')
            if any(f.filename for f in files):
                flash('⚠️ Upload de arquivos não disponível no Render. Use um link externo (Google Drive, Dropbox, etc.)', 'warning')
        
        # Se não houver arquivo, usar URL
        if not datasheets:
            url = request.form.get('datasheet_url')
            if url:
                datasheets.append(url)
        
        # Converter lista para string separada por ponto-e-vírgula
        datasheet = ';'.join(datasheets) if datasheets else None
        
        inversor = InversorSolar(
            modelo=request.form.get('modelo'),
            fabricante=request.form.get('fabricante'),
            tipo=request.form.get('tipo'),
            potencia_nominal=float(request.form.get('potencia_nominal')),
            potencia_maxima=float(potencia_maxima) if potencia_maxima else None,
            tensao_entrada_min=float(tensao_entrada_min) if tensao_entrada_min else None,
            tensao_entrada_max=float(tensao_entrada_max) if tensao_entrada_max else None,
            tensao_mppt_min=float(tensao_mppt_min) if tensao_mppt_min else None,
            tensao_mppt_max=float(tensao_mppt_max) if tensao_mppt_max else None,
            num_mppt=int(num_mppt) if num_mppt else 2,
            strings_por_mppt=int(strings_por_mppt) if strings_por_mppt else None,
            eficiencia_maxima=float(eficiencia_maxima) if eficiencia_maxima else None,
            fases=request.form.get('fases'),
            garantia_anos=int(garantia_anos) if garantia_anos else 5,
            grau_protecao=grau_protecao,
            preco_venda=float(request.form.get('preco_venda')),
            datasheet=datasheet
        )
        
        db.session.add(inversor)
        db.session.commit()
        flash(f'Inversor {inversor.modelo} adicionado ao catálogo com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao adicionar inversor: {str(e)}', 'error')
    
    return redirect(url_for('energia_solar.inversores_listar'))
    
    return redirect(url_for('energia_solar.inversores_listar'))


@energia_solar_bp.route('/inversores/excluir/<int:inversor_id>')
@login_required
def inversor_excluir(inversor_id):
    """Exclui um inversor do catálogo"""
    try:
        inversor = InversorSolar.query.get_or_404(inversor_id)
        db.session.delete(inversor)
        db.session.commit()
        flash('Inversor excluído do catálogo com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir inversor: {str(e)}', 'error')
    
    return redirect(url_for('energia_solar.inversores_listar'))


@energia_solar_bp.route('/inversores/datasheet/excluir/<int:inversor_id>/<int:index>', methods=['POST'])
@login_required
def inversor_datasheet_excluir(inversor_id, index):
    """Exclui um datasheet específico do inversor"""
    try:
        inversor = InversorSolar.query.get_or_404(inversor_id)
        
        if inversor.datasheet:
            # Separar os arquivos
            arquivos = inversor.datasheet.split(';')
            
            # Verificar se o índice é válido
            if 0 <= index < len(arquivos):
                arquivo_excluir = arquivos[index].strip()
                
                # Se for arquivo local, excluir do disco
                if arquivo_excluir.startswith('/uploads/') and not IS_RENDER:
                    caminho_arquivo = os.path.join(
                        os.path.dirname(os.path.dirname(__file__)),
                        'static',
                        arquivo_excluir.lstrip('/')
                    )
                    if os.path.exists(caminho_arquivo):
                        os.remove(caminho_arquivo)
                
                # Remover da lista
                arquivos.pop(index)
                
                # Atualizar o campo
                inversor.datasheet = ';'.join(arquivos) if arquivos else None
                db.session.commit()
                
                return jsonify({'success': True}), 200
            else:
                return jsonify({'error': 'Índice inválido'}), 400
        else:
            return jsonify({'error': 'Nenhum datasheet encontrado'}), 404
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@energia_solar_bp.route('/inversores/editar/<int:inversor_id>', methods=['GET', 'POST'])
@login_required
def inversor_editar(inversor_id):
    """Edita um inversor do catálogo"""
    inversor = InversorSolar.query.get_or_404(inversor_id)
    
    if request.method == 'POST':
        try:
            # Atualizar dados básicos
            inversor.modelo = request.form.get('modelo')
            inversor.fabricante = request.form.get('fabricante')
            inversor.tipo = request.form.get('tipo')
            inversor.potencia_nominal = float(request.form.get('potencia_nominal'))
            inversor.preco_venda = float(request.form.get('preco_venda'))
            inversor.fases = request.form.get('fases')
            
            # Campos opcionais
            potencia_maxima = request.form.get('potencia_maxima')
            tensao_entrada_min = request.form.get('tensao_entrada_min')
            tensao_entrada_max = request.form.get('tensao_entrada_max')
            tensao_mppt_min = request.form.get('tensao_mppt_min')
            tensao_mppt_max = request.form.get('tensao_mppt_max')
            num_mppt = request.form.get('num_mppt')
            strings_por_mppt = request.form.get('strings_por_mppt')
            eficiencia_maxima = request.form.get('eficiencia_maxima')
            garantia_anos = request.form.get('garantia_anos')
            grau_protecao = request.form.get('grau_protecao')
            
            inversor.potencia_maxima = float(potencia_maxima) if potencia_maxima else None
            inversor.tensao_entrada_min = float(tensao_entrada_min) if tensao_entrada_min else None
            inversor.tensao_entrada_max = float(tensao_entrada_max) if tensao_entrada_max else None
            inversor.tensao_mppt_min = float(tensao_mppt_min) if tensao_mppt_min else None
            inversor.tensao_mppt_max = float(tensao_mppt_max) if tensao_mppt_max else None
            inversor.num_mppt = int(num_mppt) if num_mppt else 2
            inversor.strings_por_mppt = int(strings_por_mppt) if strings_por_mppt else None
            inversor.eficiencia_maxima = float(eficiencia_maxima) if eficiencia_maxima else None
            inversor.garantia_anos = int(garantia_anos) if garantia_anos else 5
            inversor.grau_protecao = grau_protecao
            
            # Processar datasheet (arquivo ou URL)
            datasheet_atualizado = False
            
            # Verificar se há arquivo enviado (apenas local, não no Render)
            if 'datasheet_file' in request.files and not IS_RENDER:
                file = request.files['datasheet_file']
                if file and file.filename and allowed_file(file.filename):
                    # Excluir arquivo antigo se existir e for local
                    if inversor.datasheet and inversor.datasheet.startswith('/static/uploads/'):
                        old_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                              inversor.datasheet.lstrip('/'))
                        if os.path.exists(old_file):
                            os.remove(old_file)
                    
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(filepath)
                    inversor.datasheet = f"/uploads/datasheets/{filename}"
                    datasheet_atualizado = True
            elif 'datasheet_file' in request.files and IS_RENDER:
                file = request.files['datasheet_file']
                if file and file.filename:
                    flash('⚠️ Upload de arquivos não disponível no Render. Use um link externo na aba "Link Externo".', 'warning')
            
            # Se não enviou arquivo, verificar URL
            if not datasheet_atualizado:
                url_fornecida = request.form.get('datasheet_url', '').strip()
                if url_fornecida:
                    # Excluir arquivo local antigo se houver
                    if inversor.datasheet and inversor.datasheet.startswith('/static/uploads/'):
                        old_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                              inversor.datasheet.lstrip('/'))
                        if os.path.exists(old_file):
                            os.remove(old_file)
                    inversor.datasheet = url_fornecida
            
            db.session.commit()
            flash(f'Inversor {inversor.modelo} atualizado com sucesso!', 'success')
            return redirect(url_for('energia_solar.inversores_listar'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar inversor: {str(e)}', 'error')
    
    # GET: retornar dados em JSON
    return jsonify(inversor.to_dict())


# ========================================
# ROTAS DE KITS
# ========================================

@energia_solar_bp.route('/kits')
@login_required
def kits_listar():
    """Lista todos os kits do catálogo"""
    try:
        from app.energia_solar.catalogo_model import KitSolar, PlacaSolar, InversorSolar
        
        kits_obj = KitSolar.query.order_by(KitSolar.fabricante, KitSolar.potencia_kwp).all()
        kits = [k.to_dict() for k in kits_obj]
        placas = PlacaSolar.query.filter_by(ativo=True).order_by(PlacaSolar.fabricante, PlacaSolar.modelo).all()
        inversores = InversorSolar.query.filter_by(ativo=True).order_by(InversorSolar.fabricante, InversorSolar.modelo).all()
        
        return render_template('energia_solar/kits_crud.html', kits=kits, kits_obj=kits_obj, placas=placas, inversores=inversores)
    except Exception as e:
        logger.error(f"❌ Erro ao listar kits: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Erro ao carregar kits: {str(e)}', 'error')
        return redirect(url_for('energia_solar.dashboard'))


@energia_solar_bp.route('/kits/criar', methods=['POST'])
@login_required
def kit_criar():
    """Cria um novo kit no catálogo"""
    from app.energia_solar.catalogo_model import KitSolar
    
    try:
        kit = KitSolar(
            fabricante=request.form.get('fabricante'),
            descricao=request.form.get('descricao'),
            outras_informacoes=request.form.get('outras_informacoes'),
            potencia_kwp=float(request.form.get('potencia_kwp')),
            preco=float(request.form.get('preco')),
            placa_id=int(request.form.get('placa_id')),
            qtd_placas=int(request.form.get('qtd_placas')),
            inversor_id=int(request.form.get('inversor_id')),
            qtd_inversores=int(request.form.get('qtd_inversores'))
        )
        
        db.session.add(kit)
        db.session.commit()
        flash(f'Kit {kit.descricao} adicionado ao catálogo com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao adicionar kit: {str(e)}', 'error')
    
    return redirect(url_for('energia_solar.kits_listar'))


@energia_solar_bp.route('/kits/excluir/<int:kit_id>', methods=['POST'])
@login_required
def kit_excluir(kit_id):
    """Exclui um kit do catálogo"""
    from app.energia_solar.catalogo_model import KitSolar
    
    try:
        kit = KitSolar.query.get_or_404(kit_id)
        db.session.delete(kit)
        db.session.commit()
        flash('Kit excluído do catálogo com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir kit: {str(e)}', 'error')
    
    return redirect(url_for('energia_solar.kits_listar'))


@energia_solar_bp.route('/kits/editar/<int:kit_id>', methods=['POST'])
@login_required
def kit_editar(kit_id):
    """Edita um kit do catálogo"""
    from app.energia_solar.catalogo_model import KitSolar
    
    try:
        kit = KitSolar.query.get_or_404(kit_id)
        
        kit.fabricante = request.form.get('fabricante')
        kit.descricao = request.form.get('descricao')
        kit.outras_informacoes = request.form.get('outras_informacoes')
        kit.potencia_kwp = float(request.form.get('potencia_kwp'))
        kit.preco = float(request.form.get('preco'))
        kit.placa_id = int(request.form.get('placa_id'))
        kit.qtd_placas = int(request.form.get('qtd_placas'))
        kit.inversor_id = int(request.form.get('inversor_id'))
        kit.qtd_inversores = int(request.form.get('qtd_inversores'))
        
        db.session.commit()
        flash(f'Kit {kit.descricao} atualizado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar kit: {str(e)}', 'error')
    
    return redirect(url_for('energia_solar.kits_listar'))


# ========================================
# ROTAS DE PROJETOS SOLARES - WIZARD 6 ABAS
# ========================================

@energia_solar_bp.route('/projetos')
@login_required
def projetos_listar():
    """Lista todos os projetos solares com ordenação"""
    try:
        from app.energia_solar.catalogo_model import ProjetoSolar
        
        # Pegar parâmetro de ordenação
        ordem = request.args.get('ordem', 'recente')
        
        # Aplicar ordenação
        query = ProjetoSolar.query
        
        if ordem == 'recente':
            query = query.order_by(ProjetoSolar.data_criacao.desc())
        elif ordem == 'antigo':
            query = query.order_by(ProjetoSolar.data_criacao.asc())
        elif ordem == 'cliente':
            query = query.order_by(ProjetoSolar.nome_cliente.asc())
        elif ordem == 'valor':
            query = query.order_by(ProjetoSolar.valor_venda.desc())
        elif ordem == 'potencia':
            query = query.order_by(ProjetoSolar.potencia_kwp.desc())
        else:
            query = query.order_by(ProjetoSolar.data_criacao.desc())
        
        projetos = query.all()
        
        # Evitar cache para garantir HTML atualizado
        from flask import make_response
        response = make_response(render_template('energia_solar/projetos_lista.html', projetos=projetos))
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        logger.error(f"❌ Erro ao listar projetos: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Erro ao carregar lista de projetos: {str(e)}', 'error')
        return redirect(url_for('energia_solar.dashboard'))


@energia_solar_bp.route('/projetos/<int:projeto_id>/duplicar', methods=['POST'])
@login_required
def projeto_duplicar(projeto_id):
    """Duplica um projeto existente"""
    from app.energia_solar.catalogo_model import ProjetoSolar
    
    try:
        # Buscar projeto original
        projeto_original = ProjetoSolar.query.get_or_404(projeto_id)
        
        # Criar novo projeto (cópia)
        novo_projeto = ProjetoSolar()
        
        # Copiar todos os atributos relevantes
        for coluna in ProjetoSolar.__table__.columns:
            if coluna.name not in ['id', 'data_criacao', 'data_modificacao', 'numero_projeto']:
                valor = getattr(projeto_original, coluna.name)
                setattr(novo_projeto, coluna.name, valor)
        
        # Modificar nome do cliente para indicar cópia
        novo_projeto.nome_cliente = f"{projeto_original.nome_cliente} (CÓPIA)"
        novo_projeto.status = 'rascunho'
        novo_projeto.status_orcamento = 'pendente'
        
        db.session.add(novo_projeto)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'novo_id': novo_projeto.id,
            'mensagem': 'Projeto duplicado com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@energia_solar_bp.route('/projetos/<int:projeto_id>/dashboard')
@login_required
def projeto_dashboard(projeto_id):
    """Dashboard completo do projeto com KPIs e ações"""
    from app.energia_solar.catalogo_model import ProjetoSolar, PlacaSolar, InversorSolar, KitSolar
    
    projeto = ProjetoSolar.query.get_or_404(projeto_id)
    
    # Buscar equipamentos
    placa = None
    inversor = None
    
    # Tentar buscar via kit primeiro
    if projeto.kit_id:
        kit = KitSolar.query.get(projeto.kit_id)
        if kit:
            if kit.placa_id:
                placa = PlacaSolar.query.get(kit.placa_id)
            if kit.inversor_id:
                inversor = InversorSolar.query.get(kit.inversor_id)
    
    # Se não encontrou via kit, buscar direto
    if not placa and projeto.placa_id:
        placa = PlacaSolar.query.get(projeto.placa_id)
    if not inversor and projeto.inversor_id:
        inversor = InversorSolar.query.get(projeto.inversor_id)
    
    # Calcular KPIs adicionais se necessário
    economia_mensal = (projeto.consumo_kwh_mes or 0) * (projeto.tarifa_kwh or 0)
    economia_anual = economia_mensal * 12
    
    # Buscar concessionárias para o select
    from app.concessionaria.concessionaria_model import Concessionaria
    concessionarias = Concessionaria.query.filter_by(ativo=True).order_by(Concessionaria.nome).all()
    
    # Buscar placas e kits disponíveis para seleção no método de dimensionamento
    placas_disponiveis = PlacaSolar.query.filter_by(ativo=True).order_by(PlacaSolar.modelo).all()
    kits_disponiveis = KitSolar.query.filter_by(ativo=True).order_by(KitSolar.descricao).all()
    inversores_disponiveis = InversorSolar.query.filter_by(ativo=True).order_by(InversorSolar.fabricante, InversorSolar.modelo).all()
    
    return render_template('energia_solar/projeto_dashboard.html', 
                         projeto=projeto,
                         placa=placa,
                         inversor=inversor,
                         economia_mensal=economia_mensal,
                         economia_anual=economia_anual,
                         concessionarias=concessionarias,
                         placas_disponiveis=placas_disponiveis,
                         kits_disponiveis=kits_disponiveis,
                         inversores_disponiveis=inversores_disponiveis)


@energia_solar_bp.route('/projetos/<int:projeto_id>/dados-financeiros', methods=['POST'])
@login_required
def projeto_salvar_dados_financeiros(projeto_id):
    """Salva dados financeiros do projeto"""
    from app.energia_solar.catalogo_model import ProjetoSolar
    
    try:
        projeto = ProjetoSolar.query.get_or_404(projeto_id)
        
        # Receber dados do formulário
        concessionaria_id = request.form.get('concessionaria_id')
        tarifa_final = request.form.get('tarifa_final')
        economia_anual = request.form.get('economia_anual_prevista')
        impostos_percentual = request.form.get('impostos_percentual')
        
        # Atualizar projeto
        if concessionaria_id:
            projeto.concessionaria_id = int(concessionaria_id)
        
        if tarifa_final:
            projeto.tarifa_energia = float(tarifa_final.replace(',', '.'))
        
        if economia_anual:
            projeto.economia_anual_prevista = float(economia_anual.replace(',', '.'))
        
        if impostos_percentual:
            projeto.impostos_percentual = float(impostos_percentual.replace(',', '.'))
        
        db.session.commit()
        
        flash('Dados financeiros salvos com sucesso!', 'success')
        return redirect(url_for('energia_solar.projeto_dashboard', projeto_id=projeto_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar dados financeiros: {str(e)}', 'danger')
        return redirect(url_for('energia_solar.projeto_dashboard', projeto_id=projeto_id))


@energia_solar_bp.route('/projetos/<int:projeto_id>/dados-tecnicos', methods=['POST'])
@login_required
def projeto_salvar_dados_tecnicos(projeto_id):
    """Salva dados técnicos do projeto"""
    from app.energia_solar.catalogo_model import ProjetoSolar
    
    try:
        projeto = ProjetoSolar.query.get_or_404(projeto_id)
        
        # Aba 1: Dados iniciais
        projeto.cidade = request.form.get('cidade')
        projeto.estado = request.form.get('estado')
        projeto.latitude = float(request.form.get('latitude', 0)) if request.form.get('latitude') else None
        projeto.longitude = float(request.form.get('longitude', 0)) if request.form.get('longitude') else None
        projeto.irradiacao_solar = float(request.form.get('irradiacao_solar', 0)) if request.form.get('irradiacao_solar') else None
        projeto.tipo_instalacao = request.form.get('tipo_instalacao')
        projeto.perdas_sistema = float(request.form.get('perdas_sistema', 20)) / 100 if request.form.get('perdas_sistema') else 0.20
        projeto.consumo_kwh_mes = float(request.form.get('consumo_kwh_mes', 0)) if request.form.get('consumo_kwh_mes') else None
        
        # Aba 2: Método - processar modo de equipamento
        modo_equipamento = request.form.get('modo_equipamento', 'individual')
        projeto.modo_equipamento = modo_equipamento
        
        if modo_equipamento == 'individual':
            # Placas individuais
            projeto.placa_id = int(request.form.get('placa_id')) if request.form.get('placa_id') else None
            projeto.qtd_placas = int(request.form.get('qtd_placas', 0)) if request.form.get('qtd_placas') else None
            projeto.kit_id = None  # Limpar kit se existir
            
            # Calcular potência baseado nas placas
            if projeto.placa_id and projeto.qtd_placas:
                placa = PlacaSolar.query.get(projeto.placa_id)
                if placa:
                    projeto.potencia_kwp = (projeto.qtd_placas * placa.potencia) / 1000
                    projeto.geracao_estimada_mes = projeto.potencia_kwp * 4.5 * 30 * 0.8
        else:
            # Kit fotovoltaico
            projeto.kit_id = int(request.form.get('kit_id')) if request.form.get('kit_id') else None
            projeto.placa_id = None  # Limpar placa_id se existir
            
            # Obter dados do kit
            if projeto.kit_id:
                kit = KitSolar.query.get(projeto.kit_id)
                if kit:
                    projeto.potencia_kwp = kit.potencia_kwp
                    projeto.qtd_placas = kit.qtd_placas
                    projeto.geracao_estimada_mes = projeto.potencia_kwp * 4.5 * 30 * 0.8
        
        # Perda de eficiência anual
        projeto.perda_eficiencia_anual = float(request.form.get('perda_eficiencia_anual', 0.8)) if request.form.get('perda_eficiencia_anual') else 0.8
        
        # Aba 3: Ajustes - Inversores
        projeto.inversor_id = int(request.form.get('inversor_id')) if request.form.get('inversor_id') else None
        projeto.qtd_inversores = int(request.form.get('qtd_inversores', 1)) if request.form.get('qtd_inversores') else 1
        projeto.usar_micro_inversor = bool(request.form.get('usar_micro_inversor'))
        
        # Aba 3: Ajustes - Área de instalação
        projeto.orientacao = request.form.get('orientacao')
        projeto.linhas_placas = int(request.form.get('linhas_placas', 1)) if request.form.get('linhas_placas') else 1
        projeto.colunas_placas = int(request.form.get('colunas_placas', 1)) if request.form.get('colunas_placas') else 1
        
        # Calcular largura e comprimento da área
        if projeto.placa_id and projeto.linhas_placas and projeto.colunas_placas:
            placa = PlacaSolar.query.get(projeto.placa_id)
            if placa:
                # Obter dimensões reais da placa (em mm no banco, converter para metros)
                largura_placa = (placa.largura / 1000) if placa.largura else 0.992
                comprimento_placa = (placa.comprimento / 1000) if placa.comprimento else 1.650
                
                # Inverter dimensões se orientação for PAISAGEM
                if projeto.orientacao == 'PAISAGEM':
                    largura_placa, comprimento_placa = comprimento_placa, largura_placa
                
                # Adicionar espaçamento de 10cm entre placas
                espacamento = 0.10
                projeto.largura_area = (projeto.colunas_placas * largura_placa) + ((projeto.colunas_placas - 1) * espacamento)
                projeto.comprimento_area = (projeto.linhas_placas * comprimento_placa) + ((projeto.linhas_placas - 1) * espacamento)
        
        # Aba 4: Demais Informações (campos antigos mantidos)
        projeto.lei_14300_ano = int(request.form.get('lei_14300_ano', 2026)) if request.form.get('lei_14300_ano') else 2026
        projeto.simultaneidade = float(request.form.get('simultaneidade', 35)) if request.form.get('simultaneidade') else 35.0
        projeto.disjuntor_ca = request.form.get('disjuntor_ca')
        
        # Proteções String Box
        projeto.protecao_cc_tipo = request.form.get('protecao_cc_tipo')
        projeto.protecao_cc_corrente = request.form.get('protecao_cc_corrente')
        projeto.protecao_ca_tipo = request.form.get('protecao_ca_tipo')
        projeto.protecao_ca_corrente = request.form.get('protecao_ca_corrente')
        
        # Padrão de Entrada
        tipo_entrada = request.form.get('tipo_entrada')
        if tipo_entrada == 'monofasico':
            projeto.qtd_fases = 1
            projeto.tipo_instalacao = 'monofasica'
        elif tipo_entrada == 'bifasico':
            projeto.qtd_fases = 2
            projeto.tipo_instalacao = 'bifasica'
        elif tipo_entrada == 'trifasico':
            projeto.qtd_fases = 3
            projeto.tipo_instalacao = 'trifasica'
        else:
            projeto.qtd_fases = None
            
        projeto.cabo_fase_bitola = request.form.get('cabo_fase_bitola')
        projeto.cabo_neutro_bitola = request.form.get('cabo_neutro_bitola')
        projeto.qtd_terra = int(request.form.get('qtd_terra', 1)) if request.form.get('qtd_terra') else 1
        projeto.cabo_terra_bitola = request.form.get('cabo_terra_bitola')
        projeto.padrao_observacoes = request.form.get('padrao_observacoes')
        
        # Cabos
        projeto.cabo_ca = request.form.get('cabo_ca')
        projeto.cabo_cc = request.form.get('cabo_cc')
        
        db.session.commit()
        
        flash('✅ Dados técnicos salvos com sucesso!', 'success')
        return redirect(url_for('energia_solar.projeto_dashboard', projeto_id=projeto_id))
        
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"❌ ERRO ao salvar dados técnicos:")
        print(traceback.format_exc())
        flash(f'Erro ao salvar dados técnicos: {str(e)}', 'danger')
        return redirect(url_for('energia_solar.projeto_dashboard', projeto_id=projeto_id))


@energia_solar_bp.route('/projetos/<int:projeto_id>/orcamento/itens', methods=['GET'])
@login_required
def projeto_orcamento_listar(projeto_id):
    """Lista itens do orçamento do projeto"""
    from app.energia_solar.orcamento_model import OrcamentoItem
    
    itens = OrcamentoItem.query.filter_by(projeto_id=projeto_id).order_by(OrcamentoItem.ordem, OrcamentoItem.id).all()
    
    return jsonify({
        'success': True,
        'itens': [item.to_dict() for item in itens]
    })


@energia_solar_bp.route('/projetos/<int:projeto_id>/orcamento/itens', methods=['POST'])
@login_required
def projeto_orcamento_salvar(projeto_id):
    """Salva itens do orçamento"""
    from app.energia_solar.orcamento_model import OrcamentoItem
    from app.energia_solar.catalogo_model import ProjetoSolar
    
    try:
        # Receber dados JSON
        data = request.get_json()
        itens_data = data.get('itens', [])
        
        # Deletar itens existentes
        OrcamentoItem.query.filter_by(projeto_id=projeto_id).delete()
        
        # Criar novos itens
        total_custo = 0
        total_faturamento = 0
        
        for idx, item_data in enumerate(itens_data):
            item = OrcamentoItem()
            item.projeto_id = projeto_id
            item.descricao = item_data.get('descricao', '')
            item.categoria = item_data.get('categoria', 'outros')
            item.quantidade = float(item_data.get('quantidade', 1))
            item.unidade_medida = item_data.get('unidade_medida', 'un')
            item.preco_unitario = float(item_data.get('preco_unitario', 0))
            item.lucro_percentual = float(item_data.get('lucro_percentual', 0))
            item.ordem = idx
            
            # Calcular totais
            item.calcular_totais()
            
            db.session.add(item)
            
            total_custo += float(item.preco_total)
            total_faturamento += float(item.faturamento)
        
        # Atualizar valores no projeto
        projeto = ProjetoSolar.query.get(projeto_id)
        if projeto:
            projeto.custo_total = total_custo
            projeto.valor_venda = total_faturamento
            projeto.valor_orcamento_total = total_faturamento
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'total_custo': total_custo,
            'total_faturamento': total_faturamento,
            'mensagem': 'Orçamento salvo com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@energia_solar_bp.route('/orcamento/custos-fixos-template', methods=['GET'])
@login_required
def orcamento_custos_fixos_template():
    """Retorna template de custos fixos"""
    from app.energia_solar.orcamento_model import db
    from sqlalchemy import text
    
    try:
        result = db.session.execute(text("""
            SELECT descricao, quantidade, unidade_medida, preco_unitario, lucro_percentual, faturamento, ordem
            FROM custos_fixos_template
            WHERE ativo = true
            ORDER BY ordem
        """))
        
        custos = []
        for row in result:
            custos.append({
                'descricao': row[0],
                'quantidade': float(row[1]) if row[1] else 1,
                'unidade_medida': row[2] or 'un',
                'preco_unitario': float(row[3]) if row[3] else 0,
                'lucro_percentual': float(row[4]) if row[4] else 0,
                'faturamento': float(row[5]) if row[5] else 0
            })
        
        return jsonify({
            'success': True,
            'custos': custos
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@energia_solar_bp.route('/projetos/<int:projeto_id>/financiamento', methods=['POST'])
@login_required
def projeto_salvar_financiamento(projeto_id):
    """Salva dados de financiamento do projeto"""
    from app.energia_solar.orcamento_model import db
    from sqlalchemy import text
    
    try:
        data = request.get_json()
        
        # Deletar financiamento existente
        db.session.execute(text("""
            DELETE FROM projeto_financiamento 
            WHERE projeto_id = :projeto_id
        """), {'projeto_id': projeto_id})
        
        # Inserir novo financiamento
        db.session.execute(text("""
            INSERT INTO projeto_financiamento 
            (projeto_id, valor_financiado, n_meses, juros_mensal, valor_parcela, total_pagar, total_juros, incluir_em_pdf)
            VALUES (:projeto_id, :valor_financiado, :n_meses, :juros_mensal, :valor_parcela, :total_pagar, :total_juros, :incluir_em_pdf)
        """), {
            'projeto_id': projeto_id,
            'valor_financiado': float(data.get('valor_financiado', 0)),
            'n_meses': int(data.get('n_meses', 12)),
            'juros_mensal': float(data.get('juros_mensal', 0)),
            'valor_parcela': float(data.get('valor_parcela', 0)),
            'total_pagar': float(data.get('total_pagar', 0)),
            'total_juros': float(data.get('total_juros', 0)),
            'incluir_em_pdf': bool(data.get('incluir_em_pdf', False))
        })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'mensagem': 'Financiamento salvo com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@energia_solar_bp.route('/projetos/<int:projeto_id>/financiamento', methods=['GET'])
@login_required
def projeto_buscar_financiamento(projeto_id):
    """Busca dados de financiamento do projeto"""
    from app.energia_solar.orcamento_model import db
    from sqlalchemy import text
    
    try:
        result = db.session.execute(text("""
            SELECT valor_financiado, n_meses, juros_mensal, valor_parcela, total_pagar, total_juros, incluir_em_pdf
            FROM projeto_financiamento
            WHERE projeto_id = :projeto_id
            LIMIT 1
        """), {'projeto_id': projeto_id})
        
        row = result.fetchone()
        
        if row:
            return jsonify({
                'success': True,
                'financiamento': {
                    'valor_financiado': float(row[0]) if row[0] else 0,
                    'n_meses': int(row[1]) if row[1] else 12,
                    'juros_mensal': float(row[2]) if row[2] else 0,
                    'valor_parcela': float(row[3]) if row[3] else 0,
                    'total_pagar': float(row[4]) if row[4] else 0,
                    'total_juros': float(row[5]) if row[5] else 0,
                    'incluir_em_pdf': bool(row[6]) if row[6] else False
                }
            })
        else:
            return jsonify({
                'success': True,
                'financiamento': None
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@energia_solar_bp.route('/projetos/criar')
@login_required
def projeto_criar():
    """Renderiza o wizard de criação de projeto (6 abas)"""
    from app.energia_solar.catalogo_model import PlacaSolar, InversorSolar, KitSolar
    
    # Carregar dados para os dropdowns
    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
    placas = PlacaSolar.query.filter_by(ativo=True).order_by(PlacaSolar.fabricante, PlacaSolar.modelo).all()
    inversores = InversorSolar.query.filter_by(ativo=True).order_by(InversorSolar.fabricante, InversorSolar.modelo).all()
    kits = KitSolar.query.filter_by(ativo=True).order_by(KitSolar.fabricante).all()
    
    return render_template('energia_solar/projeto_wizard.html',
                         clientes=clientes,
                         placas=placas,
                         inversores=inversores,
                         kits=kits)


@energia_solar_bp.route('/projetos/salvar', methods=['POST'])
@login_required
def projeto_salvar():
    """Salva ou atualiza o projeto completo das 6 abas"""
    from app.energia_solar.catalogo_model import ProjetoSolar
    import json
    
    try:
        # Verificar se é edição ou criação
        projeto_id = request.form.get('projeto_id')
        
        if projeto_id:
            # ATUALIZAR projeto existente
            projeto = ProjetoSolar.query.get_or_404(int(projeto_id))
            print(f"📝 ATUALIZANDO projeto {projeto_id}")
        else:
            # CRIAR novo projeto
            projeto = ProjetoSolar()
            print(f"✨ CRIANDO novo projeto")
        
        # Aba 1 - Cliente e Localização
        projeto.cliente_id = request.form.get('cliente_id') or None
        projeto.nome_cliente = request.form.get('nome_cliente')
        projeto.cep = request.form.get('cep')
        projeto.endereco = request.form.get('endereco')
        projeto.numero = request.form.get('numero')  # 🔥 SALVAR NÚMERO
        print(f"🏠 Número do endereço: {projeto.numero}")
        projeto.cidade = request.form.get('cidade')
        projeto.estado = request.form.get('estado')
        projeto.latitude = float(request.form.get('latitude', 0)) if request.form.get('latitude') else None
        projeto.longitude = float(request.form.get('longitude', 0)) if request.form.get('longitude') else None
        projeto.irradiacao_solar = float(request.form.get('irradiacao_solar', 0)) if request.form.get('irradiacao_solar') else None
        
        # Aba 2 - Consumo e Dimensionamento
        projeto.metodo_calculo = request.form.get('metodo_calculo')
        projeto.consumo_kwh_mes = float(request.form.get('consumo_kwh_mes', 0)) if request.form.get('consumo_kwh_mes') else None
        
        # Histórico (se metodo = historico_12m)
        if projeto.metodo_calculo == 'historico_12m':
            historico = {}
            for mes in ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']:
                val = request.form.get(f'mes_{mes}', 0)
                historico[mes] = float(val) if val else 0
            projeto.historico_consumo = historico
        
        projeto.valor_conta_luz = float(request.form.get('valor_conta_luz', 0)) if request.form.get('valor_conta_luz') else None
        projeto.tarifa_kwh = float(request.form.get('tarifa_kwh', 0.85)) if request.form.get('tarifa_kwh') else 0.85  # 🔥 SALVAR TARIFA
        print(f"💰 Tarifa kWh: {projeto.tarifa_kwh}")
        
        # 🔥 TIPO DE INSTALAÇÃO - campo que faltava
        projeto.tipo_instalacao = request.form.get('tipo_instalacao', 'monofasica')  
        print(f"⚡ Tipo de instalação: {projeto.tipo_instalacao}")
        
        projeto.potencia_kwp = float(request.form.get('potencia_kwp', 0)) if request.form.get('potencia_kwp') else None
        projeto.simultaneidade = float(request.form.get('simultaneidade', 35.0)) if request.form.get('simultaneidade') else 35.0  # 🔥 SALVAR SIMULTANEIDADE
        print(f"🔄 Simultaneidade: {projeto.simultaneidade}%")
        projeto.perdas_sistema = float(request.form.get('perdas_sistema', 0.20)) if request.form.get('perdas_sistema') else 0.20
        
        # Aba 3 - Equipamentos
        projeto.modo_equipamento = request.form.get('modo_equipamento')
        if projeto.modo_equipamento == 'kit':
            kit_id = int(request.form.get('kit_id')) if request.form.get('kit_id') else None
            projeto.kit_id = kit_id
            
            # Buscar dados do kit e preencher placas/inversores automaticamente
            if kit_id:
                from app.energia_solar.catalogo_model import KitSolar
                kit = KitSolar.query.get(kit_id)
                if kit:
                    projeto.placa_id = kit.placa_id
                    projeto.inversor_id = kit.inversor_id
                    projeto.qtd_placas = kit.qtd_placas
                    projeto.qtd_inversores = kit.qtd_inversores
        else:
            projeto.placa_id = int(request.form.get('placa_id')) if request.form.get('placa_id') else None
            projeto.inversor_id = int(request.form.get('inversor_id')) if request.form.get('inversor_id') else None
            projeto.qtd_placas = int(request.form.get('qtd_placas', 0)) if request.form.get('qtd_placas') else None
            projeto.qtd_inversores = int(request.form.get('qtd_inversores', 1)) if request.form.get('qtd_inversores') else 1
        
        # 🔥 CALCULAR GERAÇÃO ESTIMADA AUTOMATICAMENTE
        if projeto.qtd_placas and projeto.placa_id and projeto.irradiacao_solar:
            # Calcular potência do sistema
            placa = PlacaSolar.query.get(projeto.placa_id)
            if placa and placa.potencia:
                projeto.potencia_kwp = (projeto.qtd_placas * placa.potencia) / 1000  # Converter Wp para kWp
                print(f"✅ Potência do sistema: {projeto.potencia_kwp} kWp ({projeto.qtd_placas} × {placa.potencia}Wp)")
            
            # Calcular geração estimada
            projeto.geracao_estimada_mes = calcular_geracao_estimada(
                projeto.qtd_placas, 
                projeto.placa_id, 
                projeto.irradiacao_solar
            )
            print(f"✅ Geração calculada: {projeto.geracao_estimada_mes} kWh/mês ({projeto.qtd_placas} placas × {projeto.irradiacao_solar} kWh/m².dia)")
        
        # Aba 4 - Layout
        projeto.orientacao = request.form.get('orientacao')
        projeto.inclinacao = float(request.form.get('inclinacao', 0)) if request.form.get('inclinacao') else None
        projeto.direcao = request.form.get('direcao')
        
        # DEBUG: Verificar valores recebidos do formulário
        linhas_raw = request.form.get('linhas_placas')
        colunas_raw = request.form.get('colunas_placas')
        print(f"🔍 DEBUG Layout - linhas_raw: '{linhas_raw}' (type: {type(linhas_raw)})")
        print(f"🔍 DEBUG Layout - colunas_raw: '{colunas_raw}' (type: {type(colunas_raw)})")
        
        projeto.linhas_placas = int(request.form.get('linhas_placas', 0)) if request.form.get('linhas_placas') else None
        projeto.colunas_placas = int(request.form.get('colunas_placas', 0)) if request.form.get('colunas_placas') else None
        
        print(f"✅ Layout salvo - {projeto.linhas_placas}x{projeto.colunas_placas} = {(projeto.linhas_placas or 0) * (projeto.colunas_placas or 0)} módulos")
        
        projeto.area_necessaria = float(request.form.get('area_necessaria', 0)) if request.form.get('area_necessaria') else None
        
        # Aba 5 - Componentes Adicionais
        projeto.string_box = request.form.get('string_box') == 'on'
        projeto.disjuntor_cc = request.form.get('disjuntor_cc')
        projeto.disjuntor_ca = request.form.get('disjuntor_ca')
        projeto.cabo_cc = request.form.get('cabo_cc')  # 🔥 SALVAR CABO CC
        projeto.cabo_ca = request.form.get('cabo_ca')  # 🔥 SALVAR CABO CA
        print(f"🔌 Cabo CC: {projeto.cabo_cc}, Cabo CA: {projeto.cabo_ca}")
        projeto.estrutura_fixacao = request.form.get('estrutura_fixacao')
        
        # Componentes extras (JSON array)
        componentes_extras = request.form.get('componentes_extras')
        if componentes_extras:
            try:
                projeto.componentes_extras = json.loads(componentes_extras)
            except:
                projeto.componentes_extras = []
        
        # Aba 6 - Financeiro
        projeto.custo_equipamentos = float(request.form.get('custo_equipamentos', 0)) if request.form.get('custo_equipamentos') else None
        projeto.custo_instalacao = float(request.form.get('custo_instalacao', 0)) if request.form.get('custo_instalacao') else None
        projeto.custo_projeto = float(request.form.get('custo_projeto', 0)) if request.form.get('custo_projeto') else None
        projeto.custo_total = float(request.form.get('custo_total', 0)) if request.form.get('custo_total') else None
        projeto.margem_lucro = float(request.form.get('margem_lucro', 0)) if request.form.get('margem_lucro') else None
        projeto.valor_venda = float(request.form.get('valor_venda', 0)) if request.form.get('valor_venda') else None
        
        # Lei 14.300
        projeto.lei_14300_ano = int(request.form.get('lei_14300_ano', 2025)) if request.form.get('lei_14300_ano') else 2025
        projeto.modalidade_gd = request.form.get('modalidade_gd')
        projeto.aliquota_fio_b = float(request.form.get('aliquota_fio_b', 0)) if request.form.get('aliquota_fio_b') else None
        projeto.economia_anual = float(request.form.get('economia_anual', 0)) if request.form.get('economia_anual') else None
        projeto.payback_anos = float(request.form.get('payback_anos', 0)) if request.form.get('payback_anos') else None
        
        # Controle
        projeto.status = request.form.get('status', 'rascunho')
        projeto.observacoes = request.form.get('observacoes')
        
        # Só atualizar usuario_criador se for novo projeto
        if not projeto_id:
            projeto.usuario_criador = current_user.nome if hasattr(current_user, 'nome') else 'Sistema'
        
        # Salvar
        if not projeto_id:
            db.session.add(projeto)
        
        db.session.commit()
        
        # Mensagem de sucesso
        if projeto_id:
            flash('✅ Projeto atualizado com sucesso!', 'success')
        else:
            flash('✅ Projeto criado com sucesso!', 'success')
        
        return redirect(url_for('energia_solar.projetos_listar'))
        
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"❌ ERRO ao salvar projeto:")
        print(traceback.format_exc())
        flash(f'Erro ao salvar projeto: {str(e)}', 'error')
        return redirect(url_for('energia_solar.projeto_criar'))


@energia_solar_bp.route('/projetos/visualizar/<int:projeto_id>')
@login_required
def projeto_visualizar(projeto_id):
    """Visualiza os detalhes completos de um projeto"""
    from app.energia_solar.catalogo_model import ProjetoSolar
    
    projeto = ProjetoSolar.query.get_or_404(projeto_id)
    
    # Verificar se python-docx está disponível
    word_disponivel = False
    try:
        from docx import Document
        word_disponivel = True
    except ImportError:
        pass
    
    return render_template('energia_solar/projeto_detalhes.html', 
                         projeto=projeto,
                         word_disponivel=word_disponivel)


@energia_solar_bp.route('/projetos/<int:projeto_id>/editar')
@login_required
def projeto_editar(projeto_id):
    """Edita um projeto existente usando o wizard"""
    from app.energia_solar.catalogo_model import ProjetoSolar, PlacaSolar, InversorSolar, KitSolar
    
    try:
        projeto = ProjetoSolar.query.get_or_404(projeto_id)
        
        # Converter projeto para dicionário serializável
        projeto_dict = {
            'id': projeto.id,
            'cliente_id': projeto.cliente_id,
            'nome_cliente': projeto.nome_cliente,
            'cep': projeto.cep,
            'endereco': projeto.endereco,
            'numero': projeto.numero,  # 🔥 ADICIONAR NÚMERO
            'cidade': projeto.cidade,
            'estado': projeto.estado,
            'latitude': float(projeto.latitude) if projeto.latitude else None,
            'longitude': float(projeto.longitude) if projeto.longitude else None,
            'irradiacao_solar': float(projeto.irradiacao_solar) if projeto.irradiacao_solar else None,
            'metodo_calculo': projeto.metodo_calculo,
            'consumo_kwh_mes': float(projeto.consumo_kwh_mes) if projeto.consumo_kwh_mes else None,
            'valor_conta_luz': float(projeto.valor_conta_luz) if projeto.valor_conta_luz else None,
            'tarifa_kwh': float(projeto.tarifa_kwh) if projeto.tarifa_kwh else 0.85,
            'tipo_instalacao': projeto.tipo_instalacao,  # 🔥 ADICIONAR TIPO INSTALAÇÃO
            'simultaneidade': float(projeto.simultaneidade) if projeto.simultaneidade else 35.0,  # Porcentagem inteira
            'perdas_sistema': float(projeto.perdas_sistema) if projeto.perdas_sistema else 0.2,
            'potencia_kwp': float(projeto.potencia_kwp) if projeto.potencia_kwp else None,
            'geracao_estimada_mes': float(projeto.geracao_estimada_mes) if projeto.geracao_estimada_mes else None,
            'modo_equipamento': projeto.modo_equipamento,
            'kit_id': projeto.kit_id,
            'placa_id': projeto.placa_id,
            'qtd_placas': projeto.qtd_placas,
            'inversor_id': projeto.inversor_id,
            'qtd_inversores': projeto.qtd_inversores,
            'orientacao': projeto.orientacao,
            'inclinacao': float(projeto.inclinacao) if projeto.inclinacao else None,
            'direcao': projeto.direcao,
            'linhas_placas': projeto.linhas_placas,
            'colunas_placas': projeto.colunas_placas,
            'area_necessaria': float(projeto.area_necessaria) if projeto.area_necessaria else None,
            'string_box': projeto.string_box,
            'disjuntor_cc': projeto.disjuntor_cc,
            'disjuntor_ca': projeto.disjuntor_ca,
            'cabo_cc': projeto.cabo_cc,
            'cabo_ca': projeto.cabo_ca,
            'estrutura_fixacao': projeto.estrutura_fixacao,
            'custo_equipamentos': float(projeto.custo_equipamentos) if projeto.custo_equipamentos else None,
            'custo_instalacao': float(projeto.custo_instalacao) if projeto.custo_instalacao else None,
            'custo_projeto': float(projeto.custo_projeto) if projeto.custo_projeto else None,
            'custo_total': float(projeto.custo_total) if projeto.custo_total else None,
            'margem_lucro': float(projeto.margem_lucro) if projeto.margem_lucro else None,
            'valor_venda': float(projeto.valor_venda) if projeto.valor_venda else None,
            'lei_14300_ano': projeto.lei_14300_ano,
            'modalidade_gd': projeto.modalidade_gd,
            'aliquota_fio_b': float(projeto.aliquota_fio_b) if projeto.aliquota_fio_b else None,
            'economia_anual': float(projeto.economia_anual) if projeto.economia_anual else None,
            'payback_anos': float(projeto.payback_anos) if projeto.payback_anos else None,
            'status': projeto.status,
            'observacoes': projeto.observacoes,
        }
    
        # Buscar dados para os selects
        clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
        placas = PlacaSolar.query.filter_by(ativo=True).all()
        inversores = InversorSolar.query.filter_by(ativo=True).all()
        kits = KitSolar.query.filter_by(ativo=True).all()
        
        # Renderizar wizard com dados do projeto para edição
        return render_template('energia_solar/projeto_wizard.html',
                             projeto=projeto_dict,
                             clientes=clientes,
                             placas=placas,
                             inversores=inversores,
                             kits=kits,
                             modo='editar')
    
    except Exception as e:
        import traceback
        print(f"❌ ERRO ao editar projeto {projeto_id}:")
        print(traceback.format_exc())
        flash(f'Erro ao carregar projeto: {str(e)}', 'error')
        return redirect(url_for('energia_solar.projetos_listar'))


@energia_solar_bp.route('/projetos/<int:projeto_id>/excluir', methods=['POST'])
@login_required
def projeto_excluir(projeto_id):
    """Exclui um projeto"""
    from app.energia_solar.catalogo_model import ProjetoSolar
    
    projeto = ProjetoSolar.query.get_or_404(projeto_id)
    
    try:
        nome_cliente = projeto.nome_cliente
        db.session.delete(projeto)
        db.session.commit()
        flash(f'Projeto do cliente "{nome_cliente}" excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir projeto: {str(e)}', 'error')
    
    return redirect(url_for('energia_solar.projetos_listar'))


@energia_solar_bp.route('/projetos/<int:projeto_id>/recalcular-geracao', methods=['POST'])
@login_required
def projeto_recalcular_geracao(projeto_id):
    """Recalcula potência e geração estimada baseado nas placas do projeto"""
    from app.energia_solar.catalogo_model import ProjetoSolar
    
    projeto = ProjetoSolar.query.get_or_404(projeto_id)
    
    try:
        if projeto.qtd_placas and projeto.placa_id and projeto.irradiacao_solar:
            # Recalcular potência
            placa = PlacaSolar.query.get(projeto.placa_id)
            if placa and placa.potencia:
                projeto.potencia_kwp = (projeto.qtd_placas * placa.potencia) / 1000
            
            # Recalcular geração
            projeto.geracao_estimada_mes = calcular_geracao_estimada(
                projeto.qtd_placas,
                projeto.placa_id,
                projeto.irradiacao_solar
            )
            
            db.session.commit()
            flash(f'✅ Geração recalculada! Potência: {projeto.potencia_kwp:.2f} kWp, Geração: {projeto.geracao_estimada_mes:.0f} kWh/mês', 'success')
        else:
            flash('⚠️ Projeto não possui dados suficientes para recalcular (placas, quantidade ou irradiação faltando)', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Erro ao recalcular geração: {str(e)}', 'error')
    
    return redirect(url_for('energia_solar.projeto_visualizar', projeto_id=projeto_id))


# ========================================
# CUSTOS FIXOS - Catálogo
# ========================================

@energia_solar_bp.route('/custos-fixos')
@login_required
def custos_fixos_listar():
    """Lista todos os custos fixos cadastrados"""
    try:
        custos = CustoFixo.query.order_by(CustoFixo.tipo, CustoFixo.descricao).all()
        return render_template('energia_solar/custos_fixos_lista.html', custos=custos)
    except Exception as e:
        logger.error(f"❌ Erro ao listar custos fixos: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Erro ao carregar custos fixos: {str(e)}', 'error')
        return redirect(url_for('energia_solar.dashboard'))


@energia_solar_bp.route('/custos-fixos/api/listar')
@login_required
def custos_fixos_api():
    """API para listar custos fixos ativos (para carregar no wizard)"""
    custos = CustoFixo.query.filter_by(ativo=True, aplicar_automaticamente=True).all()
    return jsonify([custo.to_dict() for custo in custos])


@energia_solar_bp.route('/custos-fixos/novo', methods=['GET', 'POST'])
@login_required
def custo_fixo_novo():
    """Criar novo custo fixo"""
    if request.method == 'POST':
        try:
            custo = CustoFixo(
                descricao=request.form.get('descricao'),
                unidade=request.form.get('unidade', 'un'),
                quantidade=float(request.form.get('quantidade', 1)),
                valor_unitario=float(request.form.get('valor_unitario', 0)),
                lucro_percentual=float(request.form.get('lucro_percentual', 0)),
                faturamento=request.form.get('faturamento', 'EMPRESA'),
                tipo=request.form.get('tipo'),
                categoria=request.form.get('categoria'),
                aplicar_automaticamente=request.form.get('aplicar_automaticamente') == 'on',
                observacoes=request.form.get('observacoes')
            )
            
            db.session.add(custo)
            db.session.commit()
            flash(f'Custo fixo "{custo.descricao}" criado com sucesso!', 'success')
            return redirect(url_for('energia_solar.custos_fixos_listar'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar custo fixo: {str(e)}', 'error')
    
    return render_template('energia_solar/custo_fixo_form.html', custo=None)


@energia_solar_bp.route('/custos-fixos/<int:custo_id>/editar', methods=['GET', 'POST'])
@login_required
def custo_fixo_editar(custo_id):
    """Editar custo fixo existente"""
    custo = CustoFixo.query.get_or_404(custo_id)
    
    if request.method == 'POST':
        try:
            custo.descricao = request.form.get('descricao')
            custo.unidade = request.form.get('unidade', 'un')
            custo.quantidade = float(request.form.get('quantidade', 1))
            custo.valor_unitario = float(request.form.get('valor_unitario', 0))
            custo.lucro_percentual = float(request.form.get('lucro_percentual', 0))
            custo.faturamento = request.form.get('faturamento', 'EMPRESA')
            custo.tipo = request.form.get('tipo')
            custo.categoria = request.form.get('categoria')
            custo.aplicar_automaticamente = request.form.get('aplicar_automaticamente') == 'on'
            custo.observacoes = request.form.get('observacoes')
            
            db.session.commit()
            flash(f'Custo fixo "{custo.descricao}" atualizado com sucesso!', 'success')
            return redirect(url_for('energia_solar.custos_fixos_listar'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar custo fixo: {str(e)}', 'error')
    
    return render_template('energia_solar/custo_fixo_form.html', custo=custo)


@energia_solar_bp.route('/custos-fixos/<int:custo_id>/excluir', methods=['POST'])
@login_required
def custo_fixo_excluir(custo_id):
    """Excluir custo fixo"""
    custo = CustoFixo.query.get_or_404(custo_id)
    
    try:
        descricao = custo.descricao
        db.session.delete(custo)
        db.session.commit()
        flash(f'Custo fixo "{descricao}" excluído com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir custo fixo: {str(e)}', 'error')
    
    return redirect(url_for('energia_solar.custos_fixos_listar'))


@energia_solar_bp.route('/projetos/<int:projeto_id>/recalcular-custos', methods=['POST'])
@login_required
def projeto_recalcular_custos(projeto_id):
    """Recalcula custos separados de um projeto (distribuição: 70% equip, 20% inst, 10% proj)"""
    from app.energia_solar.catalogo_model import ProjetoSolar
    
    projeto = ProjetoSolar.query.get_or_404(projeto_id)
    
    try:
        if projeto.custo_total and projeto.custo_total > 0:
            # Distribuição padrão: 70% equipamentos, 20% instalação, 10% projeto
            projeto.custo_equipamentos = projeto.custo_total * 0.70
            projeto.custo_instalacao = projeto.custo_total * 0.20
            projeto.custo_projeto = projeto.custo_total * 0.10
            
            db.session.commit()
            flash(f'Custos recalculados com sucesso! Equip: R$ {projeto.custo_equipamentos:.2f}, Inst: R$ {projeto.custo_instalacao:.2f}, Proj: R$ {projeto.custo_projeto:.2f}', 'success')
        else:
            flash('Projeto não possui custo total definido', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao recalcular custos: {str(e)}', 'error')
    
    return redirect(url_for('energia_solar.projeto_visualizar', projeto_id=projeto_id))


@energia_solar_bp.route('/admin/recalcular-todos-custos', methods=['GET', 'POST'])
@login_required
def admin_recalcular_todos_custos():
    """Recalcula custos de TODOS os projetos (página administrativa)"""
    from app.energia_solar.catalogo_model import ProjetoSolar
    
    if request.method == 'POST':
        try:
            projetos = ProjetoSolar.query.all()
            atualizados = 0
            
            for projeto in projetos:
                if projeto.custo_total and projeto.custo_total > 0:
                    # Se os custos estão zerados, recalcular
                    if not projeto.custo_equipamentos or projeto.custo_equipamentos == 0:
                        projeto.custo_equipamentos = projeto.custo_total * 0.70
                        projeto.custo_instalacao = projeto.custo_total * 0.20
                        projeto.custo_projeto = projeto.custo_total * 0.10
                        atualizados += 1
            
            db.session.commit()
            flash(f'✅ {atualizados} projetos recalculados com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Erro ao recalcular: {str(e)}', 'error')
        
        return redirect(url_for('energia_solar.admin_recalcular_todos_custos'))
    
    # GET - Mostrar página com preview
    from app.energia_solar.catalogo_model import ProjetoSolar
    projetos = ProjetoSolar.query.filter(
        ProjetoSolar.custo_total > 0,
        db.or_(
            ProjetoSolar.custo_equipamentos == None,
            ProjetoSolar.custo_equipamentos == 0
        )
    ).all()
    
    return render_template('energia_solar/admin_recalcular_custos.html', projetos=projetos)


@energia_solar_bp.route('/projetos/<int:projeto_id>/proposta-pdf')
@login_required
def projeto_proposta_pdf(projeto_id):
    """Gera PDF da proposta comercial de um projeto solar"""
    from app.energia_solar.catalogo_model import ProjetoSolar
    
    try:
        # Carregar projeto
        projeto = ProjetoSolar.query.get_or_404(projeto_id)
        
        # Carregar cliente se existir
        cliente = None
        if projeto.cliente_id:
            cliente = Cliente.query.get(projeto.cliente_id)
        
        # Importar configurações da empresa
        from app.configuracao.configuracao_utils import get_config
        config = get_config()
        
        # Calcular balanço energético para gráficos
        balanco = calcular_balanco_energetico(projeto)
        
        # Tentar gerar PDF com WeasyPrint
        try:
            import weasyprint
            from flask import current_app
            
            # Caminho absoluto para a logo
            project_root = os.path.dirname(current_app.root_path)
            logo_path = os.path.join(project_root, "static", "img", "JSP.jpg")
            logo_url = f"file:///{logo_path.replace(os.sep, '/')}"
            
            # Renderizar template HTML
            html_content = render_template('energia_solar/pdf_proposta_solar_v2.html', 
                                         projeto=projeto,
                                         cliente=cliente,
                                         logo_url=logo_url,
                                         config=config,
                                         balanco=balanco)
            
            # Base URL para resolver outros caminhos relativos
            base_url = f"file:///{project_root.replace(os.sep, '/')}/"
            
            # Gerar PDF
            pdf = weasyprint.HTML(string=html_content, base_url=base_url).write_pdf()
            
            # Criar resposta com headers anti-cache
            response = make_response(pdf)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'inline; filename=proposta_solar_{projeto_id}.pdf'
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            response.headers['Last-Modified'] = 'Wed, 11 Jan 1984 05:00:00 GMT'
            
            return response
            
        except ImportError as e:
            # WeasyPrint não instalado
            logger.error(f"WeasyPrint não encontrado: {str(e)}")
            flash(f'Biblioteca PDF não disponível - instale: pip install weasyprint', 'warning')
        except Exception as e:
            # Outro erro na geração do PDF
            logger.error(f"Erro ao gerar PDF: {str(e)}")
            flash(f'Erro ao gerar PDF: {str(e)} - exibindo HTML', 'warning')
        
        # Fallback para HTML em caso de erro
        html_response = make_response(render_template('energia_solar/pdf_proposta_solar_v2.html', 
                                                    projeto=projeto,
                                                    cliente=cliente,
                                                    config=config,
                                                    balanco=balanco))
        html_response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        html_response.headers['Pragma'] = 'no-cache'
        html_response.headers['Expires'] = '0'
        html_response.headers['Last-Modified'] = 'Wed, 11 Jan 1984 05:00:00 GMT'
        
        return html_response
            
    except Exception as e:
        logger.error(f"Erro ao gerar PDF da proposta solar {projeto_id}: {str(e)}")
        flash(f'Erro ao gerar PDF: {str(e)}', 'error')
        return redirect(url_for('energia_solar.projetos'))


@energia_solar_bp.route('/projetos/<int:projeto_id>/gerar-documento-word', methods=['GET', 'POST'])
@login_required
def gerar_documento_word(projeto_id):
    """Upload de template Word e geração de documento final"""
    try:
        # Verificar se python-docx está disponível
        try:
            from docx import Document
        except ImportError:
            flash('⚠️ Funcionalidade de documentos Word não disponível. O módulo python-docx não está instalado.', 'warning')
            return redirect(url_for('energia_solar.projeto_visualizar', projeto_id=projeto_id))
        
        try:
            from app.energia_solar.word_utils import substituir_variaveis_word, gerar_variaveis_projeto
        except Exception as e:
            flash(f'Erro ao carregar módulo Word: {str(e)}', 'error')
            return redirect(url_for('energia_solar.projeto_visualizar', projeto_id=projeto_id))
        
        from app.energia_solar.catalogo_model import ProjetoSolar
        from app.cliente.cliente_model import Cliente
        from app.configuracao.configuracao_utils import get_config
        from werkzeug.utils import secure_filename
        import io
        
        projeto = ProjetoSolar.query.get_or_404(projeto_id)
        
        if request.method == 'POST':
            # Verificar se arquivo foi enviado
            if 'template' not in request.files:
                flash('Nenhum arquivo selecionado', 'error')
                return redirect(request.url)
            
            file = request.files['template']
            
            if file.filename == '':
                flash('Nenhum arquivo selecionado', 'error')
                return redirect(request.url)
            
            if not file.filename.endswith('.docx'):
                flash('Apenas arquivos .docx são permitidos', 'error')
                return redirect(request.url)
            
            try:
                # Carregar dados
                cliente = Cliente.query.get(projeto.cliente_id) if projeto.cliente_id else None
                config = get_config()
                balanco = calcular_balanco_energetico(projeto)
                
                # Gerar variáveis
                variaveis = gerar_variaveis_projeto(projeto, cliente, config, balanco)
                
                # Processar template
                template_bytes = file.read()
                template_stream = io.BytesIO(template_bytes)
                
                # Salvar temporariamente
                temp_path = os.path.join(UPLOAD_FOLDER, 'temp_template.docx')
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                
                with open(temp_path, 'wb') as f:
                    f.write(template_bytes)
                
                # Substituir variáveis
                doc = substituir_variaveis_word(temp_path, variaveis)
                
                # Salvar em memória
                output = io.BytesIO()
                doc.save(output)
                output.seek(0)
                
                # Remover arquivo temporário
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                
                # Gerar nome do arquivo
                filename = f"Proposta_Solar_{projeto.id}_{projeto.nome_cliente.replace(' ', '_')}.docx"
                
                # Retornar arquivo
                return send_file(
                    output,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
                
            except Exception as e:
                logger.error(f"Erro ao processar template Word: {str(e)}")
                flash(f'Erro ao processar template: {str(e)}', 'error')
                return redirect(request.url)
        
        # GET - Mostrar página de upload
        return render_template('energia_solar/upload_template_word.html', projeto=projeto)
    
    except Exception as e:
        # Captura qualquer erro não tratado
        logger.error(f"Erro geral em gerar_documento_word: {str(e)}")
        flash(f'Erro ao acessar funcionalidade Word: {str(e)}', 'error')
        return redirect(url_for('energia_solar.projeto_visualizar', projeto_id=projeto_id))
