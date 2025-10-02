from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from .modelos import FormacaoPrecoConfig, calcular_ponto_equilibrio
from aplicacao.extensoes import db
import json

formacao_preco_bp = Blueprint('formacao_preco', __name__, url_prefix='/financeiro/formacao-preco')

@formacao_preco_bp.route('/')
def index():
    """Página inicial - redireciona para configurações"""
    return redirect(url_for('formacao_preco.configuracoes'))

@formacao_preco_bp.route('/configuracoes', methods=['GET', 'POST'])
def configuracoes():
    """Tela para configurar custos fixos, variáveis e parâmetros"""
    config = FormacaoPrecoConfig.get_or_create_default()
    
    if request.method == 'POST':
        try:
            # Custos fixos (JSON)
            custos_fixos_json = request.form.get('custos_fixos', '{}')
            custos_fixos = json.loads(custos_fixos_json)
            
            # Outros parâmetros
            config.custos_fixos_mensais = custos_fixos
            config.custo_variavel_hora = float(request.form.get('custo_variavel_hora', 0))
            config.preco_medio_praticado = float(request.form.get('preco_medio_praticado', 0))
            config.margem_desejada = float(request.form.get('margem_desejada', 0))
            config.horas_trabalho_mes = int(request.form.get('horas_trabalho_mes', 160))
            
            db.session.commit()
            flash('Configurações salvas com sucesso!', 'success')
            
            return redirect(url_for('formacao_preco.calculadora'))
            
        except (ValueError, json.JSONDecodeError) as e:
            flash(f'Erro ao salvar configurações: {str(e)}', 'error')
    
    return render_template('formacao_preco/configuracoes.html', config=config)

@formacao_preco_bp.route('/calculadora')
def calculadora():
    """Tela da calculadora - mostra custos por hora/dia"""
    config = FormacaoPrecoConfig.get_or_create_default()
    
    # Calcular métricas
    total_custos_fixos = sum(config.custos_fixos_mensais.values()) if config.custos_fixos_mensais else 0
    custo_fixo_hora = total_custos_fixos / config.horas_trabalho_mes if config.horas_trabalho_mes > 0 else 0
    custo_total_hora = custo_fixo_hora + config.custo_variavel_hora
    custo_dia = custo_total_hora * 8  # Assumindo 8h/dia
    
    # Calcular margem atual
    margem_atual = 0
    if config.preco_medio_praticado > 0 and custo_total_hora > 0:
        margem_atual = ((config.preco_medio_praticado - custo_total_hora) / config.preco_medio_praticado) * 100
    
    dados_calculadora = {
        'total_custos_fixos': total_custos_fixos,
        'custo_fixo_hora': custo_fixo_hora,
        'custo_total_hora': custo_total_hora,
        'custo_dia': custo_dia,
        'margem_atual': margem_atual
    }
    
    return render_template('formacao_preco/calculadora.html', 
                         config=config, 
                         dados=dados_calculadora)

@formacao_preco_bp.route('/ponto-equilibrio')
def ponto_equilibrio():
    """Tela do ponto de equilíbrio"""
    config = FormacaoPrecoConfig.get_or_create_default()
    resultado = calcular_ponto_equilibrio(config)
    
    return render_template('formacao_preco/ponto_equilibrio.html', 
                         config=config, 
                         resultado=resultado)

@formacao_preco_bp.route('/api/calcular', methods=['POST'])
def api_calcular():
    """API para recalcular em tempo real"""
    try:
        data = request.get_json()
        
        # Criar config temporário com os dados enviados
        temp_config = FormacaoPrecoConfig()
        temp_config.custos_fixos_mensais = data.get('custos_fixos', {})
        temp_config.custo_variavel_hora = float(data.get('custo_variavel_hora', 0))
        temp_config.preco_medio_praticado = float(data.get('preco_medio_praticado', 0))
        temp_config.margem_desejada = float(data.get('margem_desejada', 0))
        temp_config.horas_trabalho_mes = int(data.get('horas_trabalho_mes', 160))
        
        resultado = calcular_ponto_equilibrio(temp_config)
        
        return jsonify({
            'success': True,
            'resultado': resultado
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@formacao_preco_bp.route('/api/custos-fixos', methods=['POST'])
def api_adicionar_custo_fixo():
    """API para adicionar/remover custos fixos dinamicamente"""
    try:
        config = FormacaoPrecoConfig.get_or_create_default()
        data = request.get_json()
        
        acao = data.get('acao')  # 'adicionar' ou 'remover'
        nome = data.get('nome')
        valor = data.get('valor', 0)
        
        if not config.custos_fixos_mensais:
            config.custos_fixos_mensais = {}
        
        if acao == 'adicionar':
            config.custos_fixos_mensais[nome] = float(valor)
        elif acao == 'remover':
            config.custos_fixos_mensais.pop(nome, None)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'custos_fixos': config.custos_fixos_mensais,
            'total': sum(config.custos_fixos_mensais.values())
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
