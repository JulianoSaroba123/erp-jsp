"""
Script para gerar parcelas de proposta usando ORM (funciona em SQLite e PostgreSQL).
"""
import os
import sys
from datetime import date, timedelta
from decimal import Decimal

# Forçar UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ['FLASK_SKIP_DOTENV'] = '1'

from app import create_app
from app.extensoes import db
from app.proposta.proposta_model import Proposta, ParcelaProposta

def gerar_parcelas_proposta(proposta_id=15):
    """Gera parcelas para uma proposta específica usando ORM."""
    app = create_app()
    with app.app_context():
        try:
            print("="*80)
            print(f"🔧 GERANDO PARCELAS PARA PROPOSTA {proposta_id}")
            print("="*80)
            
            # Buscar proposta usando ORM
            proposta = Proposta.query.get(proposta_id)
            
            if not proposta:
                print(f"❌ Proposta {proposta_id} não encontrada!")
                return False
            
            print(f"\n📋 Proposta: {proposta.codigo}")
            print(f"💰 Valor Total: R$ {proposta.valor_total}")
            print(f"💳 Forma Pagamento: {proposta.forma_pagamento}")
            print(f"🏦 Entrada: {proposta.entrada_percentual}%")
            print(f"📊 Número Parcelas: {proposta.numero_parcelas}")
            print(f"📅 Intervalo: {proposta.intervalo_parcelas} dias")
            
            if proposta.forma_pagamento != 'parcelado':
                print("\n⚠️ Proposta não é parcelada. Nada a fazer.")
                return False
            
            # Deletar parcelas existentes usando ORM
            ParcelaProposta.query.filter_by(proposta_id=proposta_id).delete()
            print(f"\n🗑️ Parcelas antigas deletadas.")
            
            # Calcular valores
            valor_total = Decimal(str(proposta.valor_total))
            entrada_perc = Decimal(str(proposta.entrada_percentual or 0))
            num_parcelas = proposta.numero_parcelas or 1
            intervalo = proposta.intervalo_parcelas or 30
            
            valor_entrada = (valor_total * entrada_perc / Decimal('100')).quantize(Decimal('0.01'))
            valor_restante = valor_total - valor_entrada
            valor_parcela = (valor_restante / num_parcelas).quantize(Decimal('0.01'))
            
            # Ajustar última parcela para fechar exato
            diferenca = valor_total - valor_entrada - (valor_parcela * num_parcelas)
            
            print(f"\n🧮 Cálculos:")
            print(f"  💵 Valor Entrada: R$ {valor_entrada}")
            print(f"  💰 Valor Restante: R$ {valor_restante}")
            print(f"  📝 Valor por Parcela: R$ {valor_parcela}")
            print(f"  ⚖️ Diferença (ajuste): R$ {diferenca}")
            
            # Criar parcelas usando ORM
            data_base = date.today()
            parcelas_criadas = []
            
            # Entrada (parcela 0)
            if valor_entrada > 0:
                parcela_entrada = ParcelaProposta(
                    proposta_id=proposta_id,
                    numero_parcela=0,
                    data_vencimento=data_base,
                    valor=float(valor_entrada),
                    ativo=True
                )
                db.session.add(parcela_entrada)
                parcelas_criadas.append(("Entrada", data_base, valor_entrada))
                print(f"\n✅ Entrada criada: R$ {valor_entrada} - Vencimento: {data_base}")
            
            # Parcelas normais (1 a N)
            for i in range(1, num_parcelas + 1):
                data_vencimento = data_base + timedelta(days=intervalo * i)
                
                # Ajustar última parcela com diferença
                valor_atual = valor_parcela
                if i == num_parcelas and diferenca != 0:
                    valor_atual = valor_parcela + diferenca
                
                parcela = ParcelaProposta(
                    proposta_id=proposta_id,
                    numero_parcela=i,
                    data_vencimento=data_vencimento,
                    valor=float(valor_atual),
                    ativo=True
                )
                db.session.add(parcela)
                parcelas_criadas.append((f"Parcela {i}", data_vencimento, valor_atual))
                print(f"✅ Parcela {i} criada: R$ {valor_atual} - Vencimento: {data_vencimento}")
            
            # Commit
            db.session.commit()
            print(f"\n✅ {len(parcelas_criadas)} parcelas salvas com sucesso!")
            
            # Verificar
            parcelas_bd = ParcelaProposta.query.filter_by(
                proposta_id=proposta_id,
                ativo=True
            ).order_by(ParcelaProposta.numero_parcela).all()
            
            print(f"\n🔍 Verificação - {len(parcelas_bd)} parcelas no banco:")
            total_verificacao = Decimal('0')
            for p in parcelas_bd:
                nome = "Entrada" if p.numero_parcela == 0 else f"Parcela {p.numero_parcela}"
                print(f"  {nome}: R$ {p.valor} - Vencimento: {p.data_vencimento}")
                total_verificacao += Decimal(str(p.valor))
            
            print(f"\n💰 Total das parcelas: R$ {total_verificacao}")
            print(f"💰 Total da proposta: R$ {valor_total}")
            print(f"⚖️ Diferença: R$ {total_verificacao - valor_total}")
            
            if abs(total_verificacao - valor_total) < Decimal('0.01'):
                print("\n✅ ✅ ✅ VALORES CONFEREM! PARCELAS GERADAS COM SUCESSO!")
                return True
            else:
                print("\n⚠️ ATENÇÃO: Valores não conferem!")
                return False
                
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ ERRO: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("\n🚀 Iniciando correção de parcelas...")
    sucesso = gerar_parcelas_proposta(15)
    
    if sucesso:
        print("\n✅ Script executado com sucesso!")
        print("📝 Próximo passo: Deletar OS 111 e gerar nova OS da Proposta 15")
    else:
        print("\n❌ Script falhou. Verifique os erros acima.")
    
    print("\n" + "="*80)
