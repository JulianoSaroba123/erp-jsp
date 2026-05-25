# -*- coding: utf-8 -*-
"""
Script de Exportação de Dados - Módulo Energia Solar
=====================================================

Exporta todos os dados do módulo de Energia Solar em formato JSON.

Tabelas exportadas:
- Cálculos de Energia Solar
- Projetos Solares
- Kits Solares
- Placas Solares
- Inversores Solares
- Custos Padrão
- Itens de Orçamento

Autor: JSP Soluções
Data: 2026
"""

import os
import sys
import json
from datetime import datetime
from decimal import Decimal

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.app import create_app
from app.extensoes import db


def converter_para_json(obj):
    """Converte objetos não serializáveis para JSON"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    return str(obj)


def exportar_energia_solar():
    """Exporta todos os dados do módulo de Energia Solar"""
    
    print("=" * 80)
    print("📊 EXPORTAÇÃO DE DADOS - MÓDULO ENERGIA SOLAR")
    print("=" * 80)
    
    # Criar app
    app = create_app()
    
    with app.app_context():
        dados_exportados = {
            'data_exportacao': datetime.now().isoformat(),
            'versao': '3.0',
            'modulo': 'Energia Solar'
        }
        
        # 1. CÁLCULOS DE ENERGIA SOLAR
        print("\n🔋 Exportando Cálculos de Energia Solar...")
        try:
            from app.energia_solar.energia_solar_model import CalculoEnergiaSolar
            calculos = CalculoEnergiaSolar.query.all()
            
            calculos_list = []
            for calculo in calculos:
                calc_dict = {
                    'id': calculo.id,
                    'numero_projeto': calculo.numero_projeto,
                    'cliente_id': calculo.cliente_id,
                    'nome_cliente': calculo.nome_cliente,
                    'local_instalacao': calculo.local_instalacao,
                    'consumo_mensal': float(calculo.consumo_mensal) if calculo.consumo_mensal else 0,
                    'consumo_anual': float(calculo.consumo_anual) if calculo.consumo_anual else 0,
                    'tarifa_energia': float(calculo.tarifa_energia) if calculo.tarifa_energia else 0,
                    'cidade': calculo.cidade,
                    'estado': calculo.estado,
                    'latitude': float(calculo.latitude) if calculo.latitude else None,
                    'longitude': float(calculo.longitude) if calculo.longitude else None,
                    'irradiacao_media': float(calculo.irradiacao_media) if calculo.irradiacao_media else None
                }
                
                # Adiciona outros campos se existirem
                if hasattr(calculo, 'data_criacao'):
                    calc_dict['data_criacao'] = calculo.data_criacao.isoformat() if calculo.data_criacao else None
                if hasattr(calculo, 'data_atualizacao'):
                    calc_dict['data_atualizacao'] = calculo.data_atualizacao.isoformat() if calculo.data_atualizacao else None
                
                calculos_list.append(calc_dict)
            
            dados_exportados['calculos_energia_solar'] = calculos_list
            print(f"   ✅ {len(calculos_list)} cálculos exportados")
        except Exception as e:
            print(f"   ⚠️  Erro ao exportar cálculos: {e}")
            dados_exportados['calculos_energia_solar'] = []
        
        # 2. PROJETOS SOLARES
        print("\n☀️  Exportando Projetos Solares...")
        try:
            from app.energia_solar.catalogo_model import ProjetoSolar
            projetos = ProjetoSolar.query.all()
            
            projetos_list = []
            for projeto in projetos:
                proj_dict = {
                    'id': projeto.id,
                    'numero': projeto.numero if hasattr(projeto, 'numero') else None,
                    'cliente_id': projeto.cliente_id if hasattr(projeto, 'cliente_id') else None,
                    'status': projeto.status if hasattr(projeto, 'status') else None,
                    'potencia_sistema': float(projeto.potencia_sistema) if hasattr(projeto, 'potencia_sistema') and projeto.potencia_sistema else None,
                    'valor_total': float(projeto.valor_total) if hasattr(projeto, 'valor_total') and projeto.valor_total else None,
                }
                
                if hasattr(projeto, 'data_criacao'):
                    proj_dict['data_criacao'] = projeto.data_criacao.isoformat() if projeto.data_criacao else None
                    
                projetos_list.append(proj_dict)
            
            dados_exportados['projetos_solares'] = projetos_list
            print(f"   ✅ {len(projetos_list)} projetos exportados")
        except Exception as e:
            print(f"   ⚠️  Erro ao exportar projetos: {e}")
            dados_exportados['projetos_solares'] = []
        
        # 3. KITS SOLARES
        print("\n📦 Exportando Kits Solares...")
        try:
            from app.energia_solar.catalogo_model import KitSolar
            kits = KitSolar.query.filter_by(ativo=True).all()
            
            kits_list = []
            for kit in kits:
                kits_list.append({
                    'id': kit.id,
                    'fabricante': kit.fabricante,
                    'descricao': kit.descricao,
                    'outras_informacoes': kit.outras_informacoes,
                    'potencia_kwp': float(kit.potencia_kwp) if kit.potencia_kwp else 0,
                    'preco': float(kit.preco) if kit.preco else 0,
                    'qtd_placas': kit.qtd_placas,
                    'qtd_inversores': kit.qtd_inversores,
                    'placa_id': kit.placa_id,
                    'inversor_id': kit.inversor_id,
                    'data_cadastro': kit.data_cadastro.isoformat() if kit.data_cadastro else None
                })
            
            dados_exportados['kits_solares'] = kits_list
            print(f"   ✅ {len(kits_list)} kits exportados")
        except Exception as e:
            print(f"   ⚠️  Erro ao exportar kits: {e}")
            dados_exportados['kits_solares'] = []
        
        # 4. PLACAS SOLARES
        print("\n🔆 Exportando Placas Solares...")
        try:
            from app.energia_solar.catalogo_model import PlacaSolar
            placas = PlacaSolar.query.filter_by(ativo=True).all()
            
            placas_list = []
            for placa in placas:
                placas_list.append({
                    'id': placa.id,
                    'modelo': placa.modelo,
                    'fabricante': placa.fabricante,
                    'potencia': float(placa.potencia) if placa.potencia else 0,
                    'comprimento': float(placa.comprimento) if placa.comprimento else None,
                    'largura': float(placa.largura) if placa.largura else None,
                    'espessura': float(placa.espessura) if placa.espessura else None,
                    'peso': float(placa.peso) if placa.peso else None,
                    'num_celulas': placa.num_celulas,
                    'eficiencia': float(placa.eficiencia) if placa.eficiencia else None,
                    'preco': float(placa.preco) if hasattr(placa, 'preco') and placa.preco else None,
                    'data_cadastro': placa.data_cadastro.isoformat() if hasattr(placa, 'data_cadastro') and placa.data_cadastro else None
                })
            
            dados_exportados['placas_solares'] = placas_list
            print(f"   ✅ {len(placas_list)} placas exportadas")
        except Exception as e:
            print(f"   ⚠️  Erro ao exportar placas: {e}")
            dados_exportados['placas_solares'] = []
        
        # 5. INVERSORES SOLARES
        print("\n⚡ Exportando Inversores Solares...")
        try:
            from app.energia_solar.catalogo_model import InversorSolar
            inversores = InversorSolar.query.filter_by(ativo=True).all()
            
            # Usa o método to_dict() do modelo
            inversores_list = [inv.to_dict() for inv in inversores]
            
            dados_exportados['inversores_solares'] = inversores_list
            print(f"   ✅ {len(inversores_list)} inversores exportados")
        except Exception as e:
            print(f"   ⚠️  Erro ao exportar inversores: {e}")
            dados_exportados['inversores_solares'] = []
        
        # 6. CUSTOS PADRÃO SOLAR
        print("\n💰 Exportando Custos Padrão...")
        try:
            from app.energia_solar.custo_fixo_model import CustoPadraoSolar
            custos = CustoPadraoSolar.query.filter_by(ativo=True).all()
            
            custos_list = []
            for custo in custos:
                custos_list.append({
                    'id': custo.id,
                    'descricao': custo.descricao,
                    'unidade': custo.unidade,
                    'quantidade': float(custo.quantidade) if custo.quantidade else 0,
                    'valor_unitario': float(custo.valor_unitario) if custo.valor_unitario else 0,
                    'lucro_percentual': float(custo.lucro_percentual) if custo.lucro_percentual else 0,
                    'faturamento': custo.faturamento,
                    'tipo': custo.tipo,
                    'categoria': custo.categoria,
                    'aplicar_automaticamente': custo.aplicar_automaticamente,
                    'observacoes': custo.observacoes
                })
            
            dados_exportados['custos_padrao'] = custos_list
            print(f"   ✅ {len(custos_list)} custos padrão exportados")
        except Exception as e:
            print(f"   ⚠️  Erro ao exportar custos padrão: {e}")
            dados_exportados['custos_padrao'] = []
        
        # 7. ITENS DE ORÇAMENTO
        print("\n📋 Exportando Itens de Orçamento...")
        try:
            from app.energia_solar.orcamento_model import OrcamentoItem
            itens = OrcamentoItem.query.all()
            
            # Usa o método to_dict() do modelo para evitar erros de tipo
            itens_list = [item.to_dict() for item in itens]
            
            dados_exportados['orcamento_itens'] = itens_list
            print(f"   ✅ {len(itens_list)} itens de orçamento exportados")
        except Exception as e:
            print(f"   ⚠️  Erro ao exportar itens de orçamento: {e}")
            dados_exportados['orcamento_itens'] = []
        
        # SALVAR ARQUIVO
        print("\n💾 Salvando arquivo de exportação...")
        
        # Criar pasta exports se não existir
        exports_dir = os.path.join(os.path.dirname(__file__), 'exports')
        os.makedirs(exports_dir, exist_ok=True)
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'energia_solar_export_{timestamp}.json'
        filepath = os.path.join(exports_dir, filename)
        
        # Salvar JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dados_exportados, f, ensure_ascii=False, indent=2, default=converter_para_json)
        
        print(f"   ✅ Arquivo salvo: {filepath}")
        
        # RESUMO
        print("\n" + "=" * 80)
        print("📊 RESUMO DA EXPORTAÇÃO")
        print("=" * 80)
        print(f"📁 Arquivo: {filename}")
        print(f"📍 Local: {filepath}")
        print(f"\n📈 Estatísticas:")
        print(f"   • Cálculos: {len(dados_exportados.get('calculos_energia_solar', []))}")
        print(f"   • Projetos: {len(dados_exportados.get('projetos_solares', []))}")
        print(f"   • Kits: {len(dados_exportados.get('kits_solares', []))}")
        print(f"   • Placas: {len(dados_exportados.get('placas_solares', []))}")
        print(f"   • Inversores: {len(dados_exportados.get('inversores_solares', []))}")
        print(f"   • Custos Padrão: {len(dados_exportados.get('custos_padrao', []))}")
        print(f"   • Itens Orçamento: {len(dados_exportados.get('orcamento_itens', []))}")
        
        total_registros = sum([
            len(dados_exportados.get('calculos_energia_solar', [])),
            len(dados_exportados.get('projetos_solares', [])),
            len(dados_exportados.get('kits_solares', [])),
            len(dados_exportados.get('placas_solares', [])),
            len(dados_exportados.get('inversores_solares', [])),
            len(dados_exportados.get('custos_padrao', [])),
            len(dados_exportados.get('orcamento_itens', []))
        ])
        
        print(f"\n✅ TOTAL: {total_registros} registros exportados com sucesso!")
        print("=" * 80)
        
        return filepath


if __name__ == '__main__':
    try:
        filepath = exportar_energia_solar()
        print(f"\n🎉 Exportação concluída!")
        print(f"📂 Arquivo disponível em: {filepath}")
        
    except Exception as e:
        print(f"\n❌ Erro durante a exportação: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
