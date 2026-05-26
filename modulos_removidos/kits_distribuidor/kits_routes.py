# -*- coding: utf-8 -*-
"""
Routes para Kits Fotovoltaicos do Distribuidor
==============================================

Rotas para integração com API, listagem e gerenciamento de kits.

Autor: JSP Soluções
Data: 2026
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.extensoes import db
from app.kits_distribuidor.kits_model import KitFotovoltaico
from app.services.api_distribuidor import get_api_service, DistribuidorAPIError
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Blueprint
kits_bp = Blueprint('kits_distribuidor', __name__, template_folder='templates')


@kits_bp.route('/')
@kits_bp.route('/listar')
def listar():
    """Lista kits fotovoltaicos do distribuidor."""
    # Parâmetros de filtro
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    busca = request.args.get('busca', '').strip()
    categoria = request.args.get('categoria', '').strip()
    potencia_min = request.args.get('potencia_min', type=float)
    potencia_max = request.args.get('potencia_max', type=float)
    
    # Query base
    query = KitFotovoltaico.query.filter_by(ativo=True)
    
    # Aplicar filtros
    if busca:
        query = query.filter(
            db.or_(
                KitFotovoltaico.nome.ilike(f'%{busca}%'),
                KitFotovoltaico.codigo.ilike(f'%{busca}%'),
                KitFotovoltaico.fabricante_modulo.ilike(f'%{busca}%'),
                KitFotovoltaico.fabricante_inversor.ilike(f'%{busca}%')
            )
        )
    
    if categoria:
        query = query.filter_by(categoria=categoria)
    
    if potencia_min:
        query = query.filter(KitFotovoltaico.potencia >= potencia_min)
    
    if potencia_max:
        query = query.filter(KitFotovoltaico.potencia <= potencia_max)
    
    # Paginação
    kits = query.order_by(KitFotovoltaico.potencia.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Estatísticas
    total_kits = KitFotovoltaico.query.filter_by(ativo=True).count()
    disponiveis = KitFotovoltaico.query.filter_by(ativo=True, disponivel=True).count()
    
    return render_template(
        'kits_distribuidor/listar.html',
        kits=kits,
        total_kits=total_kits,
        disponiveis=disponiveis,
        busca=busca,
        categoria=categoria,
        potencia_min=potencia_min,
        potencia_max=potencia_max
    )


@kits_bp.route('/sincronizar', methods=['POST'])
def sincronizar():
    """Sincroniza kits da API do distribuidor."""
    try:
        api = get_api_service()
        
        # Parâmetros de sincronização
        page = 1
        total_sincronizados = 0
        total_novos = 0
        total_atualizados = 0
        
        while True:
            try:
                # Busca kits da API
                response = api.listar_kits(page=page, per_page=100)
                kits_api = response.get('kits', [])
                
                if not kits_api:
                    break
                
                # Processa cada kit
                for kit_data in kits_api:
                    kit = KitFotovoltaico.criar_ou_atualizar_da_api(kit_data)
                    
                    if kit.id:
                        total_atualizados += 1
                    else:
                        total_novos += 1
                    
                    total_sincronizados += 1
                
                db.session.commit()
                
                # Verifica se há mais páginas
                if page >= response.get('pages', 1):
                    break
                
                page += 1
                
            except DistribuidorAPIError as e:
                logger.error(f"Erro na página {page}: {e}")
                break
        
        flash(
            f'✅ Sincronização concluída! '
            f'{total_sincronizados} kits sincronizados '
            f'({total_novos} novos, {total_atualizados} atualizados)',
            'success'
        )
        
    except DistribuidorAPIError as e:
        flash(f'❌ Erro ao sincronizar: {str(e)}', 'danger')
        logger.error(f"Erro na sincronização: {e}")
    except Exception as e:
        flash(f'❌ Erro inesperado: {str(e)}', 'danger')
        logger.exception("Erro inesperado na sincronização")
        db.session.rollback()
    
    return redirect(url_for('kits_distribuidor.listar'))


@kits_bp.route('/sincronizar-unico/<kit_id_api>')
def sincronizar_unico(kit_id_api):
    """Sincroniza um kit específico da API."""
    try:
        api = get_api_service()
        kit_data = api.buscar_kit(kit_id_api)
        
        kit = KitFotovoltaico.criar_ou_atualizar_da_api(kit_data)
        db.session.commit()
        
        flash(f'✅ Kit "{kit.nome}" sincronizado com sucesso!', 'success')
        
    except DistribuidorAPIError as e:
        flash(f'❌ Erro ao sincronizar kit: {str(e)}', 'danger')
    except Exception as e:
        flash(f'❌ Erro inesperado: {str(e)}', 'danger')
        db.session.rollback()
    
    return redirect(url_for('kits_distribuidor.listar'))


@kits_bp.route('/visualizar/<int:id>')
def visualizar(id):
    """Visualiza detalhes de um kit."""
    kit = KitFotovoltaico.query.get_or_404(id)
    return render_template('kits_distribuidor/visualizar.html', kit=kit)


@kits_bp.route('/testar-api')
def testar_api():
    """Testa conexão com a API do distribuidor."""
    try:
        api = get_api_service()
        
        if api.testar_conexao():
            flash('✅ Conexão com API do distribuidor funcionando!', 'success')
        else:
            flash('❌ Falha ao conectar com API do distribuidor', 'danger')
            
    except DistribuidorAPIError as e:
        flash(f'❌ Erro na API: {str(e)}', 'danger')
    except Exception as e:
        flash(f'❌ Erro inesperado: {str(e)}', 'danger')
    
    return redirect(url_for('kits_distribuidor.listar'))


@kits_bp.route('/api/kits', methods=['GET'])
def api_listar_kits():
    """API JSON para listar kits."""
    kits = KitFotovoltaico.query.filter_by(ativo=True, disponivel=True).all()
    return jsonify([kit.to_dict() for kit in kits])


@kits_bp.route('/api/kits/<int:id>', methods=['GET'])
def api_buscar_kit(id):
    """API JSON para buscar um kit específico."""
    kit = KitFotovoltaico.query.get_or_404(id)
    return jsonify(kit.to_dict())


@kits_bp.route('/api/categorias', methods=['GET'])
def api_categorias():
    """Retorna lista de categorias disponíveis."""
    categorias = db.session.query(KitFotovoltaico.categoria).filter(
        KitFotovoltaico.categoria.isnot(None),
        KitFotovoltaico.ativo == True
    ).distinct().all()
    
    return jsonify([cat[0] for cat in categorias if cat[0]])
