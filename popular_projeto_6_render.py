"""
🔧 POPULAR PROJETO #6 COM KIT/PLACA/INVERSOR
============================================
Script para preencher os campos kit_id, placa_id, inversor_id
do projeto #6 no banco do Render.

PROBLEMA:
- Colunas existem no banco (migração funcionou)
- Mas projeto #6 tem valores NULL nesses campos
- JavaScript não consegue carregar kit porque projeto.kit é None

SOLUÇÃO:
- Detectar qual placa/inversor está sendo usado
- Buscar kit compatível
- Atualizar projeto #6 com os IDs corretos
"""

from app import create_app
from app.extensoes import db
from sqlalchemy import text
import sys


def listar_projeto_6():
    """Lista dados atuais do projeto #6"""
    print("\n🔍 DADOS ATUAIS DO PROJETO #6")
    print("=" * 60)
    
    query = text("""
        SELECT 
            id, nome_cliente, numero_paineis, numero_inversores,
            kit_id, placa_id, inversor_id,
            placa_modelo, inversor_modelo
        FROM calculo_energia_solar 
        WHERE id = 6
    """)
    
    with db.engine.connect() as conn:
        result = conn.execute(query).fetchone()
        
        if not result:
            print("❌ Projeto #6 não encontrado!")
            return None
        
        print(f"📊 Cliente: {result[1]}")
        print(f"📦 Número de painéis: {result[2]}")
        print(f"🔌 Número de inversores: {result[3]}")
        print(f"\n🆔 IDs atuais:")
        print(f"   kit_id: {result[4] or 'NULL ❌'}")
        print(f"   placa_id: {result[5] or 'NULL ❌'}")
        print(f"   inversor_id: {result[6] or 'NULL ❌'}")
        print(f"\n📝 Nomes salvos:")
        print(f"   placa_modelo: {result[7] or 'NULL'}")
        print(f"   inversor_modelo: {result[8] or 'NULL'}")
        
        return result


def buscar_placa_compativel(modelo_parcial=None):
    """Busca placa compatível no catálogo"""
    print("\n🔍 BUSCANDO PLACA NO CATÁLOGO")
    print("=" * 60)
    
    # Busca placa por modelo parcial ou a primeira disponível
    if modelo_parcial:
        query = text("""
            SELECT id, modelo, fabricante, potencia, preco_venda 
            FROM placa_solar 
            WHERE LOWER(modelo) LIKE :modelo
            LIMIT 1
        """)
        with db.engine.connect() as conn:
            result = conn.execute(query, {"modelo": f"%{modelo_parcial.lower()}%"}).fetchone()
    else:
        query = text("""
            SELECT id, modelo, fabricante, potencia, preco_venda 
            FROM placa_solar 
            ORDER BY id 
            LIMIT 1
        """)
        with db.engine.connect() as conn:
            result = conn.execute(query).fetchone()
    
    if result:
        print(f"✅ Placa encontrada:")
        print(f"   ID: {result[0]}")
        print(f"   Modelo: {result[1]}")
        print(f"   Fabricante: {result[2]}")
        print(f"   Potência: {result[3]}W")
        print(f"   Preço: R$ {result[4] or 0:.2f}")
        return result[0]
    else:
        print("❌ Nenhuma placa encontrada no catálogo")
        return None


def buscar_inversor_compativel(modelo_parcial=None):
    """Busca inversor compatível no catálogo"""
    print("\n🔍 BUSCANDO INVERSOR NO CATÁLOGO")
    print("=" * 60)
    
    # Busca inversor por modelo parcial ou o primeiro disponível
    if modelo_parcial:
        query = text("""
            SELECT id, modelo, fabricante, potencia, preco_venda 
            FROM inversor_solar 
            WHERE LOWER(modelo) LIKE :modelo
            LIMIT 1
        """)
        with db.engine.connect() as conn:
            result = conn.execute(query, {"modelo": f"%{modelo_parcial.lower()}%"}).fetchone()
    else:
        query = text("""
            SELECT id, modelo, fabricante, potencia, preco_venda 
            FROM inversor_solar 
            ORDER BY id 
            LIMIT 1
        """)
        with db.engine.connect() as conn:
            result = conn.execute(query).fetchone()
    
    if result:
        print(f"✅ Inversor encontrado:")
        print(f"   ID: {result[0]}")
        print(f"   Modelo: {result[1]}")
        print(f"   Fabricante: {result[2]}")
        print(f"   Potência: {result[3]}kW")
        print(f"   Preço: R$ {result[4] or 0:.2f}")
        return result[0]
    else:
        print("❌ Nenhum inversor encontrado no catálogo")
        return None


def buscar_kit_compativel(placa_id, inversor_id):
    """Busca kit que usa a placa e inversor especificados"""
    print("\n🔍 BUSCANDO KIT COMPATÍVEL")
    print("=" * 60)
    
    query = text("""
        SELECT id, fabricante, descricao, potencia_kwp, preco 
        FROM kit_solar 
        WHERE placa_id = :placa_id AND inversor_id = :inversor_id
        LIMIT 1
    """)
    
    with db.engine.connect() as conn:
        result = conn.execute(query, {"placa_id": placa_id, "inversor_id": inversor_id}).fetchone()
    
    if result:
        print(f"✅ Kit encontrado:")
        print(f"   ID: {result[0]}")
        print(f"   Fabricante: {result[1]}")
        print(f"   Descrição: {result[2]}")
        print(f"   Potência: {result[3]} kWp")
        print(f"   Preço: R$ {result[4] or 0:.2f}")
        return result[0]
    else:
        print("⚠️ Nenhum kit encontrado com essa combinação")
        print("   (Kit é opcional, pode continuar só com placa/inversor)")
        return None


def atualizar_projeto_6(placa_id, inversor_id, kit_id=None):
    """Atualiza projeto #6 com os IDs"""
    print("\n✍️ ATUALIZANDO PROJETO #6")
    print("=" * 60)
    
    query = text("""
        UPDATE calculo_energia_solar 
        SET placa_id = :placa_id,
            inversor_id = :inversor_id,
            kit_id = :kit_id
        WHERE id = 6
    """)
    
    try:
        with db.engine.connect() as conn:
            conn.execute(query, {
                "placa_id": placa_id,
                "inversor_id": inversor_id,
                "kit_id": kit_id
            })
            conn.commit()
        
        print("✅ Projeto #6 atualizado com sucesso!")
        print(f"   placa_id: {placa_id}")
        print(f"   inversor_id: {inversor_id}")
        print(f"   kit_id: {kit_id or 'NULL (sem kit)'}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao atualizar: {e}")
        return False


def main():
    """Função principal"""
    print("\n" + "=" * 60)
    print("🔧 POPULAR PROJETO #6 COM EQUIPAMENTOS")
    print("=" * 60)
    
    try:
        app = create_app()
        
        with app.app_context():
            # 1. Listar dados atuais
            projeto = listar_projeto_6()
            if not projeto:
                return 1
            
            placa_modelo = projeto[7]
            inversor_modelo = projeto[8]
            
            # 2. Buscar placa
            placa_id = buscar_placa_compativel(placa_modelo)
            if not placa_id:
                print("\n❌ Não foi possível encontrar placa compatível")
                return 1
            
            # 3. Buscar inversor
            inversor_id = buscar_inversor_compativel(inversor_modelo)
            if not inversor_id:
                print("\n❌ Não foi possível encontrar inversor compatível")
                return 1
            
            # 4. Buscar kit (opcional)
            kit_id = buscar_kit_compativel(placa_id, inversor_id)
            
            # 5. Atualizar projeto
            sucesso = atualizar_projeto_6(placa_id, inversor_id, kit_id)
            
            if sucesso:
                # 6. Verificar resultado
                print("\n" + "=" * 60)
                print("✅ ATUALIZAÇÃO CONCLUÍDA - VERIFICANDO RESULTADO")
                print("=" * 60)
                listar_projeto_6()
                
                print("\n🎉 SUCESSO!")
                print("=" * 60)
                print("Agora teste no navegador:")
                print("1. Ctrl+F5 para limpar cache")
                print("2. Abrir modal 'Editar Orçamento'")
                print("3. Kit/Placa/Inversor devem aparecer!")
                
                return 0
            else:
                return 1
        
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
