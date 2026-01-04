"""
Teste rápido para verificar se o layout está sendo salvo corretamente
"""
import os
from app.app import create_app
from app.extensoes import db
from app.energia_solar.catalogo_model import ProjetoSolar

def teste_layout():
    """Testa se o layout está sendo salvo e recuperado corretamente"""
    print("\n" + "=" * 80)
    print("TESTE: Salvamento e Recuperação de Layout de Placas")
    print("=" * 80)
    
    app = create_app()
    
    with app.app_context():
        # Buscar último projeto
        ultimo_projeto = ProjetoSolar.query.order_by(ProjetoSolar.id.desc()).first()
        
        if not ultimo_projeto:
            print("\n❌ Nenhum projeto encontrado!")
            print("💡 Crie um projeto primeiro pelo sistema web.")
            return
        
        print(f"\n📋 Último Projeto: #{ultimo_projeto.id} - {ultimo_projeto.nome_cliente}")
        print(f"   Data criação: {ultimo_projeto.data_criacao}")
        
        print(f"\n📐 LAYOUT SALVO NO BANCO:")
        print(f"   Linhas: {ultimo_projeto.linhas_placas}")
        print(f"   Colunas: {ultimo_projeto.colunas_placas}")
        
        if ultimo_projeto.linhas_placas and ultimo_projeto.colunas_placas:
            total = ultimo_projeto.linhas_placas * ultimo_projeto.colunas_placas
            print(f"   Total calculado: {ultimo_projeto.linhas_placas} × {ultimo_projeto.colunas_placas} = {total} módulos")
            print(f"   Qtd placas cadastrada: {ultimo_projeto.qtd_placas}")
            
            if total == ultimo_projeto.qtd_placas:
                print("   ✅ Layout consistente com quantidade de placas!")
            else:
                print(f"   ⚠️ INCONSISTÊNCIA: {total} módulos calculados ≠ {ultimo_projeto.qtd_placas} placas cadastradas")
        else:
            print("   ❌ Linhas ou colunas são NULL!")
            print("   💡 Execute o script de diagnóstico para corrigir:")
            print("      python diagnostico_layout_render.py")
        
        # Teste: Criar projeto de teste
        print(f"\n🧪 TESTE: Criando projeto com layout 1×6...")
        
        projeto_teste = ProjetoSolar(
            nome_cliente="TESTE - Layout 1x6",
            cidade="São Paulo",
            estado="SP",
            consumo_kwh_mes=500,
            potencia_kwp=3.3,
            qtd_placas=6,
            qtd_inversores=1,
            linhas_placas=1,
            colunas_placas=6,
            orientacao="Norte",
            inclinacao=15,
            status="rascunho"
        )
        
        try:
            db.session.add(projeto_teste)
            db.session.commit()
            
            print(f"✅ Projeto teste criado com ID #{projeto_teste.id}")
            print(f"   Layout salvo: {projeto_teste.linhas_placas}×{projeto_teste.colunas_placas}")
            
            # Verificar leitura
            print(f"\n🔍 Verificando leitura do banco...")
            projeto_lido = ProjetoSolar.query.get(projeto_teste.id)
            
            if projeto_lido.linhas_placas == 1 and projeto_lido.colunas_placas == 6:
                print(f"✅ SUCESSO! Layout lido: {projeto_lido.linhas_placas}×{projeto_lido.colunas_placas}")
            else:
                print(f"❌ ERRO! Layout lido: {projeto_lido.linhas_placas}×{projeto_lido.colunas_placas}")
            
            # Limpar teste
            print(f"\n🗑️ Removendo projeto teste...")
            db.session.delete(projeto_teste)
            db.session.commit()
            print("✅ Projeto teste removido")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro no teste: {str(e)}")
        
        print("\n" + "=" * 80)
        print("FIM DO TESTE")
        print("=" * 80)
        print("\n💡 Próximos passos:")
        print("   1. Se houver projetos com layout NULL, execute: python diagnostico_layout_render.py")
        print("   2. Teste criando um novo projeto pelo wizard")
        print("   3. Verifique se a visualização mostra o layout correto")
        print("\n")


if __name__ == '__main__':
    teste_layout()
