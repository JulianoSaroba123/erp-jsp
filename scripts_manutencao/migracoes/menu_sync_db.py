"""
Menu de Sincronização de Banco de Dados
Facilita operações entre Local (SQLite) e Render (PostgreSQL)
"""

import os
import sys

def mostrar_menu():
    print("\n" + "="*60)
    print("🔄 SINCRONIZAÇÃO DE BANCO DE DADOS")
    print("="*60)
    print("\n1. 📊 Verificar estrutura dos bancos (comparar)")
    print("2. ⬇️  Sincronizar Render → Local (puxar dados)")
    print("3. ℹ️  Mostrar informações de conexão")
    print("0. ❌ Sair")
    print("\n" + "="*60)

def verificar_estrutura():
    """Executa verificação de estrutura"""
    print("\n🔍 Verificando estrutura dos bancos...\n")
    os.system('python verificar_estrutura_bancos.py')

def sincronizar_render_local():
    """Sincroniza dados do Render para Local"""
    print("\n⚠️  ATENÇÃO: Esta operação irá SOBRESCREVER os dados locais!")
    print("Um backup será criado antes da sincronização.\n")
    
    resposta = input("Deseja continuar? (s/N): ").strip().lower()
    
    if resposta == 's':
        print("\n⬇️  Sincronizando Render → Local...\n")
        os.system('python sync_render_to_local.py')
    else:
        print("\n❌ Sincronização cancelada.")

def mostrar_info():
    """Mostra informações de conexão"""
    print("\n" + "="*60)
    print("ℹ️  INFORMAÇÕES DE CONEXÃO")
    print("="*60 + "\n")
    
    # Local
    print("💾 BANCO LOCAL (SQLite):")
    if os.path.exists('database/database.db'):
        tamanho = os.path.getsize('database/database.db') / 1024 / 1024
        print(f"   Arquivo: database/database.db")
        print(f"   Tamanho: {tamanho:.2f} MB")
        print(f"   ✅ Disponível")
    else:
        print(f"   ❌ Não encontrado")
    
    print()
    
    # Render
    print("📡 BANCO RENDER (PostgreSQL):")
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        # Oculta senha
        if '@' in db_url:
            antes_senha = db_url.split('://')[0] + '://' + db_url.split('://')[1].split(':')[0]
            depois_senha = '@' + db_url.split('@')[1]
            print(f"   URL: {antes_senha}:****{depois_senha}")
            print(f"   ✅ Configurado")
        else:
            print(f"   URL: {db_url[:50]}...")
            print(f"   ✅ Configurado")
    else:
        print(f"   ❌ DATABASE_URL não configurada")
        print(f"   Configure no arquivo .env")
    
    print("\n" + "="*60)

def main():
    """Menu principal"""
    while True:
        mostrar_menu()
        escolha = input("\nEscolha uma opção: ").strip()
        
        if escolha == '1':
            verificar_estrutura()
        elif escolha == '2':
            sincronizar_render_local()
        elif escolha == '3':
            mostrar_info()
        elif escolha == '0':
            print("\n👋 Até logo!")
            break
        else:
            print("\n❌ Opção inválida! Tente novamente.")
        
        if escolha != '0':
            input("\n📌 Pressione ENTER para continuar...")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Até logo!")
        sys.exit(0)
