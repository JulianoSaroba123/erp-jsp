# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Script de Importação de Dados do Módulo Energia Solar
======================================================================
Importa dados previamente exportados em formato JSON

Uso:
    python importar_energia_solar.py [arquivo.json]
    
    Se não especificar arquivo, usa o mais recente em exports/
"""

import os
import sys
import json
from datetime import datetime
from decimal import Decimal

def configurar_app():
    """Configura o Flask app e banco de dados"""
    from app.app import create_app
    from app.extensoes import db
    
    app = create_app()
    app.app_context().push()
    
    return app, db

def converter_de_json(valor):
    """Converte valores JSON de volta para tipos Python"""
    if isinstance(valor, str):
        # Tentar converter strings ISO para datetime
        try:
            if 'T' in valor or '-' in valor:
                return datetime.fromisoformat(valor.replace('Z', '+00:00'))
        except:
            pass
    return valor

def limpar_tabelas(db, limpar_tudo=False):
    """Limpa tabelas antes da importação"""
    print("\n🗑️  LIMPANDO DADOS EXISTENTES...")
    
    try:
        from app.energia_solar.energia_solar_model import CalculoEnergiaSolar
        from app.energia_solar.catalogo_model import ProjetoSolar, KitSolar, PlacaSolar, InversorSolar
        from app.energia_solar.custo_fixo_model import CustoPadraoSolar
        from app.energia_solar.orcamento_model import OrcamentoItem
        
        if limpar_tudo:
            # Limpa TODOS os dados
            OrcamentoItem.query.delete()
            print("   ✅ Itens de orçamento limpos")
            
            CalculoEnergiaSolar.query.delete()
            print("   ✅ Cálculos limpos")
            
            ProjetoSolar.query.delete()
            print("   ✅ Projetos limpos")
            
            KitSolar.query.delete()
            print("   ✅ Kits limpos")
            
            PlacaSolar.query.delete()
            print("   ✅ Placas limpas")
            
            InversorSolar.query.delete()
            print("   ✅ Inversores limpos")
            
            CustoPadraoSolar.query.delete()
            print("   ✅ Custos padrão limpos")
            
            db.session.commit()
            print("\n   ✅ Todas as tabelas limpas!")
        else:
            print("   ℹ️  Modo incremental - mantendo dados existentes")
            
    except Exception as e:
        print(f"   ⚠️  Erro ao limpar: {e}")
        db.session.rollback()

def importar_calculos(dados, db):
    """Importa cálculos de energia solar"""
    from app.energia_solar.energia_solar_model import CalculoEnergiaSolar
    
    calculos_list = dados.get('calculos_energia_solar', [])
    if not calculos_list:
        return 0
    
    print(f"\n🔋 Importando {len(calculos_list)} Cálculos...")
    importados = 0
    
    for calc_data in calculos_list:
        try:
            # Verificar se já existe
            calc_id = calc_data.get('id')
            calc_existente = CalculoEnergiaSolar.query.get(calc_id) if calc_id else None
            
            if calc_existente:
                print(f"   ⚠️  Cálculo ID {calc_id} já existe - pulando")
                continue
            
            # Criar novo cálculo
            calc = CalculoEnergiaSolar()
            for key, value in calc_data.items():
                if hasattr(calc, key) and key != 'id':
                    setattr(calc, key, converter_de_json(value))
            
            db.session.add(calc)
            importados += 1
            
        except Exception as e:
            print(f"   ❌ Erro ao importar cálculo: {e}")
            continue
    
    db.session.commit()
    print(f"   ✅ {importados} cálculos importados")
    return importados

def importar_projetos(dados, db):
    """Importa projetos solares"""
    from app.energia_solar.catalogo_model import ProjetoSolar
    
    projetos_list = dados.get('projetos_solares', [])
    if not projetos_list:
        return 0
    
    print(f"\n☀️  Importando {len(projetos_list)} Projetos...")
    importados = 0
    
    for proj_data in projetos_list:
        try:
            proj_id = proj_data.get('id')
            proj_existente = ProjetoSolar.query.get(proj_id) if proj_id else None
            
            if proj_existente:
                print(f"   ⚠️  Projeto ID {proj_id} já existe - pulando")
                continue
            
            projeto = ProjetoSolar()
            for key, value in proj_data.items():
                if hasattr(projeto, key) and key != 'id':
                    setattr(projeto, key, converter_de_json(value))
            
            db.session.add(projeto)
            importados += 1
            
        except Exception as e:
            print(f"   ❌ Erro ao importar projeto: {e}")
            continue
    
    db.session.commit()
    print(f"   ✅ {importados} projetos importados")
    return importados

def importar_kits(dados, db):
    """Importa kits solares"""
    from app.energia_solar.catalogo_model import KitSolar
    
    kits_list = dados.get('kits_solares', [])
    if not kits_list:
        return 0
    
    print(f"\n📦 Importando {len(kits_list)} Kits...")
    importados = 0
    
    for kit_data in kits_list:
        try:
            kit_id = kit_data.get('id')
            kit_existente = KitSolar.query.get(kit_id) if kit_id else None
            
            if kit_existente:
                print(f"   ⚠️  Kit ID {kit_id} já existe - pulando")
                continue
            
            kit = KitSolar()
            for key, value in kit_data.items():
                if hasattr(kit, key) and key != 'id':
                    setattr(kit, key, converter_de_json(value))
            
            db.session.add(kit)
            importados += 1
            
        except Exception as e:
            print(f"   ❌ Erro ao importar kit: {e}")
            continue
    
    db.session.commit()
    print(f"   ✅ {importados} kits importados")
    return importados

def importar_placas(dados, db):
    """Importa placas solares"""
    from app.energia_solar.catalogo_model import PlacaSolar
    
    placas_list = dados.get('placas_solares', [])
    if not placas_list:
        return 0
    
    print(f"\n🔆 Importando {len(placas_list)} Placas...")
    importados = 0
    
    for placa_data in placas_list:
        try:
            placa_id = placa_data.get('id')
            placa_existente = PlacaSolar.query.get(placa_id) if placa_id else None
            
            if placa_existente:
                print(f"   ⚠️  Placa ID {placa_id} já existe - pulando")
                continue
            
            placa = PlacaSolar()
            for key, value in placa_data.items():
                if hasattr(placa, key) and key != 'id':
                    setattr(placa, key, converter_de_json(value))
            
            db.session.add(placa)
            importados += 1
            
        except Exception as e:
            print(f"   ❌ Erro ao importar placa: {e}")
            continue
    
    db.session.commit()
    print(f"   ✅ {importados} placas importadas")
    return importados

def importar_inversores(dados, db):
    """Importa inversores solares"""
    from app.energia_solar.catalogo_model import InversorSolar
    
    inversores_list = dados.get('inversores_solares', [])
    if not inversores_list:
        return 0
    
    print(f"\n⚡ Importando {len(inversores_list)} Inversores...")
    importados = 0
    
    for inv_data in inversores_list:
        try:
            inv_id = inv_data.get('id')
            inv_existente = InversorSolar.query.get(inv_id) if inv_id else None
            
            if inv_existente:
                print(f"   ⚠️  Inversor ID {inv_id} já existe - pulando")
                continue
            
            inversor = InversorSolar()
            for key, value in inv_data.items():
                if hasattr(inversor, key) and key != 'id':
                    setattr(inversor, key, converter_de_json(value))
            
            db.session.add(inversor)
            importados += 1
            
        except Exception as e:
            print(f"   ❌ Erro ao importar inversor: {e}")
            continue
    
    db.session.commit()
    print(f"   ✅ {importados} inversores importados")
    return importados

def importar_custos_padrao(dados, db):
    """Importa custos padrão"""
    from app.energia_solar.custo_fixo_model import CustoPadraoSolar
    
    custos_list = dados.get('custos_padrao', [])
    if not custos_list:
        return 0
    
    print(f"\n💰 Importando {len(custos_list)} Custos Padrão...")
    importados = 0
    
    for custo_data in custos_list:
        try:
            custo_id = custo_data.get('id')
            custo_existente = CustoPadraoSolar.query.get(custo_id) if custo_id else None
            
            if custo_existente:
                print(f"   ⚠️  Custo ID {custo_id} já existe - pulando")
                continue
            
            custo = CustoPadraoSolar()
            for key, value in custo_data.items():
                if hasattr(custo, key) and key != 'id':
                    # Converter para Decimal se necessário
                    if key in ['quantidade', 'valor_unitario', 'lucro_percentual']:
                        value = Decimal(str(value)) if value is not None else None
                    setattr(custo, key, converter_de_json(value))
            
            db.session.add(custo)
            importados += 1
            
        except Exception as e:
            print(f"   ❌ Erro ao importar custo: {e}")
            continue
    
    db.session.commit()
    print(f"   ✅ {importados} custos padrão importados")
    return importados

def importar_orcamento_itens(dados, db):
    """Importa itens de orçamento"""
    from app.energia_solar.orcamento_model import OrcamentoItem
    
    itens_list = dados.get('orcamento_itens', [])
    if not itens_list:
        return 0
    
    print(f"\n📋 Importando {len(itens_list)} Itens de Orçamento...")
    importados = 0
    
    for item_data in itens_list:
        try:
            item_id = item_data.get('id')
            item_existente = OrcamentoItem.query.get(item_id) if item_id else None
            
            if item_existente:
                print(f"   ⚠️  Item ID {item_id} já existe - pulando")
                continue
            
            item = OrcamentoItem()
            for key, value in item_data.items():
                if hasattr(item, key) and key != 'id':
                    # Converter para Decimal se necessário
                    if key in ['quantidade', 'preco_unitario', 'preco_total', 'lucro_percentual', 'faturamento']:
                        value = Decimal(str(value)) if value is not None else None
                    setattr(item, key, converter_de_json(value))
            
            db.session.add(item)
            importados += 1
            
        except Exception as e:
            print(f"   ❌ Erro ao importar item: {e}")
            continue
    
    db.session.commit()
    print(f"   ✅ {importados} itens de orçamento importados")
    return importados

def importar_energia_solar(arquivo_json=None, limpar_antes=False):
    """Função principal de importação"""
    
    print("=" * 80)
    print("📥 IMPORTAÇÃO DE DADOS - MÓDULO ENERGIA SOLAR")
    print("=" * 80)
    
    # Determinar arquivo de importação
    if not arquivo_json:
        # Buscar arquivo mais recente em exports/
        exports_dir = os.path.join(os.path.dirname(__file__), 'exports')
        if not os.path.exists(exports_dir):
            print("❌ Pasta exports/ não encontrada!")
            return
        
        arquivos = [f for f in os.listdir(exports_dir) if f.startswith('energia_solar_export_') and f.endswith('.json')]
        if not arquivos:
            print("❌ Nenhum arquivo de exportação encontrado em exports/")
            return
        
        # Ordenar por data (mais recente primeiro)
        arquivos.sort(reverse=True)
        arquivo_json = os.path.join(exports_dir, arquivos[0])
        print(f"📂 Usando arquivo mais recente: {arquivos[0]}")
    
    # Ler arquivo JSON
    print(f"\n📖 Lendo arquivo: {arquivo_json}")
    try:
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        print(f"   ✅ Arquivo carregado com sucesso!")
    except Exception as e:
        print(f"   ❌ Erro ao ler arquivo: {e}")
        return
    
    # Configurar app
    print("\n🔧 Configurando aplicação...")
    app, db = configurar_app()
    print("   ✅ App configurado!")
    
    # Limpar dados se solicitado
    if limpar_antes:
        resposta = input("\n⚠️  ATENÇÃO: Deseja LIMPAR TODOS os dados existentes antes da importação? (s/N): ")
        if resposta.lower() == 's':
            limpar_tabelas(db, limpar_tudo=True)
        else:
            print("   ℹ️  Importação incremental - mantendo dados existentes")
    
    # Importar dados (ordem correta devido a relacionamentos)
    print("\n" + "=" * 80)
    print("📥 INICIANDO IMPORTAÇÃO")
    print("=" * 80)
    
    estatisticas = {}
    
    # 1. Placas (não tem dependências)
    estatisticas['placas'] = importar_placas(dados, db)
    
    # 2. Inversores (não tem dependências)
    estatisticas['inversores'] = importar_inversores(dados, db)
    
    # 3. Kits (depende de placas e inversores)
    estatisticas['kits'] = importar_kits(dados, db)
    
    # 4. Projetos (não tem dependências externas)
    estatisticas['projetos'] = importar_projetos(dados, db)
    
    # 5. Cálculos
    estatisticas['calculos'] = importar_calculos(dados, db)
    
    # 6. Custos Padrão
    estatisticas['custos'] = importar_custos_padrao(dados, db)
    
    # 7. Itens de Orçamento (depende de projetos)
    estatisticas['itens'] = importar_orcamento_itens(dados, db)
    
    # Resumo
    print("\n" + "=" * 80)
    print("📊 RESUMO DA IMPORTAÇÃO")
    print("=" * 80)
    print(f"📂 Arquivo: {os.path.basename(arquivo_json)}")
    print(f"\n📈 Registros Importados:")
    print(f"   • Cálculos: {estatisticas.get('calculos', 0)}")
    print(f"   • Projetos: {estatisticas.get('projetos', 0)}")
    print(f"   • Kits: {estatisticas.get('kits', 0)}")
    print(f"   • Placas: {estatisticas.get('placas', 0)}")
    print(f"   • Inversores: {estatisticas.get('inversores', 0)}")
    print(f"   • Custos Padrão: {estatisticas.get('custos', 0)}")
    print(f"   • Itens Orçamento: {estatisticas.get('itens', 0)}")
    
    total = sum(estatisticas.values())
    print(f"\n✅ TOTAL: {total} registros importados com sucesso!")
    print("=" * 80)
    print("🎉 Importação concluída!")

if __name__ == '__main__':
    # Verificar argumentos da linha de comando
    arquivo = None
    limpar = False
    
    if len(sys.argv) > 1:
        arquivo = sys.argv[1]
        if not os.path.exists(arquivo):
            print(f"❌ Arquivo não encontrado: {arquivo}")
            sys.exit(1)
    
    if '--limpar' in sys.argv or '-l' in sys.argv:
        limpar = True
    
    # Executar importação
    importar_energia_solar(arquivo, limpar_antes=limpar)
