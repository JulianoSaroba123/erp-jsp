"""
Rotas para o módulo de Cálculo de Energia Solar
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensoes import db
from app.energia_solar.energia_solar_model import CalculoEnergiaSolar
from app.cliente.cliente_model import Cliente
from datetime import datetime
import math

energia_solar_bp = Blueprint('energia_solar', __name__, url_prefix='/energia-solar',
                             template_folder='templates')


@energia_solar_bp.route('/')
@login_required
def dashboard():
    """Dashboard do módulo de Energia Solar"""
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
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    calculos = CalculoEnergiaSolar.query.order_by(
        CalculoEnergiaSolar.data_calculo.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('energia_solar/listar.html', calculos=calculos)


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
