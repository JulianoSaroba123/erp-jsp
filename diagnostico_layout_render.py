"""
Script para diagnosticar problema de salvamento de linhas_placas e colunas_placas no Render
"""
import os
import sys

# Configurar variáveis de ambiente para o Render
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', '')  # Será configurado no Render

from app.extensoes import db
from app.app import create_app
from app.energia_solar.catalogo_model import ProjetoSolar

def diagnosticar_projetos():
    """Diagnostica todos os projetos para verificar linhas e colunas"""
    print("=" * 80)
    print("DIAGNÓSTICO: Linhas e Colunas de Placas nos Projetos")
    print("=" * 80)
    
    projetos = ProjetoSolar.query.all()
    
    if not projetos:
        print("\n❌ Nenhum projeto encontrado no banco de dados!")
        return
    
    print(f"\n📊 Total de projetos: {len(projetos)}")
    print("\n" + "-" * 80)
    
    problemas = []
    
    for projeto in projetos:
        print(f"\n🔍 Projeto #{projeto.id} - {projeto.nome_cliente}")
        print(f"   Status: {projeto.status}")
        print(f"   Data criação: {projeto.data_criacao}")
        
        # Verificar campos de layout
        print(f"\n   📐 LAYOUT:")
        print(f"      Linhas de placas: {projeto.linhas_placas}")
        print(f"      Colunas de placas: {projeto.colunas_placas}")
        print(f"      Total calculado: {(projeto.linhas_placas or 0) * (projeto.colunas_placas or 0)} módulos")
        print(f"      Qtd placas cadastrada: {projeto.qtd_placas}")
        
        # Verificar se há problemas
        if projeto.linhas_placas is None or projeto.colunas_placas is None:
            problemas.append({
                'id': projeto.id,
                'nome': projeto.nome_cliente,
                'motivo': 'Linhas ou colunas NULL'
            })
            print("      ⚠️ PROBLEMA: Linhas ou colunas estão NULL!")
        elif projeto.linhas_placas == 0 or projeto.colunas_placas == 0:
            problemas.append({
                'id': projeto.id,
                'nome': projeto.nome_cliente,
                'motivo': 'Linhas ou colunas com valor 0'
            })
            print("      ⚠️ PROBLEMA: Linhas ou colunas com valor 0!")
        elif (projeto.linhas_placas * projeto.colunas_placas) != projeto.qtd_placas:
            problemas.append({
                'id': projeto.id,
                'nome': projeto.nome_cliente,
                'motivo': f'Inconsistência: {projeto.linhas_placas}x{projeto.colunas_placas}={projeto.linhas_placas * projeto.colunas_placas} != {projeto.qtd_placas} placas'
            })
            print(f"      ⚠️ PROBLEMA: Layout {projeto.linhas_placas}x{projeto.colunas_placas}={projeto.linhas_placas * projeto.colunas_placas} != {projeto.qtd_placas} placas cadastradas")
        else:
            print("      ✅ Layout OK!")
    
    print("\n" + "=" * 80)
    print(f"\n📋 RESUMO:")
    print(f"   Total de projetos: {len(projetos)}")
    print(f"   Projetos com problemas: {len(problemas)}")
    print(f"   Projetos OK: {len(projetos) - len(problemas)}")
    
    if problemas:
        print(f"\n⚠️ PROJETOS COM PROBLEMAS:")
        for p in problemas:
            print(f"   - Projeto #{p['id']} ({p['nome']}): {p['motivo']}")
    
    print("\n" + "=" * 80)


def corrigir_layout_padrao():
    """Corrige projetos com layout NULL ou 0, calculando melhor disposição"""
    print("\n" + "=" * 80)
    print("CORREÇÃO AUTOMÁTICA DE LAYOUTS")
    print("=" * 80)
    
    projetos = ProjetoSolar.query.filter(
        db.or_(
            ProjetoSolar.linhas_placas == None,
            ProjetoSolar.colunas_placas == None,
            ProjetoSolar.linhas_placas == 0,
            ProjetoSolar.colunas_placas == 0
        )
    ).all()
    
    if not projetos:
        print("\n✅ Nenhum projeto precisa de correção!")
        return
    
    print(f"\n🔧 {len(projetos)} projeto(s) precisam de correção.")
    
    for projeto in projetos:
        print(f"\n🔧 Corrigindo Projeto #{projeto.id} - {projeto.nome_cliente}")
        
        qtd_placas = projeto.qtd_placas or 10  # Default 10 se não tiver
        
        # Calcular melhor layout (mais quadrado possível)
        import math
        
        # Tentar encontrar fatores que resultem em layout mais quadrado
        melhor_linhas = 1
        melhor_colunas = qtd_placas
        menor_diferenca = abs(qtd_placas - 1)
        
        # Buscar divisores de qtd_placas
        for linhas in range(1, int(math.sqrt(qtd_placas)) + 1):
            if qtd_placas % linhas == 0:
                colunas = qtd_placas // linhas
                diferenca = abs(colunas - linhas)
                
                if diferenca < menor_diferenca:
                    melhor_linhas = linhas
                    melhor_colunas = colunas
                    menor_diferenca = diferenca
        
        # Aplicar correção
        projeto.linhas_placas = melhor_linhas
        projeto.colunas_placas = melhor_colunas
        
        print(f"   Layout definido: {melhor_linhas} linhas × {melhor_colunas} colunas = {qtd_placas} módulos")
    
    try:
        db.session.commit()
        print(f"\n✅ {len(projetos)} projeto(s) corrigido(s) com sucesso!")
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Erro ao salvar correções: {str(e)}")


def menu():
    """Menu interativo"""
    print("\n" + "=" * 80)
    print("DIAGNÓSTICO E CORREÇÃO DE LAYOUT DE PROJETOS")
    print("=" * 80)
    print("\n1 - Diagnosticar projetos (apenas leitura)")
    print("2 - Corrigir layouts com problemas (ALTERA BANCO!)")
    print("3 - Sair")
    
    escolha = input("\nEscolha uma opção: ").strip()
    
    if escolha == '1':
        diagnosticar_projetos()
        menu()
    elif escolha == '2':
        confirma = input("\n⚠️ Isso vai ALTERAR o banco de dados! Confirma? (s/N): ").strip().lower()
        if confirma == 's':
            corrigir_layout_padrao()
            diagnosticar_projetos()  # Mostrar resultado
        else:
            print("\n❌ Operação cancelada.")
        menu()
    elif escolha == '3':
        print("\n👋 Saindo...")
        sys.exit(0)
    else:
        print("\n❌ Opção inválida!")
        menu()


if __name__ == '__main__':
    print("\n🚀 Iniciando aplicação...")
    app = create_app()
    
    with app.app_context():
        menu()
