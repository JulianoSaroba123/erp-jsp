#!/usr/bin/env python3
"""
Teste direto de acesso aos dados da OS0351
"""

import sys
sys.path.append('.')

def testar_acesso_os():
    """Testar acesso direto à OS através do Flask"""
    
    try:
        from aplicacao import create_app, db
        from aplicacao.ordem_servico.os_model import OrdemServico
        
        app = create_app()
        
        with app.app_context():
            print("🔍 TESTANDO ACESSO À OS0351...")
            
            # 1. Buscar por ID
            print("\n1. Buscando por ID 2...")
            os_id2 = OrdemServico.query.get(2)
            if os_id2:
                print(f"✅ Encontrada: {os_id2.codigo} - {os_id2.solicitante}")
            else:
                print("❌ OS com ID 2 não encontrada")
            
            # 2. Buscar por código
            print("\n2. Buscando por código OS0351...")
            os_codigo = OrdemServico.query.filter_by(codigo='OS0351').first()
            if os_codigo:
                print(f"✅ Encontrada: ID {os_codigo.id} - {os_codigo.solicitante}")
            else:
                print("❌ OS0351 não encontrada")
            
            # 3. Listar todas as ordens
            print("\n3. Listando todas as ordens...")
            todas_os = OrdemServico.query.all()
            print(f"Total de ordens: {len(todas_os)}")
            
            for os in todas_os:
                print(f"   ID {os.id}: {os.codigo} - {os.solicitante} - {os.status}")
            
            # 4. Teste de atualização
            print("\n4. Testando atualização...")
            if os_id2:
                print(f"Valor atual do solicitante: '{os_id2.solicitante}'")
                
                # Salvar valor original
                valor_original = os_id2.solicitante
                
                # Atualizar
                novo_valor = f"TESTE {datetime.now().strftime('%H:%M:%S')}"
                os_id2.solicitante = novo_valor
                
                print(f"Atualizando para: '{novo_valor}'")
                
                try:
                    db.session.commit()
                    print("✅ Commit realizado com sucesso")
                    
                    # Verificar se foi salvo
                    os_verificacao = OrdemServico.query.get(2)
                    print(f"Valor após commit: '{os_verificacao.solicitante}'")
                    
                    if os_verificacao.solicitante == novo_valor:
                        print("✅ Atualização confirmada!")
                    else:
                        print("❌ Atualização não foi persistida")
                    
                    # Restaurar valor original
                    os_verificacao.solicitante = valor_original
                    db.session.commit()
                    print("✅ Valor original restaurado")
                    
                except Exception as e:
                    print(f"❌ Erro no commit: {e}")
                    db.session.rollback()
            
            return True
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    from datetime import datetime
    testar_acesso_os()