"""
Script de teste para geração de proposta Word
Demonstra como o sistema substitui as variáveis
"""

import sys
import os
from pathlib import Path

# Adicionar app ao path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app
from app.energia_solar.catalogo_model import ProjetoSolar
from app.energia_solar.proposta_word_service import gerar_docx_proposta, montar_contexto_proposta
from app.cliente.cliente_model import Cliente

def testar_geracao():
    """Testa geração de proposta Word com dados reais"""
    
    print("="*80)
    print("🧪 TESTE DE GERAÇÃO DE PROPOSTA WORD")
    print("="*80)
    
    app = create_app()
    
    with app.app_context():
        # Buscar primeiro projeto disponível
        print("\n🔍 Buscando projetos solares...")
        projetos = ProjetoSolar.query.limit(5).all()
        
        if not projetos:
            print("\n❌ Nenhum projeto encontrado no banco de dados!")
            print("Crie um projeto primeiro no sistema.")
            return
        
        print(f"\n✅ Encontrados {len(projetos)} projetos:")
        for i, p in enumerate(projetos, 1):
            cliente_nome = "Sem cliente"
            if p.cliente_id:
                cliente = Cliente.query.get(p.cliente_id)
                if cliente:
                    cliente_nome = getattr(cliente, 'nome', None) or getattr(cliente, 'razao_social', None) or cliente.nome_fantasia or "Cliente"
            print(f"  {i}. Projeto #{p.id} - {cliente_nome} - {p.potencia_kwp or 0} kWp")
        
        # Pegar primeiro projeto
        projeto = projetos[0]
        print(f"\n📋 Usando Projeto #{projeto.id} para teste")
        
        # Montar contexto (ver dados que serão substituídos)
        print("\n🔧 Montando contexto com dados do projeto...")
        contexto = montar_contexto_proposta(projeto)
        
        print("\n" + "="*80)
        print("📊 PREVIEW DOS DADOS QUE SERÃO SUBSTITUÍDOS:")
        print("="*80)
        
        # Mostrar alguns dados importantes
        dados_importantes = [
            'NOME_CLIENTE', 'CPF_CNPJ_CLIENTE', 'CIDADE', 'ESTADO',
            'NUMERO_PROJETO', 'DATA_PROPOSTA', 'VALIDADE_PROPOSTA',
            'POTENCIA_SISTEMA', 'QTD_MODULOS', 'MODELO_MODULO',
            'VALOR_INVESTIMENTO', 'ECONOMIA_MENSAL', 'PAYBACK', 'ROI_25_ANOS'
        ]
        
        for chave in dados_importantes:
            if chave in contexto:
                valor = contexto[chave]
                variavel = "{{" + chave + "}}"
                print(f"  {variavel}:".ljust(35) + f" → {valor}")
        
        print(f"\n📝 Total de variáveis: {len(contexto)}")
        
        # Caminhos
        template_path = Path("app/energia_solar/templates_word/proposta_solar_modelo.docx")
        output_dir = Path("app/energia_solar/documentos_gerados")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"TESTE_proposta_projeto_{projeto.id}.docx"
        
        # Verificar template
        print(f"\n📁 Verificando template...")
        if not template_path.exists():
            print(f"❌ Template não encontrado: {template_path}")
            print(f"\nPara corrigir, execute:")
            print(f'Copy-Item "E:\\Modelos de Documentos_Solar\\proposta_solar_COMPLETA_40_variaveis.docx" "{template_path}"')
            return
        
        print(f"✅ Template encontrado: {template_path}")
        
        # Gerar documento
        print(f"\n🔧 Gerando documento Word...")
        print(f"   Template: {template_path}")
        print(f"   Saída: {output_path}")
        
        try:
            gerar_docx_proposta(projeto, str(template_path), str(output_path))
            print(f"\n✅ DOCUMENTO GERADO COM SUCESSO!")
            print(f"\n📄 Arquivo: {output_path}")
            print(f"💾 Tamanho: {output_path.stat().st_size / 1024:.1f} KB")
            
            print("\n" + "="*80)
            print("✅ TESTE CONCLUÍDO COM SUCESSO!")
            print("="*80)
            print(f"\n📋 PRÓXIMO PASSO:")
            print(f"   1. Abra o arquivo: {output_path}")
            print(f"   2. Verifique que as variáveis {{{{NOME}}}} foram SUBSTITUÍDAS por dados reais")
            print(f"   3. Compare com o template original que tem as variáveis")
            print(f"\n💡 DIFERENÇA:")
            print(f"   • TEMPLATE (templates_word/): tem {{{{NOME_CLIENTE}}}}")
            print(f"   • GERADO (documentos_gerados/): tem 'João da Silva' (dado real)")
            
        except Exception as e:
            print(f"\n❌ ERRO ao gerar documento: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    testar_geracao()
